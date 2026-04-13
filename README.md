# 图像质量分析系统

基于 Python 的模块化图像质量分析系统，面向 JPG 实拍照片做相对画质评估。

当前版本除了命令行分析，还提供：

- 可扩展的分析 Provider API
- 可配置 AI 接口的桌面 GUI
- Windows `.exe` 打包脚本

## 核心能力

- 普通实拍照片的锐度、曝光、色彩、噪声、均匀性、对比度分析
- `No-reference IQA` 无参考画质总分
- EXIF / 机型 / 拍摄参数解释分析
- HTML 报告导出
- GUI 可视化操作
- AI 接口可替换、可配置、可持久化保存

## 项目结构

```text
PhotoTest1/
├── analyzers/                  # 核心图像分析模块
├── ai_services/                # 可配置 AI 服务层
│   ├── settings.py
│   ├── presets.py
│   └── openai_compatible_client.py
├── providers/                  # 可扩展分析 Provider API
├── gui/                        # 桌面 GUI
├── packaging_tools/            # Windows 打包脚本
├── custom_providers/           # 用户自定义 provider 目录
├── images/
├── output/
├── image_quality_analyzer.py
├── report_generator.py
├── deepseek_client.py          # 兼容层
├── run_gui.pyw
└── requirements.txt
```

## 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖包括：

- `customtkinter`
- `pyinstaller`

## 命令行使用

### 单张分析

```bash
python image_quality_analyzer.py <image_path>
```

### 批量分析

```bash
python image_quality_analyzer.py
```

分析结果默认输出到 `output/` 目录。

## 桌面 GUI

### 启动方式

```bash
python run_gui.pyw
```

或：

```bash
python -m gui.app
```

### GUI 功能

- 选择单张或多张图片
- 自定义导出目录
- 切换分析 Provider
- 启用 / 关闭 AI 分析
- 配置 AI 接口参数
- 保存 AI 配置到本地
- 后台执行分析任务
- 导出 HTML 报告
- 一键打开导出目录

### GUI 中的 AI 设置

GUI 右侧主界面负责任务操作，左侧栏里有 `AI 设置` 页签。

用户可以直接配置：

- 服务预设
  - DeepSeek
  - OpenAI
  - SiliconFlow
  - OpenRouter
  - 自定义 OpenAI 兼容接口
- API Key
- Base URL
- Model
- Temperature
- Max Tokens
- Timeout
- System Prompt
- 额外请求头 JSON

这意味着如果默认 DeepSeek 接口失效，用户可以直接在 GUI 中换成新的 API，而不需要改代码。

## AI 接口设计

当前 AI 层已经从“写死 DeepSeek”改成了“通用 OpenAI 兼容接口”。

核心模块：

- [ai_services/settings.py](./ai_services/settings.py)
  - AI 配置对象
  - 本地配置文件读写
- [ai_services/presets.py](./ai_services/presets.py)
  - 主流服务预设
- [ai_services/openai_compatible_client.py](./ai_services/openai_compatible_client.py)
  - 通用 `chat/completions` 请求客户端

### 配置保存位置

AI 配置会自动保存到本地用户目录：

- Windows 优先使用 `%LOCALAPPDATA%/PhotoQualityWorkbench/ai_settings.json`

这样打包成 `.exe` 后，普通用户改完 API 配置也能持久保存。

## Provider API

默认 GUI 使用：

- [providers/default_provider.py](./providers/default_provider.py)

它封装了：

- 图像分析
- NR-IQA
- EXIF 维度解释
- HTML 报告导出
- 可配置 AI 分析

### Provider 基础结构

- [providers/base.py](./providers/base.py)
  - `AnalysisRequest`
  - `AnalysisArtifact`
  - `AnalysisResponse`
  - `BaseAnalysisProvider`

- [providers/registry.py](./providers/registry.py)
  - Provider 注册表
  - 自动加载 `custom_providers/`

### 自定义 Provider

如果你后续想替换整套分析逻辑，不只是替换 AI 接口，可以新建 provider 放进 `custom_providers/`。

最小示例：

```python
from providers.base import BaseAnalysisProvider, AnalysisRequest, AnalysisResponse, AnalysisArtifact
from providers.registry import AnalysisProviderRegistry


class MyProvider(BaseAnalysisProvider):
    key = "my_provider"
    label = "我的分析器"
    description = "自定义分析流程"

    def analyze(self, request: AnalysisRequest, progress_callback=None) -> AnalysisResponse:
        artifacts = []
        for image_path in request.image_paths:
            artifacts.append(
                AnalysisArtifact(
                    image_path=image_path,
                    image_name=image_path.split("\\")[-1],
                    results={"message": "custom result"},
                    success=True,
                )
            )

        return AnalysisResponse(
            provider_key=self.key,
            provider_label=self.label,
            output_dir=request.output_dir,
            artifacts=artifacts,
        )


AnalysisProviderRegistry.register(MyProvider())
```

GUI 启动时会自动扫描并加载 `custom_providers/` 目录中的 `.py` 文件。

## EXIF 缺失时的处理

系统已经考虑以下情况：

- 照片没有 EXIF
- EXIF 存在但没有机型字段
- 只有部分拍摄参数

此时系统会：

- 继续完成图像内容分析
- 保留 NR-IQA 总分
- 在 EXIF / 机型分析板块中自动降级
- 在报告中明确提示缺失情况
- 不会因为 EXIF 缺失导致程序报错或中断

## Windows 打包为 `.exe`

### 打包命令

```bash
python packaging_tools/build_windows_exe.py
```

### 默认入口

- [run_gui.pyw](./run_gui.pyw)

### 默认输出目录

```text
dist/
└── PhotoQualityWorkbench/
```

你可以把整个 `PhotoQualityWorkbench` 目录打包给别人使用。

### 打包特点

- 无控制台窗口
- 自动收集 `customtkinter`
- 自动收集 `matplotlib`
- 适合 Win10 / Win11

## 报告内容

导出的 HTML 报告包含：

- 原图预览
- 核心维度概览
- RGB 直方图
- 无参考画质总分
- EXIF / 机型分析
- 各维度指标卡片
- AI 分析摘要

## 使用建议

- 更适合比较同场景、同机型、同时间拍摄的一组图片
- 单张图片建议结合原图预览、核心维度、NR-IQA 和 EXIF 一起看
- 给非技术用户交付时，优先使用 GUI + `.exe`

## 当前限制

- 没有测试卡时，不提供实验室级绝对结论
- GUI 当前主要面向 JPG / JPEG
- 某些第三方 AI 平台若要求特殊 Header，需在“额外请求头 JSON”里手动填写

## 后续可扩展方向

- 批量横向排名
- 更成熟的 no-reference IQA 模型
- 同机型 / 同 ISO / 同焦距维度的统计报告
- 测试卡接入后的 `MTF50`、`DeltaE` 等实验室指标
