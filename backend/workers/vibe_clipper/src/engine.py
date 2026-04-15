import cv2
import os
import numpy as np
from ultralytics import YOLO, SAM
from datetime import datetime

class VibeClipperEngine:
    def __init__(self):
        print("⏳ Vibe 아키텍처 엔진 시동 중... (Semantic Worker Mode)")
        
        # 통합 모델 폴더에서 가중치 로드
        self.detector = YOLO("models/yolov8s-world.pt") 
        self.detector.to("cuda")
        
        self.segmenter = SAM("models/sam2_b.pt") 
        self.segmenter.to("cuda")
        
        self.debug = False 
        self.video_writer = None
        
        print("✅ 비전 엔진 시동 완료 (분석 기능은 중앙 AI Hub로 위임됨)")

    # ==========================================
    # 🧠 Filter 1: 공간 포함 관계 필터 (Spatial Overlap)
    # ==========================================
    def _check_overlap(self, parent_box, child_box, threshold=0.3):
        """
        부모 박스(예: 사람) 영역 내부에 자식 박스(예: 모자, 가방)가 존재하는지 수학적으로 계산합니다.
        이를 통해 '가방을 멘 사람' 같은 동적 형태 속성을 하드코딩 없이 걸러냅니다.
        """
        px1, py1, px2, py2 = parent_box
        cx1, cy1, cx2, cy2 = child_box

        # 겹치는 교집합 영역의 좌표 계산
        ix1 = max(px1, cx1)
        iy1 = max(py1, cy1)
        ix2 = min(px2, cx2)
        iy2 = min(py2, cy2)

        # 겹치는 영역의 넓이
        inter_width = max(0, ix2 - ix1)
        inter_height = max(0, iy2 - iy1)
        inter_area = inter_width * inter_height

        # 자식 박스(예: 모자)의 원래 넓이
        child_area = (cx2 - cx1) * (cy2 - cy1)

        if child_area == 0:
            return False

        # 자식 박스 면적 대비 겹치는 비율이 threshold(30%) 이상이면 착용/소지한 것으로 판정!
        overlap_ratio = inter_area / child_area
        return overlap_ratio > threshold

    # ==========================================
    # 🧠 Filter 2: 픽셀 기반 색상 필터 (Color Attribute)
    # ==========================================
    def _is_target_color(self, crop_img, crop_mask, target_color):
        """
        SAM이 정밀하게 따낸 누끼(Mask) 영역 내부의 픽셀만 HSV 공간에서 분석하여 색상을 판별합니다.
        배경(아스팔트 등)의 색상 노이즈를 완벽하게 차단합니다.
        """
        if target_color not in ["white", "black", "red", "blue", "yellow", "green"]:
            return True # 시스템에 정의되지 않은 색상이면 일단 관대하게 통과

        hsv_img = cv2.cvtColor(crop_img, cv2.COLOR_BGR2HSV)
        masked_hsv = hsv_img[crop_mask > 0]
        
        if len(masked_hsv) == 0:
            return False

        # 색상별 HSV 범위 정의
        if target_color == "white":
            lower_bound = np.array([0, 0, 180])
            upper_bound = np.array([180, 50, 255])
        elif target_color == "black":
            lower_bound = np.array([0, 0, 0])
            upper_bound = np.array([180, 255, 50])
        elif target_color == "red":
            lower_bound = np.array([0, 100, 100])
            upper_bound = np.array([10, 255, 255])
        elif target_color == "blue":
            lower_bound = np.array([100, 150, 0])
            upper_bound = np.array([140, 255, 255])
        else:
            return True 

        # 설정한 색상 범위에 들어가는 픽셀 개수 계산
        color_match_mask = cv2.inRange(np.expand_dims(masked_hsv, axis=0), lower_bound, upper_bound)
        match_ratio = cv2.countNonZero(color_match_mask) / len(masked_hsv)

        # 타겟 색상이 객체 면적의 20% 이상을 차지하면 합격
        return match_ratio > 0.2

    # ==========================================
    # 🚀 Main Pipeline: 객체 수확 및 필터링
    # ==========================================
    def crop_target(self, img_array, target_object, target_color=None, target_attributes=None):
        if target_attributes is None:
            target_attributes = []
            
        cropped_images = []
        
        # 1. 탐지 세팅: 부모 객체(사람)와 요구되는 자식 속성(모자, 가방 등)을 모두 찾으라고 지시
        search_classes = [target_object] + target_attributes
        self.detector.set_classes(search_classes) 

        detection_results = self.detector.predict(
            img_array, device="cuda", conf=0.15, imgsz=1280, verbose=False
        )
        
        # [디버그] 영상 녹화 로직
        if self.debug:
            annotated_frame = detection_results[0].plot()
            if self.video_writer is None:
                base_dir = "data"
                os.makedirs(base_dir, exist_ok=True)
                filename = f"debug_video_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
                save_path = os.path.join(base_dir, filename)
                height, width, _ = annotated_frame.shape
                self.video_writer = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), 5.0, (width, height))
            self.video_writer.write(annotated_frame)

        # 2. 박스 분류: 부모 박스와 속성(자식) 박스를 따로 분류하여 저장
        parent_boxes = []
        attr_boxes_list = {attr: [] for attr in target_attributes}

        for det in detection_results[0].boxes:
            class_id = int(det.cls[0])
            box_coords = det.xyxy[0].cpu().numpy()
            detected_label = search_classes[class_id]

            if detected_label == target_object:
                parent_boxes.append(box_coords)
            elif detected_label in attr_boxes_list:
                attr_boxes_list[detected_label].append(box_coords)

        # 3. 공간 필터링 (Spatial Validation): 
        # 부모 박스 안에 요구된 속성 박스가 모두 겹쳐서 존재하는 녀석만 최종 후보로 선발
        filtered_parent_boxes = []
        for p_box in parent_boxes:
            passed_all_attributes = True
            
            for attr in target_attributes:
                attr_passed = False
                for a_box in attr_boxes_list[attr]:
                    if self._check_overlap(p_box, a_box): # 겹치는지 확인!
                        attr_passed = True
                        break 
                
                if not attr_passed:
                    passed_all_attributes = False
                    break # 요구한 속성 중 하나라도 없으면 이 부모 객체는 버림
            
            if passed_all_attributes:
                filtered_parent_boxes.append(p_box)

        # 통과한 부모 객체가 없다면 여기서 조기 종료
        if not filtered_parent_boxes:
            return cropped_images

        # 4. 정밀 누끼 (SAM Segmentation)
        seg_results = self.segmenter(
            img_array, bboxes=filtered_parent_boxes, device="cuda", verbose=False
        )

        for result in seg_results:
            if result.masks is None:
                continue
            masks = result.masks.data.cpu().numpy()
            
            for mask in masks:
                ys, xs = (mask > 0).nonzero()
                if len(xs) == 0 or len(ys) == 0:
                    continue
                
                x1, x2 = xs.min(), xs.max()
                y1, y2 = ys.min(), ys.max()

                crop_img = img_array[y1:y2, x1:x2]
                crop_mask = mask[y1:y2, x1:x2]

                # 5. 속성 필터링 (Color Validation): 지정된 색상이 있다면 최종 검사
                if target_color:
                    if not self._is_target_color(crop_img, crop_mask, target_color):
                        continue # 색상이 다르면 버림

                # 모든 고난의 필터를 통과한 에셋 수확!
                cropped_images.append(crop_img)

        return cropped_images

    def close_debug_video(self):
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            print("🛑 디버그 비디오 녹화가 안전하게 저장되었습니다.")