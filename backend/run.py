import subprocess
import re
import threading
import os
import time
import sys

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, db

# 1. 환경 변수 및 Firebase 초기화
load_dotenv()
cred = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(cred, {'databaseURL': os.getenv("FIREBASE_DB_URL")})

def run_cloudflared():
    print("☁️ [Manager] Cloudflare 터널을 백그라운드에서 실행합니다...")
    
    if not os.path.exists("cloudflared.exe"):
        print("❌ [Manager] 오류: 현재 폴더에 'cloudflared.exe' 파일이 없습니다!")
        return

    process = subprocess.Popen(
        ["cloudflared.exe", "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='ignore'
    )

    try:
        for line in process.stdout:
            match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if match:
                cloud_url = match.group(0)
                print(f"\n🌍 [Manager] 터널 주소 획득 성공!: {cloud_url}")
                
                try:
                    ref = db.reference('server_status')
                    # online 상태 업데이트
                    ref.update({'backend_url': cloud_url, 'status': 'online'})
                    print("🚀 [Manager] Firebase 자동 동기화 완료!")
                except Exception as e:
                    print(f"❌ [Manager] Firebase 업데이트 실패: {e}")
                
                print("\n⏳ 터널이 활성화되었습니다. (종료하려면 터미널에서 Ctrl+C를 누르세요)\n")
                break # URL을 찾았으므로 로그 출력 감시 루프는 종료

        # 🌟 핵심: 스크립트가 바로 종료되지 않고 프로세스가 끝날 때까지 대기합니다.
        process.wait()

    except KeyboardInterrupt:
        # 사용자가 터미널 창에서 Ctrl+C를 누르면 실행됨
        print("\n🛑 [Manager] 사용자에 의해 터널이 종료됩니다...")
        
    finally:
        # 🌟 우아한 종료 (Clean up)
        if process.poll() is None: # 아직 프로세스가 살아있다면 강제 종료
            process.terminate()
            process.wait() # 완전히 죽을 때까지 잠깐 대기
        
        try: # Firebase 상태를 오프라인으로 원복
            ref = db.reference('server_status')
            ref.update({'status': 'offline'})
            print("💤 [Manager] Firebase 상태를 'offline'으로 변경했습니다.")
        except Exception as e:
            pass
            
        print("👋 [Manager] 프로그램이 안전하게 종료되었습니다.")

if __name__ == "__main__":
    # 1. 터널 실행 및 주소 훔치기 작업을 별도의 쓰레드(백그라운드)로 지시
    tunnel_thread = threading.Thread(target=run_cloudflared, daemon=True)
    tunnel_thread.start()

    # 2. 터널이 열릴 시간을 3초 정도로 넉넉히 줌 (Cloudflare 서버 응답 대기 시간 확보)
    time.sleep(3)
    
    # 3. 본체인 백엔드(FastAPI) 서버 가동!
    print("🔥 [Manager] 백엔드(FastAPI) 엔진을 가동합니다...")
    subprocess.run([sys.executable, "-m", "uvicorn", "app:app", "--reload"])