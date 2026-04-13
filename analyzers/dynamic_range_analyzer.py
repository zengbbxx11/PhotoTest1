import cv2
import numpy as np


class DynamicRangeAnalyzer:
    def __init__(self, image):
        self.image = image
        self.image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def _count_histogram_gaps(self, hist, low_index, high_index):
        if high_index <= low_index:
            return 0

        threshold = max(1.0, hist.sum() * 0.00002)
        active = hist[low_index: high_index + 1] > threshold
        gaps = 0
        in_gap = False

        for is_active in active:
            if not is_active and not in_gap:
                gaps += 1
                in_gap = True
            elif is_active:
                in_gap = False

        return int(gaps)

    def analyze(self):
        gray = self.image_gray
        hist = cv2.calcHist([gray.astype(np.uint8)], [0], None, [256], [0, 256]).flatten()

        p1, p5, p50, p95, p99 = np.percentile(gray, [1, 5, 50, 95, 99])
        effective_dynamic_range = float(p99 - p1)

        target_midtone = 118.0
        exposure_bias = float(p50 - target_midtone)
        exposure_deviation = float(abs(exposure_bias))

        low_index = int(np.floor(p1))
        high_index = int(np.ceil(p99))
        consecutive_gaps = self._count_histogram_gaps(hist, low_index, high_index)

        highlight_ratio = float(np.mean(gray >= 250.0))
        shadow_clip_ratio = float(np.mean(gray <= 5.0))
        rgb_clipping_ratio = float(np.mean(np.any(self.image >= 250, axis=2)))
        midtone_coverage = float(np.mean((gray >= p5) & (gray <= p95)))
        exposure_confidence = float(min(1.0, max(0.0, effective_dynamic_range / 140.0)))

        return {
            "effective_dynamic_range": effective_dynamic_range,
            "exposure_deviation": exposure_deviation,
            "exposure_bias": exposure_bias,
            "consecutive_gaps": consecutive_gaps,
            "highlight_ratio": highlight_ratio,
            "shadow_clip_ratio": shadow_clip_ratio,
            "rgb_clipping_ratio": rgb_clipping_ratio,
            "midtone_coverage": midtone_coverage,
            "brightness_p1": float(p1),
            "brightness_p5": float(p5),
            "brightness_p50": float(p50),
            "brightness_p95": float(p95),
            "brightness_p99": float(p99),
            "exposure_confidence": exposure_confidence,
        }
