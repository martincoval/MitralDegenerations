import json, math, os
import numpy as np
from PIL import Image, ImageDraw
import cv2

SRC_DIR = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/PSAX"
OUT_BASE = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/samus_dataset/Echocardiography-DogPSAX"
TARGET_SIZE = 256

LABEL_TO_ID = {"aorta": 1, "left_atrium": 2}

img_out = os.path.join(OUT_BASE, "img")
label_out = os.path.join(OUT_BASE, "label")
os.makedirs(img_out, exist_ok=True)
os.makedirs(label_out, exist_ok=True)

def letterbox_resize(arr, target_size, interpolation):
    h, w = arr.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(arr, (new_w, new_h), interpolation=interpolation)
    canvas = np.zeros((target_size, target_size), dtype=arr.dtype)
    top, left = (target_size - new_h) // 2, (target_size - new_w) // 2
    canvas[top:top+new_h, left:left+new_w] = resized
    return canvas, scale

def build_combined_mask(json_path):
    with open(json_path) as f:
        data = json.load(f)
    h, w = data["imageHeight"], data["imageWidth"]
    combined = np.zeros((h, w), dtype=np.uint8)

    for shape in data["shapes"]:
        label = shape["label"].strip().lower().replace(" ", "_")
        class_id = LABEL_TO_ID.get(label)
        if class_id is None:
            print(f"  varování: neznámý label '{label}', přeskočeno")
            continue

        single = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(single)
        if shape["shape_type"] == "circle":
            (cx, cy), (ex, ey) = shape["points"]
            r = math.hypot(ex - cx, ey - cy)
            draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=1, fill=1)
        elif shape["shape_type"] == "polygon":
            pts = [(round(p[0]), round(p[1])) for p in shape["points"]]
            draw.polygon(pts, outline=1, fill=1)
        else:
            continue

        single_arr = np.array(single, dtype=np.uint8)
        combined[single_arr == 1] = class_id

    return combined

json_files = sorted([f for f in os.listdir(SRC_DIR) if f.endswith(".json")])
manifest = []

for idx, jf in enumerate(json_files):
    json_path = os.path.join(SRC_DIR, jf)
    with open(json_path) as f:
        data = json.load(f)
    img_filename = data["imagePath"]
    img_path = os.path.join(SRC_DIR, img_filename)

    if not os.path.exists(img_path):
        print(f"CHYBA: obrázek nenalezen: {img_path} (json: {jf})")
        continue

    print(f"Zpracovávám {jf} -> {img_filename}")

    mask = build_combined_mask(json_path)
    img = np.array(Image.open(img_path).convert("L"))

    mask_resized, scale = letterbox_resize(mask, TARGET_SIZE, cv2.INTER_NEAREST)  # NEAREST! nesmí se rozmazat
    img_resized, _ = letterbox_resize(img, TARGET_SIZE, cv2.INTER_AREA)

    name = f"{idx:04d}_PSAX_000"
    cv2.imwrite(os.path.join(img_out, f"{name}.png"), img_resized)
    cv2.imwrite(os.path.join(label_out, f"{name}.png"), mask_resized)

    print(f"  aorta px: {(mask_resized==1).sum()}, LA px: {(mask_resized==2).sum()}, scale: {scale:.4f}")
    manifest.append({"name": name, "source_json": jf, "scale": scale})

with open(os.path.join(OUT_BASE, "manifest.json"), "w") as f:
    json.dump(manifest, f, indent=2)

print(f"\nHotovo, zpracováno {len(manifest)} snímků.")