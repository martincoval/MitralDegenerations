"""
simple_dicom_tags.py
Jednoduchý výpis všech DICOM tagů - OPRAVENÁ VERZE.
"""

import pydicom
from pathlib import Path

# ===== NASTAVTE CESTU =====
DICOM_PATH = "data/raw_dicom/000000.dcm"  # váš soubor


# =========================


def safe_value_str(value):
    """
    Bezpečně převede hodnotu na řetězec pro výpis.
    Řeší problém s PersonName a jinými speciálními objekty.
    """
    if value is None:
        return "None"

    # Pro PersonName (jméno pacienta) – převedeme na prostý řetězec
    if hasattr(value, 'family_name') or hasattr(value, 'given_name'):
        return str(value)

    # Pro bytes
    if isinstance(value, bytes):
        if len(value) > 50:
            return f"<bytes, délka {len(value)}>"
        return str(value)

    # Pro seznamy a tuple
    if isinstance(value, (list, tuple)):
        if len(value) > 5:
            return f"[{value[0]}, {value[1]}, ...] (délka {len(value)})"
        return str(value)

    # Pro všechno ostatní
    try:
        return str(value)
    except:
        return f"<{type(value).__name__}>"


def print_all_tags_simple(dicom_path: str):
    """Jednoduchý výpis všech tagů."""

    print("=" * 80)
    print(f"📁 Soubor: {dicom_path}")
    print("=" * 80)

    # Načtení DICOM
    ds = pydicom.dcmread(dicom_path)

    print(f"\n📏 Počet tagů: {len(ds)}")
    print("\n" + "-" * 80)

    # Výpis všech tagů (prvních 50, aby to nebylo moc dlouhé)
    count = 0
    for elem in ds:
        value_str = safe_value_str(elem.value)
        print(f"{elem.tag} - {elem.name}: {value_str}")
        count += 1
        if count >= 50:
            print(f"... a {len(ds) - count} dalších tagů")
            break

    print("-" * 80)

    # ===== KONTROLA, ZDA DICOM OBSAHUJE OBRAZ =====
    print("\n" + "=" * 80)
    print("🔍 KONTROLA OBRAZOVÝCH DAT")
    print("=" * 80)

    if hasattr(ds, 'pixel_array'):
        print(f"✅ Obrazová data nalezena!")
        print(f"   Rozměr: {ds.pixel_array.shape}")
        print(f"   Typ dat: {ds.pixel_array.dtype}")
    else:
        print("❌ DICOM neobsahuje obrazová data!")
        print("   Je to pravděpodobně jen hlavička (metadata).")

    return ds


