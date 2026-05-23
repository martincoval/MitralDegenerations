import os
import json
import cv2
import pydicom
import numpy as np
from pathlib import Path
from typing import Tuple, Dict, Optional, Any

from .utils import normalize_image, resize_keep_aspect_ratio
from .calibration import get_calibration
from .patient_name import get_patient_name

DEFAULT_MM_PER_PIXEL = 0.185
IMAGE_SIZE = (1024, 1024)


def load_dicom_with_calibration(dicom_path: str,
                                  manual_calibration: Optional[float] = None,
                                  verbose: bool = True) -> Tuple[np.ndarray, float, Optional[str]]:
    if verbose:
        print(f"\nProcessing: {os.path.basename(dicom_path)}")

    ds = pydicom.dcmread(dicom_path)

    if not hasattr(ds, 'pixel_array'):
        raise ValueError(f"DICOM does not contain image data")

    image = ds.pixel_array.astype(np.float32)
    if verbose:
        print(f"Original shape: {image.shape}")

    image = normalize_image(image)

    patient_name = get_patient_name(ds)

    if manual_calibration is not None:
        mm_per_pixel = manual_calibration
        if verbose:
            print(f"Calibration: Manual {mm_per_pixel:.4f} mm/pixel")
    else:
        mm_per_pixel = get_calibration(ds)
        if mm_per_pixel is None:
            mm_per_pixel = DEFAULT_MM_PER_PIXEL
            if verbose:
                print(f"Using default calibration {mm_per_pixel:.4f} mm/pixel")

    h, w = image.shape[:2]
    target_h, target_w = IMAGE_SIZE
    ratio = min(target_h / h, target_w / w)
    new_mm_per_pixel = mm_per_pixel / ratio

    image = resize_keep_aspect_ratio(image, IMAGE_SIZE)
    if verbose:
        print(f"After resize: {image.shape}, calibration → {new_mm_per_pixel:.4f} mm/pixel")

    del ds
    return image, new_mm_per_pixel, patient_name


def process_dicom_file(dicom_path: str,
                       output_image_dir: str,
                       manual_calibration: Optional[float] = None,
                       verbose: bool = True) -> Dict[str, Any]:
    image, mm_per_pixel, patient_name = load_dicom_with_calibration(
        dicom_path,
        manual_calibration=manual_calibration,
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


def process_all_dicoms(input_dir: str,
                       output_dir: str,
                       manual_calibration: Optional[float] = None,
                       verbose: bool = True) -> Dict[str, Dict]:
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    input_path = Path(input_dir)
    dicom_files = list(input_path.glob("*.dcm")) + list(input_path.glob("*.DCM"))

    if not dicom_files:
        dicom_files = [f for f in input_path.iterdir() if f.is_file() and not f.name.startswith(".")]

    if not dicom_files:
        print(f"No DICOM files in {input_dir}")
        return {}

    print(f"\nFound {len(dicom_files)} DICOM files")
    print(f"Output: {images_dir}")
    print("=" * 70)

    results = {}
    for dicom_path in dicom_files:
        try:
            result = process_dicom_file(
                str(dicom_path),
                images_dir,
                manual_calibration=manual_calibration,
                verbose=verbose
            )
            results[result["output_image"]] = {
                "mm_per_pixel": result["mm_per_pixel"],
                "patient_name": result["patient_name"],
                "original_file": result["original_file"]
            }
        except Exception as e:
            print(f"Error in {dicom_path.name}: {e}")
            continue

    calib_file = os.path.join(output_dir, "calibrations.json")
    with open(calib_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print(f"Done! {len(results)}/{len(dicom_files)} files converted")
    print(f"JPG: {images_dir}")
    print(f"JSON: {calib_file}")
    print("=" * 70)

    return results