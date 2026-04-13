import math

import numpy as np


class NrIqaAnalyzer:
    def __init__(self, results):
        self.results = results

    def _clamp(self, value, lower=0.0, upper=100.0):
        return float(max(lower, min(upper, value)))

    def _grade_label(self, score):
        if score >= 85:
            return "优秀"
        if score >= 70:
            return "良好"
        if score >= 50:
            return "一般"
        return "待优化"

    def _component(self, key, label, score, description):
        return {
            "key": key,
            "label": label,
            "score": round(score, 1),
            "grade": self._grade_label(score),
            "description": description,
        }

    def analyze(self):
        sharpness = self.results["sharpness"]
        dynamic_range = self.results["dynamic_range"]
        color = self.results["color_reproduction"]
        noise = self.results["noise"]
        uniformity = self.results["uniformity"]
        contrast = self.results["contrast"]

        detail_score = self._clamp(
            math.log1p(sharpness["laplacian_variance"]) * 14.0 * 0.32
            + math.log1p(sharpness["tenengrad"]) * 9.0 * 0.32
            + sharpness["sharpness_consistency"] * 100.0 * 0.18
            + sharpness["sharpness_confidence"] * 100.0 * 0.18
        )

        exposure_score = self._clamp(
            (dynamic_range["effective_dynamic_range"] / 1.8) * 0.32
            + (100.0 - dynamic_range["exposure_deviation"] * 0.9) * 0.33
            + (100.0 - (dynamic_range["highlight_ratio"] + dynamic_range["shadow_clip_ratio"] + dynamic_range["rgb_clipping_ratio"]) * 1600.0) * 0.2
            + dynamic_range["exposure_confidence"] * 100.0 * 0.15
        )

        color_uniformity = np.mean(color["color_uniformity_std"][1:]) if len(color["color_uniformity_std"]) >= 3 else np.mean(color["color_uniformity_std"])
        color_score = self._clamp(
            (100.0 - color["white_balance_error"] * 350.0) * 0.45
            + (100.0 - color_uniformity * 3.0) * 0.2
            + min(100.0, color["neutral_pixel_ratio"] * 2000.0) * 0.15
            + color["white_balance_confidence"] * 100.0 * 0.2
        )

        chroma_noise_peak = max(noise["chrominance_noise_u"], noise["chrominance_noise_v"])
        cleanliness_score = self._clamp(
            (100.0 - noise["luminance_noise"] * 3.0) * 0.38
            + (100.0 - chroma_noise_peak * 4.0) * 0.24
            + (100.0 - math.log1p(noise["block_boundary_artifacts_per_mp"]) * 12.0) * 0.18
            + noise["noise_confidence"] * 100.0 * 0.2
        )

        tonal_score = self._clamp(
            (contrast["global_contrast"] / 2.1) * 0.45
            + math.log1p(contrast["avg_local_contrast"]) * 28.0 * 0.32
            + contrast["rms_contrast"] * 320.0 * 0.13
            + uniformity["uniformity_confidence"] * 100.0 * 0.1
        )

        component_scores = [
            self._component("detail", "细节保留", detail_score, "综合锐度、梯度能量和区域一致性估计清晰感。"),
            self._component("exposure", "曝光控制", exposure_score, "综合曝光偏差、动态范围和剪切风险判断层次保留。"),
            self._component("color", "色彩自然度", color_score, "基于白平衡风险、中性像素和色彩均匀性估计自然度。"),
            self._component("cleanliness", "画面洁净度", cleanliness_score, "结合噪声、色彩噪点和压缩痕迹评估画面纯净度。"),
            self._component("tonal", "层次与反差", tonal_score, "结合全局反差和局部纹理层次判断观感张力。"),
        ]

        weights = {
            "detail": 0.24,
            "exposure": 0.24,
            "color": 0.18,
            "cleanliness": 0.2,
            "tonal": 0.14,
        }
        overall_score = round(sum(component["score"] * weights[component["key"]] for component in component_scores), 1)

        confidence_score = round(
            np.mean(
                [
                    sharpness["sharpness_confidence"],
                    dynamic_range["exposure_confidence"],
                    color["white_balance_confidence"],
                    noise["noise_confidence"],
                    uniformity["uniformity_confidence"],
                ]
            )
            * 100.0,
            1,
        )

        ordered = sorted(component_scores, key=lambda item: item["score"], reverse=True)
        strengths = [item["label"] for item in ordered[:2]]
        weaknesses = [item["label"] for item in ordered[-2:]]

        if overall_score >= 85:
            summary = "整体观感处于较高水平，核心维度比较均衡。"
        elif overall_score >= 70:
            summary = "整体观感较稳，局部短板存在但不至于完全破坏成片质量。"
        elif overall_score >= 50:
            summary = "整体处于可用到一般之间，建议优先关注短板维度。"
        else:
            summary = "整体主观画质偏弱，建议先处理明显缺陷后再做横向比较。"

        return {
            "overall_score": overall_score,
            "overall_grade": self._grade_label(overall_score),
            "confidence_score": confidence_score,
            "confidence_grade": self._grade_label(confidence_score),
            "summary": summary,
            "components": component_scores,
            "strengths": strengths,
            "weaknesses": weaknesses,
        }
