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
        
        # 🌟 [신규] 객체 추적기(Tracker) 초기화
        self.reset_tracker()
        
        print("✅ 텍스트 기반 공간 검증 엔진 시동 완료!")

    def reset_tracker(self):
        """🌟 [신규] 새로운 영상 수확을 시작할 때마다 트래커의 기억을 초기화합니다."""
        self.tracks = [] # [{"id": int, "box": [x1,y1,x2,y2], "missed": int}]
        self.next_track_id = 100 # ID는 100번부터 시작

    def _get_track_ids(self, new_boxes):
        """🌟 [신규] 초경량 자체 IoU(박스 겹침) 기반 객체 추적기"""
        if len(new_boxes) == 0:
            for t in self.tracks: t['missed'] += 1
            return []

        track_ids = []
        new_tracks = []
        used_track_indices = set()

        for box in new_boxes:
            best_iou = 0.15 # 최소 15% 이상 겹쳐야 동일 객체로 인정
            best_track_idx = -1
            
            for i, t in enumerate(self.tracks):
                if i in used_track_indices: continue
                # IoU (Intersection over Union) 계산
                xA, yA = max(box[0], t['box'][0]), max(box[1], t['box'][1])
                xB, yB = min(box[2], t['box'][2]), min(box[3], t['box'][3])
                interArea = max(0, xB - xA) * max(0, yB - yA)
                boxAArea = (box[2] - box[0]) * (box[3] - box[1])
                boxBArea = (t['box'][2] - t['box'][0]) * (t['box'][3] - t['box'][1])
                
                iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)

                if iou > best_iou:
                    best_iou = iou
                    best_track_idx = i
            
            if best_track_idx != -1:
                # 기존 객체와 일치하면 기존 ID 부여
                track_id = self.tracks[best_track_idx]['id']
                used_track_indices.add(best_track_idx)
                new_tracks.append({"id": track_id, "box": box, "missed": 0})
                track_ids.append(track_id)
            else:
                # 겹치는 게 없으면 새로운 객체로 간주하고 새 ID 발급
                track_id = self.next_track_id
                self.next_track_id += 1
                new_tracks.append({"id": track_id, "box": box, "missed": 0})
                track_ids.append(track_id)

        # 잠깐 화면에서 사라졌지만(놓침) 아직 완전히 버리기엔 이른 객체 유지 (최대 3프레임 기억)
        for i, t in enumerate(self.tracks):
            if i not in used_track_indices:
                t['missed'] += 1
                if t['missed'] < 3:
                    new_tracks.append(t)
        
        self.tracks = new_tracks
        return track_ids

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
            "white": [([0, 0, 180], [180, 50, 255])], 
            "black": [([0, 0, 0], [180, 255, 60])],
            "blue": [([100, 150, 0], [140, 255, 255])],
            "yellow": [([20, 100, 100], [35, 255, 255])],
            "green": [([35, 100, 100], [85, 255, 255])]
        }
        
        if target_color not in color_ranges:
            return True 

        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        for (lower, upper) in color_ranges[target_color]:
            lower_np, upper_np = np.array(lower), np.array(upper)
            mask |= cv2.inRange(hsv, lower_np, upper_np)
            
        color_ratio = np.count_nonzero(mask) / (hsv.shape[0] * hsv.shape[1])
        return color_ratio > 0.05 

    def crop_target(self, image: np.ndarray, parsed_json: dict):
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        main_target = parsed_json.get("main_target", "object").lower()
        target_shape = parsed_json.get("shape", "vertical")
        clues = parsed_json.get("clues", [])
        
        for c in clues: c["target"] = c["target"].lower()

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

        img_area = image.shape[0] * image.shape[1] 
        valid_main_boxes, valid_main_scores = [], []

        for m_box, m_score in main_boxes:
            w, h = m_box[2] - m_box[0], m_box[3] - m_box[1]
            if w == 0 or h == 0: continue
            
            max_ratio = 15.0 if target_shape == "slender" else 4.0
            if (h / w > max_ratio) or (w / h > max_ratio): continue 
            if (w * h) < (img_area * 0.001): continue

            is_valid = True
            geom_score_bonus = 0.0 
            
            for clue in clues:
                clue_target, condition, relation = clue["target"], clue["condition"], clue.get("relation", "none")
                
                if clue.get("type", "object") == "color":
                    m_crop = image[int(m_box[1]):int(m_box[3]), int(m_box[0]):int(m_box[2])]
                    color_matched = self._is_color_match(m_crop, clue_target)
                    
                    if condition == "include" and not color_matched: is_valid = False; break
                    elif condition == "exclude" and color_matched: is_valid = False; break
                    
                    if condition == "include" and color_matched: geom_score_bonus += 0.2
                    continue

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
                valid_main_scores.append(m_score + geom_score_bonus) 

        if not valid_main_boxes: return []
            
        boxes_tensor = torch.tensor(valid_main_boxes, dtype=torch.float32)
        scores_tensor = torch.tensor(valid_main_scores, dtype=torch.float32) 
        
        nms_indices = torchvision.ops.nms(boxes_tensor, scores_tensor, iou_threshold=0.6)
        final_boxes = boxes_tensor[nms_indices].numpy()
        
        # 🌟 [신규] 최종 확정된 박스들에 Track ID 부여
        track_ids = self._get_track_ids(final_boxes)
        
        print(f"🎯 [공간 검증 합격] '{main_target}' 최종 객체 {len(final_boxes)}개 추출 (Track IDs: {track_ids})")
            
        seg_results = self.segmenter(image, bboxes=final_boxes, verbose=False)
        
        final_crops = []
        for idx, result in enumerate(seg_results):
            if result.masks is None: continue
            masks = result.masks.data.cpu().numpy()
            orig_boxes = result.boxes.xyxy.cpu().numpy()
            
            # 박스 하나당 하나의 마스크라고 가정
            for m_idx, mask in enumerate(masks):
                x1, y1, x2, y2 = map(int, orig_boxes[m_idx])
                crop_img = image[y1:y2, x1:x2]
                
                full_mask = cv2.resize(mask.astype(np.uint8), (image.shape[1], image.shape[0]))
                mask_crop = full_mask[y1:y2, x1:x2]
                
                bgra = cv2.cvtColor(crop_img, cv2.COLOR_BGR2BGRA)
                bgra[:, :, 3] = mask_crop * 255
                
                # 🌟 [신규] 단순 이미지가 아닌 "이미지와 ID"를 세트로 묶어서 반환 (app.py에서 파일명에 사용)
                final_crops.append({
                    "image": bgra,
                    "track_id": track_ids[idx]
                })
                break # 한 박스에 대해 가장 첫 번째 마스크만 취함
                
        return final_crops

    def close_debug_video(self):
        pass