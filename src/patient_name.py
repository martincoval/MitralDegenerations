from typing import Optional


def get_patient_name(ds) -> Optional[str]:
    if hasattr(ds, 'PatientName'):
        name = str(ds.PatientName).strip()
        if name and name != "":
            print(f"Name from DICOM tag: {name}")
            return name
    print(f"Name not found in DICOM tag: {ds}")
    return None