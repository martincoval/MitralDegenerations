import json, math, os
import numpy as np
from PIL import Image, ImageDraw
import cv2

TARGET_SIZE = 256

TASKS = {
    "PSAX": {
        "src_dir": "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/PSAX",
        "subtask_name": "Echocardiography-DogPSAX",
        "label_to_id": {"aorta": 1, "left_atrium": 2},
        "frame_code": "PSAX",
    },
    "PLAX": {
        "src_dir": "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/PLAX",
        "subtask_name": "Echocardiography-DogPLAX",
        "label_to_id": {"left_ventriculus": 1},
        "frame_code": "PLAX",
    },
}

OUT_ROOT = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/samus_dataset"

def letterbox_resize(arr, target_size, interpolation):
    h, w = arr.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(round(w * scale)), int(round(h * scale))
    resized = cv2.resize(arr, (new_w, new_h), interpolation=interpolation)
    canvas = np.zeros((target_size, target_size), dtype=arr.dtype)
    top, left = (target_size - new_h) // 2, (target_size - new_w) // 2
    canvas[top:top+new_h, left:left+new_w] = resized
    return canvas, scale

def build_combined_mask(json_path, label_to_id):
    with open(json_path) as f:
        data = json.load(f)
    h, w = data["imageHeight"], data["imageWidth"]
    combined = np.zeros((h, w), dtype=np.uint8)
    for shape in data["shapes"]:
        label = shape["label"].strip().lower().replace(" ", "_")
        class_id = label_to_id.get(label)
        if class_id is None:
            print(f"  varování: neznámý label '{label}' v {os.path.basename(json_path)}, přeskočeno")
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

manifest_all = {}

for task_key, cfg in TASKS.items():
    src_dir = cfg["src_dir"]
    subtask = cfg["subtask_name"]
    label_to_id = cfg["label_to_id"]

    img_out = os.path.join(OUT_ROOT, subtask, "img")
    label_out = os.path.join(OUT_ROOT, subtask, "label")
    os.makedirs(img_out, exist_ok=True)
    os.makedirs(label_out, exist_ok=True)

    json_files = sorted([f for f in os.listdir(src_dir) if f.endswith(".json")])
    manifest = []

    print(f"\n=== {task_key}: {len(json_files)} anotovaných souborů nalezeno ===")

    for idx, jf in enumerate(json_files):
        json_path = os.path.join(src_dir, jf)
        with open(json_path) as f:
            data = json.load(f)
        img_filename = data["imagePath"]
        img_path = os.path.join(src_dir, img_filename)

        if not os.path.exists(img_path):
            print(f"CHYBA: obrázek nenalezen: {img_path} (json: {jf})")
            continue

        mask = build_combined_mask(json_path, label_to_id)
        img = np.array(Image.open(img_path).convert("L"))

        mask_resized, scale = letterbox_resize(mask, TARGET_SIZE, cv2.INTER_NEAREST)
        img_resized, _ = letterbox_resize(img, TARGET_SIZE, cv2.INTER_AREA)

        name = f"{idx:04d}_{cfg['frame_code']}_000"
        cv2.imwrite(os.path.join(img_out, f"{name}.png"), img_resized)
        cv2.imwrite(os.path.join(label_out, f"{name}.png"), mask_resized)

        px_report = ", ".join(f"{k}px:{(mask_resized==v).sum()}" for k, v in label_to_id.items())
        print(f"  {jf} -> {name}  [{px_report}]  scale:{scale:.4f}")

        manifest.append({"name": name, "source_json": jf, "scale": scale, "source_image": img_filename})

    with open(os.path.join(OUT_ROOT, subtask, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    manifest_all[task_key] = manifest
    print(f"{task_key}: zpracováno {len(manifest)} snímků")

print("\nHOTOVO")