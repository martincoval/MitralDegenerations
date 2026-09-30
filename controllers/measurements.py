import cv2
import numpy as np
from typing import Optional


def get_diameter_from_mask(mask: np.ndarray, mm_per_pixel: float) -> Optional[dict]:
    """
    Z binární masky (0/1) vyfituje elipsu a vrátí rozměry v mm.
    mm_per_pixel musí odpovídat kalibraci PŘEPOČTENÉ na velikost masky
    (tj. původní kalibrace vydělená scale faktorem z letterbox resize).
    """
    mask_uint8 = (mask.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if len(largest) < 5:
        return None
    (center, (minor_axis, major_axis), angle) = cv2.fitEllipse(largest)
    return {
        "minor_axis_mm": minor_axis * mm_per_pixel,
        "major_axis_mm": major_axis * mm_per_pixel,
        "pixel_count": int(mask.sum()),
    }


def rescale_calibration(original_mm_per_pixel: float, letterbox_scale: float) -> float:
    """Přepočet kalibrace z originálního rozlišení na 256x256 verzi."""
    return original_mm_per_pixel / letterbox_scale