import cv2
import numpy as np
import re
from typing import Optional

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


def extract_patient_name(image: np.ndarray) -> Optional[str]:
    if not TESSERACT_AVAILABLE:
        return None

    h, w = image.shape[:2]

    crop_height = int(h * 0.15)
    top_region = image[0:crop_height, :]

    processed = preprocess_for_ocr(top_region)

    try:
        text = pytesseract.image_to_string(processed, config='--psm 6')
        text = text.strip()

        clean_text = re.sub(r'[^a-zA-ZáčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\s]', '', text)
        clean_text = ' '.join(clean_text.split())

        if len(clean_text) > 2:  # alespoň 3 znaky
            return clean_text
    except Exception as e:
        print(f"   ⚠️ OCR selhalo: {e}")
        return None

    return None