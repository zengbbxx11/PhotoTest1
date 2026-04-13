import cv2
import numpy as np


class ColorAnalyzer:
    def __init__(self, image):
        self.image = image

    def analyze(self):
        height, width = self.image.shape[:2]
        lab_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2LAB)
        hsv_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)

        grid_size = 10
        block_height = max(height // grid_size, 1)
        block_width = max(width // grid_size, 1)
        color_means = []

        for i in range(grid_size):
            for j in range(grid_size):
                block = lab_image[i * block_height:(i + 1) * block_height, j * block_width:(j + 1) * block_width]
                if block.size > 0:
                    color_means.append(np.mean(block, axis=(0, 1)))

        color_std = np.std(color_means, axis=0) if color_means else np.array([0.0, 0.0, 0.0])

        saturation = hsv_image[:, :, 1].astype(np.float32)
        value = hsv_image[:, :, 2].astype(np.float32)
        neutral_mask = (saturation < 40) & (value > 32) & (value < 240)
        neutral_pixel_ratio = float(np.mean(neutral_mask))

        if np.count_nonzero(neutral_mask) < 500:
            neutral_mask = (saturation < 60) & (value > 24) & (value < 248)
            neutral_pixel_ratio = float(np.mean(neutral_mask))

        neutral_pixels = self.image[neutral_mask]
        used_fallback_region = False
        if neutral_pixels.size == 0:
            center_y, center_x = height // 2, width // 2
            center_region = self.image[max(center_y - 20, 0):center_y + 20, max(center_x - 20, 0):center_x + 20]
            neutral_pixels = center_region.reshape(-1, 3)
            used_fallback_region = True

        avg_bgr = np.mean(neutral_pixels, axis=0).astype(np.float32)
        safe_mean = max(float(np.mean(avg_bgr)), 1e-6)
        bgr_ratio = avg_bgr / safe_mean
        white_balance_error = float(np.std(bgr_ratio))
        channel_bias = (bgr_ratio - 1.0).tolist()
        white_balance_confidence = float(min(1.0, neutral_pixel_ratio * 20.0))
        if used_fallback_region:
            white_balance_confidence = min(white_balance_confidence, 0.2)

        return {
            "color_uniformity_std": color_std.tolist(),
            "white_balance_error": white_balance_error,
            "channel_bias": channel_bias,
            "neutral_pixel_ratio": neutral_pixel_ratio,
            "white_balance_confidence": white_balance_confidence,
            "neutral_sample_count": int(len(neutral_pixels)),
        }
