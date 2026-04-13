from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path

try:
    from deepseek_config import AI_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL
except Exception:
    AI_MODEL = ""
    OPENAI_API_KEY = ""
    OPENAI_BASE_URL = ""


DEFAULT_SYSTEM_PROMPT = (
    "你是一名专业的图像质量分析专家，擅长根据量化指标评估照片的清晰度、曝光、噪声、"
    "色彩、压缩痕迹和整体观感。请输出结构清晰、结论明确、可操作的专业分析。"
)


@dataclass
class AIServiceConfig:
    preset_key: str = "deepseek"
    provider_label: str = "DeepSeek"
    api_key: str = OPENAI_API_KEY or ""
    base_url: str = OPENAI_BASE_URL or "https://api.deepseek.com/v1"
    model: str = AI_MODEL or "deepseek-chat"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    temperature: float = 0.3
    max_tokens: int = 900
    timeout: int = 60
    extra_headers_json: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> "AIServiceConfig":
        if not data:
            return cls()
        merged = cls().to_dict()
        merged.update(data)
        return cls(**merged)


class AIConfigStore:
    APP_DIR_NAME = "PhotoQualityWorkbench"
    FILE_NAME = "ai_settings.json"

    @classmethod
    def _base_dir(cls) -> Path:
        local_app_data = os.getenv("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / cls.APP_DIR_NAME
        return Path.home() / ".photo_quality_workbench"

    @classmethod
    def path(cls) -> Path:
        return cls._base_dir() / cls.FILE_NAME

    @classmethod
    def load(cls) -> AIServiceConfig:
        path = cls.path()
        if not path.exists():
            return AIServiceConfig()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return AIServiceConfig.from_dict(data)
        except Exception:
            return AIServiceConfig()

    @classmethod
    def save(cls, config: AIServiceConfig) -> Path:
        path = cls.path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(config.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return path
