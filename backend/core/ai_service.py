import requests
import json
import re

class AIService:
    def __init__(self, model="gemma2:2b"):
        self.url = "http://localhost:11434/api/generate"
        self.model = model

    def parse_semantic(self, user_input):
        prompt = f"""
        당신은 Vision AI 시스템(Grounding DINO)을 위한 '계층적 공간 파서(Hierarchical Spatial Parser)'입니다.
        사용자의 요청을 분석하여 최종적으로 크롭할 '메인 타겟(main_target)'과, 이를 기하학적으로 검증할 '단서들(clues)'로 완벽하게 분해하세요.
        결과는 반드시 영어로 번역해야 하며, 아래의 [규칙]을 엄격하게 따르는 순수 JSON 형식으로만 응답하세요.

        [핵심 규칙]
        1. 메인 타겟(main_target) 단수화: '사람들', '무리' 등 복수형 요구가 있어도 반드시 단수형(예: person, car, dog)으로 출력하세요.
        2. 역전 관계 무시: '차 안의 강아지'처럼 크기가 큰 객체 안에 작은 객체가 있어도, 사용자가 최종적으로 원하는 것을 main_target으로 삼으세요.
        3. 단일 객체 처리: '독수리', '사과'처럼 아무런 수식어나 단서가 없는 단일 객체 요청일 경우, clues는 빈 배열([])을 반환하세요. 단순 색상('빨간 사과')도 main_target에 합치고 clues는 비우세요.
        4. 포함/제외(Condition): 각 단서가 반드시 있어야 하면 "include", 없어야 하면 "exclude"로 표시하세요.
        5. 관계성(Relation) 추론: 메인 타겟과 단서 사이의 물리적/공간적 관계를 추론하여 "inside" (안에 있음), "wearing" (입고/쓰고 있음), "holding" (들고 있음), "next_to" (옆에 있음), "none" 중 하나로 지정하세요.

        [JSON 출력 포맷 예시]
        입력: "독수리" (단일 객체)
        출력: {{
            "main_target": "eagle",
            "clues": []
        }}

        입력: "빨간 모자를 쓰고 파란 가방을 들고 있는 사람"
        출력: {{
            "main_target": "person",
            "clues": [
                {{"target": "red hat", "condition": "include", "relation": "wearing"}},
                {{"target": "blue bag", "condition": "include", "relation": "holding"}}
            ]
        }}

        입력: "자동차 안에 있는 강아지 무리"
        출력: {{
            "main_target": "dog",
            "clues": [
                {{"target": "car", "condition": "include", "relation": "inside"}}
            ]
        }}

        입력: "나무 옆에 서 있는 안경을 쓰지 않은 남자"
        출력: {{
            "main_target": "man",
            "clues": [
                {{"target": "tree", "condition": "include", "relation": "next_to"}},
                {{"target": "glasses", "condition": "exclude", "relation": "wearing"}}
            ]
        }}

        입력: "{user_input}"
        출력:
        """

        data = {"model": self.model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.url, json=data)
            response.raise_for_status()
            text_response = response.json().get("response", "")
            
            # JSON 텍스트만 안전하게 추출
            match = re.search(r'\{.*\}', text_response.replace('\n', ''))
            if match:
                return json.loads(match.group(0))
            return {"main_target": "object", "clues": []}
            
        except Exception as e:
            print(f"❌ [AIService] 분석 실패: {e}")
            return {"main_target": "object", "clues": []}
        
        
if __name__ == "__main__":
    # 테스트를 위한 객체 생성
    service = AIService()
    
    test_inputs = [
        "독수리",
        "차 안에 있는 강아지",
        "빨간 모자를 쓴 사람",
        "나무 옆에 있는 고양이"
    ]
    
    print("🚀 Gemma 세맨틱 분석 테스트 시작...\n")
    for text in test_inputs:
        result = service.parse_semantic(text)
        print(f"입력: {text}")
        print(f"결과: {json.dumps(result, indent=4, ensure_ascii=False)}")
        print("-" * 30)