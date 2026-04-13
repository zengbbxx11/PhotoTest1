from __future__ import annotations

import os
from pathlib import Path

from ai_services import AIConfigStore, AIServiceConfig, OpenAICompatibleAIClient
from config import Config
from image_quality_analyzer import ImageQualityAnalyzer
from providers.base import AnalysisArtifact, AnalysisRequest, AnalysisResponse, BaseAnalysisProvider
from report_generator import ReportGenerator


class DefaultPhotoQualityProvider(BaseAnalysisProvider):
    key = "default_photo_quality"
    label = "默认图像质量分析"
    description = "使用当前项目内置的图像质量分析、NR-IQA、EXIF 解释和可配置 AI 接口。"

    def _notify(self, callback, stage: str, current: int, total: int, message: str) -> None:
        if callback is not None:
            callback(stage, current, total, message)

    def _resolve_ai_config(self, request: AnalysisRequest) -> AIServiceConfig:
        metadata = request.metadata or {}
        if "ai_config" in metadata:
            return AIServiceConfig.from_dict(metadata["ai_config"])
        return AIConfigStore.load()

    def _run_ai_analysis(self, successful_artifacts: list[AnalysisArtifact], request: AnalysisRequest) -> None:
        if not request.use_ai_analysis or not successful_artifacts:
            return

        ai_config = self._resolve_ai_config(request)
        client = OpenAICompatibleAIClient(ai_config)

        if not client.is_ready():
            request.metadata.setdefault("warnings", []).append("AI 分析已跳过：API Key / Base URL / Model 未完整配置。")
            return

        payload = [
            {
                "image_path": artifact.image_path,
                "image_name": artifact.image_name,
                "results": artifact.results,
            }
            for artifact in successful_artifacts
        ]

        try:
            ai_results = client.analyze_image_quality(payload)
            analysis_map = {
                item["image_name"]: item["analysis"]
                for item in ai_results
                if "image_name" in item and "analysis" in item
            }
            for artifact in successful_artifacts:
                artifact.ai_analysis = analysis_map.get(artifact.image_name)
        except Exception as exc:
            request.metadata.setdefault("warnings", []).append(f"AI 分析失败: {exc}")

    def analyze(self, request: AnalysisRequest, progress_callback=None) -> AnalysisResponse:
        output_dir = request.output_dir or Config.get_output_dir()
        os.makedirs(output_dir, exist_ok=True)

        total = len(request.image_paths)
        artifacts: list[AnalysisArtifact] = []

        self._notify(progress_callback, "prepare", 0, total, "开始准备分析任务")

        for index, image_path in enumerate(request.image_paths, start=1):
            image_name = os.path.basename(image_path)
            self._notify(progress_callback, "analyze", index - 1, total, f"正在分析 {image_name}")

            try:
                analyzer = ImageQualityAnalyzer(image_path)
                results = analyzer.run_analysis()
                artifacts.append(
                    AnalysisArtifact(
                        image_path=image_path,
                        image_name=image_name,
                        results=results,
                    )
                )
            except Exception as exc:
                artifacts.append(
                    AnalysisArtifact(
                        image_path=image_path,
                        image_name=image_name,
                        success=False,
                        error=str(exc),
                    )
                )

        successful_artifacts = [artifact for artifact in artifacts if artifact.success and artifact.results]
        self._notify(progress_callback, "ai", len(successful_artifacts), total, "正在生成 AI 分析")
        self._run_ai_analysis(successful_artifacts, request)

        for index, artifact in enumerate(successful_artifacts, start=1):
            self._notify(progress_callback, "report", index - 1, len(successful_artifacts), f"正在导出报告 {artifact.image_name}")
            report_filename = Config.get_report_filename(artifact.image_name)
            report_path = str(Path(output_dir) / report_filename)
            generator = ReportGenerator(artifact.image_path, artifact.results, artifact.ai_analysis)
            generator.save(report_path)
            artifact.report_path = report_path

        warnings = request.metadata.get("warnings", [])
        if warnings:
            warning_text = "；".join(warnings)
            self._notify(progress_callback, "warning", len(successful_artifacts), total, warning_text)

        self._notify(progress_callback, "done", total, total, "分析完成")

        return AnalysisResponse(
            provider_key=self.key,
            provider_label=self.label,
            output_dir=output_dir,
            artifacts=artifacts,
        )
