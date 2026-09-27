import os
import json
import pydicom

# UPRAV: import tvé existující funkce na výpočet kalibrace
# (podle toho, jak přesně jmenuješ soubor a funkci z minula)
from models.calibration import get_calibration

# UPRAV: cesta ke složce, kde máš DICOM soubory nových vyšetření
DICOM_DIR = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/dataset_dicom"

# UPRAV: kam se má uložit výsledný JSON s kalibracemi
OUTPUT_JSON = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/calibrations_new.json"


def batch_calibration(dicom_dir: str, output_json: str) -> dict:
    results = {}
    missing = []

    dcm_files = sorted([f for f in os.listdir(dicom_dir) if f.lower().endswith(".dcm")])
    print(f"Nalezeno {len(dcm_files)} DICOM souborů ve složce {dicom_dir}\n")

    for fname in dcm_files:
        path = os.path.join(dicom_dir, fname)
        try:
            ds = pydicom.dcmread(path)
        except Exception as e:
            print(f"CHYBA při čtení {fname}: {e}")
            missing.append(fname)
            continue

        cal = get_calibration(ds)
        results[fname] = cal

        if cal is None:
            print(f"  {fname}: CHYBÍ kalibrace")
            missing.append(fname)
        else:
            print(f"  {fname}: {cal:.6f} mm/pixel")

    with open(output_json, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nHotovo. Zpracováno {len(results)} souborů, uloženo do {output_json}")
    if missing:
        print(f"\nPOZOR — {len(missing)} souborů bez kalibrace nebo s chybou při čtení:")
        for m in missing:
            print(f"  - {m}")
    else:
        print("Všechny soubory mají platnou kalibraci.")

    return results


if __name__ == "__main__":
    batch_calibration(DICOM_DIR, OUTPUT_JSON)