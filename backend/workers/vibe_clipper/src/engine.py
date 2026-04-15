import cv2
import torch
import torchvision
import numpy as np
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
from ultralytics import SAM

class VibeClipperEngine:
    def __init__(self, device="cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        print(f"⏳ Vibe 계층적 공간 검증 엔진 시동 중... (Device: {self.device})")
        
        # 1. Grounding DINO 
        model_id = "IDEA-Research/grounding-dino-tiny" 
        self.dino_processor = AutoProcessor.from_pretrained(model_id)
        self.dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(model_id).to(self.device)
        
        # 2. SAM 
        self.segmenter = SAM("models/sam2_b.pt") 
        self.segmenter.to(self.device)
        
        # 💡 CLIP 모델은 제거되었습니다! (메모리 절약 & 연산 속도 2배 향상)
        print("✅ 텍스트 기반 공간 검증 엔진 시동 완료!")

    def _calculate_intersection(self, boxA, boxB):
        """[핵심 수학] 두 박스의 교집합 면적 및 포함 비율(IoM, IoC)을 계산합니다."""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        if areaA == 0 or areaB == 0:
            return 0, 0

        iom = interArea / areaA  # Main 박스 대비 교집합 비율
        ioc = interArea / areaB  # Clue 박스 대비 교집합 비율
        return iom, ioc

    def crop_target(self, image: np.ndarray, parsed_json: dict):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # Gemma가 넘겨준 JSON 데이터 파싱 및 🌟 무조건 소문자로 강제 변환
        main_target = parsed_json.get("main_target", "object").lower()
        clues = parsed_json.get("clues", [])
        for c in clues:
            c["target"] = c["target"].lower()

        # 🟢 [1. Detection] DINO에게 메인 타겟과 단서들을 한 번에 모두 찾게 함
        search_phrases = [main_target] + [c["target"] for c in clues]
        dino_prompt = " . ".join(search_phrases) + " ." 
        
        inputs = self.dino_processor(images=pil_image, text=dino_prompt, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.dino_model(**inputs)
            
        dino_results = self.dino_processor.post_process_grounded_object_detection(
            outputs, inputs.input_ids, target_sizes=[pil_image.size[::-1]]
        )[0]
        
        boxes = dino_results["boxes"].cpu().numpy()
        scores = dino_results["scores"].cpu().numpy()
        labels = dino_results.get("text_labels", dino_results.get("labels"))
        
        valid_indices = scores >= 0.2
        boxes = boxes[valid_indices]
        scores = scores[valid_indices] # 🌟 점수도 같이 필터링!
        labels = [labels[i] for i, valid in enumerate(valid_indices) if valid]

        if len(boxes) == 0:
            print(f"👀 [DINO] 탐색 실패: 프롬프트 '{dino_prompt}'에 해당하는 객체가 화면에 없습니다.")
            return []

        main_boxes = []
        clue_boxes_dict = {c["target"]: [] for c in clues}
        main_norm = main_target.replace("-", " ")
        
        # 🌟 [폭탄 1 해체] zip에 scores 추가 및 튜플로 저장!
        for box, score, label in zip(boxes, scores, labels):
            label_norm = label.lower().replace("-", " ")
            if main_norm in label_norm:
                main_boxes.append((box, score)) # 박스와 점수 함께 보관
            for c in clues:
                c_norm = c["target"].replace("-", " ")
                if c_norm in label_norm:
                    clue_boxes_dict[c["target"]].append(box)
        
        if not main_boxes:
            print(f"👀 [DINO] '{main_target}' (메인 타겟) 박스를 하나도 찾지 못했습니다.")
            return []

        # 🟢 [2. 공간 기하학적 검증] 
        img_area = image.shape[0] * image.shape[1] 
        valid_main_boxes = []
        valid_main_scores = []
        
        for m_box, m_score in main_boxes:
            w, h = m_box[2] - m_box[0], m_box[3] - m_box[1]
            
            if w == 0 or h == 0: continue
            if (h / w > 10.0) or (w / h > 10.0): continue 
            if (w * h) < (img_area * 0.001): continue

            is_valid = True
            
            for clue in clues:
                clue_target = clue["target"]
                condition = clue["condition"]
                relation = clue.get("relation", "none")
                
                found_match = False
                for c_box in clue_boxes_dict[clue_target]:
                    iom, ioc = self._calculate_intersection(m_box, c_box)
                    
                    if relation in ["inside", "wearing", "holding"]:
                        if iom > 0.25 or ioc > 0.25:
                            found_match = True
                            break
                    elif relation == "next_to":
                        m_center = np.array([(m_box[0]+m_box[2])/2, (m_box[1]+m_box[3])/2])
                        c_center = np.array([(c_box[0]+c_box[2])/2, (c_box[1]+c_box[3])/2])
                        dist = np.linalg.norm(m_center - c_center)
                        diag = np.sqrt(w**2 + h**2)
                        if dist < (diag * 1.5) or iom > 0.1:
                            found_match = True
                            break
                    elif relation == "none":
                        if iom > 0.1 or ioc > 0.1:
                            found_match = True
                            break
                
                if condition == "include" and not found_match:
                    is_valid = False 
                    break
                elif condition == "exclude" and found_match:
                    is_valid = False 
                    break
                    
            if is_valid:
                valid_main_boxes.append(m_box)
                valid_main_scores.append(m_score) # 점수 저장

        if not valid_main_boxes:
            print(f"👀 [공간 검증] 메인 타겟은 찾았으나, 단서(clues) 조건을 만족하지 못해 최종 탈락했습니다.")
            return []
            
        # 🌟 [폭탄 2 해체] NMS에서 평등주의(torch.ones) 폐기, DINO의 원본 점수(Confidence) 활용!
        boxes_tensor = torch.tensor(valid_main_boxes, dtype=torch.float32)
        scores_tensor = torch.tensor(valid_main_scores, dtype=torch.float32) 
        
        nms_indices = torchvision.ops.nms(boxes_tensor, scores_tensor, iou_threshold=0.6)
        final_boxes = boxes_tensor[nms_indices].numpy()
        print(f"🎯 [공간 검증 합격] '{main_target}' 최종 객체 {len(final_boxes)}개 추출!")
            
        # 🟢 [3. Segmentation] 합격한 박스만 누끼 따기
        seg_results = self.segmenter(image, bboxes=final_boxes, verbose=False)
        
        final_crops = []
        for result in seg_results:
            if result.masks is None: continue
            masks = result.masks.data.cpu().numpy()
            orig_boxes = result.boxes.xyxy.cpu().numpy()
            
            for idx, mask in enumerate(masks):
                x1, y1, x2, y2 = map(int, orig_boxes[idx])
                
                crop_img = image[y1:y2, x1:x2]
                mask_numeric = mask.astype(np.uint8)
                
                # 🌟 [폭탄 3 해체] 압축 버그 수정! 캔버스 전체로 먼저 펼치고, 박스만큼 가위로 오려내기!
                full_mask = cv2.resize(mask_numeric, (image.shape[1], image.shape[0]))
                mask_crop = full_mask[y1:y2, x1:x2]
                
                bgra = cv2.cvtColor(crop_img, cv2.COLOR_BGR2BGRA)
                bgra[:, :, 3] = mask_crop * 255
                final_crops.append(bgra)
                
        return final_crops

    def close_debug_video(self):
        pass