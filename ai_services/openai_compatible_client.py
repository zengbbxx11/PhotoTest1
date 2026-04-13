from __future__ import annotations

import json
from typing import Any

import requests

from ai_services.settings import AIServiceConfig


class OpenAICompatibleAIClient:
    def __init__(self, config: AIServiceConfig):
        self.config = config

    def is_ready(self) -> bool:
        return bool(self.config.api_key and self.config.base_url and self.config.model)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.api_key}",
        }
        if self.config.extra_headers_json.strip():
            extra_headers = json.loads(self.config.extra_headers_json)
            if not isinstance(extra_headers, dict):
                raise ValueError("额外请求头必须是 JSON 对象。")
            headers.update({str(key): str(value) for key, value in extra_headers.items()})
        return headers

    def analyze_image_quality(self, analysis_results: list[dict[str, Any]]) -> list[dict[str, str]]:
        responses = []
        for analysis in analysis_results:
            prompt = self._build_prompt(analysis["image_name"], analysis["results"])
            payload = {
                "model": self.config.model,
                "messages": [
                    {
                        "role": "system",
                        "content": self.config.system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
            }

            response = requests.post(
                f"{self.config.base_url.rstrip('/')}/chat/completions",
                headers=self._headers(),
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            response_json = response.json()
            content = response_json["choices"][0]["message"]["content"]
            responses.append(
                {
                    "image_name": analysis["image_name"],
                    "analysis": content,
                }
            )
        return responses

    def _build_prompt(self, image_name: str, results: dict[str, Any]) -> str:
        nr_iqa = results.get("nr_iqa", {})
        capture_analysis = results.get("capture_analysis", {})

        prompt_lines = [
            f"请基于以下量化指标，分析照片 {image_name} 的画质表现。",
            "",
            "请重点输出：",
            "1. 整体结论",
            "2. 主要优点",
            "3. 主要短板",
            "4. 改进建议",
            "",
            "量化结果：",
            f"- 像素相关性: {results['pixel_attributes']['avg_pixel_correlation']:.4f}",
            f"- 纹理强度: {results['pixel_attributes'].get('texture_strength', 0.0):.2f}",
            f"- Laplacian 方差: {results['sharpness']['laplacian_variance']:.2f}",
            f"- Tenengrad: {results['sharpness']['tenengrad']:.2f}",
            f"- 锐度一致性: {results['sharpness']['sharpness_consistency']:.3f}",
            f"- 有效动态范围: {results['dynamic_range']['effective_dynamic_range']:.2f}",
            f"- 曝光偏差: {results['dynamic_range']['exposure_deviation']:.2f}",
            f"- 高光比例: {results['dynamic_range']['highlight_ratio']:.4f}",
            f"- 阴影剪切比例: {results['dynamic_range']['shadow_clip_ratio']:.4f}",
            f"- 白平衡误差: {results['color_reproduction']['white_balance_error']:.4f}",
            f"- 中性像素占比: {results['color_reproduction']['neutral_pixel_ratio']:.4f}",
            f"- 亮度噪声: {results['noise']['luminance_noise']:.2f}",
            f"- 色度噪声峰值: {max(results['noise']['chrominance_noise_u'], results['noise']['chrominance_noise_v']):.2f}",
            f"- 块效应/MP: {results['noise']['block_boundary_artifacts_per_mp']:.0f}",
            f"- 全局对比度: {results['contrast']['global_contrast']:.2f}",
            f"- 局部对比度: {results['contrast']['avg_local_contrast']:.2f}",
            f"- RMS 对比度: {results['contrast']['rms_contrast']:.4f}",
        ]

        if nr_iqa:
            prompt_lines.extend(
                [
                    f"- NR-IQA 总分: {nr_iqa.get('overall_score', 0):.1f}",
                    f"- NR-IQA 等级: {nr_iqa.get('overall_grade', '未知')}",
                    f"- NR-IQA 优势: {', '.join(nr_iqa.get('strengths', [])) or '无'}",
                    f"- NR-IQA 短板: {', '.join(nr_iqa.get('weaknesses', [])) or '无'}",
                ]
            )

        if capture_analysis:
            prompt_lines.extend(
                [
                    f"- EXIF 是否可用: {'是' if capture_analysis.get('metadata_available') else '否'}",
                    f"- 机型: {capture_analysis.get('camera_label', '未读取到')}",
                    f"- ISO: {capture_analysis.get('iso_display', '未读取到')}",
                    f"- 快门: {capture_analysis.get('exposure_time_display', '未读取到')}",
                    f"- 光圈: {capture_analysis.get('f_number_display', '未读取到')}",
                    f"- 焦距: {capture_analysis.get('focal_length_display', '未读取到')}",
                ]
            )

        prompt_lines.extend(
            [
                "",
                "要求：",
                "- 结论清晰，避免空泛表述",
                "- 结合量化指标给出理由",
                "- 如果 EXIF 缺失，请明确说明这会限制结论的确定性",
            ]
        )

        return "\n".join(prompt_lines)
