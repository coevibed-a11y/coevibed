import os
import shutil
import time
import glob

class FileManager:
    def __init__(self, dataset_dir="dataset"):
        self.dataset_dir = dataset_dir
        if not os.path.exists(self.dataset_dir):
            os.makedirs(self.dataset_dir)

    def clean_dataset_folder(self):
        """새로운 수확 시작 시 이전 결과물(PNG, ZIP 모두) 청소"""
        print("🧹 [FileManager] 새로운 수확을 위해 기존 데이터를 청소합니다...")
        for filename in os.listdir(self.dataset_dir):
            file_path = os.path.join(self.dataset_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"파일 삭제 실패: {e}")

    def create_zip(self, suffix="all") -> str:
        """
        현재 폴더의 PNG들을 압축합니다. 
        suffix를 통해 '전체(all)' 또는 '필터링(filtered)'을 구분합니다.
        """
        timestamp = int(time.time())
        final_zip_name = f"vibe_{suffix}_{timestamp}.zip"
        final_zip_path = os.path.join(self.dataset_dir, final_zip_name)

        # 구 버전 압축 파일들만 먼저 삭제 (용량 확보)
        for old_zip in glob.glob(os.path.join(self.dataset_dir, f"vibe_{suffix}_*.zip")):
            try: os.remove(old_zip)
            except: pass

        # PNG 파일들만 압축 (ZIP 파일 자신은 포함되지 않게 주의)
        temp_zip_base = f"temp_{suffix}_{timestamp}"
        
        # 임시 폴더에 PNG만 복사해서 압축하는 방식 (가장 안전)
        temp_dir = f"temp_dir_{timestamp}"
        os.makedirs(temp_dir, exist_ok=True)
        for f in glob.glob(os.path.join(self.dataset_dir, "gold_*.png")):
            shutil.copy(f, temp_dir)
            
        shutil.make_archive(temp_zip_base, 'zip', temp_dir)
        shutil.move(f"{temp_zip_base}.zip", final_zip_path)
        
        # 임시 폴더 삭제
        shutil.rmtree(temp_dir)
        
        return final_zip_name