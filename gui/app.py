from __future__ import annotations

import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk

from ai_services import AIConfigStore, AIServiceConfig, apply_preset, preset_by_label, preset_labels
from providers import AnalysisProviderRegistry, AnalysisRequest, initialize_providers


class PhotoQualityWorkbenchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        initialize_providers()

        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")

        self.title("Photo Quality Workbench")
        self.geometry("1400x900")
        self.minsize(1200, 780)

        self.colors = {
            "app_bg": ("#edf3f8", "#0b1220"),
            "sidebar_bg": ("#0f172a", "#0f172a"),
            "sidebar_card": ("#162338", "#162338"),
            "sidebar_text": "#eef4ff",
            "sidebar_muted": "#b7c5d9",
            "sidebar_border": "#5a6b84",
            "sidebar_hover": "#22344d",
            "main_bg": ("#f8fbff", "#111827"),
            "panel": ("#ffffff", "#101826"),
            "panel_alt": ("#f5f8fc", "#0f172a"),
            "border": ("#dbe4ee", "#243244"),
            "text": ("#0f172a", "#f8fafc"),
            "muted": ("#526171", "#94a3b8"),
            "primary": ("#2563eb", "#3b82f6"),
            "primary_hover": ("#1d4ed8", "#2563eb"),
            "secondary_hover": ("#edf3ff", "#172033"),
            "success": ("#1f9d74", "#34d399"),
        }

        self.configure(fg_color=self.colors["app_bg"])

        self.selected_images: list[str] = []
        self.output_dir = os.path.abspath("output")
        self.provider_var = tk.StringVar(value=AnalysisProviderRegistry.default().label)
        self.use_ai_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="准备就绪")
        self.image_count_var = tk.StringVar(value="0 张图片待分析")
        self.output_var = tk.StringVar(value=self.output_dir)
        self.progress_value = tk.DoubleVar(value=0.0)

        self.ai_config = AIConfigStore.load()
        self.ai_preset_var = tk.StringVar(value=self.ai_config.provider_label)
        self.ai_api_key_var = tk.StringVar(value=self.ai_config.api_key)
        self.ai_base_url_var = tk.StringVar(value=self.ai_config.base_url)
        self.ai_model_var = tk.StringVar(value=self.ai_config.model)
        self.ai_temperature_var = tk.StringVar(value=str(self.ai_config.temperature))
        self.ai_max_tokens_var = tk.StringVar(value=str(self.ai_config.max_tokens))
        self.ai_timeout_var = tk.StringVar(value=str(self.ai_config.timeout))

        self.message_queue: "queue.Queue[tuple[str, object]]" = queue.Queue()
        self.worker_thread: threading.Thread | None = None

        self._build_layout()
        self._refresh_image_list()
        self._append_log("应用已启动，等待任务。")
        self.after(120, self._drain_queue)

    def _font(self, size: int, weight: str = "normal"):
        return ctk.CTkFont(family="Microsoft YaHei UI", size=size, weight=weight)

    def _build_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self,
            fg_color=self.colors["sidebar_bg"],
            corner_radius=34,
            border_width=0,
        )
        self.sidebar.grid(row=0, column=0, padx=(18, 10), pady=18, sticky="nsew")
        self.sidebar.grid_columnconfigure(0, weight=1)

        self.main_panel = ctk.CTkFrame(
            self,
            fg_color=self.colors["main_bg"],
            corner_radius=34,
            border_width=0,
        )
        self.main_panel.grid(row=0, column=1, padx=(10, 18), pady=18, sticky="nsew")
        self.main_panel.grid_columnconfigure(0, weight=1)
        self.main_panel.grid_rowconfigure(2, weight=1)

        self._build_sidebar()
        self._build_main_panel()

    def _create_card(self, parent, fg_color=None, border=False, corner_radius=24):
        return ctk.CTkFrame(
            parent,
            fg_color=fg_color or self.colors["panel"],
            corner_radius=corner_radius,
            border_width=1 if border else 0,
            border_color=self.colors["border"],
        )

    def _create_entry(self, parent, variable=None, placeholder="", show=None):
        return ctk.CTkEntry(
            parent,
            textvariable=variable,
            placeholder_text=placeholder,
            height=44,
            corner_radius=16,
            border_width=1,
            border_color=self.colors["border"],
            fg_color=self.colors["panel"],
            text_color=self.colors["text"],
            placeholder_text_color=self.colors["muted"],
            show=show,
        )

    def _create_primary_button(self, parent, text, command):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=46,
            corner_radius=16,
            fg_color=self.colors["primary"],
            hover_color=self.colors["primary_hover"],
            text_color="#ffffff",
            font=self._font(15, "bold"),
        )

    def _create_secondary_button(self, parent, text, command, on_dark=False):
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            height=42,
            corner_radius=16,
            fg_color="transparent",
            hover_color=self.colors["sidebar_hover"] if on_dark else self.colors["secondary_hover"],
            border_width=1,
            border_color=self.colors["sidebar_border"] if on_dark else self.colors["border"],
            text_color=self.colors["sidebar_text"] if on_dark else self.colors["text"],
            font=self._font(14, "bold"),
        )

    def _build_sidebar(self):
        hero = self._create_card(self.sidebar, fg_color=self.colors["sidebar_card"], corner_radius=28)
        hero.grid(row=0, column=0, padx=18, pady=(18, 14), sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            hero,
            text="Photo Quality\nWorkbench",
            font=self._font(30, "bold"),
            justify="left",
            text_color="#f8fafc",
        )
        title.grid(row=0, column=0, padx=22, pady=(22, 8), sticky="w")

        subtitle = ctk.CTkLabel(
            hero,
            text="给 Win10 / Win11 用户直接使用的图像分析工作台。支持切换分析引擎、选择图片、配置 AI 接口并导出报告。",
            wraplength=290,
            justify="left",
            text_color="#cbd5e1",
            font=self._font(13),
        )
        subtitle.grid(row=1, column=0, padx=22, pady=(0, 20), sticky="w")

        self.sidebar_tabs = ctk.CTkTabview(
            self.sidebar,
            width=340,
            corner_radius=28,
            fg_color=self.colors["sidebar_card"],
            segmented_button_fg_color="#203149",
            segmented_button_selected_color="#3b82f6",
            segmented_button_selected_hover_color="#2563eb",
            segmented_button_unselected_hover_color="#253650",
            text_color="#e2e8f0",
            border_width=0,
        )
        self.sidebar_tabs.grid(row=1, column=0, padx=18, pady=(0, 14), sticky="nsew")
        self.sidebar_tabs.add("基础设置")
        self.sidebar_tabs.add("AI 设置")

        self._build_basic_tab(self.sidebar_tabs.tab("基础设置"))
        self._build_ai_tab(self.sidebar_tabs.tab("AI 设置"))

        footer = ctk.CTkLabel(
            self.sidebar,
            text="界面现在优先强调更圆润、更柔和的视觉风格。\n如果默认 AI 接口失效，用户可以直接在 AI 设置里切换新的 API。",
            wraplength=300,
            justify="left",
            text_color="#94a3b8",
            font=self._font(12),
        )
        footer.grid(row=2, column=0, padx=22, pady=(0, 22), sticky="sw")

    def _section_label(self, parent, text, on_dark=False):
        return ctk.CTkLabel(
            parent,
            text=text,
            font=self._font(14, "bold"),
            text_color=self.colors["sidebar_text"] if on_dark else self.colors["text"],
        )

    def _hint_label(self, parent, text, on_dark=False):
        return ctk.CTkLabel(
            parent,
            text=text,
            wraplength=290,
            justify="left",
            text_color=self.colors["sidebar_muted"] if on_dark else self.colors["muted"],
            font=self._font(12),
        )

    def _build_basic_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        provider_label = self._section_label(tab, "分析 API", on_dark=True)
        provider_label.grid(row=0, column=0, padx=16, pady=(18, 8), sticky="w")

        providers = AnalysisProviderRegistry.labels()
        self.provider_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.provider_var,
            values=providers,
            height=44,
            corner_radius=16,
            fg_color="#203149",
            button_color="#2d4263",
            button_hover_color="#3b82f6",
            dropdown_fg_color=self.colors["panel_alt"],
            dropdown_hover_color=("#eaf1fb", "#162033"),
            text_color="#f8fafc",
            font=self._font(13, "bold"),
            dropdown_text_color=self.colors["text"],
        )
        self.provider_menu.grid(row=1, column=0, padx=16, sticky="ew")

        provider_hint = self._hint_label(
            tab,
            "默认使用当前项目内置分析器。后续如果你放入新的 provider，GUI 会自动识别并可切换。",
            on_dark=True,
        )
        provider_hint.grid(row=2, column=0, padx=16, pady=(8, 18), sticky="w")

        output_label = self._section_label(tab, "导出目录", on_dark=True)
        output_label.grid(row=3, column=0, padx=16, pady=(0, 8), sticky="w")

        self.output_entry = self._create_entry(tab, variable=self.output_var)
        self.output_entry.grid(row=4, column=0, padx=16, sticky="ew")

        output_button = self._create_secondary_button(tab, "选择导出文件夹", self._choose_output_dir, on_dark=True)
        output_button.grid(row=5, column=0, padx=16, pady=(10, 18), sticky="ew")

        self.ai_switch = ctk.CTkSwitch(
            tab,
            text="启用 AI 分析",
            variable=self.use_ai_var,
            onvalue=True,
            offvalue=False,
            progress_color="#3b82f6",
            button_color="#ffffff",
            button_hover_color="#dbeafe",
            text_color=self.colors["sidebar_text"],
            font=self._font(13, "bold"),
        )
        self.ai_switch.grid(row=6, column=0, padx=16, pady=(0, 18), sticky="w")

        self.run_button = self._create_primary_button(tab, "开始分析", self._start_analysis)
        self.run_button.grid(row=7, column=0, padx=16, pady=(0, 10), sticky="ew")

        open_output_button = self._create_secondary_button(tab, "打开导出目录", self._open_output_dir, on_dark=True)
        open_output_button.grid(row=8, column=0, padx=16, pady=(0, 12), sticky="ew")

    def _build_ai_tab(self, tab):
        tab.grid_columnconfigure(0, weight=1)

        preset_label = self._section_label(tab, "AI 服务预设", on_dark=True)
        preset_label.grid(row=0, column=0, padx=16, pady=(18, 8), sticky="w")

        self.ai_preset_menu = ctk.CTkOptionMenu(
            tab,
            variable=self.ai_preset_var,
            values=preset_labels(),
            command=self._on_ai_preset_change,
            height=44,
            corner_radius=16,
            fg_color="#203149",
            button_color="#2d4263",
            button_hover_color="#3b82f6",
            dropdown_fg_color=self.colors["panel_alt"],
            dropdown_hover_color=("#eaf1fb", "#162033"),
            text_color="#f8fafc",
            font=self._font(13, "bold"),
            dropdown_text_color=self.colors["text"],
        )
        self.ai_preset_menu.grid(row=1, column=0, padx=16, sticky="ew")

        preset_hint = self._hint_label(
            tab,
            "支持 DeepSeek、OpenAI、SiliconFlow、OpenRouter 和自定义 OpenAI 兼容接口。失效时用户可以直接换新的。",
            on_dark=True,
        )
        preset_hint.grid(row=2, column=0, padx=16, pady=(8, 14), sticky="w")

        self.ai_api_key_entry = self._create_entry(tab, variable=self.ai_api_key_var, placeholder="API Key", show="*")
        self.ai_api_key_entry.grid(row=3, column=0, padx=16, pady=(0, 10), sticky="ew")

        self.ai_base_url_entry = self._create_entry(tab, variable=self.ai_base_url_var, placeholder="Base URL")
        self.ai_base_url_entry.grid(row=4, column=0, padx=16, pady=(0, 10), sticky="ew")

        self.ai_model_entry = self._create_entry(tab, variable=self.ai_model_var, placeholder="Model")
        self.ai_model_entry.grid(row=5, column=0, padx=16, pady=(0, 10), sticky="ew")

        advanced_grid = ctk.CTkFrame(tab, fg_color="transparent")
        advanced_grid.grid(row=6, column=0, padx=16, pady=(0, 10), sticky="ew")
        advanced_grid.grid_columnconfigure((0, 1, 2), weight=1)

        self.ai_temperature_entry = self._create_entry(advanced_grid, variable=self.ai_temperature_var, placeholder="温度")
        self.ai_temperature_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")

        self.ai_max_tokens_entry = self._create_entry(advanced_grid, variable=self.ai_max_tokens_var, placeholder="Max Tokens")
        self.ai_max_tokens_entry.grid(row=0, column=1, padx=4, sticky="ew")

        self.ai_timeout_entry = self._create_entry(advanced_grid, variable=self.ai_timeout_var, placeholder="超时秒数")
        self.ai_timeout_entry.grid(row=0, column=2, padx=(8, 0), sticky="ew")

        system_prompt_label = self._section_label(tab, "System Prompt", on_dark=True)
        system_prompt_label.grid(row=7, column=0, padx=16, pady=(4, 6), sticky="w")

        self.system_prompt_box = ctk.CTkTextbox(
            tab,
            height=120,
            corner_radius=16,
            fg_color=self.colors["panel"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
        )
        self.system_prompt_box.grid(row=8, column=0, padx=16, pady=(0, 10), sticky="ew")
        self.system_prompt_box.insert("1.0", self.ai_config.system_prompt)

        extra_header_label = self._section_label(tab, "额外请求头 JSON", on_dark=True)
        extra_header_label.grid(row=9, column=0, padx=16, pady=(0, 6), sticky="w")

        self.extra_headers_box = ctk.CTkTextbox(
            tab,
            height=84,
            corner_radius=16,
            fg_color=self.colors["panel"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
        )
        self.extra_headers_box.grid(row=10, column=0, padx=16, pady=(0, 12), sticky="ew")
        if self.ai_config.extra_headers_json:
            self.extra_headers_box.insert("1.0", self.ai_config.extra_headers_json)

        button_row = ctk.CTkFrame(tab, fg_color="transparent")
        button_row.grid(row=11, column=0, padx=16, pady=(0, 14), sticky="ew")
        button_row.grid_columnconfigure((0, 1), weight=1)

        save_button = self._create_primary_button(button_row, "保存 AI 配置", self._save_ai_settings)
        save_button.configure(height=42)
        save_button.grid(row=0, column=0, padx=(0, 6), sticky="ew")

        reset_button = self._create_secondary_button(button_row, "恢复当前预设", self._reset_ai_preset, on_dark=True)
        reset_button.grid(row=0, column=1, padx=(6, 0), sticky="ew")

    def _build_main_panel(self):
        header = self._create_card(self.main_panel, fg_color=self.colors["panel"], border=True, corner_radius=26)
        header.grid(row=0, column=0, padx=20, pady=(20, 14), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(
            header,
            text="任务面板",
            font=self._font(26, "bold"),
            text_color=self.colors["text"],
        )
        title.grid(row=0, column=0, padx=22, pady=(20, 6), sticky="w")

        count_label = ctk.CTkLabel(header, textvariable=self.image_count_var, text_color=self.colors["muted"], font=self._font(13))
        count_label.grid(row=1, column=0, padx=22, pady=(0, 18), sticky="w")

        actions = ctk.CTkFrame(self.main_panel, fg_color="transparent")
        actions.grid(row=1, column=0, padx=20, pady=(0, 14), sticky="ew")

        add_button = self._create_primary_button(actions, "选择图片", self._choose_images)
        add_button.configure(width=120, height=42)
        add_button.grid(row=0, column=0, padx=(0, 10), sticky="w")

        clear_button = self._create_secondary_button(actions, "清空列表", self._clear_images)
        clear_button.grid(row=0, column=1, padx=(0, 10), sticky="w")

        hint = ctk.CTkLabel(
            actions,
            text="支持多选 JPG / JPEG；任务会在后台执行，界面不会卡住。",
            text_color=self.colors["muted"],
            font=self._font(13),
        )
        hint.grid(row=0, column=2, sticky="w")

        self.image_box = ctk.CTkTextbox(
            self.main_panel,
            corner_radius=24,
            wrap="none",
            fg_color=self.colors["panel"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
        )
        self.image_box.grid(row=2, column=0, padx=20, sticky="nsew")

        progress_card = self._create_card(self.main_panel, fg_color=self.colors["panel"], border=True, corner_radius=24)
        progress_card.grid(row=3, column=0, padx=20, pady=16, sticky="ew")
        progress_card.grid_columnconfigure(0, weight=1)

        progress_title = ctk.CTkLabel(
            progress_card,
            text="执行状态",
            font=self._font(17, "bold"),
            text_color=self.colors["text"],
        )
        progress_title.grid(row=0, column=0, padx=20, pady=(18, 8), sticky="w")

        progress_status = ctk.CTkLabel(progress_card, textvariable=self.status_var, text_color=self.colors["muted"], font=self._font(13))
        progress_status.grid(row=1, column=0, padx=20, sticky="w")

        self.progress_bar = ctk.CTkProgressBar(
            progress_card,
            variable=self.progress_value,
            progress_color=self.colors["primary"],
            fg_color=("#e7eef8", "#1b2637"),
            corner_radius=999,
            height=12,
        )
        self.progress_bar.grid(row=2, column=0, padx=20, pady=(14, 16), sticky="ew")
        self.progress_bar.set(0.0)

        log_title = ctk.CTkLabel(
            progress_card,
            text="日志",
            font=self._font(14, "bold"),
            text_color=self.colors["text"],
        )
        log_title.grid(row=3, column=0, padx=20, pady=(0, 8), sticky="w")

        self.log_box = ctk.CTkTextbox(
            progress_card,
            height=180,
            corner_radius=18,
            fg_color=self.colors["panel_alt"],
            text_color=self.colors["text"],
            border_width=1,
            border_color=self.colors["border"],
        )
        self.log_box.grid(row=4, column=0, padx=20, pady=(0, 20), sticky="ew")

    def _append_log(self, message: str):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{message}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def _set_image_box(self, content: str):
        self.image_box.configure(state="normal")
        self.image_box.delete("1.0", "end")
        self.image_box.insert("1.0", content)
        self.image_box.configure(state="disabled")

    def _refresh_image_list(self):
        if not self.selected_images:
            self.image_count_var.set("0 张图片待分析")
            self._set_image_box("还没有选择图片。\n点击“选择图片”开始。")
            return

        self.image_count_var.set(f"{len(self.selected_images)} 张图片待分析")
        lines = [f"{index + 1}. {path}" for index, path in enumerate(self.selected_images)]
        self._set_image_box("\n".join(lines))

    def _read_ai_config_from_form(self) -> AIServiceConfig:
        preset_key, preset = preset_by_label(self.ai_preset_var.get())
        return AIServiceConfig(
            preset_key=preset_key,
            provider_label=preset["label"],
            api_key=self.ai_api_key_var.get().strip(),
            base_url=self.ai_base_url_var.get().strip(),
            model=self.ai_model_var.get().strip(),
            system_prompt=self.system_prompt_box.get("1.0", "end").strip(),
            temperature=float(self.ai_temperature_var.get().strip() or "0.3"),
            max_tokens=int(self.ai_max_tokens_var.get().strip() or "900"),
            timeout=int(self.ai_timeout_var.get().strip() or "60"),
            extra_headers_json=self.extra_headers_box.get("1.0", "end").strip(),
        )

    def _apply_ai_config_to_form(self, config: AIServiceConfig):
        self.ai_preset_var.set(config.provider_label)
        self.ai_api_key_var.set(config.api_key)
        self.ai_base_url_var.set(config.base_url)
        self.ai_model_var.set(config.model)
        self.ai_temperature_var.set(str(config.temperature))
        self.ai_max_tokens_var.set(str(config.max_tokens))
        self.ai_timeout_var.set(str(config.timeout))
        self.system_prompt_box.delete("1.0", "end")
        self.system_prompt_box.insert("1.0", config.system_prompt)
        self.extra_headers_box.delete("1.0", "end")
        if config.extra_headers_json:
            self.extra_headers_box.insert("1.0", config.extra_headers_json)

    def _on_ai_preset_change(self, label: str):
        current = self._read_ai_config_from_form()
        preset_key, _ = preset_by_label(label)
        config = apply_preset(current, preset_key, keep_api_key=True)
        self._apply_ai_config_to_form(config)
        self._append_log(f"已切换 AI 预设：{label}")

    def _reset_ai_preset(self):
        current = self._read_ai_config_from_form()
        config = apply_preset(current, current.preset_key or "deepseek", keep_api_key=True)
        self._apply_ai_config_to_form(config)
        self._append_log("已恢复当前预设的默认 Base URL 和 Model。")

    def _save_ai_settings(self):
        try:
            config = self._read_ai_config_from_form()
            path = AIConfigStore.save(config)
            self.ai_config = config
            self._append_log(f"AI 配置已保存：{path}")
            messagebox.showinfo("保存成功", f"AI 配置已保存到：\n{path}")
        except Exception as exc:
            messagebox.showerror("保存失败", str(exc))

    def _choose_images(self):
        file_paths = filedialog.askopenfilenames(
            title="选择待分析图片",
            filetypes=[
                ("JPEG Images", "*.jpg *.jpeg *.JPG *.JPEG"),
                ("All Files", "*.*"),
            ],
        )
        if not file_paths:
            return

        if isinstance(file_paths, str):
            file_paths = self.tk.splitlist(file_paths)

        normalized = [os.path.normpath(path) for path in file_paths if os.path.isfile(path)]
        if not normalized:
            messagebox.showwarning("导入失败", "没有识别到有效图片文件，请重新选择。")
            self._append_log("导入失败：未识别到有效图片文件。")
            return
        existing = set(self.selected_images)
        added_count = 0
        for path in normalized:
            if path not in existing:
                self.selected_images.append(path)
                added_count += 1
        self._refresh_image_list()
        self._append_log(f"已加入 {added_count} 张图片。")

    def _clear_images(self):
        self.selected_images.clear()
        self._refresh_image_list()
        self._append_log("已清空图片列表。")

    def _choose_output_dir(self):
        directory = filedialog.askdirectory(title="选择报告导出目录", initialdir=self.output_dir)
        if not directory:
            return
        self.output_dir = os.path.normpath(directory)
        self.output_var.set(self.output_dir)
        self._append_log(f"导出目录已更新为：{self.output_dir}")

    def _open_output_dir(self):
        os.makedirs(self.output_dir, exist_ok=True)
        if hasattr(os, "startfile"):
            os.startfile(self.output_dir)
        else:
            messagebox.showinfo("导出目录", self.output_dir)

    def _start_analysis(self):
        if self.worker_thread and self.worker_thread.is_alive():
            messagebox.showinfo("提示", "当前已有任务在运行，请等待完成。")
            return

        if not self.selected_images:
            messagebox.showwarning("未选择图片", "请先选择至少一张待分析图片。")
            return

        try:
            ai_config = self._read_ai_config_from_form()
        except Exception as exc:
            messagebox.showerror("AI 配置不合法", str(exc))
            return

        os.makedirs(self.output_dir, exist_ok=True)
        provider = AnalysisProviderRegistry.by_label(self.provider_var.get())
        request = AnalysisRequest(
            image_paths=list(self.selected_images),
            output_dir=self.output_dir,
            use_ai_analysis=self.use_ai_var.get(),
            metadata={
                "ai_config": ai_config.to_dict(),
                "warnings": [],
            },
        )

        self.run_button.configure(state="disabled")
        self.progress_value.set(0.0)
        self.progress_bar.set(0.0)
        self.status_var.set("任务已启动")
        self._append_log(f"开始执行：{provider.label}")

        self.worker_thread = threading.Thread(
            target=self._run_analysis_worker,
            args=(provider, request),
            daemon=True,
        )
        self.worker_thread.start()

    def _run_analysis_worker(self, provider, request: AnalysisRequest):
        try:
            response = provider.analyze(request, progress_callback=self._queue_progress)
            self.message_queue.put(("done", response))
        except Exception as exc:
            self.message_queue.put(("error", str(exc)))

    def _queue_progress(self, stage: str, current: int, total: int, message: str):
        if total <= 0:
            progress = 0.0
        elif stage == "analyze":
            progress = 0.1 + (current / max(total, 1)) * 0.45
        elif stage == "ai":
            progress = 0.62
        elif stage == "report":
            progress = 0.7 + (current / max(total, 1)) * 0.25
        elif stage == "warning":
            progress = 0.92
        elif stage == "done":
            progress = 1.0
        else:
            progress = 0.04
        self.message_queue.put(("progress", (progress, message)))

    def _drain_queue(self):
        try:
            while True:
                event, payload = self.message_queue.get_nowait()
                if event == "progress":
                    progress, message = payload
                    self.progress_value.set(progress)
                    self.progress_bar.set(progress)
                    self.status_var.set(message)
                    self._append_log(message)
                elif event == "done":
                    response = payload
                    self.progress_value.set(1.0)
                    self.progress_bar.set(1.0)
                    self.status_var.set("全部任务已完成")
                    self.run_button.configure(state="normal")
                    self._append_log(f"完成：成功 {response.success_count}，失败 {response.failure_count}。导出目录：{response.output_dir}")
                elif event == "error":
                    self.status_var.set("执行失败")
                    self.run_button.configure(state="normal")
                    self._append_log(f"错误：{payload}")
                    messagebox.showerror("执行失败", str(payload))
        except queue.Empty:
            pass

        self.after(120, self._drain_queue)


def main():
    app = PhotoQualityWorkbenchApp()
    app.mainloop()


if __name__ == "__main__":
    main()
