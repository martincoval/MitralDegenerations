import cv2
import numpy as np
from models.dicom_reader import load_dicom_with_calibration

# 1. Načtení přesně toho obrázku, který dostává model po ořezu a úpravách
img_psax, _, _, _ = load_dicom_with_calibration("data/raw_dicom/003 PSAX.dcm")

h, w = img_psax.shape[:2]
print(f"Skutečné rozměry snímku vstupujícího do modelu: šířka={w}, výška={h}")

# Původní zadané souřadnice
la_x, la_y = 374, 583
ao_x, ao_y = 494, 499

# Vykreslení bodů do obrázku (LA = Červená, Ao = Modrá)
debug_img = img_psax.copy()
cv2.circle(debug_img, (la_x, la_y), 10, (0, 0, 255), -1)  # Červená LA
cv2.circle(debug_img, (ao_x, ao_y), 10, (255, 0, 0), -1)  # Modrá Ao

cv2.putText(debug_img, "LA (Cervena)", (la_x + 15, la_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
cv2.putText(debug_img, "Ao (Modra)", (ao_x + 15, ao_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

# Funkce pro kliknutí
def click_event(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f"--> NOVÉ PŘESNÉ SOUŘADNICE: x={x}, y={y}")

cv2.imshow("DEBUG: Zkontroluj pozici bodu (Klikni pro nove souradnice)", debug_img)
cv2.setMouseCallback("DEBUG: Zkontroluj pozici bodu (Klikni pro nove souradnice)", click_event)
cv2.waitKey(0)
cv2.destroyAllWindows()