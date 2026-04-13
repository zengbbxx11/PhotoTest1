# Custom Providers

把你自己的分析 provider 放在这个目录下即可。

要求：

1. 继承 `providers.base.BaseAnalysisProvider`
2. 在模块加载时调用 `AnalysisProviderRegistry.register(...)`
3. 返回 `AnalysisResponse`

GUI 启动时会自动扫描并导入这个目录下的 `.py` 文件。
