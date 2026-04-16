import json
import os
import time
from google import genai
from google.genai import types # 🌟 신규 추가: 신형 SDK의 타입 지정을 위해 필요
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일에 GEMINI_API_KEY가 있어야 합니다)
load_dotenv()

class AIService:
    """
    Gemini API를 활용하여 사용자의 자연어 명령을 
    Vision 엔진(DINO)이 이해할 수 있는 공간 기하학적 JSON으로 파싱하는 모듈입니다.
    """
    def __init__(self, model_name="gemini-2.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("🚨 .env 파일에 GEMINI_API_KEY가 설정되지 않았습니다!")
        
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def parse_semantic(self, user_input):
        # ... (기존 parse_semantic 프롬프트 및 로직 내용 동일) ...
        prompt = f"""
        당신은 Vision AI 시스템을 위한 '계층적 공간 파서(Hierarchical Spatial Parser)'입니다.
        결과는 반드시 영어로 번역해야 하며, 아래 규칙을 엄격하게 지키는 순수 JSON만 출력하세요.

        [핵심 규칙]
        1. main_target: 사용자가 의도한 '가장 구체적인 핵심 명사'를 영어로 번역하여 단일 단어로 사용하세요. 
           - 절대로 상위 개념으로 뭉뚱그리지 마세요! (예: '허스키' -> 'husky' (O), 'dog' (X) / '포르쉐' -> 'porsche' (O), 'car' (X))
           - 괄호나 부가 설명에 상위 개념(예: 강아지, 자동차)이 섞여 있어도, 반드시 가장 구체적인 대상을 main_target으로 삼으세요.
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

        입력: "가방을 들고 있는 사람 (우산은 제외)"
        출력: {{"main_target": "person", "shape": "vertical", "clues": [{{"target": "bag", "condition": "include", "relation": "holding", "type": "object"}}, {{"target": "umbrella", "condition": "exclude", "relation": "none", "type": "object"}}]}}

        입력: "허스키 (흰색 강아지는 제외)"
        출력: {{"main_target": "husky", "shape": "vertical", "clues": [{{"target": "white", "condition": "exclude", "relation": "none", "type": "color"}}]}}

        입력: "나무 옆에 있는 벤치"
        출력: {{"main_target": "bench", "shape": "horizontal", "clues": [{{"target": "tree", "condition": "include", "relation": "next_to", "type": "object"}}]}}

        입력: "{user_input}"
        출력:
        """

        max_retries = 4
        base_wait_time = 2 

        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
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
        return None
    
    # 🌟 1번 문제 해결: 클래스 안쪽으로 들여쓰기 완료!
    def chat_with_vibe_assistant(self, message: str, current_page: str, has_data: bool, history: list = None) -> str:
        """
        사용자의 현재 상황(동적 컨텍스트)과 UI 구조를 바탕으로 답변을 생성하는 챗봇 엔진
        """
        base_prompt = "너는 Vibe-Clipper V2의 똑똑하고 친절한 AI 비서야. 전문적이지만 딱딱하지 않게, 친근한 말투(해요체 위주에 가끔 친근한 반말 허용)로 대답하고, 대답할 때 마크다운 문법(예: **, #, *)을 절대 사용하지 마. 모든 대답은 특수기호 없이 자연스러운 평문(Plain text)으로만 작성해."

        ui_schema = """
        [현재 Vibe-Clipper 웹 서비스 기능 명세서]
        - 📺 유튜브 URL 입력: 분석할 유튜브 영상 링크를 입력하는 곳
        - 🎯 타겟 입력: 자연어로 추출할 객체를 지정 (예: '빨간 모자 쓴 사람', '가방 멘 사람')
        - ⏱️ 시간 설정: 00:00:00 형식으로 수확할 영상의 시작/종료 시간 지정
        - 🗑️ 오탐지 일괄 삭제: 결과 이미지 우측 상단의 '✕' 힌트 버튼에 마우스를 올리면 나타나는 빨간색 '🗑️ 오탐지 일괄 삭제' 버튼 클릭 시, 해당 Track ID와 관련된 모든 오탐지 사진을 한 번에 지움
        - 📦 ZIP 다운로드: '📦 원본 전체 ZIP'과 오탐지를 지운 '🎯 필터링 완료 ZIP' 다운로드 지원
        - 🏠 홈 이동: 화면 좌측 상단의 '🏠 Back to Hub' 버튼 클릭
        """

        data_status = "수확된 데이터가 화면에 표시되어 있음." if has_data else "아직 수확된 데이터가 없거나 수확 전임."
        dynamic_state = f"""
        [사용자의 현재 상황]
        - 위치: {current_page} 페이지
        - 상태: {data_status}
        
        위 명세서와 현재 상황을 바탕으로 질문에 대답해. 없는 기능은 지어내지 말고, 사용자가 헤매고 있다면 현재 상황에 맞는 가장 적절한 다음 행동이나 버튼을 안내해줘.
        """

        system_instruction = f"{base_prompt}\n\n{ui_schema}\n\n{dynamic_state}"

        # 🌟 2번 문제 해결: 신규 SDK(google-genai) 방식에 맞춘 대화 이력 및 세션 처리
        formatted_history = []
        if history:
            for chat in history:
                role = "model" if chat.get("role") == "assistant" else "user"
                formatted_history.append(
                    types.Content(role=role, parts=[types.Part.from_text(text=chat.get("content"))])
                )

        # 신형 SDK 방식의 chat 세션 열기
        chat_session = self.client.chats.create(
            model=self.model_name,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction
            ),
            history=formatted_history if formatted_history else None
        )

        response = chat_session.send_message(message)
        return response.text

if __name__ == "__main__":
    # 테스트 코드
    service = AIService()
    
    test_inputs = [
        "하얀색 고양이 (강아지는 제외)"
    ]
    
    print("🚀 Gemini 세맨틱 분석 테스트 시작...\n")
    for text in test_inputs:
        result = service.parse_semantic(text)
        print(f"입력: {text}")
        print(f"결과: {json.dumps(result, indent=4, ensure_ascii=False)}")
        print("-" * 30)