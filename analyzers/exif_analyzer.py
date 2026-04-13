class ExifAnalyzer:
    def __init__(self, exif_data, results):
        self.exif_data = exif_data or {}
        self.results = results

    def _normalize_text(self, value):
        if value is None:
            return None
        if isinstance(value, bytes):
            for encoding in ("utf-8", "latin-1", "gbk"):
                try:
                    return value.decode(encoding).strip() or None
                except Exception:
                    continue
            return None
        text = str(value).strip()
        return text or None

    def _to_float(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if hasattr(value, "numerator") and hasattr(value, "denominator"):
            denominator = float(value.denominator)
            if denominator == 0:
                return None
            return float(value.numerator) / denominator
        if isinstance(value, (tuple, list)):
            if len(value) == 2:
                denominator = self._to_float(value[1])
                numerator = self._to_float(value[0])
                if denominator in (None, 0) or numerator is None:
                    return None
                return numerator / denominator
            if len(value) == 1:
                return self._to_float(value[0])
        try:
            return float(value)
        except Exception:
            return None

    def _to_int(self, value):
        number = self._to_float(value)
        return int(round(number)) if number is not None else None

    def _format_exposure_time(self, seconds):
        if seconds is None:
            return "未读取到"
        if seconds <= 0:
            return "未读取到"
        if seconds >= 1:
            return f"{seconds:.1f}s"
        denominator = round(1.0 / seconds)
        return f"1/{denominator}s" if denominator > 0 else f"{seconds:.4f}s"

    def _format_optional(self, value, suffix=""):
        return f"{value}{suffix}" if value is not None else "未读取到"

    def _flash_label(self, value):
        if value is None:
            return "未读取到"
        if isinstance(value, int):
            return "使用闪光灯" if value & 0x1 else "未使用闪光灯"
        return self._normalize_text(value) or "未读取到"

    def _white_balance_label(self, value):
        if value is None:
            return "未读取到"
        if value == 0:
            return "自动白平衡"
        if value == 1:
            return "手动白平衡"
        return self._normalize_text(value) or "未读取到"

    def _append(self, insights, tone, title, text):
        insights.append({"tone": tone, "title": title, "text": text})

    def analyze(self):
        make = self._normalize_text(self.exif_data.get("Make"))
        model = self._normalize_text(self.exif_data.get("Model"))
        lens_model = self._normalize_text(self.exif_data.get("LensModel"))
        software = self._normalize_text(self.exif_data.get("Software"))
        capture_time = self._normalize_text(self.exif_data.get("DateTimeOriginal") or self.exif_data.get("DateTime"))

        iso = self._to_int(self.exif_data.get("PhotographicSensitivity") or self.exif_data.get("ISOSpeedRatings"))
        exposure_time_s = self._to_float(self.exif_data.get("ExposureTime"))
        f_number = self._to_float(self.exif_data.get("FNumber"))
        focal_length_mm = self._to_float(self.exif_data.get("FocalLength"))
        exposure_bias_ev = self._to_float(self.exif_data.get("ExposureBiasValue"))

        sharpness = self.results["sharpness"]
        dynamic_range = self.results["dynamic_range"]
        noise = self.results["noise"]

        metadata_fields = [
            make,
            model,
            lens_model,
            software,
            capture_time,
            iso,
            exposure_time_s,
            f_number,
            focal_length_mm,
            exposure_bias_ev,
        ]
        present_count = sum(item is not None for item in metadata_fields)
        metadata_completeness = round((present_count / len(metadata_fields)) * 100.0, 1)
        metadata_available = present_count > 0
        model_available = bool(make or model)

        camera_label = " / ".join([item for item in (make, model) if item]) or "未读取到机型信息"
        insights = []

        if not metadata_available:
            self._append(
                insights,
                "neutral",
                "未读取到 EXIF",
                "本次已自动降级为仅基于图像内容的分析，机型和拍摄参数维度无法参与解释。",
            )
        else:
            if not model_available:
                self._append(
                    insights,
                    "neutral",
                    "EXIF 存在但缺少机型字段",
                    "报告仍会保留图像内容分析，但无法准确关联到具体机型或品牌。",
                )

            if iso is not None:
                if iso >= 1600:
                    self._append(insights, "risk", "ISO 较高", f"当前 ISO 为 {iso}，高感设置可能明显推高噪声和涂抹风险。")
                elif iso >= 800:
                    self._append(insights, "neutral", "ISO 中高档位", f"当前 ISO 为 {iso}，建议结合噪声与细节表现一起判断。")
                else:
                    self._append(insights, "positive", "ISO 较低", f"当前 ISO 为 {iso}，通常更有利于保留细节和压低噪声。")
            elif noise["luminance_noise"] > 18:
                self._append(insights, "neutral", "噪声偏高但无 ISO 信息", "画面噪声偏高，但由于缺少 ISO，无法直接判断是否由高感触发。")

            if exposure_time_s is not None:
                if focal_length_mm is not None and focal_length_mm > 0:
                    safe_handheld = 1.0 / max(focal_length_mm, 24.0)
                    if exposure_time_s > safe_handheld * 1.2 and sharpness["sharpness_confidence"] > 0.3:
                        self._append(
                            insights,
                            "risk",
                            "快门偏慢",
                            f"当前快门约 {self._format_exposure_time(exposure_time_s)}，相对 {focal_length_mm:.0f}mm 焦距可能存在手抖或拖影风险。",
                        )
                elif exposure_time_s > 1 / 30:
                    self._append(
                        insights,
                        "neutral",
                        "快门接近低速区间",
                        f"当前快门约 {self._format_exposure_time(exposure_time_s)}，在手持场景下建议结合锐度结果一起看。",
                    )

            if exposure_bias_ev is not None and abs(exposure_bias_ev) >= 0.7:
                self._append(
                    insights,
                    "neutral",
                    "曝光补偿幅度较大",
                    f"当前曝光补偿为 {exposure_bias_ev:+.1f} EV，说明拍摄时对亮度策略做过较明显干预。",
                )

            if software:
                self._append(
                    insights,
                    "neutral",
                    "存在软件处理痕迹",
                    f"EXIF 中记录的软件字段为 {software}，结果可能同时受机内或后期处理影响。",
                )

            if dynamic_range["highlight_ratio"] > 0.03 and exposure_time_s is None:
                self._append(
                    insights,
                    "neutral",
                    "高光偏紧但无曝光参数",
                    "当前存在一定高光剪切，但缺少曝光时间等参数，建议结合拍摄环境人工判断。",
                )

        if not insights:
            self._append(insights, "positive", "拍摄参数较完整", "当前 EXIF 信息较完整，可用于辅助解释画质表现。")

        if not metadata_available:
            summary = "未读取到 EXIF，本次机型/拍摄参数分析已降级。"
        elif not model_available:
            summary = "读取到了部分 EXIF，但缺少明确机型字段，参数解释能力有限。"
        else:
            summary = "已读取到机型与部分拍摄参数，可结合图像指标做更有针对性的解释。"

        return {
            "metadata_available": metadata_available,
            "model_available": model_available,
            "metadata_completeness": metadata_completeness,
            "camera_make": make,
            "camera_model": model,
            "camera_label": camera_label,
            "lens_model": lens_model,
            "software": software,
            "capture_time": capture_time,
            "iso": iso,
            "iso_display": self._format_optional(iso),
            "exposure_time_s": exposure_time_s,
            "exposure_time_display": self._format_exposure_time(exposure_time_s),
            "f_number": f_number,
            "f_number_display": f"f/{f_number:.1f}" if f_number is not None else "未读取到",
            "focal_length_mm": focal_length_mm,
            "focal_length_display": f"{focal_length_mm:.0f}mm" if focal_length_mm is not None else "未读取到",
            "exposure_bias_ev": exposure_bias_ev,
            "exposure_bias_display": f"{exposure_bias_ev:+.1f} EV" if exposure_bias_ev is not None else "未读取到",
            "white_balance_mode": self._white_balance_label(self.exif_data.get("WhiteBalance")),
            "flash_mode": self._flash_label(self.exif_data.get("Flash")),
            "summary": summary,
            "insights": insights,
        }
