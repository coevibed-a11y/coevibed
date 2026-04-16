import requests
import firebase_admin
import os
import cv2
import asyncio 
import glob # 🌟 신규 추가: 파일 패턴 검색용
import logging  # 🌟 3번: 로깅 도입

# 로컬 모듈 임포트
from firebase_admin import credentials, db
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

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

# 🌟 3번: 로깅 설정 (콘솔 출력 및 파일 저장 가능)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("vibe-clipper")

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

# 🌟 [수정] 전역 deduplicator는 삭제했습니다. (동시성 및 메모리 초기화 버그 원인)

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
    
# 🌟 챗봇 요청 형식을 위한 Pydantic 모델
class ChatMessage(BaseModel):
    role: str # "user" 또는 "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    current_page: str = "vibe_clipper"
    has_data: bool = False
    history: Optional[List[ChatMessage]] = []

# ==========================================
# 6. 메인 API 엔드포인트
# ==========================================
@app.post("/api/mine")
async def mine_video(request: CropRequest, x_api_key: str = Header(None)):
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="인증 실패")

    async with gpu_semaphore:
        # 🌟 1번: 전체 로직 예외 처리 시작
        try:
            logger.info(f"🚀 작업 시작: {request.target_label} (URL: {request.youtube_url})")
            engine.reset_tracker()
            
            # 🛠️ [수정 완료] global 중복 선언 제거 -> 요청마다 완벽히 독립된 인스턴스 생성
            local_deduplicator = ImageDeduplicator(threshold=0.9, memory_size=15)
            
            # 1. Gemini 분석
            try:
                parsed_data = ai_service.parse_semantic(request.target_label)
                logger.info(f"🧠 Gemini 분석 결과: {parsed_data}")
            except Exception as e:
                logger.error(f"Gemini 분석 실패: {e}")
                return {"status": "error", "message": "타겟 분석 중 오류가 발생했습니다."}

            # 2. 유튜브 스트림 획득 (예외 처리 강화)
            try:
                stream_url = yt_streamer.get_direct_url(request.youtube_url)
                if not stream_url: raise ValueError("URL이 유효하지 않습니다.")
            except Exception as e:
                logger.error(f"스트림 획득 실패: {e}")
                return {"status": "error", "message": "유튜브 스트림을 가져올 수 없습니다. URL을 확인해주세요."}

            file_mgr = FileManager("dataset")
            file_mgr.clean_dataset_folder()
            
            # 🌟 4번 관련: 시간 입력 처리 (마이너스 기호 등 제거)
            clean_start = request.start_time.replace("-", "").strip()
            clean_end = request.end_time.replace("-", "").strip()
            time_mgr = TimeManager(clean_start, clean_end)
            
            # 🌟 [복구] safe_label 생성 로직 부활
            main_target = parsed_data.get("main_target", "object")
            safe_label = main_target.replace(" ", "_").replace("/", "")
            
            video_proc = VideoProcessor(target_fps=1)
            total_crops = 0
            saved_files = []

            # 3. 프레임 추출 및 처리 루프
            for time_sec, frame in video_proc.extract_frames_stream(stream_url):
                if not time_mgr.is_time_to_start(time_sec): continue
                if time_mgr.is_time_to_stop(time_sec): break
                
                results = engine.crop_target(frame, parsed_json=parsed_data)
                
                for res in results:
                    crop_img, tid = res["image"], res["track_id"]
                    
                    # 🌟 2번: 지역 변수로 생성한 중복 제거 로직 가동
                    if local_deduplicator.is_duplicate(crop_img):
                        continue
                    
                    filename = f"dataset/gold_{safe_label}_tr{tid}_{total_crops}.png"
                    cv2.imwrite(filename, crop_img)
                    saved_files.append(filename)
                    total_crops += 1
                    
                    if total_crops >= request.max_crops:
                        break
                if total_crops >= request.max_crops: break

            zip_filename = file_mgr.create_zip(suffix="original") if total_crops > 0 else None
            logger.info(f"✅ 작업 완료: {total_crops}장 수확")
            
            # 🛠️ [수정 완료] 프론트엔드와 규격을 맞춘 '✨'가 포함된 최종 성공 메시지
            return {
                "status": "success", 
                "message": f"{total_crops}장의 이미지 수확 완료! ✨",
                "files": saved_files, 
                "zip_url": f"dataset/{zip_filename}" if zip_filename else None
            }

        except Exception as e:
            logger.critical(f"서버 내부 치명적 오류: {e}")
            return {"status": "error", "message": f"서버 연산 중 예기치 못한 오류가 발생했습니다: {str(e)}"}

# ==========================================
# 7. 트랙 일괄 삭제 API
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
            logger.error(f"❌ 파일 삭제 오류 ({f}): {e}") 

    logger.info(f"🧹 [일괄 삭제] Track ID {request.track_id} 관련 파일 {deleted_count}개 삭제 완료") 
    
    # 4. 🌟 [Code B 적용] 필터링된 결과만 따로 압축
    file_mgr = FileManager("dataset")
    filtered_zip = file_mgr.create_zip(suffix="filtered")

    # 5. 프론트엔드 UI 갱신을 위해 남은 파일 리스트 재스캔 (경로 정규화 포함)
    remaining_files = [f.replace("\\", "/") for f in glob.glob(os.path.join("dataset", "gold_*.png"))]

    # 6. 결과 반환 (프론트엔드 page.tsx와 약속된 키값 사용)
    return {
        "status": "success", 
        "message": f"Track {request.track_id} 삭제 완료 ({deleted_count}개 파일 지워짐)",
        "files": remaining_files, 
        "filtered_zip_url": f"dataset/{filtered_zip}" 
    }

# ==========================================
# 8. [신규] Vibe AI 비서 챗봇 API
# ==========================================
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest, x_api_key: str = Header(None)):
    # 보안 인증
    if x_api_key != API_KEY_SECRET:
        raise HTTPException(status_code=401, detail="API Key 인증 실패")

    try:
        dict_history = [{"role": msg.role, "content": msg.content} for msg in request.history] if request.history else []
        
        reply = ai_service.chat_with_vibe_assistant(
            message=request.message,
            current_page=request.current_page,
            has_data=request.has_data,
            history=dict_history
        )
        
        return {"status": "success", "reply": reply}
        
    except Exception as e:
        logger.error(f"❌ 챗봇 응답 오류: {e}")
        return {"status": "error", "reply": "앗, 뇌에 잠깐 쥐가 났어요. 다시 한 번 말씀해주시겠어요? 😅"}