import os
import numpy as np

import cv2
from PIL import ExifTags, Image

from analyzers import (
    ColorAnalyzer,
    ContrastAnalyzer,
    DynamicRangeAnalyzer,
    ExifAnalyzer,
    NoiseAnalyzer,
    NrIqaAnalyzer,
    PixelAnalyzer,
    SharpnessAnalyzer,
    UniformityAnalyzer,
)
from config import Config
from report_generator import ReportGenerator


class ImageQualityAnalyzer:
    def __init__(self, image_path):
        self.image_path = image_path
        # 尝试使用OpenCV读取
        self.image = cv2.imread(image_path)
        
        # 如果OpenCV读取失败，尝试使用PIL读取并转换
        if self.image is None:
            try:
                from PIL import Image as PILImage
                pil_image = PILImage.open(image_path)
                # 转换为RGB格式
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                # 转换为OpenCV格式 (BGR)
                self.image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                if self.image is None:
                    raise ValueError(f"无法读取图像文件: {image_path}")
            except Exception as e:
                raise ValueError(f"无法读取图像文件: {image_path}\n错误: {str(e)}")
        
        self.exif_data = self._get_exif_data()
        self.results = {}

    def _get_exif_data(self):
        try:
            image = Image.open(self.image_path)
            exif_data = {}
            exif_items = image._getexif() or {}
            for tag, value in exif_items.items():
                if tag in ExifTags.TAGS:
                    exif_data[ExifTags.TAGS[tag]] = value
            return exif_data
        except Exception:
            return {}

    def run_analysis(self):
        self.results["pixel_attributes"] = PixelAnalyzer(self.image).analyze()
        self.results["sharpness"] = SharpnessAnalyzer(self.image).analyze()
        self.results["dynamic_range"] = DynamicRangeAnalyzer(self.image).analyze()
        self.results["color_reproduction"] = ColorAnalyzer(self.image).analyze()
        self.results["noise"] = NoiseAnalyzer(self.image).analyze()
        self.results["uniformity"] = UniformityAnalyzer(self.image).analyze()
        self.results["contrast"] = ContrastAnalyzer(self.image).analyze()
        self.results["exif"] = self.exif_data
        self.results["nr_iqa"] = NrIqaAnalyzer(self.results).analyze()
        self.results["capture_analysis"] = ExifAnalyzer(self.exif_data, self.results).analyze()
        return self.results


def process_image(image_path):
    analyzer = ImageQualityAnalyzer(image_path)
    results = analyzer.run_analysis()

    print(f"分析完成: {os.path.basename(image_path)}")

    return {
        "image_path": image_path,
        "image_name": os.path.basename(image_path),
        "results": results,
    }


def process_batch():
    input_dir = Config.get_input_dir()

    if not os.path.exists(input_dir):
        print(f"{input_dir} 文件夹不存在")
        return

    image_files = [file_name for file_name in os.listdir(input_dir) if Config.is_supported_image(file_name)]
    if not image_files:
        print(f"{input_dir} 文件夹中没有找到支持的图像文件")
        return

    print(f"找到 {len(image_files)} 个图像，开始分析...")

    analysis_results = []
    for image_file in image_files:
        image_path = os.path.join(input_dir, image_file)
        analysis_results.append(process_image(image_path))

    print("\n正在使用 DeepSeek 进行 AI 分析...")
    try:
        from deepseek_client import DeepSeekClient

        deepseek_client = DeepSeekClient()
        ai_analyses = deepseek_client.analyze_image_quality(analysis_results)
        print("AI 分析完成")
    except Exception as exc:
        print(f"AI 分析失败: {exc}")
        ai_analyses = []

    output_dir = Config.get_output_dir()
    for analysis in analysis_results:
        ai_analysis = None
        for ai_item in ai_analyses:
            if ai_item["image_name"] == analysis["image_name"]:
                ai_analysis = ai_item["analysis"]
                break

        report_generator = ReportGenerator(analysis["image_path"], analysis["results"], ai_analysis)
        report_filename = Config.get_report_filename(analysis["image_name"])
        report_path = os.path.join(output_dir, report_filename)
        report_generator.save(report_path)
        print(f"报告已保存到: {report_path}")

    print(f"\n共分析了 {len(analysis_results)} 个图像，并生成了对应的 HTML 报告。")


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 2:
        process_image(sys.argv[1])
    else:
        process_batch()
