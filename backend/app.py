import requests
import firebase_admin
import os
import cv2

# 로컬 모듈 임포트
from firebase_admin import credentials, db
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 로컬 엔진과 유틸리티 모듈 임포트
from workers.vibe_clipper.src.engine import VibeClipperEngine
from workers.vibe_clipper.src.youtube import YouTubeStreamer
from workers.vibe_clipper.src.video import VideoProcessor
from dotenv import load_dotenv

# 스마트 필터, 파일 관리, 그리고 🧠 중앙 AI 서비스(Gemma) 임포트
from workers.vibe_clipper.src.time_manager import TimeManager
from workers.vibe_clipper.src.deduplicator import ImageDeduplicator
from workers.vibe_clipper.src.file_manager import FileManager
from core.ai_service import AIService  # 🌟 신규 추가: 세맨틱 분석용

# ==========================================
# 1. 환경 변수(.env) 로드 및 보안 설정 적용
# ==========================================
load_dotenv() 

DATABASE_URL = os.getenv("FIREBASE_DB_URL")
API_KEY_SECRET = os.getenv("VIBE_API_KEY")

# ==========================================
# 2. Firebase 초기화
# ==========================================
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-adminsdk.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': DATABASE_URL 
    })

app = FastAPI(title="Vibe-Clipper API")

# ==========================================
# 3. FastAPI 미들웨어 및 정적 파일 설정
# ==========================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("dataset"):
    os.makedirs("dataset")
app.mount("/dataset", StaticFiles(directory="dataset"), name="dataset")

# ==========================================
# 4. 전역 서비스 객체 로드
# ==========================================
engine = VibeClipperEngine()
yt_streamer = YouTubeStreamer()
ai_service = AIService() # 🧠 Gemma 뇌 이식

# 중복 제거기 설정
deduplicator = ImageDeduplicator(threshold=0.7, memory_size=10)

class CropRequest(BaseModel):
    youtube_url: str
    target_label: str = "white car"
    max_crops: int = 50
    start_time: str = "00:00:00"
    end_time: str = "00:05:00"

# ==========================================
# 6. 메인 API 엔드포인트
# ==========================================
@app.post("/api/mine")
async def mine_video(
    request: CropRequest, 
    x_api_key: str = Header(None)  
):
    # 보안 로직
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="API Key가 틀렸거나 없습니다! 접근 금지 🚫")

    print(f"🌐 웹 요청 수신: {request.target_label}")
    
    # 🌟 [수정 포인트 1] 루프 밖에서 딱 한 번만 번역합니다! (Gemma 과로 방지 및 이전 JSON 코드 제거)
    parsed_data = ai_service.parse_semantic(request.target_label)
    main_target = parsed_data.get("main_target", "object")
    
    print(f"🧠 [Gemma 전략] JSON 분석 완료: {parsed_data}")
    
    # 파일명은 main_target 기반으로 생성
    safe_label = main_target.replace(" ", "_").replace("/", "")

    # 유튜브 스트림 주소 획득
    stream_url = yt_streamer.get_direct_url(request.youtube_url)
    if not stream_url:
        return {"status": "error", "message": "유튜브 스트림을 가져올 수 없습니다."}

    # 매니저 초기화
    time_mgr = TimeManager(request.start_time, request.end_time)
    file_mgr = FileManager("dataset")
    file_mgr.clean_dataset_folder() # 기존 데이터 청소
    
    video_proc = VideoProcessor(target_fps=1)
    total_crops = 0
    saved_files = []

    print(f"🎬 {request.start_time} 부터 수확을 시작합니다...")

    # [Step 2] 파이프라인 가동
    for time_sec, frame in video_proc.extract_frames_stream(stream_url):
        
        if not time_mgr.is_time_to_start(time_sec):
            continue 
            
        if time_mgr.is_time_to_stop(time_sec):
            print("🛑 [수확 종료] 설정한 종료 시간에 도달했습니다.")
            break 
            
        # 🌟 [수정 포인트 2] 여기서는 이미 번역된 target_prompt만 넘겨서 엔진 연산에만 집중!
        cropped_images = engine.crop_target(
            frame, 
            parsed_json=parsed_data  
        )
        
        for crop_img in cropped_images:
            # 중복 제거 활성화 시 아래 주석 해제
            # if deduplicator.is_duplicate(crop_img): continue

            filename = f"dataset/gold_{safe_label}_{total_crops}.png"
            cv2.imwrite(filename, crop_img)
            saved_files.append(filename)
            total_crops += 1
            
            # 최대 수확량 도달 시 처리
            if total_crops >= request.max_crops:
                # engine.close_debug_video() # (사용하지 않는 더미 함수이므로 제거해도 무방합니다)
                zip_filename = file_mgr.create_zip_and_cleanup()
                
                return {
                    "status": "success", 
                    "message": f"최대 수확량({request.max_crops}장) 도달! 고순도 에셋 압축 완료",
                    "files": saved_files,
                    "zip_url": f"dataset/{zip_filename}"
                }

    # 영상이 정상적으로 종료되었을 때
    if total_crops > 0:
        zip_filename = file_mgr.create_zip_and_cleanup()
        zip_url = f"dataset/{zip_filename}"
    else:
        zip_url = None

    return {
        "status": "success", 
        "message": f"작업 완료 (총 {total_crops}장 수확)", 
        "files": saved_files,
        "zip_url": zip_url
    }