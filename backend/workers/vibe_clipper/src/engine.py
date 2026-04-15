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
        
        print("✅ 텍스트 기반 공간 검증 엔진 시동 완료!")

    def _calculate_intersection(self, boxA, boxB):
        """[핵심 수학] 두 박스의 교집합 면적 및 포함 비율(IoM, IoC)을 계산합니다."""
        xA, yA = max(boxA[0], boxB[0]), max(boxA[1], boxB[1])
        xB, yB = min(boxA[2], boxB[2]), min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        areaA = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        areaB = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        if areaA == 0 or areaB == 0: return 0, 0
        return interArea / areaA, interArea / areaB

    def _is_color_match(self, crop_img, target_color):
        """[핵심] HSV 픽셀 기반 색상 검증기 (물리적 필터)"""
        if crop_img.size == 0: return False
        hsv = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)
        
        # 대표적인 색상 HSV 범위 지정
        color_ranges = {
            "red": [([0, 100, 100], [10, 255, 255]), ([160, 100, 100], [180, 255, 255])],
            "white": [([0, 0, 180], [180, 50, 255])], # 채도 낮고 명도 높은 영역
            "black": [([0, 0, 0], [180, 255, 60])],
            "blue": [([100, 150, 0], [140, 255, 255])],
            "yellow": [([20, 100, 100], [35, 255, 255])],
            "green": [([35, 100, 100], [85, 255, 255])]
        }
        
        if target_color not in color_ranges:
            return True # 엔진 모르는 애매한 색상(beige 등)은 일단 DINO를 믿고 패스

        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for (lower, upper) in color_ranges[target_color]:
            lower_np, upper_np = np.array(lower), np.array(upper)
            mask |= cv2.inRange(hsv, lower_np, upper_np)
            
        color_ratio = np.count_nonzero(mask) / (hsv.shape[0] * hsv.shape[1])
        return color_ratio > 0.05 # 타겟 박스 안에 해당 색상이 5% 이상 있으면 합격!

    def crop_target(self, image: np.ndarray, parsed_json: dict):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        main_target = parsed_json.get("main_target", "object").lower()
        target_shape = parsed_json.get("shape", "vertical")
        clues = parsed_json.get("clues", [])
        
        for c in clues: c["target"] = c["target"].lower()

        # 🌟 [최적화] DINO에게는 "물리적 객체(object)"만 찾아달라고 합니다. 색상은 픽셀로 검사할 거니까요!
        object_clues = [c for c in clues if c.get("type", "object") != "color"]
        search_phrases = [main_target] + [c["target"] for c in object_clues]
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
        
        # 🌟 [강아지 철벽 방어] 커트라인을 0.2 -> 0.35로 상향 조정!
        valid_indices = scores >= 0.35
        boxes, scores = boxes[valid_indices], scores[valid_indices]
        labels = [labels[i] for i, valid in enumerate(valid_indices) if valid]

        if len(boxes) == 0: return []

        main_boxes = []
        clue_boxes_dict = {c["target"]: [] for c in object_clues}
        main_norm = main_target.replace("-", " ")
        
        for box, score, label in zip(boxes, scores, labels):
            label_norm = label.lower().replace("-", " ")
            if main_norm in label_norm:
                main_boxes.append((box, score)) 
            for c in object_clues:
                if c["target"].replace("-", " ") in label_norm:
                    clue_boxes_dict[c["target"]].append(box)
        
        if not main_boxes: return []

        # 🟢 [2. 공간 기하학적 검증 & 픽셀 색상 검증] 
        img_area = image.shape[0] * image.shape[1] 
        valid_main_boxes, valid_main_scores = [], []

        for m_box, m_score in main_boxes:
            w, h = m_box[2] - m_box[0], m_box[3] - m_box[1]
            if w == 0 or h == 0: continue
            
            # 🌟 [가변 비율 필터] 배트/검은 15배 허용, 일반 객체는 4배까지만! (이쑤시개 방지)
            max_ratio = 15.0 if target_shape == "slender" else 4.0
            if (h / w > max_ratio) or (w / h > max_ratio): continue 
            if (w * h) < (img_area * 0.001): continue

            is_valid = True
            geom_score_bonus = 0.0 # 💡 랭킹 보너스
            
            for clue in clues:
                clue_target, condition, relation = clue["target"], clue["condition"], clue.get("relation", "none")
                
                # 🎨 [색상 픽셀 검증]
                if clue.get("type", "object") == "color":
                    m_crop = image[int(m_box[1]):int(m_box[3]), int(m_box[0]):int(m_box[2])]
                    color_matched = self._is_color_match(m_crop, clue_target)
                    
                    if condition == "include" and not color_matched: is_valid = False; break
                    elif condition == "exclude" and color_matched: is_valid = False; break
                    
                    if condition == "include" and color_matched: geom_score_bonus += 0.2
                    continue

                # 📐 [물리적 객체 검증]
                found_match = False
                for c_box in clue_boxes_dict.get(clue_target, []):
                    iom, ioc = self._calculate_intersection(m_box, c_box)
                    
                    if relation == "wearing":
                        if ioc > 0.8: found_match = True; geom_score_bonus += 0.3; break
                    elif relation in ["inside", "holding"]:
                        if iom > 0.2 or ioc > 0.2: found_match = True; geom_score_bonus += 0.2; break
                    elif relation == "next_to":
                        m_center = np.array([(m_box[0]+m_box[2])/2, (m_box[1]+m_box[3])/2])
                        c_center = np.array([(c_box[0]+c_box[2])/2, (c_box[1]+c_box[3])/2])
                        if np.linalg.norm(m_center - c_center) < (np.sqrt(w**2 + h**2) * 1.5):
                            found_match = True; geom_score_bonus += 0.1; break
                    else:
                        if iom > 0.1 or ioc > 0.1: found_match = True; break
                
                if condition == "include" and not found_match: is_valid = False; break
                elif condition == "exclude" and found_match: is_valid = False; break
                    
            if is_valid:
                valid_main_boxes.append(m_box)
                valid_main_scores.append(m_score + geom_score_bonus) # 🌟 종합 랭킹 점수

        if not valid_main_boxes: return []
            
        # 🌟 [지능형 NMS] DINO 확신도 + 기하학/색상 보너스 점수 합산으로 1등 뽑기
        boxes_tensor = torch.tensor(valid_main_boxes, dtype=torch.float32)
        scores_tensor = torch.tensor(valid_main_scores, dtype=torch.float32) 
        
        nms_indices = torchvision.ops.nms(boxes_tensor, scores_tensor, iou_threshold=0.6)
        final_boxes = boxes_tensor[nms_indices].numpy()
        print(f"🎯 [공간 검증 합격] '{main_target}' 최종 객체 {len(final_boxes)}개 추출!")
            
        # 🟢 [3. Segmentation] 
        seg_results = self.segmenter(image, bboxes=final_boxes, verbose=False)
        
        final_crops = []
        for result in seg_results:
            if result.masks is None: continue
            masks = result.masks.data.cpu().numpy()
            orig_boxes = result.boxes.xyxy.cpu().numpy()
            
            for idx, mask in enumerate(masks):
                x1, y1, x2, y2 = map(int, orig_boxes[idx])
                crop_img = image[y1:y2, x1:x2]
                
                full_mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]))
                mask_crop = full_mask[y1:y2, x1:x2]
                
                bgra = cv2.cvtColor(crop_img, cv2.COLOR_BGR2BGRA)
                bgra[:, :, 3] = mask_crop * 255
                final_crops.append(bgra)
                
        return final_crops

    def close_debug_video(self):
        pass