import json
import os
import time
from google import genai
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일에 GEMINI_API_KEY가 있어야 합니다)
load_dotenv()

class AIService:
    """
    Gemini API를 활용하여 사용자의 자연어 명령을 
    Vision 엔진(DINO)이 이해할 수 있는 공간 기하학적 JSON으로 파싱하는 모듈입니다.
    """
    def __init__(self, model_name="gemini-2.5-flash"):
        # processor.py의 로직 차용: GenAI 클라이언트 안전 초기화
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("🚨 .env 파일에 GEMINI_API_KEY가 설정되지 않았습니다!")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name # 속도가 미치도록 빠른 flash 모델 추천!

    def parse_semantic(self, user_input):
        prompt = f"""
        당신은 Vision AI 시스템을 위한 '계층적 공간 파서(Hierarchical Spatial Parser)'입니다.
        결과는 반드시 영어로 번역해야 하며, 아래 규칙을 엄격하게 지키는 순수 JSON만 출력하세요.

        [핵심 규칙]
        1. main_target: 수식어가 없는 순수 명사(예: person, cat, car).
        2. shape: "vertical", "horizontal", "slender", "square" 중 택 1.
        3. clues: 단서 배열.
           - target: 단서 이름 (예: white, hat, tree, dog)
           - condition: 반드시 "include" 또는 "exclude" 중 하나만 선택!
           - relation: 반드시 "inside", "wearing", "holding", "next_to", "none" 중 하나만 선택!
           - type: 물리적 사물이면 "object", 단순 색상이면 "color".

        [학습용 예시 (Few-Shot)]
        입력: "차 안에 있는 강아지"
        출력: {{"main_target": "dog", "shape": "vertical", "clues": [{{"target": "car", "condition": "include", "relation": "inside", "type": "object"}}]}}

        입력: "빨간 모자를 쓴 사람"
        출력: {{"main_target": "person", "shape": "vertical", "clues": [{{"target": "red", "condition": "include", "relation": "none", "type": "color"}}, {{"target": "hat", "condition": "include", "relation": "wearing", "type": "object"}}]}}

        입력: "나무 옆에 있는 하얀색 고양이"
        출력: {{"main_target": "cat", "shape": "vertical", "clues": [{{"target": "white", "condition": "include", "relation": "none", "type": "color"}}, {{"target": "tree", "condition": "include", "relation": "next_to", "type": "object"}}]}}

        입력: "가방을 들고 있는 사람 (우산은 제외)"
        출력: {{"main_target": "person", "shape": "vertical", "clues": [{{"target": "bag", "condition": "include", "relation": "holding", "type": "object"}}, {{"target": "umbrella", "condition": "exclude", "relation": "none", "type": "object"}}]}}

        입력: "{user_input}"
        출력:
        """

        # processor.py의 지수 백오프(Exponential Backoff) 및 마크다운 정제 로직 차용
        max_retries = 3 
        base_wait_time = 1 

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
                # LLM 응답 텍스트에 포함될 수 있는 불필요한 마크다운 태그 정제
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                
                return json.loads(text.strip())

            except Exception as e:
                wait_time = base_wait_time * (2 ** attempt)
                print(f"⚠️ [AIService] API 오류 발생 ({e})... {wait_time}초 후 재시도 ({attempt + 1}/{max_retries})")
                time.sleep(wait_time)
        
        print(f"❌ [AIService] 최종 실패: 분석을 건너뜁니다.")
        return {"main_target": "object", "clues": []}

if __name__ == "__main__":
    # 테스트 코드
    service = AIService()
    
    test_inputs = [
        "하얀색 고양이 (강아지는 제외)",
        "노란색 우산을 쓰고 있는 사람",
        "검을 들고 있는 기사",
        "꽃밭에 앉아 있는 나비"
    ]
    
    print("🚀 Gemini 세맨틱 분석 테스트 시작...\n")
    for text in test_inputs:
        result = service.parse_semantic(text)
        print(f"입력: {text}")
        print(f"결과: {json.dumps(result, indent=4, ensure_ascii=False)}")
        print("-" * 30)