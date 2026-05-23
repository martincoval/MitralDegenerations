import os
from pathlib import Path

script_dir = Path(__file__).parent.parent  # scripts/ -> MitralDegenerations/
DICOM_FOLDER = script_dir / "data" / "raw_dicom"

def add_dcm_extension(folder_path:str):
    for item in Path(folder_path).iterdir():
        if item.name == ".DS_Store":
            continue
        if item.is_file() and not item.suffix:
            new_name = item.with_suffix(".dcm")
            item.rename(new_name)
            print(f"Přidána přípona k souboru {item.name}")

if __name__ == "__main__":
    add_dcm_extension(DICOM_FOLDER)