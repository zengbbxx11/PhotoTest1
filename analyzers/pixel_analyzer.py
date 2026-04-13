import cv2
import numpy as np


class PixelAnalyzer:
    def __init__(self, image):
        self.image = image
        self.image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def _sample_indices(self, length, max_samples=32):
        if length <= 1:
            return []
        count = min(length, max_samples)
        return np.unique(np.linspace(0, length - 1, count, dtype=int))

    def _collect_correlations(self, samples):
        correlations = []
        for sample in samples:
            if len(sample) < 2:
                continue
            corr = np.corrcoef(sample[:-1], sample[1:])[0, 1]
            if not np.isnan(corr):
                correlations.append(float(corr))
        return correlations

    def analyze(self):
        height, width = self.image_gray.shape
        total_pixels = int(height * width)

        row_indices = self._sample_indices(height)
        col_indices = self._sample_indices(width)

        row_samples = [self.image_gray[row, :] for row in row_indices]
        col_samples = [self.image_gray[:, col] for col in col_indices]

        correlations = []
        correlations.extend(self._collect_correlations(row_samples))
        correlations.extend(self._collect_correlations(col_samples))

        diagonal_limit = min(height, width)
        if diagonal_limit > 1:
            main_diag = self.image_gray[np.arange(diagonal_limit), np.arange(diagonal_limit)]
            anti_diag = self.image_gray[np.arange(diagonal_limit), width - 1 - np.arange(diagonal_limit)]
            correlations.extend(self._collect_correlations([main_diag, anti_diag]))

        avg_correlation = float(np.mean(correlations)) if correlations else 0.0
        texture_strength = float(np.std(self.image_gray))

        return {
            "width": int(width),
            "height": int(height),
            "total_pixels": total_pixels,
            "avg_pixel_correlation": avg_correlation,
            "texture_strength": texture_strength,
            "sampled_line_count": int(len(row_indices) + len(col_indices) + 2),
        }
