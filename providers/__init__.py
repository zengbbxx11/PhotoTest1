from providers.base import AnalysisArtifact, AnalysisRequest, AnalysisResponse, BaseAnalysisProvider
from providers.default_provider import DefaultPhotoQualityProvider
from providers.registry import AnalysisProviderRegistry, load_custom_providers


def initialize_providers() -> None:
    if not AnalysisProviderRegistry.list():
        AnalysisProviderRegistry.register(DefaultPhotoQualityProvider())
    load_custom_providers()


__all__ = [
    "AnalysisArtifact",
    "AnalysisRequest",
    "AnalysisResponse",
    "BaseAnalysisProvider",
    "AnalysisProviderRegistry",
    "DefaultPhotoQualityProvider",
    "initialize_providers",
    "load_custom_providers",
]
