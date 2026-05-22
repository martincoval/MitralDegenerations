import os
import json
import pydicom
import numpy as np
import cv2
from pathlib import Path
from tqdm import tqdm
from typing import Dict, Tuple
import matplotlib.pyplot as plt

INPUT_DIR = "data/raw_dicom"
OUTPUT_DIR = "data/anonymized"
IMAGE_SIZE = (512, 512)

def load_dicom_anonymous(dicom_path:str) -> Tuple[np.ndarray, float]:
    ds = pydicom.dcmread(dicom_path)
    image = ds.pixel_array.astype(np.float32)
    image_min = image.min()
    image_max = image.max()

    if image_max - image_min > 0:
        image = (image - image_min)/(image_max - image_min) * 255
    else:
        image = np.zeros_like(image)

    image = image.astype(np.uint8)
    if image.shape != IMAGE_SIZE:
        image = cv2.resize(image, IMAGE_SIZE, interpolation=cv2.INTER_LINEAR)

    try:
        pixel_spacing = ds.PixelSpacing
        mm_per_pixel = float(pixel_spacing[0])
    except (AttributeError, IndexError, TypeError):
        print(f"Varování, {dicom_path} nemá pixel spacing tag. Nastavuji 0,185 mm/pixel")
        mm_per_pixel = 0.185

    del ds

    return image, mm_per_pixel

def save_image_without_metadata(image:np.ndarray, output_path:str) -> None:
    cv2.imwrite(output_path, image, [ cv2.IMWRITE_JPEG_QUALITY, 95])

def process_all_dicoms(input_dir:str, output_dir:str) -> Dict[str, float]:
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)

    input_path = Path(input_dir)
    dicom_files = list(input_path.glob("*.dcm")) + list(input_path.glob("*.DCM"))

    if not dicom_files:
        print("Chyba: Nebyl nalezen žádný DICOM soubor...")
        print("Podporované přípony .dcm, .DCM")
        return {}

    print(f"Nalezeno {len(dicom_files)} DICOM souborů")
    print(f"Výstup {images_dir}")
    print(f"Velikost výstupních obrázků {IMAGE_SIZE[0]}*{IMAGE_SIZE[1]}")
    print("-" * 50)

    calibrations = {}

    for dicom_path in tqdm(dicom_files, desc="Konverze DICOM -> JPG"):
        try:
            image, mm_per_pixel = load_dicom_anonymous(str(dicom_path))

            output_name = dicom_path.stem + ".jpg"
            output_path = os.path.join(images_dir, output_name)
            save_image_without_metadata(image, output_path)

            calibrations[output_name] = mm_per_pixel

        except Exception as e:
            print(f"Chyba u {dicom_path.name}: {e}")
            continue

    calib_file = os.path.join(output_dir, "calibrations.json")
    with open(calib_file, "w", encoding="utf-8") as f:
        json.dump(calibrations, f, indent=2, ensure_ascii=False)

    print("-" * 50)
    print("Hotovo!")
    print(f"JPG obrázky: {images_dir}")
    print(f"Kalibrace: {calib_file}")
    print(f"Úspěšně převedeno: {len(calibrations)}/{len(dicom_files)}")

    return calibrations

def preview_image(image_path:str) -> None:
    image = cv2.imread(image_path)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    plt.figure(figsize=(8,8))
    plt.imshow(image, cmap="gray")
    plt.title(f"Náhled: {os.path.basename(image_path)}")
    plt.axis("off")
    plt.show()

if __name__ == "__main__":
    print("=" * 50)
    print("DICOM -> JPG konvertor s anonymizací")
    print("=" * 50)

    if not os.path.exists(INPUT_DIR):
        print(f"Chyba: Vstupní složka {INPUT_DIR} neexistuje!")
        print("Vytvořte ji a vložte do ní DICOM soubory.")
        exit(1)

    calibrations = process_all_dicoms(INPUT_DIR, OUTPUT_DIR)

    if calibrations:
        images_dir = os.path.join(OUTPUT_DIR, "images")
        first_image = list(calibrations.keys())[0]
        first_image_path = os.path.join(images_dir, first_image)

        print("Chcete zobrazit náhled prvního obrázku? (y/n)")
        if input().lower() == "y":
            preview_image(first_image_path)