from ai_services import AIConfigStore, OpenAICompatibleAIClient


class DeepSeekClient:
    """
    向后兼容层。
    旧代码仍可通过 DeepSeekClient 调用，但底层已改为通用 OpenAI 兼容接口客户端。
    """

    def __init__(self):
        self.config = AIConfigStore.load()
        self.client = OpenAICompatibleAIClient(self.config)

    def analyze_image_quality(self, analysis_results):
        return self.client.analyze_image_quality(analysis_results)
