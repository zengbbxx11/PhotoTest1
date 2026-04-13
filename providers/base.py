from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable


ProgressCallback = Callable[[str, int, int, str], None]


@dataclass
class AnalysisRequest:
    image_paths: list[str]
    output_dir: str
    use_ai_analysis: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisArtifact:
    image_path: str
    image_name: str
    report_path: str | None = None
    results: dict[str, Any] | None = None
    ai_analysis: str | None = None
    success: bool = True
    error: str | None = None


@dataclass
class AnalysisResponse:
    provider_key: str
    provider_label: str
    output_dir: str
    artifacts: list[AnalysisArtifact]
    generated_at: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def success_count(self) -> int:
        return sum(1 for item in self.artifacts if item.success)

    @property
    def failure_count(self) -> int:
        return sum(1 for item in self.artifacts if not item.success)


class BaseAnalysisProvider(ABC):
    key: str = "base"
    label: str = "Base Provider"
    description: str = "Abstract analysis provider."

    @abstractmethod
    def analyze(
        self,
        request: AnalysisRequest,
        progress_callback: ProgressCallback | None = None,
    ) -> AnalysisResponse:
        raise NotImplementedError
