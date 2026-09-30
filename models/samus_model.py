import os
import sys
import numpy as np
import torch
import torch.nn.functional as F

current_dir = os.path.dirname(os.path.abspath(__file__))
samus_net_dir = os.path.join(current_dir, "samus_net")

if samus_net_dir not in sys.path:
    sys.path.insert(0, samus_net_dir)

try:
    from build_samus import build_samus_vit_b
except ImportError:
    from models.samus_net.build_samus import build_samus_vit_b


class ArgsDummy:
    def __init__(self, encoder_input_size=256):
        self.encoder_input_size = encoder_input_size


class SAMUSInference:

    def __init__(
            self,
            checkpoint_path: str = "checkpoints/SAMUS__best_PSAX.pth",
            num_classes: int = 3,
            device: str = "cpu",
    ):
        self.device = torch.device(device)
        self.num_classes = num_classes

        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(f"Checkpoint neexistuje: {checkpoint_path}")

        try:
            args = ArgsDummy(encoder_input_size=256)
            self.model = build_samus_vit_b(args, checkpoint=checkpoint_path)
            self.model.to(self.device)
            self.model.eval()
            print(f"SAMUS načten z '{checkpoint_path}'.")
        except Exception as e:
            print(f"CHYBA načítání checkpointu '{checkpoint_path}': {e}")
            self.model = None

    def predict(
            self,
            image_np: np.ndarray,
            click_la: tuple = None,
            click_ao: tuple = None,
            click_lv: tuple = None,
    ) -> np.ndarray:
        orig_h, orig_w = image_np.shape[:2]

        if image_np.ndim == 3:
            gray = np.mean(image_np, axis=2) if image_np.shape[2] == 3 else image_np[:, :, 0]
        else:
            gray = image_np.astype(np.float32)

        if gray.max() > 1.0:
            gray = gray / 255.0

        tensor = torch.from_numpy(gray).unsqueeze(0).unsqueeze(0).float()

        # Převod na 256x256 pro ViT enkodér
        tensor_256 = F.interpolate(
            tensor, size=(256, 256), mode="bilinear", align_corners=False
        ).to(self.device)

        with torch.no_grad():
            if self.model is None:
                return np.zeros((orig_h, orig_w), dtype=np.uint8)

            if self.num_classes > 2:
                # === PSAX: LA + Ao ===
                if click_la is None or click_ao is None:
                    raise ValueError("Pro PSAX je nutné předat 'click_la' a 'click_ao'!")

                la_x = (float(click_la[0]) / float(orig_w)) * 256.0
                la_y = (float(click_la[1]) / float(orig_h)) * 256.0
                ao_x = (float(click_ao[0]) / float(orig_w)) * 256.0
                ao_y = (float(click_ao[1]) / float(orig_h)) * 256.0

                pt_la_coords = torch.tensor([[[la_x, la_y]]], dtype=torch.float32, device=self.device)
                pt_la_labels = torch.tensor([[1]], dtype=torch.int, device=self.device)
                out_la = self.model(tensor_256, (pt_la_coords, pt_la_labels))
                mask_la_256 = (torch.sigmoid(out_la.get("masks", out_la)) > 0.5).cpu().numpy()[0, 0].astype(np.uint8)

                pt_ao_coords = torch.tensor([[[ao_x, ao_y]]], dtype=torch.float32, device=self.device)
                pt_ao_labels = torch.tensor([[1]], dtype=torch.int, device=self.device)
                out_ao = self.model(tensor_256, (pt_ao_coords, pt_ao_labels))
                mask_ao_256 = (torch.sigmoid(out_ao.get("masks", out_ao)) > 0.5).cpu().numpy()[0, 0].astype(np.uint8)

                combined_256 = np.zeros((256, 256), dtype=np.uint8)
                combined_256[mask_la_256 == 1] = 1
                combined_256[mask_ao_256 == 1] = 2

                mask_tensor = torch.from_numpy(combined_256.astype(np.float32)).unsqueeze(0).unsqueeze(0).float()
                mask_orig = F.interpolate(
                    mask_tensor, size=(orig_h, orig_w), mode="nearest"
                ).squeeze().cpu().numpy().astype(np.uint8)

                return mask_orig

            else:
                # === PLAX: LV (s jemnějším prahem pro správný záchyt komory) ===
                if click_lv is None:
                    raise ValueError("Pro PLAX je nutné předat 'click_lv'!")

                lv_x = (float(click_lv[0]) / float(orig_w)) * 256.0
                lv_y = (float(click_lv[1]) / float(orig_h)) * 256.0

                pt_lv_coords = torch.tensor([[[lv_x, lv_y]]], dtype=torch.float32, device=self.device)
                pt_lv_labels = torch.tensor([[1]], dtype=torch.int, device=self.device)
                out_lv = self.model(tensor_256, (pt_lv_coords, pt_lv_labels))

                # Změna prahu z 0.5 na 0.15, aby model nevynechal pixely levé komory
                mask_lv_256 = (torch.sigmoid(out_lv.get("masks", out_lv)) > 0.15).cpu().numpy()[0, 0].astype(np.uint8)

                mask_tensor = torch.from_numpy(mask_lv_256.astype(np.float32)).unsqueeze(0).unsqueeze(0).float()
                mask_orig = F.interpolate(
                    mask_tensor, size=(orig_h, orig_w), mode="nearest"
                ).squeeze().cpu().numpy().astype(np.uint8)

                return mask_orig