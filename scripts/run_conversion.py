import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DICOM_DIR = DATA_DIR / "raw_dicom"
ANONYMIZED_DIR = DATA_DIR / "anonymized"
IMAGES_DIR = ANONYMIZED_DIR / "images"

sys.path.insert(0, str(PROJECT_ROOT))

from src.dicom_processor import process_all_dicoms

def add_dcm_extension(folder_path: Path) -> None:
    print("\n File extension control...")

    renamed_count = 0
    for item in folder_path.iterdir():
        if item.is_file() and not item.suffix and item.name != ".DS_Store":
            new_name = item.with_suffix(".dcm")
            item.rename(new_name)
            print(f"Renamed: {item.name} → {new_name.name}")
            renamed_count += 1

    if renamed_count == 0:
        print("All files were renamed")
    else:
        print(f"Renamed {renamed_count} files")


def run_full_conversion(input_dir: str = None, output_dir: str = None, verbose: bool = True):
    if input_dir is None:
        input_dir = str(Path(__file__).parent.parent / "data" / "raw_dicom")
    if output_dir is None:
        output_dir = str(Path(__file__).parent.parent / "data" / "anonymized")

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    print("=" * 70)
    print("DICOM full conversion...")
    print("=" * 70)
    print(f"Input path: {input_path}")
    print(f"Output path: {output_path}")

    if not input_path.exists():
        print(f"\nInput folder {input_path} nonexistent!")
        print("Creating...")
        input_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {input_path}")
        print("Add your files into this folder and try again.")
        return

    add_dcm_extension(input_path)

    print("\n" + "=" * 70)
    print("Conversion DICOM → JPG")
    print("=" * 70)

    results = process_all_dicoms(
        str(input_path),
        str(output_path),
        verbose=verbose
    )

    if results:
        print("\n" + "=" * 70)
        print("Results overview")
        print("=" * 70)

        for img_name, data in results.items():
            print(f"\n 📸 {img_name}:")
            print(f"Patient: {data['patient_name'] or 'Not found'}")
            print(f"mm/pixel: {data['mm_per_pixel']:.6f}")
            print(f"Original file: {data['original_file']}")

        print("\n" + "=" * 70)
        print(f"Done! {len(results)} files were converted.")
        print(f"JPG: {output_path / 'images'}")
        print(f"JSON: {output_path / 'calibrations.json'}")
        print("=" * 70)
    else:
        print("\nNo files were converted.")
        print("Check your files for the correct extension.")


if __name__ == "__main__":
    run_full_conversion(verbose=True)