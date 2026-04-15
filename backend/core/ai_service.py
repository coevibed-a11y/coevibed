import requests
import json

class AIService:
    def __init__(self, model="gemma2:2b"):
        # Ollama 로컬 API 주소 (기본값)
        self.url = "http://localhost:11434/api/generate"
        self.model = model

    def parse_semantic(self, user_input):
        """
        사용자의 자연어를 분석하여 객체(Object)와 속성(Attribute)을 JSON으로 추출합니다.
        """
        # Gemma에게 내리는 정밀한 지시문(Prompt)
        prompt = f"""
        당신은 영상 분석 시스템의 세맨틱 파서(Semantic Parser)입니다.
        사용자의 입력 문장에서 '물체(object)', '색상(color)', '기타 특징(attributes)'을 추출해 JSON으로만 응답하세요.

        [규칙]
        1. 결과는 반드시 정형화된 JSON 형식이어야 합니다.
        2. 물체(object)는 반드시 영어 단어 하나로 번역하세요 (예: 자동차 -> car).
        3. 색상(color)이 없으면 null로 표시하세요.
        4. 다른 설명은 하지 말고 오직 JSON만 출력하세요.

        [예시]
        입력: "길거리에 서 있는 빨간색 버스" -> {{"object": "bus", "color": "red", "attributes": ["standing"]}}
        
        입력: "{user_input}"
        JSON:
        """

        try:
            # 💡 stream=False로 설정해야 응답이 다 올 때까지 기다렸다가 한 번에 받습니다.
            response = requests.post(self.url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json" 
            })
            
            # Ollama의 응답 파싱
            result_text = response.json().get("response", "{}")
            return json.loads(result_text)
            
        except Exception as e:
            print(f"❌ Gemma 분석 중 오류 발생: {e}")
            return None