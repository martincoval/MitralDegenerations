import cv2
import numpy as np
import re
from typing import Tuple, Optional, List

try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    print("Pytesseract not available. OCR wont work.")

def preprocess_for_ocr(roi: np.ndarray) -> np.ndarray:
    if roi.size == 0:
        return roi
    gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    return thresh

def read_label_from_roi(roi: np.ndarray) -> Optional[Tuple[float, str]]:
    if not TESSERACT_AVAILABLE or roi.size == 0:
        return None

    processed = preprocess_for_ocr(roi)
    try:
        text = pytesseract.image_to_string(processed, config='--psm 6')
        text = text.lower().strip()
        match = re.search(r'(d+(?:\.\d+)?)\s*(cm|mm)', text)
        if match:
            value = float(match.group(1))
            unit = match.group(2)
            return value, unit
    except Exception:
        pass
    return None

def is_likely_scale_bar(w: int, h: int, img_w: int, img_h: int, x: int, y: int) -> bool:
    if max(w, h) < 20 or max(w, h) > 500:
        return False

    if max(w, h) < 3 * min(w, h):
        return False

    margin_ratio = 0.2
    near_left = x < img_w * margin_ratio
    near_right = x + w > img_w * (1-margin_ratio)
    near_top = y < img_h * margin_ratio
    near_bottom = y + h > img_h * (1-margin_ratio)

    return near_left or near_right or near_top or near_bottom

def detect_scale_bar(image: np.ndarray) -> Optional[float]:
    img_h, img_w = image.shape[:2]

    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    best_scale = None
    best_length_px = 0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)

        if not is_likely_scale_bar(w, h, img_w, img_h, x, y):
            continue

        length_px = max(w, h)
        is_horizontal = (w > h)

        label_value = None
        label_unit = None

        if is_horizontal:
            roi_top = image[max(0, y-40):y, x:x+w]
            label = read_label_from_roi(roi_top)
            if label:
                label_value, label_unit = label
            else:
                roi_bottom = image[y+h:min(img_h, y+h+40), x:x+w]
                label = read_label_from_roi(roi_bottom)
                if label:
                    label_value, label_unit = label
        else:
            roi_left = image[y:y+h, max(0, x-40):x]
            label = read_label_from_roi(roi_left)
            if label:
                label_value, label_unit = label
            else:
                roi_right = image[y:y+h, x+w:min(img_w, x+w+40)]
                label = read_label_from_roi(roi_right)
                if label:
                    label_value, label_unit = label

        if label_value and label_unit:
            if label_unit == 'cm':
                length_mm = label_value * 10
            else:
                length_mm = label_value

            mm_per_pixel = length_mm / length_px
            return mm_per_pixel
        else:
            if length_px > best_length_px:
                best_length_px = length_px
                best_scale = 10.0 / length_px

    if best_scale:
        return best_scale

    return None