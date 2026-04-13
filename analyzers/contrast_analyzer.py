import cv2
import numpy as np


class ContrastAnalyzer:
    def __init__(self, image):
        self.image = image
        self.image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def analyze(self):
        gray = self.image_gray / 255.0
        percentile_low, percentile_high = np.percentile(gray, [1, 99])
        global_contrast = float((percentile_high - percentile_low) * 255.0)

        local_mean = cv2.blur(gray, (9, 9))
        local_sq_mean = cv2.blur(gray * gray, (9, 9))
        local_std = np.sqrt(np.maximum(local_sq_mean - local_mean * local_mean, 0.0))
        avg_local_contrast = float(np.mean(local_std) * 255.0)
        rms_contrast = float(np.std(gray))

        return {
            "global_contrast": global_contrast,
            "avg_local_contrast": avg_local_contrast,
            "rms_contrast": rms_contrast,
            "contrast_p1": float(percentile_low * 255.0),
            "contrast_p99": float(percentile_high * 255.0),
        }
