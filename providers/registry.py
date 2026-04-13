from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import importlib.util
import sys

from providers.base import BaseAnalysisProvider


class AnalysisProviderRegistry:
    _providers: "OrderedDict[str, BaseAnalysisProvider]" = OrderedDict()

    @classmethod
    def register(cls, provider: BaseAnalysisProvider) -> None:
        cls._providers[provider.key] = provider

    @classmethod
    def get(cls, key: str) -> BaseAnalysisProvider:
        return cls._providers[key]

    @classmethod
    def list(cls) -> list[BaseAnalysisProvider]:
        return list(cls._providers.values())

    @classmethod
    def labels(cls) -> list[str]:
        return [provider.label for provider in cls.list()]

    @classmethod
    def by_label(cls, label: str) -> BaseAnalysisProvider:
        for provider in cls.list():
            if provider.label == label:
                return provider
        raise KeyError(label)

    @classmethod
    def default(cls) -> BaseAnalysisProvider:
        if not cls._providers:
            raise RuntimeError("No analysis providers registered.")
        return next(iter(cls._providers.values()))


def load_custom_providers(custom_dir: str | Path = "custom_providers") -> None:
    directory = Path(custom_dir)
    if not directory.exists() or not directory.is_dir():
        return

    for module_path in directory.glob("*.py"):
        if module_path.name.startswith("_"):
            continue
        module_name = f"custom_providers.{module_path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
