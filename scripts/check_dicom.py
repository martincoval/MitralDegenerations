import pydicom
import sys

path = sys.argv[1]
ds = pydicom.dcmread(path)

print("Pixel spacing (kalibrace):", ds.get("PixelSpacing", "nenalezeno"))
print("Jméno pacienta:", ds.get("PatientName", "nenalezeno"))
print("Rozměr obrazu:", ds.pixel_array.shape)

