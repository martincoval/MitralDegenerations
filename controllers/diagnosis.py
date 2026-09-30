import cv2
import numpy as np
from typing import Optional, Dict, Any


def rescale_calibration(original_mm_per_pixel: float, letterbox_scale: float) -> float:
    """Přepočet kalibrace z originálního rozlišení na velikost masky/modelu."""
    return original_mm_per_pixel / letterbox_scale


def get_diameter_from_mask(mask: np.ndarray, mm_per_pixel: float) -> Optional[Dict[str, float]]:
    """
    Z binární masky (0/1) vyfituje elipsu a vrátí rozměry v mm.
    """
    mask_uint8 = (mask.astype(np.uint8)) * 255
    contours, _ = cv2.findContours(mask_uint8, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    largest = max(contours, key=cv2.contourArea)
    if len(largest) < 5:
        # Pokud je kontura moc malá pro elipsu, vrátíme alespoň ekvivalentní průměr z plochy
        pixels = int(mask.sum())
        diameter_mm = 2.0 * np.sqrt(pixels / np.pi) * mm_per_pixel
        return {
            "minor_axis_mm": diameter_mm,
            "major_axis_mm": diameter_mm,
            "pixel_count": pixels,
        }

    (center, (minor_axis, major_axis), angle) = cv2.fitEllipse(largest)
    return {
        "minor_axis_mm": minor_axis * mm_per_pixel,
        "major_axis_mm": major_axis * mm_per_pixel,
        "pixel_count": int(mask.sum()),
    }


def evaluate_patient_diagnosis(
        aorta_mask: np.ndarray,
        la_mask: np.ndarray,
        lv_mask: np.ndarray,
        original_mm_per_pixel: float,
        scale: float = 0.25,
        body_weight_kg: float = 10.0
) -> Dict[str, Any]:
    """
    Kompletní vyhodnocení vyšetření pro stanovení ACVIM stadia MMVD.
    """
    calib = rescale_calibration(original_mm_per_pixel, scale)

    ao_metrics = get_diameter_from_mask(aorta_mask, calib)
    la_metrics = get_diameter_from_mask(la_mask, calib)
    lv_metrics = get_diameter_from_mask(lv_mask, calib)

    la_ao_ratio = 0.0
    if ao_metrics and ao_metrics["minor_axis_mm"] > 0:
        # Pro LA/Ao se obvykle porovnává majoritní osa nebo průměr
        la_ao_ratio = la_metrics["major_axis_mm"] / ao_metrics["major_axis_mm"] if la_metrics else 0.0

    lvidd_mm = lv_metrics["major_axis_mm"] if lv_metrics else 0.0
    # Normalizace LVIDd (allometrické škálování podle hmotnosti, např. LVIDdN)
    lviddn = lvidd_mm / (body_weight_kg ** 0.294) if body_weight_kg > 0 else 0.0

    # ACVIM logika
    # B1: bez kardiomegalie (LA/Ao < 1.6, LVIDdn < 1.7)
    # B2: kardiomegalie (LA/Ao >= 1.6 a LVIDdn >= 1.7)
    stage = "B1"
    recommendation = "Pacient ve stádiu B1. Kontrola za 6–12 měsíců, farmakoterapie není indikována."

    if la_ao_ratio >= 1.6 and lviddn >= 1.7:
        stage = "B2"
        recommendation = "Pacient ve stádiu B2 (kardiomegalie přítomna). Indikováno zahájení podávání pimobendanu."

    return {
        "LA_mm": la_metrics["major_axis_mm"] if la_metrics else 0.0,
        "Ao_mm": ao_metrics["major_axis_mm"] if ao_metrics else 0.0,
        "LA_Ao_ratio": la_ao_ratio,
        "LVIDd_mm": lvidd_mm,
        "LVIDdn": lviddn,
        "stage": stage,
        "recommendation": recommendation
    }