from typing import Optional


def extract_calibration_from_dicom(ds) -> Optional[float]:
    tag_region = (0x0018, 0x6011)
    if tag_region in ds:
        regions = ds[tag_region].value
        if len(regions) > 0:
            region = regions[0]
            if hasattr(region, 'PhysicalUnitsYDirection') and hasattr(region, 'PhysicalDeltaY'):
                unit = region.PhysicalUnitsYDirection
                delta = region.PhysicalDeltaY
                if unit == 3:
                    return delta * 10
                elif unit == 4:
                    return delta

    if hasattr(ds, 'PixelSpacing'):
        try:
            return float(ds.PixelSpacing[0])
        except (IndexError, ValueError, TypeError):
            pass

    return None


def get_calibration(ds) -> Optional[float]:

    mm_per_pixel = extract_calibration_from_dicom(ds)
    if mm_per_pixel:
        print(f"Calibration from DICOM tags: {mm_per_pixel:.6f} mm/pixel")
    else:
        print(f"Calibration wasn't found in DICOM tags: {ds}")
    return mm_per_pixel