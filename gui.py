"""
NitroLite - Ultra-Lightweight Acer Nitro Management Dashboard
Built with CustomTkinter for sleek aesthetics and minimal memory consumption.
"""

import sys
import os
import threading
import time
import psutil
from typing import Optional, Dict, Any
import customtkinter as ctk
from PIL import Image, ImageDraw
import pystray

from backend import AcerNitroController, OperatingMode, FanMode


def create_tray_icon_image():
    """Generate a crisp dark-mode flame/N icon for the system tray."""
    width, height = 64, 64
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Outer circle background
    draw.ellipse((4, 4, 60, 60), fill=(28, 32, 40, 255), outline=(255, 51, 75, 255), width=3)
    # Inner "N" emblem
    draw.polygon([(20, 48), (20, 16), (28, 16), (38, 36), (38, 16), (44, 16), (44, 48), (36, 48), (26, 28), (26, 48)], fill=(255, 51, 75, 255))
    return image


class NitroLiteApp(ctk.CTk):
    def __init__(self, controller: AcerNitroController, start_minimized: bool = False):
        super().__init__()

        self.controller = controller
        self.running = True
        self.is_minimized_to_tray = False
        self.current_process = psutil.Process()

        # Window Setup
        self.title("NitroLite - Hardware Controller")
        self.geometry("860x650")
        self.minsize(800, 600)
        
        # Window Icon
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        ico_file = os.path.join(base_dir, "assets", "icon.ico")
        if os.path.exists(ico_file):
            try:
                self.iconbitmap(ico_file)
            except Exception:
                pass

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        # Color Palette
        self.COLOR_BG = "#0f1115"
        self.COLOR_CARD = "#171a21"
        self.COLOR_CARD_HOVER = "#202530"
        self.COLOR_ACCENT = "#ff334b"
        self.COLOR_GREEN = "#10b981"
        self.COLOR_ORANGE = "#f59e0b"
        self.COLOR_CYAN = "#06b6d4"
        self.COLOR_BLUE = "#3b82f6"
        self.COLOR_TEXT_MUTED = "#8b949e"

        self.configure(fg_color=self.COLOR_BG)

        # State Variables
        self.active_mode = ctk.IntVar(value=OperatingMode.BALANCED)
        self.active_fan_mode = ctk.IntVar(value=FanMode.AUTO)
        self.cpu_fan_val = ctk.IntVar(value=40)
        self.gpu_fan_val = ctk.IntVar(value=40)
        
        self.var_win_key = ctk.BooleanVar(value=True)
        self.var_lcd_od = ctk.BooleanVar(value=False)
        self.var_backlight = ctk.BooleanVar(value=False)

        # Build Interface
        self._build_header()
        self._build_telemetry_cards()
        self._build_mode_selector()
        self._build_fan_controls()
        self._build_quick_toggles()
        self._build_footer()

        # Setup System Tray
        self._setup_tray()

        # Window events
        self.protocol("WM_DELETE_WINDOW", self.on_close_requested)

        # Connect & fetch initial state
        self._init_controller_state()

        # Start background polling
        self.poll_thread = threading.Thread(target=self._telemetry_poll_worker, daemon=True)
        self.poll_thread.start()

        if start_minimized:
            self.withdraw()
            self.is_minimized_to_tray = True

    def _build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=24, pady=(18, 10))

        # Title + Model Name
        left_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_box.pack(side="left")

        title_label = ctk.CTkLabel(
            left_box,
            text="NITRO LITE",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=self.COLOR_ACCENT
        )
        title_label.pack(anchor="w")

        self.model_label = ctk.CTkLabel(
            left_box,
            text=f"Model: {self.controller.model_name}",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color=self.COLOR_TEXT_MUTED
        )
        self.model_label.pack(anchor="w")

        # Right status badges
        right_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        right_box.pack(side="right")

        self.mem_badge = ctk.CTkLabel(
            right_box,
            text="RAM: ~28 MB (vs 560 MB NitroSense)",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#1f2937",
            text_color="#10b981",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.mem_badge.pack(side="right", padx=(8, 0))

        self.status_badge = ctk.CTkLabel(
            right_box,
            text="Connected",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#064e3b",
            text_color="#34d399",
            corner_radius=8,
            padx=10,
            pady=4
        )
        self.status_badge.pack(side="right")

    def _build_telemetry_cards(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=24, pady=6)
        cards_container.grid_columnconfigure((0, 1, 2), weight=1, uniform="card")

        # --- CPU Card ---
        self.cpu_card = ctk.CTkFrame(cards_container, fg_color=self.COLOR_CARD, corner_radius=12)
        self.cpu_card.grid(row=0, column=0, padx=(0, 6), sticky="nsew")

        ctk.CTkLabel(self.cpu_card, text="CPU TELEMETRY", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 2))
        self.cpu_name_lbl = ctk.CTkLabel(self.cpu_card, text=self.controller.cpu_name, font=ctk.CTkFont(size=12, weight="bold"), text_color="#ffffff")
        self.cpu_name_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        cpu_stats_box = ctk.CTkFrame(self.cpu_card, fg_color="transparent")
        cpu_stats_box.pack(fill="x", padx=16, pady=4)

        self.cpu_temp_lbl = ctk.CTkLabel(cpu_stats_box, text="-- °C", font=ctk.CTkFont(size=26, weight="bold"), text_color=self.COLOR_GREEN)
        self.cpu_temp_lbl.pack(side="left")

        self.cpu_fan_lbl = ctk.CTkLabel(cpu_stats_box, text="-- RPM", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_CYAN)
        self.cpu_fan_lbl.pack(side="right")

        self.cpu_usage_bar = ctk.CTkProgressBar(self.cpu_card, fg_color="#2b313d", progress_color=self.COLOR_ACCENT, height=8)
        self.cpu_usage_bar.pack(fill="x", padx=16, pady=(8, 4))
        self.cpu_usage_bar.set(0)

        self.cpu_sub_lbl = ctk.CTkLabel(self.cpu_card, text="Usage: 0% | Clock: -- MHz", font=ctk.CTkFont(size=11), text_color=self.COLOR_TEXT_MUTED)
        self.cpu_sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # --- GPU Card ---
        self.gpu_card = ctk.CTkFrame(cards_container, fg_color=self.COLOR_CARD, corner_radius=12)
        self.gpu_card.grid(row=0, column=1, padx=4, sticky="nsew")

        ctk.CTkLabel(self.gpu_card, text="GPU TELEMETRY", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 2))
        self.gpu_name_lbl = ctk.CTkLabel(self.gpu_card, text=self.controller.gpu_name, font=ctk.CTkFont(size=12, weight="bold"), text_color="#ffffff")
        self.gpu_name_lbl.pack(anchor="w", padx=16, pady=(0, 6))

        gpu_stats_box = ctk.CTkFrame(self.gpu_card, fg_color="transparent")
        gpu_stats_box.pack(fill="x", padx=16, pady=4)

        self.gpu_temp_lbl = ctk.CTkLabel(gpu_stats_box, text="-- °C", font=ctk.CTkFont(size=26, weight="bold"), text_color=self.COLOR_GREEN)
        self.gpu_temp_lbl.pack(side="left")

        self.gpu_fan_lbl = ctk.CTkLabel(gpu_stats_box, text="-- RPM", font=ctk.CTkFont(size=14, weight="bold"), text_color=self.COLOR_CYAN)
        self.gpu_fan_lbl.pack(side="right")

        self.gpu_usage_bar = ctk.CTkProgressBar(self.gpu_card, fg_color="#2b313d", progress_color=self.COLOR_ACCENT, height=8)
        self.gpu_usage_bar.pack(fill="x", padx=16, pady=(8, 4))
        self.gpu_usage_bar.set(0)

        self.gpu_sub_lbl = ctk.CTkLabel(self.gpu_card, text="Usage: 0% | Clock: -- MHz", font=ctk.CTkFont(size=11), text_color=self.COLOR_TEXT_MUTED)
        self.gpu_sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

        # --- RAM & System Card ---
        self.sys_card = ctk.CTkFrame(cards_container, fg_color=self.COLOR_CARD, corner_radius=12)
        self.sys_card.grid(row=0, column=2, padx=(6, 0), sticky="nsew")

        ctk.CTkLabel(self.sys_card, text="SYSTEM & RAM", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_TEXT_MUTED).pack(anchor="w", padx=16, pady=(12, 2))
        ctk.CTkLabel(self.sys_card, text="Memory & Ambient", font=ctk.CTkFont(size=12, weight="bold"), text_color="#ffffff").pack(anchor="w", padx=16, pady=(0, 6))

        sys_stats_box = ctk.CTkFrame(self.sys_card, fg_color="transparent")
        sys_stats_box.pack(fill="x", padx=16, pady=4)

        self.ram_pct_lbl = ctk.CTkLabel(sys_stats_box, text="-- %", font=ctk.CTkFont(size=26, weight="bold"), text_color=self.COLOR_BLUE)
        self.ram_pct_lbl.pack(side="left")

        self.sys_temp_lbl = ctk.CTkLabel(sys_stats_box, text="Sys: -- °C", font=ctk.CTkFont(size=13, weight="bold"), text_color=self.COLOR_TEXT_MUTED)
        self.sys_temp_lbl.pack(side="right")

        self.ram_bar = ctk.CTkProgressBar(self.sys_card, fg_color="#2b313d", progress_color=self.COLOR_BLUE, height=8)
        self.ram_bar.pack(fill="x", padx=16, pady=(8, 4))
        self.ram_bar.set(0)

        self.ram_sub_lbl = ctk.CTkLabel(self.sys_card, text="RAM: -- / -- GB", font=ctk.CTkFont(size=11), text_color=self.COLOR_TEXT_MUTED)
        self.ram_sub_lbl.pack(anchor="w", padx=16, pady=(0, 12))

    def _build_mode_selector(self):
        mode_box = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, corner_radius=12)
        mode_box.pack(fill="x", padx=24, pady=8)

        ctk.CTkLabel(
            mode_box,
            text="PERFORMANCE MODE",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(12, 8))

        btn_row = ctk.CTkFrame(mode_box, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 12))
        btn_row.grid_columnconfigure((0, 1, 2, 3), weight=1, uniform="mode_btn")

        self.mode_buttons = {}
        modes = [
            (OperatingMode.ECO, "Eco", "#059669", "Battery Saver & Cool"),
            (OperatingMode.QUIET, "Quiet", "#0284c7", "Silent Fans"),
            (OperatingMode.BALANCED, "Balanced", "#4f46e5", "Optimal Daily"),
            (OperatingMode.GAMING, "Gaming", "#dc2626", "Max Clocks & Power")
        ]

        for col, (mode_id, name, color, desc) in enumerate(modes):
            btn = ctk.CTkButton(
                btn_row,
                text=f"{name}\n{desc}",
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color="#1f242d",
                hover_color=color,
                height=52,
                corner_radius=8,
                command=lambda m=mode_id: self.on_select_mode(m)
            )
            btn.grid(row=0, column=col, padx=4, sticky="nsew")
            self.mode_buttons[mode_id] = btn

    def _build_fan_controls(self):
        fan_box = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, corner_radius=12)
        fan_box.pack(fill="x", padx=24, pady=6)

        header_row = ctk.CTkFrame(fan_box, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            header_row,
            text="FAN CONTROL",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.COLOR_TEXT_MUTED
        ).pack(side="left")

        self.fan_seg = ctk.CTkSegmentedButton(
            header_row,
            values=["Auto", "Max (100%)", "Custom"],
            command=self.on_fan_seg_change,
            selected_color=self.COLOR_ACCENT,
            selected_hover_color="#d61f36",
            height=30
        )
        self.fan_seg.pack(side="right")
        self.fan_seg.set("Auto")

        # Custom Fan Sliders (shown when Custom is active)
        self.slider_frame = ctk.CTkFrame(fan_box, fg_color="transparent")
        self.slider_frame.pack(fill="x", padx=16, pady=(4, 12))
        self.slider_frame.grid_columnconfigure((0, 1), weight=1)

        # CPU Fan Slider
        cpu_box = ctk.CTkFrame(self.slider_frame, fg_color="#13161c", corner_radius=8)
        cpu_box.grid(row=0, column=0, padx=(0, 6), sticky="nsew", pady=4)
        
        cpu_lbl_row = ctk.CTkFrame(cpu_box, fg_color="transparent")
        cpu_lbl_row.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(cpu_lbl_row, text="CPU Custom Speed", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.cpu_slider_val_lbl = ctk.CTkLabel(cpu_lbl_row, text="40%", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_CYAN)
        self.cpu_slider_val_lbl.pack(side="right")

        self.cpu_slider = ctk.CTkSlider(
            cpu_box,
            from_=0,
            to=100,
            number_of_steps=100,
            variable=self.cpu_fan_val,
            command=lambda v: self.cpu_slider_val_lbl.configure(text=f"{int(v)}%"),
            progress_color=self.COLOR_CYAN,
            button_color=self.COLOR_CYAN
        )
        self.cpu_slider.pack(fill="x", padx=12, pady=(4, 10))

        # GPU Fan Slider
        gpu_box = ctk.CTkFrame(self.slider_frame, fg_color="#13161c", corner_radius=8)
        gpu_box.grid(row=0, column=1, padx=(6, 0), sticky="nsew", pady=4)

        gpu_lbl_row = ctk.CTkFrame(gpu_box, fg_color="transparent")
        gpu_lbl_row.pack(fill="x", padx=12, pady=(8, 2))
        ctk.CTkLabel(gpu_lbl_row, text="GPU Custom Speed", font=ctk.CTkFont(size=11, weight="bold")).pack(side="left")
        self.gpu_slider_val_lbl = ctk.CTkLabel(gpu_lbl_row, text="40%", font=ctk.CTkFont(size=11, weight="bold"), text_color=self.COLOR_CYAN)
        self.gpu_slider_val_lbl.pack(side="right")

        self.gpu_slider = ctk.CTkSlider(
            gpu_box,
            from_=0,
            to=100,
            number_of_steps=100,
            variable=self.gpu_fan_val,
            command=lambda v: self.gpu_slider_val_lbl.configure(text=f"{int(v)}%"),
            progress_color=self.COLOR_CYAN,
            button_color=self.COLOR_CYAN
        )
        self.gpu_slider.pack(fill="x", padx=12, pady=(4, 10))

        # Apply Custom Button
        self.apply_btn = ctk.CTkButton(
            self.slider_frame,
            text="Apply Custom Speeds",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#2b313d",
            hover_color=self.COLOR_CYAN,
            height=32,
            command=self.on_apply_custom_fan
        )
        self.apply_btn.grid(row=1, column=0, columnspan=2, pady=(6, 2), sticky="ew")

        # Disable sliders initially (Auto mode)
        self._toggle_slider_state(False)

    def _build_quick_toggles(self):
        toggle_box = ctk.CTkFrame(self, fg_color=self.COLOR_CARD, corner_radius=12)
        toggle_box.pack(fill="x", padx=24, pady=6)

        ctk.CTkLabel(
            toggle_box,
            text="SYSTEM & GAMING TOGGLES",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.COLOR_TEXT_MUTED
        ).pack(anchor="w", padx=16, pady=(10, 6))

        row = ctk.CTkFrame(toggle_box, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(0, 10))
        row.grid_columnconfigure((0, 1, 2), weight=1)

        self.sw_win = ctk.CTkSwitch(
            row,
            text="Windows Key Lock",
            variable=self.var_win_key,
            command=self.on_toggle_win_key,
            progress_color=self.COLOR_ACCENT
        )
        self.sw_win.grid(row=0, column=0, sticky="w", padx=4)

        self.sw_lcd = ctk.CTkSwitch(
            row,
            text="LCD Overdrive (Fast Res)",
            variable=self.var_lcd_od,
            command=self.on_toggle_lcd,
            progress_color=self.COLOR_ACCENT
        )
        self.sw_lcd.grid(row=0, column=1, sticky="w", padx=4)

        self.sw_bk = ctk.CTkSwitch(
            row,
            text="Backlight 30s Timeout",
            variable=self.var_backlight,
            command=self.on_toggle_backlight,
            progress_color=self.COLOR_ACCENT
        )
        self.sw_bk.grid(row=0, column=2, sticky="w", padx=4)

    def _build_footer(self):
        footer = ctk.CTkFrame(self, fg_color="transparent")
        footer.pack(fill="x", padx=24, pady=(6, 12))

        ctk.CTkLabel(
            footer,
            text="NitroLite • Zero Bloat Alternative to NitroSense • Antigravity",
            font=ctk.CTkFont(size=11),
            text_color=self.COLOR_TEXT_MUTED
        ).pack(side="left")

        tray_btn = ctk.CTkButton(
            footer,
            text="Minimize to Tray",
            font=ctk.CTkFont(size=11),
            fg_color="#1f242d",
            hover_color="#2c3340",
            width=110,
            height=28,
            command=self.minimize_to_tray
        )
        tray_btn.pack(side="right")

    def _init_controller_state(self):
        """Fetch current hardware state on startup."""
        def init_task():
            if self.controller.connect():
                cur_mode = self.controller.get_operating_mode()
                win_status = self.controller.get_toggle_status("WIN_KEY")
                lcd_status = self.controller.get_toggle_status("LCD_OVERDRIVE")
                bk_status = self.controller.get_toggle_status("BACKLIGHT_30S")

                self.after(0, lambda: self._apply_initial_state(cur_mode, win_status, lcd_status, bk_status))
            else:
                self.after(0, lambda: self.status_badge.configure(text="Disconnected", fg_color="#7f1d1d", text_color="#fca5a5"))

        threading.Thread(target=init_task, daemon=True).start()

    def _apply_initial_state(self, cur_mode, win_status, lcd_status, bk_status):
        self.status_badge.configure(text="Connected", fg_color="#064e3b", text_color="#34d399")
        self.cpu_name_lbl.configure(text=self.controller.cpu_name)
        self.gpu_name_lbl.configure(text=self.controller.gpu_name)
        self.model_label.configure(text=f"Model: {self.controller.model_name}")

        if cur_mode is not None:
            self.active_mode.set(cur_mode)
            self._highlight_mode_button(cur_mode)

        if win_status is not None:
            self.var_win_key.set(win_status == 1)
        if lcd_status is not None:
            self.var_lcd_od.set(lcd_status == 1)
        if bk_status is not None:
            self.var_backlight.set(bk_status == 1)

    def _highlight_mode_button(self, active_mode_id):
        colors = {
            OperatingMode.ECO: "#059669",
            OperatingMode.QUIET: "#0284c7",
            OperatingMode.BALANCED: "#4f46e5",
            OperatingMode.GAMING: "#dc2626"
        }
        for mode_id, btn in self.mode_buttons.items():
            if mode_id == active_mode_id:
                btn.configure(fg_color=colors.get(mode_id, self.COLOR_ACCENT))
            else:
                btn.configure(fg_color="#1f242d")

    def on_select_mode(self, mode_id: int):
        self.active_mode.set(mode_id)
        self._highlight_mode_button(mode_id)
        threading.Thread(target=lambda: self.controller.set_operating_mode(mode_id), daemon=True).start()

    def on_fan_seg_change(self, value: str):
        if value == "Auto":
            self.active_fan_mode.set(FanMode.AUTO)
            self._toggle_slider_state(False)
            threading.Thread(target=lambda: self.controller.set_fan_control(FanMode.AUTO), daemon=True).start()
        elif value == "Max (100%)":
            self.active_fan_mode.set(FanMode.MAX)
            self._toggle_slider_state(False)
            threading.Thread(target=lambda: self.controller.set_fan_control(FanMode.MAX), daemon=True).start()
        elif value == "Custom":
            self.active_fan_mode.set(FanMode.CUSTOM)
            self._toggle_slider_state(True)
            self.on_apply_custom_fan()

    def _toggle_slider_state(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self.cpu_slider.configure(state=state)
        self.gpu_slider.configure(state=state)
        self.apply_btn.configure(state=state)
        if enabled:
            self.apply_btn.configure(fg_color=self.COLOR_CYAN, text_color="#000000")
        else:
            self.apply_btn.configure(fg_color="#2b313d", text_color=self.COLOR_TEXT_MUTED)

    def on_apply_custom_fan(self):
        cpu_spd = self.cpu_fan_val.get()
        gpu_spd = self.gpu_fan_val.get()
        threading.Thread(
            target=lambda: self.controller.set_fan_control(FanMode.CUSTOM, cpu_spd, gpu_spd),
            daemon=True
        ).start()

    def on_toggle_win_key(self):
        val = 1 if self.var_win_key.get() else 0
        threading.Thread(target=lambda: self.controller.set_toggle_status("WIN_KEY", val), daemon=True).start()

    def on_toggle_lcd(self):
        val = 1 if self.var_lcd_od.get() else 0
        threading.Thread(target=lambda: self.controller.set_toggle_status("LCD_OVERDRIVE", val), daemon=True).start()

    def on_toggle_backlight(self):
        val = 1 if self.var_backlight.get() else 0
        threading.Thread(target=lambda: self.controller.set_toggle_status("BACKLIGHT_30S", val), daemon=True).start()

    def _telemetry_poll_worker(self):
        """Poll telemetry every 1.5s when active, 8s when in tray."""
        while self.running:
            try:
                if self.is_minimized_to_tray:
                    time.sleep(8.0)
                else:
                    time.sleep(1.5)

                if not self.running:
                    break

                data = self.controller.get_monitoring_data()
                mem_mb = self.current_process.memory_info().rss / (1024 * 1024)

                if data:
                    self.after(0, lambda d=data, m=mem_mb: self._update_ui_telemetry(d, m))
                else:
                    self.after(0, lambda: self.status_badge.configure(text="Reconnecting...", fg_color="#78350f", text_color="#fde68a"))
            except Exception:
                pass

    def _update_ui_telemetry(self, data: Dict[str, Any], mem_mb: float):
        if not self.running or self.is_minimized_to_tray:
            return

        self.status_badge.configure(text="Connected", fg_color="#064e3b", text_color="#34d399")
        self.mem_badge.configure(text=f"RAM: {mem_mb:.1f} MB (vs 560 MB NitroSense)")

        # CPU
        cpu_temp = data.get("CPU_TEMPERATURE", 0)
        cpu_fan = data.get("CPU_FANSPEED", 0)
        cpu_usage = data.get("CPU_USAGE", 0)
        cpu_freq = data.get("CPU_FREQUENCY", 0)

        self.cpu_temp_lbl.configure(
            text=f"{cpu_temp} °C",
            text_color=self.COLOR_GREEN if cpu_temp < 65 else (self.COLOR_ORANGE if cpu_temp < 80 else self.COLOR_ACCENT)
        )
        self.cpu_fan_lbl.configure(text=f"{cpu_fan} RPM")
        self.cpu_usage_bar.set(min(1.0, max(0.0, cpu_usage / 100.0)))
        self.cpu_sub_lbl.configure(text=f"Usage: {cpu_usage:.1f}% | Clock: {cpu_freq:.0f} MHz")

        # GPU
        gpu_temp = data.get("GPU1_TEMPERATURE", 0)
        gpu_fan = data.get("GPU1_FANSPEED", 0)
        gpu_usage = data.get("GPU1_USAGE", 0)
        gpu_freq = data.get("GPU1_FREQUENCY", 0)

        self.gpu_temp_lbl.configure(
            text=f"{gpu_temp} °C",
            text_color=self.COLOR_GREEN if gpu_temp < 65 else (self.COLOR_ORANGE if gpu_temp < 80 else self.COLOR_ACCENT)
        )
        self.gpu_fan_lbl.configure(text=f"{gpu_fan} RPM")
        self.gpu_usage_bar.set(min(1.0, max(0.0, gpu_usage / 100.0)))
        self.gpu_sub_lbl.configure(text=f"Usage: {gpu_usage}% | Clock: {gpu_freq:.0f} MHz")

        # RAM & System
        ram_pct = data.get("RAM_USAGE", 0)
        ram_total = data.get("RAM_TOTAL", 16384) / 1024.0
        ram_used = (ram_pct / 100.0) * ram_total
        sys_temp = data.get("SYS1_TEMPERATURE", 0)

        self.ram_pct_lbl.configure(text=f"{ram_pct:.0f}%")
        self.sys_temp_lbl.configure(text=f"Sys: {sys_temp} °C")
        self.ram_bar.set(min(1.0, max(0.0, ram_pct / 100.0)))
        self.ram_sub_lbl.configure(text=f"RAM: {ram_used:.1f} / {ram_total:.1f} GB")

    def _setup_tray(self):
        """Set up system tray icon with quick actions."""
        tray_image = create_tray_icon_image()

        def on_tray_show(icon, item):
            self.after(0, self.restore_from_tray)

        def on_tray_mode(icon, item, mode_id):
            self.after(0, lambda: self.on_select_mode(mode_id))

        def on_tray_fan(icon, item, fan_mode):
            if fan_mode == FanMode.AUTO:
                self.after(0, lambda: self.fan_seg.set("Auto"))
                self.after(0, lambda: self.on_fan_seg_change("Auto"))
            elif fan_mode == FanMode.MAX:
                self.after(0, lambda: self.fan_seg.set("Max (100%)"))
                self.after(0, lambda: self.on_fan_seg_change("Max (100%)"))

        def on_tray_exit(icon, item):
            self.after(0, self.quit_app)

        menu = pystray.Menu(
            pystray.MenuItem("Show NitroLite", on_tray_show, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quiet Mode", lambda icon, item: on_tray_mode(icon, item, OperatingMode.QUIET)),
            pystray.MenuItem("Balanced Mode", lambda icon, item: on_tray_mode(icon, item, OperatingMode.BALANCED)),
            pystray.MenuItem("Gaming Mode", lambda icon, item: on_tray_mode(icon, item, OperatingMode.GAMING)),
            pystray.MenuItem("Eco Mode", lambda icon, item: on_tray_mode(icon, item, OperatingMode.ECO)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Fan: Auto", lambda icon, item: on_tray_fan(icon, item, FanMode.AUTO)),
            pystray.MenuItem("Fan: Max (100%)", lambda icon, item: on_tray_fan(icon, item, FanMode.MAX)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", on_tray_exit)
        )

        self.tray_icon = pystray.Icon("NitroLite", tray_image, "NitroLite - Acer Nitro Controller", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def minimize_to_tray(self):
        self.withdraw()
        self.is_minimized_to_tray = True

    def restore_from_tray(self):
        self.deiconify()
        self.lift()
        self.focus_force()
        self.is_minimized_to_tray = False

    def on_close_requested(self):
        self.minimize_to_tray()

    def quit_app(self):
        self.running = False
        try:
            self.tray_icon.stop()
        except Exception:
            pass
        self.controller.close()
        self.destroy()
        sys.exit(0)
