import cv2
import numpy as np
from typing import Tuple

def resize_keep_aspect_ratio(image: np.ndarray, target_size: Tuple[int, int] = (512, 512)) -> np.ndarray:
    target_h, target_w = target_size
    h, w = image.shape[:2]

    ratio = min(target_h / h, target_w / w)
    new_h = int(h * ratio)
    new_w = int(w * ratio)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    if len(image.shape) == 2:
        canvas = np.zeros((target_h, target_w), dtype=image.dtype)
    else:
        canvas = np.zeros((target_h, target_w, image.shape[2]), dtype=image.dtype)

    y_offset = (target_h - new_h) //2
    x_offset = (target_w - new_w) //2
    canvas[y_offset:y_offset + new_h, x_offset:x_offset + new_w] = resized

    return canvas

def normalize_image(image: np.ndarray) -> np.ndarray:
    image = image.astype(np.float32)
    image_min = image.min()
    image_max = image.max()

    if image_max - image_min > 0:
        image = (image - image_min) / (image_max - image_min) * 255
    else:
        image = np.zeros_like(image)

    return image.astype(np.uint8)