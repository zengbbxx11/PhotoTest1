import cv2
import numpy as np


class SharpnessAnalyzer:
    def __init__(self, image):
        self.image = image
        self.image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY).astype(np.float32)

    def _region_energy(self, gradient_energy):
        height, width = gradient_energy.shape
        h_step = max(height // 3, 1)
        w_step = max(width // 3, 1)

        center = gradient_energy[h_step: 2 * h_step, w_step: 2 * w_step]
        edges = np.concatenate(
            [
                gradient_energy[:h_step, w_step: 2 * w_step].ravel(),
                gradient_energy[2 * h_step:, w_step: 2 * w_step].ravel(),
                gradient_energy[h_step: 2 * h_step, :w_step].ravel(),
                gradient_energy[h_step: 2 * h_step, 2 * w_step:].ravel(),
            ]
        )
        corners = np.concatenate(
            [
                gradient_energy[:h_step, :w_step].ravel(),
                gradient_energy[:h_step, 2 * w_step:].ravel(),
                gradient_energy[2 * h_step:, :w_step].ravel(),
                gradient_energy[2 * h_step:, 2 * w_step:].ravel(),
            ]
        )

        center_value = float(np.mean(center)) if center.size else 0.0
        edge_value = float(np.mean(edges)) if edges.size else center_value
        corner_value = float(np.mean(corners)) if corners.size else edge_value
        strongest = max(center_value, edge_value, corner_value, 1e-6)

        return center_value, edge_value, corner_value, float(min(center_value, edge_value, corner_value) / strongest)

    def analyze(self):
        gray_uint8 = self.image_gray.astype(np.uint8)
        laplacian = cv2.Laplacian(self.image_gray, cv2.CV_32F)
        laplacian_variance = float(np.var(laplacian))

        sobel_x = cv2.Sobel(self.image_gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(self.image_gray, cv2.CV_32F, 0, 1, ksize=3)
        gradient_magnitude = cv2.magnitude(sobel_x, sobel_y)
        gradient_energy = gradient_magnitude ** 2
        tenengrad = float(np.mean(gradient_energy))

        median_intensity = float(np.median(gray_uint8))
        lower = int(max(0, 0.66 * median_intensity))
        upper = int(min(255, 1.33 * median_intensity + 15))
        edges = cv2.Canny(gray_uint8, lower, upper)
        edge_density = float(np.count_nonzero(edges) / edges.size)

        edge_widths = []
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            if len(contour) <= 10:
                continue
            perimeter = cv2.arcLength(contour, True)
            area = cv2.contourArea(contour)
            if area > 0:
                edge_widths.append(perimeter / (2.0 * np.sqrt(area)))
        avg_edge_width = float(np.mean(edge_widths)) if edge_widths else 0.0

        center_sharpness, edge_sharpness, corner_sharpness, sharpness_consistency = self._region_energy(gradient_energy)
        sharpness_confidence = float(min(1.0, edge_density * 6.0 + 0.15))

        return {
            "laplacian_variance": laplacian_variance,
            "avg_edge_width": avg_edge_width,
            "tenengrad": tenengrad,
            "edge_density": edge_density,
            "center_sharpness": center_sharpness,
            "edge_sharpness": edge_sharpness,
            "corner_sharpness": corner_sharpness,
            "sharpness_consistency": sharpness_consistency,
            "sharpness_confidence": sharpness_confidence,
        }
