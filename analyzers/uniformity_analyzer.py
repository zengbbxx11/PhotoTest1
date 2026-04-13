import cv2
import numpy as np


class UniformityAnalyzer:
    def __init__(self, image):
        self.image = image
        self.image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def analyze(self):
        height, width = self.image_gray.shape
        grid_size = 10
        block_height = max(height // grid_size, 1)
        block_width = max(width // grid_size, 1)
        brightness_means = []

        for i in range(grid_size):
            for j in range(grid_size):
                block = self.image_gray[i * block_height:(i + 1) * block_height, j * block_width:(j + 1) * block_width]
                if block.size > 0:
                    brightness_means.append(float(np.mean(block)))

        brightness_std = float(np.std(brightness_means)) if brightness_means else 0.0
        brightness_max_diff = float(np.max(brightness_means) - np.min(brightness_means)) if brightness_means else 0.0

        center_region = self.image_gray[height // 4:3 * height // 4, width // 4:3 * width // 4]
        corner_regions = [
            self.image_gray[:height // 4, :width // 4],
            self.image_gray[:height // 4, 3 * width // 4:],
            self.image_gray[3 * height // 4:, :width // 4],
            self.image_gray[3 * height // 4:, 3 * width // 4:],
        ]

        center_brightness = float(np.mean(center_region)) if center_region.size else 0.0
        corner_brightness = float(np.mean([np.mean(region) for region in corner_regions if region.size])) if corner_regions else 0.0
        vignetting_ratio = float(corner_brightness / center_brightness) if center_brightness > 0 else 0.0

        sobel_x = cv2.Sobel(self.image_gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(self.image_gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient = cv2.magnitude(sobel_x, sobel_y)
        scene_complexity = float(np.mean(gradient > 12.0))
        uniformity_confidence = float(max(0.0, min(1.0, 1.0 - scene_complexity * 2.5)))

        return {
            "brightness_std": brightness_std,
            "brightness_max_diff": brightness_max_diff,
            "vignetting_ratio": vignetting_ratio,
            "scene_complexity": scene_complexity,
            "uniformity_confidence": uniformity_confidence,
        }
