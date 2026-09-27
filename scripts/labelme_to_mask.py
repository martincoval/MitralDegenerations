import json
import math
import numpy as np
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt

def labelme_to_masks(json_path):
    with open(json_path) as f:
        data = json.load(f)
    h, w = data["imageHeight"], data["imageWidth"]
    masks = {}

    for shape in data["shapes"]:
        label = shape["label"].strip().lower().replace(" ", "_")
        mask_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask_img)

        if shape["shape_type"] == "circle":
            (cx, cy), (ex, ey) = shape["points"]
            radius = math.hypot(ex - cx, ey - cy)
            bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.ellipse(bbox, outline=1, fill=1)

        elif shape["shape_type"] == "polygon":
            points = [(round(p[0]), round(p[1])) for p in shape["points"]]
            draw.polygon(points, outline=1, fill=1)

        else:
            print(f"Neošetřený shape_type: {shape['shape_type']} u {label}, přeskočeno")
            continue

        mask_arr = np.array(mask_img, dtype=np.uint8)
        masks[label] = mask_arr
        print(f"{label}: {mask_arr.sum()} pixelů")

    return masks


json_path = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/PSAX/001 PSAX.json"
img_path = "/Users/lindamartincova/PycharmProjects/MitralDegenerations/data/PSAX/001 PSAX.jpg"

masks = labelme_to_masks(json_path)

img = Image.open(img_path).convert("L")
img_np = np.array(img)

overlay = np.zeros((*img_np.shape, 3))
overlay[..., 0] = masks.get("left_atrium", 0)   # LA červeně
overlay[..., 1] = masks.get("aorta", 0)         # aorta zeleně

plt.figure(figsize=(8, 8))
plt.imshow(img_np, cmap="gray")
plt.imshow(overlay, alpha=0.5)
plt.title("Kontrola anotace: červená=LA, zelená=aorta")
plt.axis("off")
plt.show()