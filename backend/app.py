import requests
import firebase_admin
import os
import cv2
import asyncio 
import glob # 🌟 신규 추가: 파일 패턴 검색용

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

# 스마트 필터, 파일 관리, 그리고 🧠 중앙 AI 서비스 임포트
from workers.vibe_clipper.src.time_manager import TimeManager
from workers.vibe_clipper.src.deduplicator import ImageDeduplicator
from workers.vibe_clipper.src.file_manager import FileManager
from core.ai_service import AIService 

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
ai_service = AIService() 

# 🌟 [복구 완료] 중복 제거기 설정 유지
deduplicator = ImageDeduplicator(threshold=0.7, memory_size=10)

# 🌟 [핵심 방어막] GPU 연산 방에 1명씩만 들여보내는 문지기 생성
gpu_semaphore = asyncio.Semaphore(1)

class CropRequest(BaseModel):
    youtube_url: str
    target_label: str = "white car"
    max_crops: int = 50
    start_time: str = "00:00:00"
    end_time: str = "00:05:00"

# 🌟 [신규] 삭제 요청 모델
class TrackDeleteRequest(BaseModel):
    track_id: int

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

    print(f"\n🌐 웹 요청 수신: {request.target_label}")
    print("🚦 GPU 대기열에 진입했습니다. 앞선 작업이 있다면 대기합니다...")

    async with gpu_semaphore:
        print(f"🚀 내 차례입니다! '{request.target_label}' 작업 시작!")
        
        # 🌟 [신규] 새 영상 시작 시 엔진의 트래커(기억) 초기화
        engine.reset_tracker()
        
        # 1. Gemini 파싱
        parsed_data = ai_service.parse_semantic(request.target_label)
        main_target = parsed_data.get("main_target", "object")
        
        print(f"🧠 [Gemini 전략] JSON 분석 완료: {parsed_data}")
        
        safe_label = main_target.replace(" ", "_").replace("/", "")

        # 2. 유튜브 스트림 획득
        stream_url = yt_streamer.get_direct_url(request.youtube_url)
        if not stream_url:
            return {"status": "error", "message": "유튜브 스트림을 가져올 수 없습니다."}

        # 3. 매니저 초기화 및 데이터 청소
        time_mgr = TimeManager(request.start_time, request.end_time)
        file_mgr = FileManager("dataset")
        
        # 🌟 [버그 수정] 시작할 때 단 한 번만 폴더를 청소합니다! (과잉 청소 방지)
        file_mgr.clean_dataset_folder() 
        
        video_proc = VideoProcessor(target_fps=1)
        total_crops = 0
        saved_files = []

        print(f"🎬 {request.start_time} 부터 수확을 시작합니다...")

        # 4. 프레임 단위 처리
        for time_sec, frame in video_proc.extract_frames_stream(stream_url):
            
            if not time_mgr.is_time_to_start(time_sec):
                continue 
                
            if time_mgr.is_time_to_stop(time_sec):
                print("🛑 [수확 종료] 설정한 종료 시간에 도달했습니다.")
                break 
                
            # 🌟 엔진 연산 (딕셔너리 리스트 반환: [{"image": img, "track_id": id}])
            results = engine.crop_target(
                frame, 
                parsed_json=parsed_data  
            )
            
            for res in results:
                crop_img = res["image"]
                tid = res["track_id"]
                
                # 🌟 [사용자 요청] 일단 많은 데이터를 모으기 위해 중복 제거 끄기
                # if deduplicator.is_duplicate(crop_img):
                #    continue
                
                # 🌟 [파일명 규칙] 중간에 _tr{ID}_ 삽입
                filename = f"dataset/gold_{safe_label}_tr{tid}_{total_crops}.png"
                cv2.imwrite(filename, crop_img)
                saved_files.append(filename)
                total_crops += 1
                
                # 최대 수확량 도달
                if total_crops >= request.max_crops:
                    # 🌟 [신규] 원본(original) 용 ZIP 파일 생성 (기존 create_zip_and_cleanup 대체)
                    zip_filename = file_mgr.create_zip(suffix="original")
                    print("✅ 작업 완료 및 대기열 양보") 
                    return {
                        "status": "success", 
                        "message": f"최대 수확량({request.max_crops}장) 도달! 원본 에셋 압축 완료",
                        "files": saved_files,
                        "zip_url": f"dataset/{zip_filename}"
                    }

        # 영상 종료 시점 처리
        if total_crops > 0:
            # 🌟 [신규] 원본(original) 용 ZIP 파일 생성
            zip_filename = file_mgr.create_zip(suffix="original")
            zip_url = f"dataset/{zip_filename}"
        else:
            zip_url = None

        print("✅ 작업 완료 및 대기열 양보") 
        return {
            "status": "success", 
            "message": f"작업 완료 (총 {total_crops}장 수확)", 
            "files": saved_files,
            "zip_url": zip_url
        }

# ==========================================
# 7. [신규] 트랙 일괄 삭제 API
# ==========================================
@app.post("/api/delete-track")
async def delete_track(request: TrackDeleteRequest, x_api_key: str = Header(None)):
    # 1. 보안 인증 (기존 로직 유지)
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="API Key 인증 실패")

    # 2. 삭제 대상 검색 (패턴 매칭)
    # 패턴 예: dataset/gold_*_tr101_*.png
    pattern = os.path.join("dataset", f"gold_*_tr{request.track_id}_*.png")
    target_files = glob.glob(pattern)
    
    deleted_count = 0
    for f in target_files:
        try:
            os.remove(f)
            deleted_count += 1
        except Exception as e:
            print(f"❌ 파일 삭제 오류 ({f}): {e}")

    # 3. 상세 로그 출력 (사용자 선호 스타일 보존)
    print(f"🧹 [일괄 삭제] Track ID {request.track_id}와 관련된 파일 {deleted_count}개 삭제 완료")
    
    # 4. 🌟 [Code B 적용] 필터링된 결과만 따로 압축
    # 이제 create_zip_and_cleanup 대신 suffix를 받는 create_zip을 사용합니다.
    file_mgr = FileManager("dataset")
    filtered_zip = file_mgr.create_zip(suffix="filtered")

    # 5. 프론트엔드 UI 갱신을 위해 남은 파일 리스트 재스캔 (경로 정규화 포함)
    remaining_files = [f.replace("\\", "/") for f in glob.glob(os.path.join("dataset", "gold_*.png"))]

    # 6. 결과 반환 (프론트엔드 page.tsx와 약속된 키값 사용)
    return {
        "status": "success", 
        "message": f"Track {request.track_id} 삭제 완료 ({deleted_count}개 파일 지워짐)",
        "files": remaining_files, 
        "filtered_zip_url": f"dataset/{filtered_zip}" # 🌟 필터링된 파일 주소
    }