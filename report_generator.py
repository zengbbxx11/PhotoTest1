import base64
import html
import os
import re
from datetime import datetime
from io import BytesIO

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt


class ReportGenerator:
    def __init__(self, image_path, results, ai_analysis=None):
        self.image_path = image_path
        self.results = results
        self.ai_analysis = ai_analysis or ""
        self.image_name = os.path.basename(image_path)
        self._configure_matplotlib()

    def _configure_matplotlib(self):
        plt.rcParams["font.sans-serif"] = [
            "Microsoft YaHei",
            "SimHei",
            "Noto Sans CJK SC",
            "Arial Unicode MS",
            "DejaVu Sans",
        ]
        plt.rcParams["axes.unicode_minus"] = False

    def _clamp(self, value, lower=0.0, upper=100.0):
        return float(max(lower, min(upper, value)))

    def _format_number(self, value, decimals=2, percent=False):
        if isinstance(value, (int, np.integer)):
            text = f"{int(value):,}"
        else:
            text = f"{float(value):,.{decimals}f}"
        return f"{text}%" if percent else text

    def _status_class(self, score):
        if score >= 85:
            return "excellent"
        if score >= 70:
            return "good"
        if score >= 50:
            return "fair"
        return "weak"

    def _status_label(self, score):
        return {
            "excellent": "优秀",
            "good": "良好",
            "fair": "一般",
            "weak": "待优化",
        }[self._status_class(score)]

    def _metric(self, label, value, score, note):
        return {
            "label": label,
            "value": value,
            "score": round(score, 1),
            "status_class": self._status_class(score),
            "status_label": self._status_label(score),
            "note": note,
        }

    def _section(self, section_id, title, description, score, metrics):
        best_metric = max(metrics, key=lambda item: item["score"])
        weakest_metric = min(metrics, key=lambda item: item["score"])
        return {
            "id": section_id,
            "title": title,
            "description": description,
            "score": round(score, 1),
            "status_class": self._status_class(score),
            "status_label": self._status_label(score),
            "summary": f"{best_metric['label']}表现更稳，{weakest_metric['label']}建议优先复核。",
            "metrics": metrics,
        }

    def _figure_to_data_uri(self, figure):
        buffer = BytesIO()
        figure.savefig(buffer, format="png", dpi=150, bbox_inches="tight", facecolor=figure.get_facecolor())
        buffer.seek(0)
        encoded = base64.b64encode(buffer.read()).decode("utf-8")
        plt.close(figure)
        return f"data:image/png;base64,{encoded}"

    def _image_preview_uri(self):
        if not os.path.exists(self.image_path):
            return None

        extension = os.path.splitext(self.image_path)[1].lower().lstrip(".") or "jpeg"
        mime = "jpeg" if extension in {"jpg", "jpeg"} else extension
        with open(self.image_path, "rb") as image_file:
            encoded = base64.b64encode(image_file.read()).decode("utf-8")
        return f"data:image/{mime};base64,{encoded}"

    def _format_inline_markdown(self, text):
        escaped = html.escape(text)
        escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
        return escaped

    def _format_ai_analysis(self):
        text = self.ai_analysis.strip()
        if not text:
            return ""

        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        parts = []
        list_stack = []

        def close_lists():
            while list_stack:
                parts.append(f"</{list_stack.pop()}>")

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                close_lists()
                continue

            if re.fullmatch(r"[-*_]{3,}", line):
                close_lists()
                parts.append("<hr>")
                continue

            heading_match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if heading_match:
                close_lists()
                level = min(len(heading_match.group(1)) + 1, 4)
                parts.append(f"<h{level}>{self._format_inline_markdown(heading_match.group(2))}</h{level}>")
                continue

            ordered_match = re.match(r"^(\d+)\.\s+(.*)$", line)
            if ordered_match:
                if not list_stack or list_stack[-1] != "ol":
                    close_lists()
                    list_stack.append("ol")
                    parts.append("<ol>")
                parts.append(f"<li>{self._format_inline_markdown(ordered_match.group(2))}</li>")
                continue

            unordered_match = re.match(r"^[-*+]\s+(.*)$", line)
            if unordered_match:
                if not list_stack or list_stack[-1] != "ul":
                    close_lists()
                    list_stack.append("ul")
                    parts.append("<ul>")
                parts.append(f"<li>{self._format_inline_markdown(unordered_match.group(1))}</li>")
                continue

            close_lists()
            parts.append(f"<p>{self._format_inline_markdown(line)}</p>")

        close_lists()
        return "".join(parts)

    def _generate_histogram(self):
        image = cv2.imread(self.image_path)
        if image is None:
            return None

        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        figure, axis = plt.subplots(figsize=(8.2, 4.8))
        figure.patch.set_facecolor("#f7f4ee")
        axis.set_facecolor("#fffdfa")

        x_axis = np.arange(256)
        for channel, color in enumerate(("#da5a3f", "#17856f", "#2f6fdf")):
            histogram = cv2.calcHist([image_rgb], [channel], None, [256], [0, 256]).flatten()
            axis.plot(x_axis, histogram, color=color, linewidth=1.8, alpha=0.95)
            axis.fill_between(x_axis, histogram, color=color, alpha=0.08)

        axis.set_title("RGB 像素分布", fontsize=13, color="#17313c")
        axis.set_xlabel("像素值", fontsize=10, color="#5d6e77")
        axis.set_ylabel("频数", fontsize=10, color="#5d6e77")
        axis.grid(axis="y", linestyle="--", linewidth=0.8, alpha=0.35)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        figure.tight_layout()
        return self._figure_to_data_uri(figure)

    def _generate_score_chart(self, sections):
        figure, axis = plt.subplots(figsize=(8.2, 4.8))
        figure.patch.set_facecolor("#f7f4ee")
        axis.set_facecolor("#fffdfa")

        labels = [section["title"] for section in sections]
        scores = [section["score"] for section in sections]
        colors = [
            {
                "excellent": "#1d8f6a",
                "good": "#0f766e",
                "fair": "#d07b24",
                "weak": "#c24d41",
            }[self._status_class(score)]
            for score in scores
        ]

        bars = axis.barh(labels, scores, color=colors, alpha=0.92, height=0.58)
        axis.invert_yaxis()
        axis.set_xlim(0, 100)
        axis.set_xlabel("维度得分", fontsize=10, color="#5d6e77")
        axis.set_title("核心维度概览", fontsize=13, color="#17313c")
        axis.grid(axis="x", linestyle="--", linewidth=0.8, alpha=0.3)
        axis.spines["top"].set_visible(False)
        axis.spines["right"].set_visible(False)
        axis.spines["left"].set_visible(False)

        for bar, score in zip(bars, scores):
            axis.text(min(score + 2, 96), bar.get_y() + bar.get_height() / 2, f"{score:.0f}",
                      va="center", ha="left", fontsize=10, color="#17313c")

        figure.tight_layout()
        return self._figure_to_data_uri(figure)

    def _build_sections(self):
        sharpness = self.results["sharpness"]
        dynamic_range = self.results["dynamic_range"]
        color = self.results["color_reproduction"]
        noise = self.results["noise"]
        uniformity = self.results["uniformity"]
        contrast = self.results["contrast"]

        lap_score = self._clamp(np.log1p(sharpness["laplacian_variance"]) * 14.0)
        tenengrad_score = self._clamp(np.log1p(sharpness["tenengrad"]) * 9.0)
        edge_width_score = self._clamp(100.0 - sharpness["avg_edge_width"] * 4.0)
        sharpness_score = lap_score * 0.35 + tenengrad_score * 0.35 + edge_width_score * 0.15 + sharpness["sharpness_confidence"] * 100.0 * 0.15
        sharpness_metrics = [
            self._metric("Laplacian 方差", self._format_number(sharpness["laplacian_variance"], 2), lap_score, "观察边缘对比和清晰感。"),
            self._metric("Tenengrad", self._format_number(sharpness["tenengrad"], 2), tenengrad_score, "用梯度能量补充锐度判断。"),
            self._metric("区域一致性", self._format_number(sharpness["sharpness_consistency"], 3), sharpness["sharpness_consistency"] * 100.0, "比较中心、边缘、角落的清晰度是否均衡。"),
            self._metric("可信度", self._format_number(sharpness["sharpness_confidence"] * 100.0, 0, True), sharpness["sharpness_confidence"] * 100.0, "边缘信息越充分，锐度判断越稳。"),
        ]

        dynamic_range_score = self._clamp(dynamic_range["effective_dynamic_range"] / 1.8)
        exposure_score = self._clamp(100.0 - dynamic_range["exposure_deviation"] * 0.9)
        clip_penalty = (dynamic_range["highlight_ratio"] + dynamic_range["shadow_clip_ratio"] + dynamic_range["rgb_clipping_ratio"]) * 1600.0
        clip_score = self._clamp(100.0 - clip_penalty)
        dynamic_score = dynamic_range_score * 0.35 + exposure_score * 0.35 + clip_score * 0.15 + dynamic_range["exposure_confidence"] * 100.0 * 0.15
        dynamic_metrics = [
            self._metric("有效动态范围", self._format_number(dynamic_range["effective_dynamic_range"], 2), dynamic_range_score, "基于亮度分位数估计，更适合普通照片。"),
            self._metric("曝光偏差", self._format_number(dynamic_range["exposure_deviation"], 2), exposure_score, "基于中位亮度偏移估计曝光稳定性。"),
            self._metric("高光 / 阴影剪切", f"{self._format_number(dynamic_range['highlight_ratio'] * 100.0, 2, True)} / {self._format_number(dynamic_range['shadow_clip_ratio'] * 100.0, 2, True)}", clip_score, "同时观察高光溢出和阴影压死。"),
            self._metric("可信度", self._format_number(dynamic_range["exposure_confidence"] * 100.0, 0, True), dynamic_range["exposure_confidence"] * 100.0, "亮度分布越充分，曝光估计越稳。"),
        ]

        color_uniformity = np.mean(color["color_uniformity_std"][1:]) if len(color["color_uniformity_std"]) >= 3 else np.mean(color["color_uniformity_std"])
        color_uniformity_score = self._clamp(100.0 - color_uniformity * 3.0)
        white_balance_score = self._clamp(100.0 - color["white_balance_error"] * 350.0)
        neutral_score = self._clamp(color["neutral_pixel_ratio"] * 2000.0)
        color_score = color_uniformity_score * 0.35 + white_balance_score * 0.35 + neutral_score * 0.15 + color["white_balance_confidence"] * 100.0 * 0.15
        color_metrics = [
            self._metric("色彩均匀性", " / ".join(self._format_number(value, 2) for value in color["color_uniformity_std"]), color_uniformity_score, "观察分块 LAB 均值波动。"),
            self._metric("白平衡误差", self._format_number(color["white_balance_error"], 4), white_balance_score, "优先基于低饱和中性像素估计色偏风险。"),
            self._metric("中性像素占比", self._format_number(color["neutral_pixel_ratio"] * 100.0, 2, True), neutral_score, "中性色区域越多，白平衡结论越可靠。"),
            self._metric("可信度", self._format_number(color["white_balance_confidence"] * 100.0, 0, True), color["white_balance_confidence"] * 100.0, "中性区域越充分，色偏判断越稳。"),
        ]

        chroma_noise_peak = max(noise["chrominance_noise_u"], noise["chrominance_noise_v"])
        luminance_score = self._clamp(100.0 - noise["luminance_noise"] * 3.0)
        chroma_score = self._clamp(100.0 - chroma_noise_peak * 4.0)
        artifact_score = self._clamp(100.0 - np.log1p(noise["block_boundary_artifacts_per_mp"]) * 12.0)
        noise_score = luminance_score * 0.35 + chroma_score * 0.25 + artifact_score * 0.2 + noise["noise_confidence"] * 100.0 * 0.2
        noise_metrics = [
            self._metric("亮度噪声", self._format_number(noise["luminance_noise"], 2), luminance_score, "只在平坦区域统计，更贴近真实噪声观感。"),
            self._metric("色度噪声峰值", self._format_number(chroma_noise_peak, 2), chroma_score, "观察彩色噪点与色彩纯净度风险。"),
            self._metric("块效应 / MP", self._format_number(noise["block_boundary_artifacts_per_mp"], 0), artifact_score, "按每百万像素归一化，更适合横向比较。"),
            self._metric("可信度", self._format_number(noise["noise_confidence"] * 100.0, 0, True), noise["noise_confidence"] * 100.0, "平坦区域越多，噪声估计越稳。"),
        ]

        brightness_std_score = self._clamp(100.0 - uniformity["brightness_std"] * 2.0)
        max_diff_score = self._clamp(100.0 - uniformity["brightness_max_diff"] * 0.6)
        vignette_score = self._clamp(100.0 - abs(uniformity["vignetting_ratio"] - 1.0) * 260.0)
        uniformity_score = brightness_std_score * 0.35 + max_diff_score * 0.3 + vignette_score * 0.15 + uniformity["uniformity_confidence"] * 100.0 * 0.2
        uniformity_metrics = [
            self._metric("亮度标准差", self._format_number(uniformity["brightness_std"], 2), brightness_std_score, "分块亮度波动越小越均匀。"),
            self._metric("最大亮度差", self._format_number(uniformity["brightness_max_diff"], 2), max_diff_score, "观察画面不同区域的亮度落差。"),
            self._metric("暗角比值", self._format_number(uniformity["vignetting_ratio"], 4), vignette_score, "越接近 1 越理想。"),
            self._metric("可信度", self._format_number(uniformity["uniformity_confidence"] * 100.0, 0, True), uniformity["uniformity_confidence"] * 100.0, "自然场景越复杂，这项结果越应谨慎解读。"),
        ]

        global_contrast_score = self._clamp(contrast["global_contrast"] / 2.1)
        local_contrast_score = self._clamp(np.log1p(contrast["avg_local_contrast"]) * 28.0)
        rms_score = self._clamp(contrast["rms_contrast"] * 320.0)
        contrast_score = global_contrast_score * 0.4 + local_contrast_score * 0.35 + rms_score * 0.25
        contrast_metrics = [
            self._metric("全局对比度", self._format_number(contrast["global_contrast"], 2), global_contrast_score, "采用亮度分位差，避免极端像素带偏。"),
            self._metric("局部对比度", self._format_number(contrast["avg_local_contrast"], 2), local_contrast_score, "观察细节层次和纹理起伏。"),
            self._metric("RMS 对比度", self._format_number(contrast["rms_contrast"], 4), rms_score, "补充整体反差感。"),
        ]

        return [
            self._section("sharpness", "锐度", "更关注梯度能量和区域一致性。", sharpness_score, sharpness_metrics),
            self._section("dynamic-range", "曝光与动态范围", "改用分位数口径，减少普通场景内容干扰。", dynamic_score, dynamic_metrics),
            self._section("color", "色彩还原", "优先用低饱和像素评估白平衡和色偏风险。", color_score, color_metrics),
            self._section("noise", "噪声与压缩", "平坦区域噪声 + 归一化块效应。", noise_score, noise_metrics),
            self._section("uniformity", "均匀性", "保留亮度 / 暗角指标，并加入可信度。", uniformity_score, uniformity_metrics),
            self._section("contrast", "对比度", "使用分位数对比度和 RMS 对比度。", contrast_score, contrast_metrics),
        ]

    def _build_findings(self, sections):
        dynamic_range = self.results["dynamic_range"]
        noise = self.results["noise"]
        capture_analysis = self.results.get("capture_analysis", {})
        findings = []

        if dynamic_range["exposure_deviation"] > 18:
            findings.append(("risk", "曝光存在偏移", f"当前曝光偏差为 {self._format_number(dynamic_range['exposure_deviation'], 2)}，建议优先检查测光策略。"))
        if noise["block_boundary_artifacts_per_mp"] > 500:
            findings.append(("risk", "压缩痕迹较重", f"块效应强度约为 {self._format_number(noise['block_boundary_artifacts_per_mp'], 0)} / MP，JPEG 痕迹可能较明显。"))
        if capture_analysis and not capture_analysis.get("metadata_available", False):
            findings.append(("neutral", "EXIF 缺失", "没有读取到 EXIF，机型和拍摄参数分析已降级为图像内容解释。"))

        strongest = max(sections, key=lambda item: item["score"])
        weakest = min(sections, key=lambda item: item["score"])
        findings.append(("positive", "当前最佳维度", f"{strongest['title']} 得分 {strongest['score']:.0f}，是目前最稳的一项。"))
        findings.append(("neutral", "当前短板维度", f"{weakest['title']} 得分 {weakest['score']:.0f}，建议下一轮优先复核。"))
        return findings[:4]

    def _render_metric_card(self, metric):
        return f"""
        <article class="metric-card">
            <div class="metric-head">
                <span>{html.escape(metric['label'])}</span>
                <span class="pill {metric['status_class']}">{metric['status_label']}</span>
            </div>
            <div class="metric-value">{html.escape(metric['value'])}</div>
            <div class="meter"><span class="fill {metric['status_class']}" style="width:{metric['score']:.0f}%"></span></div>
            <p>{html.escape(metric['note'])}</p>
        </article>
        """

    def _render_section(self, section):
        metrics_html = "".join(self._render_metric_card(metric) for metric in section["metrics"])
        return f"""
        <section id="{section['id']}" class="card section-card">
            <div class="section-head">
                <div>
                    <p class="kicker">分析维度</p>
                    <h2>{html.escape(section['title'])}</h2>
                    <p class="desc">{html.escape(section['description'])}</p>
                </div>
                <div class="section-score {section['status_class']}">
                    <strong>{section['score']:.0f}</strong>
                    <span>{section['status_label']}</span>
                </div>
            </div>
            <p class="summary">{html.escape(section['summary'])}</p>
            <div class="metrics-grid">{metrics_html}</div>
        </section>
        """

    def _render_nr_iqa_panel(self, nr_iqa):
        components_html = "".join(
            f"""
            <article class="metric-card compact">
                <div class="metric-head">
                    <span>{html.escape(component['label'])}</span>
                    <span class="pill {self._status_class(component['score'])}">{component['grade']}</span>
                </div>
                <div class="metric-value">{component['score']:.0f}</div>
                <div class="meter"><span class="fill {self._status_class(component['score'])}" style="width:{component['score']:.0f}%"></span></div>
                <p>{html.escape(component['description'])}</p>
            </article>
            """
            for component in nr_iqa.get("components", [])
        )
        strengths = "、".join(nr_iqa.get("strengths", [])) or "暂无"
        weaknesses = "、".join(nr_iqa.get("weaknesses", [])) or "暂无"
        return f"""
        <section class="card section-card">
            <div class="section-head">
                <div>
                    <p class="kicker">No-reference IQA</p>
                    <h2>无参考画质总分</h2>
                    <p class="desc">在没有标准参考图和测试卡的情况下，基于单张图片自身特征估计整体主观画质。</p>
                </div>
                <div class="section-score {self._status_class(nr_iqa['overall_score'])}">
                    <strong>{nr_iqa['overall_score']:.0f}</strong>
                    <span>{html.escape(nr_iqa['overall_grade'])}</span>
                </div>
            </div>
            <p class="summary">{html.escape(nr_iqa['summary'])}</p>
            <div class="hero-stats inline">
                <div class="stat"><span class="meta-label">分析可信度</span><strong>{nr_iqa['confidence_score']:.0f}</strong><span class="desc">{html.escape(nr_iqa['confidence_grade'])}</span></div>
                <div class="stat"><span class="meta-label">优势维度</span><strong>{html.escape(strengths)}</strong><span class="desc">来自 NR-IQA 组件排序</span></div>
                <div class="stat"><span class="meta-label">短板维度</span><strong>{html.escape(weaknesses)}</strong><span class="desc">建议优先人工复核</span></div>
            </div>
            <div class="metrics-grid">{components_html}</div>
        </section>
        """

    def _render_capture_analysis(self, capture_analysis):
        metadata_items = [
            ("机型", capture_analysis.get("camera_label", "未读取到")),
            ("镜头", capture_analysis.get("lens_model") or "未读取到"),
            ("ISO", capture_analysis.get("iso_display", "未读取到")),
            ("快门", capture_analysis.get("exposure_time_display", "未读取到")),
            ("光圈", capture_analysis.get("f_number_display", "未读取到")),
            ("焦距", capture_analysis.get("focal_length_display", "未读取到")),
            ("曝光补偿", capture_analysis.get("exposure_bias_display", "未读取到")),
            ("白平衡", capture_analysis.get("white_balance_mode", "未读取到")),
            ("闪光灯", capture_analysis.get("flash_mode", "未读取到")),
            ("软件", capture_analysis.get("software") or "未读取到"),
            ("拍摄时间", capture_analysis.get("capture_time") or "未读取到"),
            ("信息完整度", f"{capture_analysis.get('metadata_completeness', 0):.0f}%"),
        ]

        metadata_html = "".join(
            f'<div class="stat compact"><span class="meta-label">{html.escape(label)}</span><strong>{html.escape(str(value))}</strong></div>'
            for label, value in metadata_items
        )
        insights_html = "".join(
            f'<article class="finding-card {item["tone"]}"><p class="meta-label">{"亮点" if item["tone"] == "positive" else "风险" if item["tone"] == "risk" else "关注"}</p><h3>{html.escape(item["title"])}</h3><p>{html.escape(item["text"])}</p></article>'
            for item in capture_analysis.get("insights", [])
        )

        return f"""
        <section class="card section-card">
            <div class="section-head">
                <div>
                    <p class="kicker">EXIF / 机型维度</p>
                    <h2>拍摄参数与机型分析</h2>
                    <p class="desc">用于把画质结果和拍摄条件关联起来看；当 EXIF 缺失时，报告会自动降级而不是报错。</p>
                </div>
                <div class="section-score {self._status_class(capture_analysis.get('metadata_completeness', 0))}">
                    <strong>{capture_analysis.get('metadata_completeness', 0):.0f}</strong>
                    <span>完整度</span>
                </div>
            </div>
            <p class="summary">{html.escape(capture_analysis.get('summary', '未提供拍摄参数分析。'))}</p>
            <div class="hero-stats inline">{metadata_html}</div>
            <div class="grid findings inline">{insights_html}</div>
        </section>
        """

    def _styles(self):
        return """
        :root{--bg:#f6f1e8;--panel:#fffdfa;--line:#dde4e1;--text:#18323d;--muted:#5d6e77;--accent:#0f766e;--good:#1d8f6a;--good-bg:#e4f5ec;--fair:#d07b24;--fair-bg:#fbefdf;--weak:#c24d41;--weak-bg:#f9e4e1;--shadow:0 18px 40px rgba(24,50,61,.07)}
        *{box-sizing:border-box}body{margin:0;padding:28px;font-family:"Avenir Next","PingFang SC","Microsoft YaHei UI","Segoe UI",sans-serif;color:var(--text);background:radial-gradient(circle at top left,rgba(208,123,36,.12),transparent 28%),radial-gradient(circle at top right,rgba(15,118,110,.16),transparent 32%),linear-gradient(180deg,#f8f3eb 0%,#eef7f3 100%)}.page{max-width:1280px;margin:0 auto}.card{background:rgba(255,253,250,.92);border:1px solid var(--line);border-radius:24px;box-shadow:var(--shadow)}.hero{padding:30px}.hero-grid{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(260px,340px);gap:24px}.eyebrow,.kicker,.meta-label{margin:0 0 8px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700}h1{margin:0;font-size:clamp(30px,4vw,42px);line-height:1.06}h2{margin:0;font-size:24px}h3{margin:0 0 10px;font-size:18px}.lead,.desc,.summary,.finding-card p,.metric-card p,.footnote,.score-panel p{color:var(--muted);line-height:1.72;font-size:14px}.lead{margin:14px 0 18px}.meta-row,.nav,.hero-stats{display:flex;flex-wrap:wrap;gap:12px}.chip,.nav a{padding:8px 12px;border-radius:999px;border:1px solid var(--line);background:#fff;text-decoration:none;color:var(--text);font-size:13px}.hero-stats{margin-top:18px}.hero-stats.inline{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.stat{min-width:170px;padding:16px;border-radius:18px;background:#fff;border:1px solid var(--line)}.stat.compact strong{font-size:16px}.stat strong{display:block;margin-top:8px;font-size:24px;line-height:1.2}.score-panel{padding:24px;border-radius:24px;background:linear-gradient(180deg,#17313c 0%,#204954 100%);color:#f8fbfa;display:flex;flex-direction:column;justify-content:space-between}.score-panel p{color:rgba(248,251,250,.82)}.score-ring{width:140px;height:140px;border-radius:50%;margin:18px 0;display:grid;place-items:center;background:conic-gradient(#bce9de 0deg,#70cab7 240deg,#f1c891 360deg)}.score-ring-inner{width:96px;height:96px;border-radius:50%;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#17313c}.score-ring-inner strong{font-size:34px}.score-ring-inner span{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:rgba(255,255,255,.72)}.nav{position:sticky;top:14px;z-index:10;margin:22px 0;padding:14px;background:rgba(255,253,250,.84);backdrop-filter:blur(12px);border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 24px rgba(24,50,61,.05)}.grid{display:grid;gap:18px}.findings{grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-bottom:20px}.findings.inline{margin-top:18px;margin-bottom:0}.finding-card{padding:20px;border-radius:22px;border:1px solid var(--line);background:#fff}.finding-card.positive{background:linear-gradient(180deg,#fff,var(--good-bg))}.finding-card.risk{background:linear-gradient(180deg,#fff,var(--weak-bg))}.finding-card.neutral{background:linear-gradient(180deg,#fff,#f3f7f6)}.visuals{grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);margin-bottom:20px}.visual-card{padding:22px}.visual-card.full{grid-column:1/-1}.preview,.chart{display:block;width:100%;margin-top:16px;border-radius:18px;border:1px solid var(--line);background:#fff}.section-card{padding:24px}.section-head{display:flex;justify-content:space-between;align-items:start;gap:18px}.section-score{min-width:92px;height:92px;border-radius:22px;display:flex;flex-direction:column;align-items:center;justify-content:center}.section-score strong{font-size:30px;line-height:1}.section-score span{font-size:13px;margin-top:6px}.summary{margin:16px 0 0;padding:14px 16px;border-radius:16px;background:#f7faf8}.metrics-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:18px}.metric-card{padding:16px;border-radius:18px;border:1px solid var(--line);background:#fff}.metric-card.compact .metric-value{font-size:24px}.metric-head{display:flex;justify-content:space-between;gap:12px;font-weight:700}.metric-value{margin-top:14px;font-size:28px;font-weight:700}.pill{padding:6px 10px;border-radius:999px;font-size:12px;font-weight:700}.meter{height:8px;border-radius:999px;background:#edf2f1;margin-top:14px;overflow:hidden}.fill{display:block;height:100%;border-radius:inherit}.excellent{background:var(--good-bg);color:var(--good)}.good{background:#d9f0ec;color:var(--accent)}.fair{background:var(--fair-bg);color:var(--fair)}.weak{background:var(--weak-bg);color:var(--weak)}.fill.excellent{background:linear-gradient(90deg,#79d0b5,#1d8f6a)}.fill.good{background:linear-gradient(90deg,#8ad8ca,#0f766e)}.fill.fair{background:linear-gradient(90deg,#f0c786,#d07b24)}.fill.weak{background:linear-gradient(90deg,#ef9d95,#c24d41)}.ai{padding:24px;background:linear-gradient(180deg,rgba(23,50,61,.97),rgba(28,68,80,.96));color:#f4faf8;border-color:rgba(255,255,255,.08)}.ai .desc,.ai p,.ai li{color:rgba(244,250,248,.88)}.ai h2,.ai h3,.ai h4{color:#fff}.ai ul,.ai ol{margin:10px 0 16px 20px}.ai code{background:rgba(255,255,255,.12);padding:2px 6px;border-radius:8px}.ai hr{border:0;border-top:1px solid rgba(255,255,255,.12);margin:18px 0}.footnote{text-align:center;margin-top:20px}@media (max-width:980px){body{padding:18px}.hero-grid,.visuals{grid-template-columns:1fr}}@media (max-width:640px){.section-head,.metric-head{flex-direction:column}.section-score{width:100%;height:auto;padding:16px;flex-direction:row;justify-content:space-between}}
        """

    def generate(self):
        pixel_attributes = self.results["pixel_attributes"]
        nr_iqa = self.results.get("nr_iqa", {})
        capture_analysis = self.results.get("capture_analysis", {})
        sections = self._build_sections()
        findings = self._build_findings(sections)

        preview_uri = self._image_preview_uri()
        histogram_uri = self._generate_histogram()
        score_chart_uri = self._generate_score_chart(sections)
        ai_html = self._format_ai_analysis()

        overall_score = nr_iqa.get("overall_score", round(sum(section["score"] for section in sections) / max(len(sections), 1), 1))
        overall_label = nr_iqa.get("overall_grade", self._status_label(overall_score))
        camera_label = capture_analysis.get("camera_label", "未读取到机型信息")
        exif_status = "已读取 EXIF" if capture_analysis.get("metadata_available", False) else "EXIF 缺失"

        findings_html = "".join(
            f'<article class="finding-card {tone}"><p class="meta-label">{"亮点" if tone == "positive" else "风险" if tone == "risk" else "关注"}</p><h3>{html.escape(title)}</h3><p>{html.escape(text)}</p></article>'
            for tone, title, text in findings
        )
        section_nav = "".join(f'<a href="#{section["id"]}">{html.escape(section["title"])}</a>' for section in sections)
        sections_html = "".join(self._render_section(section) for section in sections)
        nr_iqa_html = self._render_nr_iqa_panel(nr_iqa) if nr_iqa else ""
        capture_html = self._render_capture_analysis(capture_analysis) if capture_analysis else ""

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(self.image_name)} - 图像质量分析报告</title>
    <style>{self._styles()}</style>
