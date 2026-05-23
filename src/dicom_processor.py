import os
import json
import cv2
import pydicom
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, Any

from utils import normalize_image, resize_keep_aspect_ratio
from calibration import detect_scale_bar
from patient_name import extract_patient_name

PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_INPUT_DIR = str(PROJECT_ROOT / "data" / "raw_dicom")
DEFAULT_OUTPUT_DIR = str(PROJECT_ROOT / "data" / "anonymized")


DEFAULT_MM_PER_PIXEL = 0.185
IMAGE_SIZE = (512, 512)


def extract_patient_name_from_dicom(ds) -> Optional[str]:
    if hasattr(ds, 'PatientName'):
        name = str(ds.PatientName).strip()
        if name and name != "":
            return name
    return None


def extract_calibration_from_dicom(ds) -> Optional[float]:
    if hasattr(ds, 'PixelSpacing'):
        try:
            return float(ds.PixelSpacing[0])
        except (IndexError, ValueError, TypeError):
            pass
    return None


def print_dicom_tags_info(ds):
    print("\n Dicom tags (Control):")

    tags_to_check = [
        ('PatientName', 'Jméno pacienta'),
        ('PixelSpacing', 'Kalibrace (mm/pixel)'),
        ('Rows', 'Výška obrazu'),
        ('Columns', 'Šířka obrazu'),
        ('Modality', 'Modalita'),
        ('Manufacturer', 'Výrobce'),
    ]

    for tag_name, description in tags_to_check:
        if hasattr(ds, tag_name):
            value = getattr(ds, tag_name)
            print(f"{description}: {value}")
        else:
            print(f"{description}: Nenalezen")


def load_dicom_with_calibration(dicom_path: str,
                                 manual_calibration: Optional[float] = None,
                                 auto_detect_scale_bar: bool = True,
                                 verbose: bool = True) -> Tuple[np.ndarray, float, Optional[str]]:
    if verbose:
        print(f"\n Zpracovávám: {os.path.basename(dicom_path)}")

    ds = pydicom.dcmread(dicom_path)

    if not hasattr(ds, 'pixel_array'):
        raise ValueError(f"DICOM {dicom_path} neobsahuje obrazová data")

    image = ds.pixel_array.astype(np.float32)
    if verbose:
        print(f"Původní rozměr: {image.shape}")

    image = normalize_image(image)

    if verbose:
        print_dicom_tags_info(ds)

    # Extrakce jména
    patient_name = extract_patient_name_from_dicom(ds)
    if verbose:
        if patient_name:
            print(f"Patient name: {patient_name}")
        else:
            print(f"Patient name: Nenalezen (zkouším OCR...)")
            patient_name = extract_patient_name(image)
            if patient_name:
                print(f"Patient name z OCR: {patient_name}")
            else:
                print(f"Patient name: Nenalezen ani OCR")

    # Extrakce kalibrace
    mm_per_pixel = None

    if manual_calibration is not None:
        mm_per_pixel = manual_calibration
        if verbose:
            print(f"Manual calibration: {mm_per_pixel:.4f} mm/pixel")
    elif extract_calibration_from_dicom(ds) is not None:
        mm_per_pixel = extract_calibration_from_dicom(ds)
        if verbose:
            print(f"Calibration from DICOM tag: {mm_per_pixel:.4f} mm/pixel")
    elif auto_detect_scale_bar:
        if verbose:
            print(f"Searching for scale bar...")
        mm_per_pixel = detect_scale_bar(image)
        if mm_per_pixel:
            if verbose:
                print(f"Calibration from scale bar: {mm_per_pixel:.4f} mm/pixel")
        else:
            if verbose:
                print(f"Scale bar not found, using default: {DEFAULT_MM_PER_PIXEL:.4f} mm/pixel")
            mm_per_pixel = DEFAULT_MM_PER_PIXEL
    else:
        mm_per_pixel = DEFAULT_MM_PER_PIXEL
        if verbose:
            print(f"Calibration: default {mm_per_pixel:.4f} mm/pixel")

    # Změna velikosti
    h, w = image.shape[:2]
    target_h, target_w = IMAGE_SIZE
    ratio = min(target_h / h, target_w / w)
    new_mm_per_pixel = mm_per_pixel / ratio

    image = resize_keep_aspect_ratio(image, IMAGE_SIZE)
    if verbose:
        print(f"After resize: {image.shape}, calibration changed to {new_mm_per_pixel:.4f} mm/pixel")

    del ds

    return image, new_mm_per_pixel, patient_name


def process_dicom_file(dicom_path: str,
                       output_image_dir: str,
                       manual_calibration: Optional[float] = None,
                       auto_detect_scale_bar: bool = True,
                       verbose: bool = True) -> Dict[str, Any]:
    image, mm_per_pixel, patient_name = load_dicom_with_calibration(
        dicom_path,
        manual_calibration=manual_calibration,
        auto_detect_scale_bar=auto_detect_scale_bar,
        verbose=verbose
    )

    input_path = Path(dicom_path)
    output_name = input_path.stem + ".jpg"
    output_path = os.path.join(output_image_dir, output_name)
    cv2.imwrite(output_path, image, [cv2.IMWRITE_JPEG_QUALITY, 95])

    if verbose:
        print(f"Saved: {output_path}")

    return {
        "original_file": input_path.name,
        "output_image": output_name,
        "mm_per_pixel": mm_per_pixel,
        "patient_name": patient_name,
        "image_shape": image.shape
    }


def process_all_dicoms(input_dir: Optional[str] = None,
                       output_dir: Optional[str] = None,
                       manual_calibration: Optional[float] = None,
                       auto_detect_scale_bar: bool = True,
                       verbose: bool = True) -> Dict[str, Dict]:
    # Použij výchozí cesty, pokud nejsou zadány
    if input_dir is None:
        input_dir = DEFAULT_INPUT_DIR
    if output_dir is None:
        output_dir = DEFAULT_OUTPUT_DIR

    print(f"Input directory: {input_dir}")
    print(f"Output directory: {output_dir}")

    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    input_path = Path(input_dir)
    dicom_files = list(input_path.glob("*.dcm")) + list(input_path.glob("*.DCM"))

    if not dicom_files:
        dicom_files = [f for f in input_path.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not dicom_files:
        print(f"No DICOM files found in {input_dir}")
        return {}

    print(f"Found {len(dicom_files)} DICOM files")
    print(f"Output: {images_dir}")
    print("=" * 70)

    results = {}
    for dicom_path in dicom_files:
        try:
            result = process_dicom_file(
                str(dicom_path),
                images_dir,
                manual_calibration=manual_calibration,
                auto_detect_scale_bar=auto_detect_scale_bar,
                verbose=verbose
            )
            results[result["output_image"]] = {
                "mm_per_pixel": result["mm_per_pixel"],
                "patient_name": result["patient_name"],
                "original_file": result["original_file"]
            }
        except Exception as e:
            print(f"Error processing {dicom_path.name}: {e}")
            continue

    calib_file = os.path.join(output_dir, "calibrations.json")
    with open(calib_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"Finished {len(results)}/{len(dicom_files)} DICOM files converted.")
    print(f"JPG: {images_dir}")
    print(f"Calibration + name: {calib_file}")
    print("=" * 70)

    return results