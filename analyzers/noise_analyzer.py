import cv2
import numpy as np


class NoiseAnalyzer:
    def __init__(self, image):
        self.image = image
        self.image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def _flat_mask(self, luminance):
        mean = cv2.blur(luminance, (7, 7))
        sq_mean = cv2.blur(luminance * luminance, (7, 7))
        local_variance = np.maximum(sq_mean - mean * mean, 0.0)

        threshold = np.percentile(local_variance, 15)
        mask = local_variance <= threshold

        if np.mean(mask) < 0.01:
            threshold = np.percentile(local_variance, 30)
            mask = local_variance <= threshold

        return mask, local_variance

    def _block_artifacts(self, gray):
        block_size = 8
        height, width = gray.shape
        artifact_count = 0

        for row in range(block_size, height, block_size):
            boundary = np.abs(gray[row - 1, :] - gray[row, :])
            artifact_count += int(np.sum(boundary > 10))

        for col in range(block_size, width, block_size):
            boundary = np.abs(gray[:, col - 1] - gray[:, col])
            artifact_count += int(np.sum(boundary > 10))

        megapixels = max((height * width) / 1_000_000.0, 1e-6)
        return artifact_count, float(artifact_count / megapixels)

    def analyze(self):
        ycrcb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2YCrCb).astype(np.float32)
        y_channel, cr_channel, cb_channel = cv2.split(ycrcb_image)
        flat_mask, _ = self._flat_mask(y_channel)
        original_flat_ratio = float(np.mean(flat_mask))
        used_full_frame_fallback = False

        if np.count_nonzero(flat_mask) < 128:
            flat_mask = np.ones_like(y_channel, dtype=bool)
            used_full_frame_fallback = True

        luminance_noise = float(np.std(y_channel[flat_mask]))
        chrominance_noise_u = float(np.std(cb_channel[flat_mask]))
        chrominance_noise_v = float(np.std(cr_channel[flat_mask]))
        flat_region_ratio = float(np.mean(flat_mask))
        noise_confidence = float(min(1.0, original_flat_ratio * 10.0))
        if used_full_frame_fallback:
            noise_confidence = min(noise_confidence, 0.25)

        artifact_raw, artifact_per_mp = self._block_artifacts(self.image_gray)

        return {
            "luminance_noise": luminance_noise,
            "chrominance_noise_u": chrominance_noise_u,
            "chrominance_noise_v": chrominance_noise_v,
            "block_boundary_artifacts": artifact_raw,
            "block_boundary_artifacts_per_mp": artifact_per_mp,
            "flat_region_ratio": flat_region_ratio,
            "noise_confidence": noise_confidence,
        }