</head>
<body>
    <main class="page">
        <section class="card hero">
            <div class="hero-grid">
                <div>
                    <p class="eyebrow">Image Quality Report</p>
                    <h1>{html.escape(self.image_name)} 图像质量分析报告</h1>
                    <p class="lead">这份报告同时提供可解释的工程指标、无参考主观总分，以及基于 EXIF 的拍摄条件分析。即使读不到 EXIF，也会自动降级而不会中断报告。</p>
                    <div class="meta-row">
                        <span class="chip">图像路径：{html.escape(self.image_path)}</span>
                        <span class="chip">机型：{html.escape(camera_label)}</span>
                        <span class="chip">{html.escape(exif_status)}</span>
                        <span class="chip">生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</span>
                    </div>
                    <div class="hero-stats">
                        <div class="stat"><span class="meta-label">图像尺寸</span><strong>{pixel_attributes['width']} × {pixel_attributes['height']}</strong><span class="desc">总像素 {self._format_number(pixel_attributes['total_pixels'], 0)}</span></div>
                        <div class="stat"><span class="meta-label">像素相关性</span><strong>{self._format_number(pixel_attributes['avg_pixel_correlation'], 4)}</strong><span class="desc">纹理强度 {self._format_number(pixel_attributes.get('texture_strength', 0.0), 2)}</span></div>
                        <div class="stat"><span class="meta-label">NR-IQA 总分</span><strong>{overall_score:.0f}</strong><span class="desc">{html.escape(overall_label)}</span></div>
                        <div class="stat"><span class="meta-label">EXIF 完整度</span><strong>{capture_analysis.get('metadata_completeness', 0):.0f}%</strong><span class="desc">{html.escape(exif_status)}</span></div>
                    </div>
                </div>
                <aside class="score-panel">
                    <div>
                        <p class="meta-label">Overall Score</p>
                        <div class="score-ring"><div class="score-ring-inner"><strong>{overall_score:.0f}</strong><span>{html.escape(overall_label)}</span></div></div>
                        <h2>整体判断</h2>
                        <p>{html.escape(nr_iqa.get('summary', '建议结合原图、核心维度和拍摄参数一起看结果。'))}</p>
                    </div>
                </aside>
            </div>
        </section>

        <nav class="nav">
            <a href="#overview">概览</a>
            <a href="#nr-iqa">NR-IQA</a>
            <a href="#capture-analysis">EXIF / 机型</a>
            {section_nav}
            {'<a href="#ai-analysis">AI 分析</a>' if ai_html else ''}
        </nav>

        <section class="grid findings">{findings_html}</section>

        <section id="overview" class="grid visuals">
            <article class="card visual-card">
                <p class="kicker">原图预览</p>
                <h2>样张展示</h2>
                <p class="desc">先看原图，再看指标和解释，通常更容易判断结论是否合理。</p>
                {f'<img class="preview" src="{preview_uri}" alt="{html.escape(self.image_name)}">' if preview_uri else '<div class="preview">原图预览不可用</div>'}
            </article>
            <article class="card visual-card">
                <p class="kicker">维度总览</p>
                <h2>核心维度概览</h2>
                <p class="desc">把主要维度归一化到 0-100，帮助快速定位强项与短板。</p>
                <img class="chart" src="{score_chart_uri}" alt="核心维度概览">
            </article>
            <article class="card visual-card full">
                <p class="kicker">像素分布</p>
                <h2>RGB 像素分布图</h2>
                <p class="desc">帮助判断亮度覆盖、色彩通道分布和高光聚集情况。</p>
                <img class="chart" src="{histogram_uri}" alt="RGB 像素分布图">
            </article>
        </section>

        <div id="nr-iqa">{nr_iqa_html}</div>
        <div id="capture-analysis">{capture_html}</div>

        <section class="grid">{sections_html}</section>

        {f'<section id="ai-analysis" class="card ai"><p class="kicker">AI 辅助解读</p><h2>DeepSeek 分析摘要</h2><p class="desc">以下内容保留原始分析思路，并做了结构化排版。</p>{ai_html}</section>' if ai_html else ''}

        <p class="footnote">注：NR-IQA 总分用于单张图片的无参考主观估计；EXIF / 机型分析用于解释“为什么会这样”。当 EXIF 缺失时，系统会自动降级而不是中断。</p>
    </main>
</body>
</html>
"""

    def save(self, output_path):
        if not output_path.endswith(".html"):
            output_path = os.path.splitext(output_path)[0] + ".html"

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(self.generate())
        return output_path
