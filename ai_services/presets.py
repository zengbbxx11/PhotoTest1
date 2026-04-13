from __future__ import annotations

from ai_services.settings import AIServiceConfig


AI_PROVIDER_PRESETS = {
    "deepseek": {
        "label": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
    },
    "openai": {
        "label": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4.1-mini",
    },
    "siliconflow": {
        "label": "SiliconFlow",
        "base_url": "https://api.siliconflow.cn/v1",
        "model": "deepseek-ai/DeepSeek-V3",
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini",
    },
    "custom": {
        "label": "自定义 OpenAI 兼容接口",
        "base_url": "",
        "model": "",
    },
}


def preset_labels() -> list[str]:
    return [preset["label"] for preset in AI_PROVIDER_PRESETS.values()]


def preset_by_label(label: str) -> tuple[str, dict]:
    for key, preset in AI_PROVIDER_PRESETS.items():
        if preset["label"] == label:
            return key, preset
    return "custom", AI_PROVIDER_PRESETS["custom"]


def apply_preset(config: AIServiceConfig, preset_key: str, keep_api_key: bool = True) -> AIServiceConfig:
    preset = AI_PROVIDER_PRESETS.get(preset_key, AI_PROVIDER_PRESETS["custom"])
    api_key = config.api_key if keep_api_key else ""
    return AIServiceConfig(
        preset_key=preset_key,
        provider_label=preset["label"],
        api_key=api_key,
        base_url=preset["base_url"] or config.base_url,
        model=preset["model"] or config.model,
        system_prompt=config.system_prompt,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
        timeout=config.timeout,
        extra_headers_json=config.extra_headers_json,
    )
