# 图像质量分析系统

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/OpenCV-4.x-green.svg" alt="OpenCV">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="MIT License">
</p>

<p align="center">
  <b>基于 Python 的模块化图像质量分析系统，面向 JPG 实拍照片做相对画质评估</b>
</p>

---

## 📋 目录

- [功能特性](#-功能特性)
- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [使用指南](#-使用指南)
  - [命令行使用](#命令行使用)
  - [GUI 使用](#gui-使用)
- [核心分析维度](#-核心分析维度)
- [AI 接口配置](#-ai-接口配置)
- [自定义扩展](#-自定义扩展)
- [打包分发](#-打包分发)
- [常见问题](#-常见问题)

---

## ✨ 功能特性

### 图像质量分析
- **锐度评估** - Laplacian 方差、边缘宽度分析
- **动态范围** - 有效动态范围、曝光偏差、高光溢出检测
- **色彩还原** - 色彩均匀性、白平衡误差分析
- **噪声分析** - 亮度噪声、色度噪声、块效应检测
- **均匀性分析** - 亮度分布、暗角比例检测
- **对比度分析** - 全局对比度、局部对比度

### 智能分析
- **无参考画质评估** - 基于 NR-IQA 的综合评分
- **EXIF 解析** - 机型识别、拍摄参数分析
- **AI 智能分析** - 接入 DeepSeek/OpenAI 等接口，提供专业建议

### 输出报告
- 📊 **HTML 可视化报告** - 包含图表、表格和详细分析
- 📈 **像素分布直方图** - RGB 通道可视化
- 🎯 **质量雷达图** - 多维度综合评估

### 使用方式
- 💻 **命令行工具** - 适合批量处理和自动化
- 🖥️ **桌面 GUI** - 现代化界面，操作便捷
- 📦 **独立 EXE** - 无需 Python 环境，开箱即用

---

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- Windows 10/11（GUI 和打包功能）
- 4GB 以上内存（推荐 8GB）

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd PhotoTest1
```

2. **创建虚拟环境（推荐）**
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

**主要依赖**：
- `numpy` - 数值计算
- `opencv-python` - 图像处理
- `pillow` - 图像处理和 EXIF 读取
- `scipy` - 科学计算
- `matplotlib` - 图表生成
- `imageio` - 图像 I/O
- `pyexiftool` - EXIF 数据提取
- `scikit-image` - 图像处理算法
- `requests` - HTTP 请求
- `customtkinter` - 现代化 GUI
- `pyinstaller` - 打包工具

4. **启动 GUI**
```bash
python run_gui.pyw
```

---

## 📁 项目结构

```
PhotoTest1/
├── 📂 analyzers/               # 核心图像分析模块
│   ├── pixel_analyzer.py       # 像素基础属性
│   ├── sharpness_analyzer.py   # 锐度评估
│   ├── dynamic_range_analyzer.py # 动态范围与曝光
│   ├── color_analyzer.py       # 色彩还原
│   ├── noise_analyzer.py       # 噪声分析
│   ├── uniformity_analyzer.py  # 均匀性分析
│   ├── contrast_analyzer.py    # 对比度分析
│   ├── nr_iqa_analyzer.py      # 无参考画质评估
│   └── exif_analyzer.py        # EXIF 数据解析
│
├── 📂 ai_services/             # AI 服务层
│   ├── settings.py             # 配置管理
│   ├── presets.py              # 服务预设
│   └── openai_compatible_client.py # 通用客户端
│
├── 📂 providers/               # 分析 Provider API
│   ├── base.py                 # 基础抽象类
│   ├── default_provider.py     # 默认实现
│   └── registry.py             # 注册表
│
├── 📂 gui/                     # 桌面 GUI
│   ├── app.py                  # 主应用
│   └── components/             # 界面组件
│
├── 📂 packaging_tools/         # 打包工具
├── 📂 custom_providers/        # 自定义 Provider
├── 📂 images/                  # 待分析图片目录
├── 📂 output/                  # 分析结果输出目录
│
├── 🐍 image_quality_analyzer.py  # 命令行入口
├── 🐍 report_generator.py        # 报告生成器
├── 🐍 run_gui.pyw                # GUI 启动脚本
└── 📄 requirements.txt           # 依赖列表
```

---

## 📖 使用指南

### 命令行使用

#### 单张图片分析
```bash
python image_quality_analyzer.py path/to/image.jpg
```

#### 批量分析（images 目录）
```bash
python image_quality_analyzer.py
```

**输出位置**：`output/<图片名>_quality_report.html`

---

### GUI 使用

#### 启动方式
```bash
# 方式一
python run_gui.pyw

# 方式二
python -m gui.app
```

#### 操作步骤

1. **选择图片**
   - 点击"选择图片"按钮
   - 支持多选（Ctrl/Shift + 点击）
   - 支持 JPG、JPEG、PNG 格式

2. **配置选项**
   - 设置导出目录（默认 output/）
   - 选择分析 Provider
   - 启用/禁用 AI 分析

3. **开始分析**
   - 点击"开始分析"按钮
   - 等待进度完成
   - 自动打开报告或导出目录

#### AI 设置

在左侧"AI 设置"页签中配置：

| 配置项 | 说明 | 示例 |
|--------|------|------|
| 服务预设 | 快速选择主流服务 | DeepSeek / OpenAI |
| API Key | 服务商提供的密钥 | sk-xxx... |
| Base URL | API 接口地址 | https://api.xxx.com/v1 |
| Model | 模型名称 | deepseek-chat |
| Temperature | 创造性程度 | 0.7 |
| Max Tokens | 最大输出长度 | 2000 |

**支持的 AI 服务**：
- DeepSeek
- OpenAI
- SiliconFlow
- OpenRouter
- 自定义 OpenAI 兼容接口

---

## 🔬 核心分析维度

### 1. 像素基础属性
| 指标 | 说明 |
|------|------|
| 图像尺寸 | 宽 x 高（像素） |
| 总像素数 | 百万像素（MP） |
| 平均像素相关性 | 相邻像素相关性分析 |
| 纹理强度 | 图像纹理丰富程度 |

### 2. 锐度评估
| 指标 | 说明 | 参考范围 |
|------|------|----------|
| Laplacian 方差 | 整体清晰度 | > 100 较好 |
| 平均边缘宽度 | 边缘锐利程度 | < 2.0 较好 |

### 3. 动态范围与曝光
| 指标 | 说明 | 参考范围 |
|------|------|----------|
| 有效动态范围 | 可用亮度范围 | > 8 EV 较好 |
| 曝光偏差 | 曝光准确度 | ±0.5 EV 内较好 |
| 色阶断层数 | 色彩过渡平滑度 | 越少越好 |
| 高光溢出比例 | 过曝区域占比 | < 5% 较好 |

### 4. 色彩还原
| 指标 | 说明 | 参考范围 |
|------|------|----------|
| 色彩均匀性 | 色彩分布一致性 | < 20 较好 |
| 白平衡误差 | 色温准确度 | < 10 较好 |

### 5. 噪声分析
| 指标 | 说明 | 参考范围 |
|------|------|----------|
| 亮度噪声 | Y 通道噪声水平 | < 5 较好 |
| 色度噪声(U) | U 通道噪声 | < 3 较好 |
| 色度噪声(V) | V 通道噪声 | < 3 较好 |
| 块效应 | JPEG 压缩 artifacts | < 1.0 较好 |

### 6. 均匀性分析
| 指标 | 说明 | 参考范围 |
|------|------|----------|
| 亮度标准差 | 亮度分布均匀性 | < 30 较好 |
| 亮度最大差异 | 最亮与最暗区域差异 | < 80 较好 |
| 暗角比例 | 边缘暗角程度 | < 15% 较好 |

### 7. 对比度分析
| 指标 | 说明 | 参考范围 |
|------|------|----------|
| 全局对比度 | 整体明暗对比 | > 50 较好 |
| 平均局部对比度 | 局部细节对比 | > 30 较好 |

---

## 🤖 AI 接口配置

### 配置保存位置

AI 配置自动保存到本地用户目录：

- **Windows**: `%LOCALAPPDATA%/PhotoQualityWorkbench/ai_settings.json`

这样打包成 `.exe` 后，普通用户改完 API 配置也能持久保存。

### 快速配置示例

#### DeepSeek
```json
{
  "base_url": "https://api.deepseek.com/v1",
  "api_key": "sk-your-api-key",
  "model": "deepseek-chat",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

#### OpenAI
```json
{
  "base_url": "https://api.openai.com/v1",
  "api_key": "sk-your-api-key",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

---

## 🔧 自定义扩展

### 自定义 Provider

如果你想替换整套分析逻辑，可以新建 provider 放进 `custom_providers/`。

**最小示例**：

```python
from providers.base import (
    BaseAnalysisProvider, 
    AnalysisRequest, 
    AnalysisResponse, 
    AnalysisArtifact
)
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


# 注册 Provider
AnalysisProviderRegistry.register(MyProvider())
```

GUI 启动时会自动扫描并加载 `custom_providers/` 目录中的 `.py` 文件。

---

## 📦 打包分发

### 打包为 Windows EXE

```bash
python packaging_tools/build_windows_exe.py
```

### 输出目录

```
dist/
└── PhotoQualityWorkbench/
    ├── PhotoQualityWorkbench.exe
    └── _internal/
```

### 打包特点

- ✅ 无控制台窗口
- ✅ 自动收集 `customtkinter`
- ✅ 自动收集 `matplotlib`
- ✅ 适合 Win10 / Win11
- ✅ 包含所有依赖，无需额外安装

### 分发方式

将整个 `PhotoQualityWorkbench` 目录压缩后分发给用户，用户直接运行 `PhotoQualityWorkbench.exe` 即可。

---

## ❓ 常见问题

### Q: 图片无法读取怎么办？

**A:** 系统采用双重读取机制：
1. 首先尝试 OpenCV 读取
2. 失败时自动使用 PIL 作为备用

如果仍然失败，请检查：
- 图片格式是否支持（JPG、JPEG、PNG）
- 图片文件是否损坏
- 文件路径是否正确

### Q: AI 分析失败怎么办？

**A:** 请检查以下配置：
- API Key 是否正确
- Base URL 是否可访问
- 网络连接是否正常
- 尝试更换其他 AI 服务

### Q: 打包失败怎么办？

**A:** 请检查：
- 所有依赖是否已正确安装
- PyInstaller 版本是否兼容
- 项目路径是否包含非 ASCII 字符

### Q: EXIF 信息缺失会影响分析吗？

**A:** 不会。系统会：
- 继续完成图像内容分析
- 保留 NR-IQA 总分
- 在报告中提示缺失情况
- 不会因为 EXIF 缺失导致程序报错

---

## 📝 使用建议

1. **批量比较**：更适合比较同场景、同机型、同时间拍摄的一组图片
2. **单张分析**：建议结合原图预览、核心维度、NR-IQA 和 EXIF 一起看
3. **非技术用户**：优先使用 GUI + `.exe` 方式交付
4. **自动化**：命令行方式适合集成到工作流中

---

## 🚧 当前限制

- 没有测试卡时，不提供实验室级绝对结论
- GUI 当前主要面向 JPG / JPEG 格式
- 某些第三方 AI 平台若要求特殊 Header，需在"额外请求头 JSON"里手动填写

---

##  许可证

MIT License

---

## 🤝 贡献

欢迎提交 issue 和 pull request，帮助改进这个项目。

---

## 📧 联系方式

如有问题或建议，请通过项目 issue 与我们联系。