def find_calibration(dicom_path: str):
    """Specializované hledání kalibrace včetně ESAOTE private tagů."""

    ds = pydicom.dcmread(dicom_path)

    print("\n" + "=" * 80)
    print("🔍 HLEDÁNÍ KALIBRAČNÍCH TAGŮ")
    print("=" * 80)

    # Standardní tagy
    standard_tags = [
        (0x0028, 0x0030),  # PixelSpacing
        (0x0018, 0x1164),  # ImagerPixelSpacing
        (0x0018, 0x6024),  # PhysicalDeltaX
        (0x0018, 0x6025),  # PhysicalDeltaY
        (0x0028, 0x0034),  # PixelAspectRatio
        (0x0018, 0x0088),  # SpacingBetweenSlices
        (0x0018, 0x0050),  # SliceThickness
    ]

    found_any = False

    print("\n📌 Standardní tagy:")
    for tag in standard_tags:
        if tag in ds:
            elem = ds[tag]
            print(f"   ✅ {elem.tag} - {elem.name}: {elem.value}")
            found_any = True
        else:
            print(f"   ❌ {hex(tag[0] << 16 | tag[1])} - nenalezen")

    # ===== ESAOTE PRIVATE TAGY =====
    print("\n📌 ESAOTE private tagy (běžné):")

    esaote_tags = [
        0x00511000,
        0x00511001,
        0x00511002,
        0x00511003,
        0x00511004,
        0x00511005,
        0x00511006,
        0x00511007,
        0x00511008,
        0x00511009,
        0x0051100A,
        0x0051100B,
        0x0051100C,
        0x0051100D,
        0x0051100E,
        0x0051100F,
    ]

    esaote_found = False
    for tag_hex in esaote_tags:
        tag = pydicom.tag.Tag(tag_hex)
        if tag in ds:
            elem = ds[tag]
            print(f"   ✅ {elem.tag} - {elem.name}: {elem.value}")
            found_any = True
            esaote_found = True

    if not esaote_found:
        print("   ❌ Žádné z běžných ESAOTE tagů nenalezeny")

    # Hledání všech private tagů
    print("\n📌 Všechny private tagy:")
    private_found = False
    for elem in ds:
        if elem.tag.is_private:
            print(f"   {elem.tag} - {elem.name}: {safe_value_str(elem.value)}")
            private_found = True
            found_any = True

    if not private_found:
        print("   ❌ Žádné private tagy nenalezeny")

    # ===== DŮLEŽITÉ TAGY PRO ROZMĚRY =====
    print("\n📌 Rozměrové tagy:")

    dimension_tags = [
        (0x0028, 0x0010),  # Rows
        (0x0028, 0x0011),  # Columns
    ]

    for tag in dimension_tags:
        if tag in ds:
            elem = ds[tag]
            print(f"   ✅ {elem.tag} - {elem.name}: {elem.value}")
        else:
            print(f"   ❌ {hex(tag[0] << 16 | tag[1])} - nenalezen")

    if not found_any:
        print("\n" + "=" * 80)
        print("❌ NEBYL NALEZEN ŽÁDNÝ KALIBRAČNÍ TAG!")
        print("=" * 80)
        print("\n💡 Doporučení:")
        print("   1. Zkontrolujte nastavení exportu na ultrazvuku")
        print("   2. Zkuste exportovat v jiném formátu (např. JPEG + DICOM)")
        print("   3. Nastavte v kódu výchozí hodnotu mm_per_pixel = 0.185")
    else:
        print("\n" + "=" * 80)
        print("✅ Kalibrační tagy nalezeny! Lze použít automatickou kalibraci.")
        print("=" * 80)

    return found_any


def try_to_extract_image(dicom_path: str):
    """Pokusí se extrahovat obraz z DICOM a uložit ho jako JPG."""

    print("\n" + "=" * 80)
    print("🖼️  EXTRAKCE OBRAZU Z DICOM")
    print("=" * 80)

    ds = pydicom.dcmread(dicom_path)

    if not hasattr(ds, 'pixel_array'):
        print("❌ DICOM neobsahuje obrazová data. Nelze extrahovat.")
        return None

    import numpy as np
    import cv2

    image = ds.pixel_array.astype(np.float32)

    # Normalizace
    image_min = image.min()
    image_max = image.max()

    if image_max - image_min > 0:
        image = (image - image_min) / (image_max - image_min) * 255
    else:
        image = np.zeros_like(image)

    image = image.astype(np.uint8)

    print(f"✅ Obraz extrahován, rozměr: {image.shape}")

    # Uložení zkušebního JPG
    output_path = "data/test_extract.jpg"
    import os
    os.makedirs("data", exist_ok=True)
    cv2.imwrite(output_path, image)
    print(f"✅ Zkušební JPG uložen: {output_path}")

    return image


if __name__ == "__main__":
    # Kontrola existence souboru
    if not Path(DICOM_PATH).exists():
        print(f"❌ Soubor {DICOM_PATH} neexistuje!")
        print(f"\n📁 Vytvořte složku data/raw_dicom/ a vložte do ní DICOM soubor.")
        print(f"   Poté upravte proměnnou DICOM_PATH v tomto skriptu.")
        exit(1)

    # 1. Výpis všech tagů
    ds = print_all_tags_simple(DICOM_PATH)

    # 2. Hledání kalibrace
    find_calibration(DICOM_PATH)

    # 3. Pokus o extrakci obrazu
    try_to_extract_image(DICOM_PATH)

    print("\n" + "=" * 80)
    print("🏁 SKRIPT DOKONČEN")
    print("=" * 80)