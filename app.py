"""DECART LIVE PRO - REAL-TIME AI SOFTWARE
Standalone Desktop Client with Direct Video Platform API Key Connection.
"""

import asyncio
import os
import sys

# Ensure Tkinter / Tcl is located correctly within Windows virtual environments
if not getattr(sys, "frozen", False):
    base_prefix = getattr(sys, "base_prefix", sys.prefix)
    for tcl_candidate in [
        os.path.join(base_prefix, "tcl", "tcl8.6"),
        os.path.join(base_prefix, "lib", "tcl8.6"),
        r"C:\Users\IT-ADMIN\AppData\Local\Programs\Python\Python313\tcl\tcl8.6",
    ]:
        if os.path.exists(tcl_candidate):
            os.environ["TCL_LIBRARY"] = tcl_candidate
            break

    for tk_candidate in [
        os.path.join(base_prefix, "tcl", "tk8.6"),
        os.path.join(base_prefix, "lib", "tk8.6"),
        r"C:\Users\IT-ADMIN\AppData\Local\Programs\Python\Python313\tcl\tk8.6",
    ]:
        if os.path.exists(tk_candidate):
            os.environ["TK_LIBRARY"] = tk_candidate
            break


import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

import cv2
import customtkinter as ctk
import numpy as np
from PIL import Image, ImageTk

from config import load_config, save_config
from engine import StreamingEngine
from vidu_sdk import CameraAspectChecker, EditType, SessionPhase

# Set CustomTkinter theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Curated palette matching Decart Live Pro design
COLOR_BG = "#080c14"
COLOR_CARD = "#0d1424"
COLOR_CARD_BORDER = "#1a243a"
COLOR_INPUT_BG = "#0a0f1c"
COLOR_INPUT_BORDER = "#1c263c"
COLOR_ACCENT_GREEN = "#00ffa3"
COLOR_BADGE_BG = "#042c1c"
COLOR_BADGE_BORDER = "#064e3b"
COLOR_START_BTN = "#00e676"
COLOR_START_BTN_HOVER = "#00c853"
COLOR_STOP_BTN = "#3d141c"
COLOR_STOP_BTN_HOVER = "#5c1b27"
COLOR_STOP_TEXT = "#f87171"
COLOR_BTN_SEC = "#121a2c"
COLOR_BTN_SEC_HOVER = "#1c263c"
COLOR_TEXT_MUTED = "#64748b"
COLOR_TEXT_PRIMARY = "#f1f5f9"
COLOR_BADGE_BLUE_BG = "#0f233a"
COLOR_BADGE_BLUE_TEXT = "#38bdf8"


LOG_FILE = Path.home() / ".decart_live_pro" / "decart_live.log"


def log_app(msg: str):
    """Write timestamped log message to stdout and persistent decart_live.log file."""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {msg}"
    print(formatted, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass


class DecartLiveProApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("DECART LIVE PRO")
        # Fixed compact geometry fitting full detailed UI without any scrollbars
        self.geometry("490x750")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)

        # Load persisted settings
        self.config = load_config()
        self.api_key = self.config.get("api_key", os.getenv("REACTOR_API_KEY", ""))
        self.telegram_url = self.config.get("telegram_url", "https://t.me/p3g4z3us")
        self.ref_image_path = self.config.get("reference_image", "")
        self.selected_mode = self.config.get("editing_type", "style_transfer")
        self.zoom_factor = self.config.get("zoom_factor", 0.5)
        self.is_streaming = False
        self.is_actively_transforming = False
        self.show_api_key = False

        # Streaming engine (direct connection)
        self.engine = StreamingEngine()

        # Threading and streaming state
        self.worker_thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.latest_edited_frame = None
        self.latest_local_frame = None
        self.stop_requested = False
        self.thumbnail_photo = None

        self._build_ui()
        self._load_saved_reference_image()

    def _build_ui(self):
        # Non-scrollable fixed frame fitting all rich controls
        self.container = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.container.pack(fill="both", expand=True, padx=12, pady=8)

        # 1. Header
        self._create_header()

        # 2. Direct API Key Configuration Card
        self._create_api_key_card()

        # 3. Model & Transformation Card
        self._create_model_card()

        # 4. Reference Image Card
        self._create_reference_card()

        # 5. Main Action Buttons (START / STOP LIVE)
        self._create_action_buttons()

        # 6. Utilities (Test Webcam & User Guide)
        self._create_utilities()

        # 7. Status Footer
        self._create_footer()

    def _create_header(self):
        header_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(2, 6))

        title_lbl = ctk.CTkLabel(
            header_frame,
            text="DECART  LIVE  PRO",
            font=ctk.CTkFont(family="Segoe UI", size=21, weight="bold"),
            text_color=COLOR_ACCENT_GREEN,
        )
        title_lbl.pack(pady=(0, 1))

        sub_lbl = ctk.CTkLabel(
            header_frame,
            text="REAL-TIME AI SOFTWARE · DIRECT CONNECT",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#64748b",
        )
        sub_lbl.pack()

    def _create_card(self) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            self.container,
            fg_color=COLOR_CARD,
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=10,
        )
        card.pack(fill="x", pady=5)
        return card

    def _create_badge_header(self, parent, badge_text: str, sub_text: str, sub_color=COLOR_TEXT_MUTED):
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=12, pady=(8, 6))

        badge = ctk.CTkLabel(
            header,
            text=f" {badge_text} ",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            fg_color=COLOR_BADGE_BG,
            text_color=COLOR_ACCENT_GREEN,
            corner_radius=4,
            height=18,
        )
        badge.pack(side="left")

        sub = ctk.CTkLabel(
            header,
            text=f"  {sub_text}",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=sub_color,
        )
        sub.pack(side="left")

    def _create_api_key_card(self):
        """Card for entering and managing the direct Reactor/Decart API key."""
        card = self._create_card()
        self._create_badge_header(card, "API KEY", "Direct Video Platform Access", sub_color=COLOR_BADGE_BLUE_TEXT)

        entry_row = ctk.CTkFrame(card, fg_color="transparent")
        entry_row.pack(fill="x", padx=12, pady=(0, 8))

        self.key_entry = ctk.CTkEntry(
            entry_row,
            placeholder_text="Enter API Key (rk_...)",
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            text_color=COLOR_TEXT_PRIMARY,
            height=34,
            show="•",
        )
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        if self.api_key:
            self.key_entry.insert(0, self.api_key)

        self.key_entry.bind("<KeyRelease>", self._on_key_changed)

        self.toggle_eye_btn = ctk.CTkButton(
            entry_row,
            text="👁",
            width=34,
            height=34,
            fg_color=COLOR_BTN_SEC,
            hover_color=COLOR_BTN_SEC_HOVER,
            command=self._toggle_show_key,
        )
        self.toggle_eye_btn.pack(side="left", padx=(0, 6))

        paste_btn = ctk.CTkButton(
            entry_row,
            text="Paste",
            width=50,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_BTN_SEC,
            hover_color=COLOR_BTN_SEC_HOVER,
            text_color=COLOR_BADGE_BLUE_TEXT,
            command=self._paste_api_key,
        )
        paste_btn.pack(side="left")

    def _toggle_show_key(self):
        self.show_api_key = not self.show_api_key
        if self.show_api_key:
            self.key_entry.configure(show="")
            self.toggle_eye_btn.configure(text="🔒")
        else:
            self.key_entry.configure(show="•")
            self.toggle_eye_btn.configure(text="👁")

    def _paste_api_key(self):
        try:
            val = self.clipboard_get().strip()
            if val:
                self.key_entry.delete(0, "end")
                self.key_entry.insert(0, val)
                self.api_key = val
                self._save_settings()
                self.set_status("● API Key saved", COLOR_ACCENT_GREEN)
        except Exception:
            pass

    def _on_key_changed(self, event=None):
        val = self.key_entry.get().strip()
        self.api_key = val
        self._save_settings()

    def _create_model_card(self):
        card = self._create_card()
        self._create_badge_header(card, "MODEL", "⚡ Auto-Identity Prompt: Active", sub_color=COLOR_ACCENT_GREEN)

        self.model_combo = ctk.CTkComboBox(
            card,
            values=[
                "Realtime Video PRO",
                "Live Avatar PRO",
                "Interactive World PRO",
            ],
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            button_color=COLOR_BTN_SEC,
            button_hover_color=COLOR_BTN_SEC_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=11),
        )
        self.model_combo.set("Realtime Video PRO")
        self.model_combo.pack(fill="x", padx=12, pady=(0, 6))

        # Mode Selection
        mode_lbl = ctk.CTkLabel(
            card,
            text="Realtime Transformation Mode:",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#94a3b8",
            anchor="w",
        )
        mode_lbl.pack(fill="x", padx=12, pady=(0, 2))

        self.mode_combo = ctk.CTkComboBox(
            card,
            values=[
                "Style Transfer (Full Scene)",
                "Virtual Try-On (Garment/Outfit)",
                "Subject Replacement (Character)",
                "Background Replacement (Scene)",
            ],
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            button_color=COLOR_BTN_SEC,
            button_hover_color=COLOR_BTN_SEC_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._on_mode_changed,
        )
        self.mode_combo.set("Style Transfer (Full Scene)")
        self.mode_combo.pack(fill="x", padx=12, pady=(0, 6))

        # Camera FOV Zoom Selection
        zoom_lbl = ctk.CTkLabel(
            card,
            text="Camera Field of View (Framing):",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color="#94a3b8",
            anchor="w",
        )
        zoom_lbl.pack(fill="x", padx=12, pady=(0, 2))

        self.zoom_combo = ctk.CTkComboBox(
            card,
            values=[
                "0.5x (Ultra-Wide - iPhone Style)",
                "0.65x (Wide - Balanced)",
                "0.8x (Medium)",
                "1.0x (Standard Normal)",
            ],
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            button_color=COLOR_BTN_SEC,
            button_hover_color=COLOR_BTN_SEC_HOVER,
            text_color=COLOR_TEXT_PRIMARY,
            dropdown_fg_color=COLOR_CARD,
            height=34,
            font=ctk.CTkFont(family="Segoe UI", size=11),
            command=self._on_zoom_changed,
        )
        self.zoom_combo.set("0.5x (Ultra-Wide - iPhone Style)")
        self.zoom_combo.pack(fill="x", padx=12, pady=(0, 6))

        # Picture-in-Picture Toggle
        self.show_pip_var = ctk.BooleanVar(value=self.config.get("show_pip", False))
        self.pip_checkbox = ctk.CTkCheckBox(
            card,
            text="Show Camera PIP Preview (Picture-in-Picture)",
            variable=self.show_pip_var,
            command=self._on_pip_toggled,
            text_color="#94a3b8",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color=COLOR_ACCENT_GREEN,
            hover_color=COLOR_START_BTN_HOVER,
            checkmark_color="#042314",
        )
        self.pip_checkbox.pack(fill="x", padx=14, pady=(0, 8))

    def _create_reference_card(self):
        card = self._create_card()
        self._create_badge_header(card, "REFERENCE IMAGE", "Character or Style Target")

        body = ctk.CTkFrame(card, fg_color="transparent")
        body.pack(fill="x", padx=12, pady=(0, 8))

        self.thumb_frame = ctk.CTkFrame(
            body,
            width=70,
            height=70,
            fg_color=COLOR_INPUT_BG,
            border_color=COLOR_INPUT_BORDER,
            border_width=1,
            corner_radius=6,
        )
        self.thumb_frame.pack(side="left", padx=(0, 10))
        self.thumb_frame.pack_propagate(False)

        self.thumb_label = ctk.CTkLabel(
            self.thumb_frame,
            text="No Image",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color=COLOR_TEXT_MUTED,
        )
        self.thumb_label.pack(expand=True)

        btn_column = ctk.CTkFrame(body, fg_color="transparent")
        btn_column.pack(side="left", fill="both", expand=True)

        pick_btn = ctk.CTkButton(
            btn_column,
            text="Select Target Image...",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_BTN_SEC,
            hover_color=COLOR_BTN_SEC_HOVER,
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=6,
            height=32,
            command=self._select_reference_image,
        )
        pick_btn.pack(fill="x", pady=(2, 4))

        clear_btn = ctk.CTkButton(
            btn_column,
            text="✕ Clear Image",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color="transparent",
            hover_color="#182236",
            text_color=COLOR_TEXT_MUTED,
            height=22,
            command=self._clear_reference_image,
        )
        clear_btn.pack(anchor="w")

    def _create_action_buttons(self):
        btn_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(4, 6))

        self.start_btn = ctk.CTkButton(
            btn_frame,
            text="START LIVE",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_START_BTN,
            hover_color=COLOR_START_BTN_HOVER,
            text_color="#042314",
            height=40,
            corner_radius=8,
            command=self.start_live,
        )
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.stop_btn = ctk.CTkButton(
            btn_frame,
            text="STOP LIVE",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            fg_color=COLOR_STOP_BTN,
            hover_color=COLOR_STOP_BTN_HOVER,
            text_color=COLOR_STOP_TEXT,
            height=40,
            corner_radius=8,
            state="disabled",
            command=self.stop_live,
        )
        self.stop_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))

    def _create_utilities(self):
        test_cam_btn = ctk.CTkButton(
            self.container,
            text="📷   Test Webcam (Preview & Aspect Check)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_BTN_SEC,
            hover_color=COLOR_BTN_SEC_HOVER,
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=6,
            height=34,
            command=self._test_webcam_dialog,
        )
        test_cam_btn.pack(fill="x", pady=(2, 4))

        guide_btn = ctk.CTkButton(
            self.container,
            text="📘   User Guide (Step-by-Step Instructions)",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color=COLOR_BTN_SEC,
            hover_color=COLOR_BTN_SEC_HOVER,
            border_color=COLOR_CARD_BORDER,
            border_width=1,
            corner_radius=6,
            height=34,
            command=self._open_user_guide_modal,
        )
        guide_btn.pack(fill="x", pady=(0, 4))

    def _create_footer(self):
        footer_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(4, 2))

        self.status_lbl = ctk.CTkLabel(
            footer_frame,
            text="● Ready",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=COLOR_ACCENT_GREEN,
            anchor="w",
        )
        self.status_lbl.pack(fill="x", pady=(0, 2))

        footer_sub = ctk.CTkLabel(
            footer_frame,
            text="Direct Video Platform Connection · Standalone Client",
            font=ctk.CTkFont(family="Segoe UI", size=9),
            text_color="#475569",
            anchor="w",
        )
        footer_sub.pack(fill="x")

    def _open_user_guide_modal(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("DECART LIVE PRO — User Guide")
        dialog.geometry("460x520")
        dialog.configure(fg_color=COLOR_BG)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="📘 USER GUIDE",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=COLOR_ACCENT_GREEN,
        ).pack(pady=(14, 4))

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=16, pady=4)

        steps = [
            ("1. API Key", "Enter your direct Reactor / Decart API key (rk_...) in the API Key box. It is saved locally and connects directly to the streaming platform."),
            ("2. The 3 AI Models",
             "• Realtime Video PRO: Full-scene cinematic style transfer.\n"
             "• Live Avatar PRO: Character replacement & virtual outfit try-on.\n"
             "• Interactive World PRO: Replaces your background while keeping you intact."),
            ("3. Target Reference Image", "Upload your character, outfit, or background style image. You can hot-swap target images live mid-stream!"),
            ("4. Start Streaming", "Click 'START LIVE'. The live AI video window pops up immediately at native widescreen 7:4 format. Press 'Q' or 'STOP LIVE' when done."),
        ]

        for title, desc in steps:
            card = ctk.CTkFrame(scroll, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1, corner_radius=8)
            card.pack(fill="x", pady=4)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=COLOR_ACCENT_GREEN, anchor="w").pack(fill="x", padx=10, pady=(6, 2))
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(family="Segoe UI", size=10), text_color="#e2e8f0", justify="left", wraplength=380, anchor="w").pack(fill="x", padx=10, pady=(0, 6))

        ctk.CTkButton(dialog, text="Close Guide", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), fg_color=COLOR_BTN_SEC, height=32, command=dialog.destroy).pack(pady=10)

    # ---------------- UI Event Handlers ----------------

    def _on_mode_changed(self, choice: str):
        mode_map = {
            "Style Transfer (Full Scene)": "style_transfer",
            "Virtual Try-On (Garment/Outfit)": "virtual_tryon",
            "Subject Replacement (Character)": "subject_replacement",
            "Background Replacement (Scene)": "background_replacement",
        }
        self.selected_mode = mode_map.get(choice, "style_transfer")
        self._save_settings()

        if self.is_streaming and self.engine.client and self.loop:
            self.set_status("🟡 Hot-switching mode...", COLOR_BADGE_BLUE_TEXT)
            asyncio.run_coroutine_threadsafe(
                self.engine.client.switch_reference(editing_type=self.selected_mode),
                self.loop,
            )

    def _on_zoom_changed(self, choice: str):
        zoom_map = {
            "0.5x (Ultra-Wide - iPhone Style)": 0.5,
            "0.65x (Wide - Balanced)": 0.65,
            "0.8x (Medium)": 0.8,
            "1.0x (Standard Normal)": 1.0,
        }
        self.zoom_factor = zoom_map.get(choice, 0.5)
        self._save_settings()

        if self.engine.client:
            self.engine.client.set_webcam_zoom(self.zoom_factor)

    def _on_pip_toggled(self):
        self._save_settings()

    def _select_reference_image(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select Reference Image",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp")],
        )
        if path:
            self.ref_image_path = path
            self._display_thumbnail(path)
            self._save_settings()

            if self.is_streaming and self.engine.client and self.loop:
                self.set_status("🟡 Hot-switching image...", COLOR_BADGE_BLUE_TEXT)
                asyncio.run_coroutine_threadsafe(
                    self.engine.client.switch_reference(reference_image=path),
                    self.loop,
                )

    def _clear_reference_image(self):
        self.ref_image_path = ""
        self.thumb_label.configure(image="", text="No Image")
        self._save_settings()

    def _display_thumbnail(self, path: str):
        try:
            pil_img = Image.open(path)
            pil_img.thumbnail((70, 70))
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            self.thumb_label.configure(image=ctk_img, text="")
        except Exception:
            self.thumb_label.configure(image="", text="Invalid")

    def _load_saved_reference_image(self):
        if self.ref_image_path and os.path.exists(self.ref_image_path):
            self._display_thumbnail(self.ref_image_path)
        else:
            bundle_dir = getattr(sys, "_MEIPASS", os.path.dirname(__file__))
            default_asset = os.path.join(bundle_dir, "assets", "sample_reference.png")
            if os.path.exists(default_asset):
                self.ref_image_path = default_asset
                self._display_thumbnail(default_asset)

    def _save_settings(self):
        self.config["api_key"] = self.api_key
        self.config["reference_image"] = self.ref_image_path
        self.config["editing_type"] = self.selected_mode
        self.config["zoom_factor"] = getattr(self, "zoom_factor", 0.5)
        self.config["show_pip"] = self.show_pip_var.get() if hasattr(self, "show_pip_var") else False
        save_config(self.config)

    def set_status(self, text: str, color: str = COLOR_ACCENT_GREEN):
        self.after(0, lambda: self.status_lbl.configure(text=text, text_color=color))

    # ---------------- Live Streaming Worker ----------------

    def start_live(self):
        key = self.key_entry.get().strip()
        if not key:
            self.set_status("● Missing API Key: Enter your key above", COLOR_STOP_TEXT)
            self.key_entry.focus()
            return

        self.api_key = key
        self._save_settings()

        self.is_actively_transforming = False
        self.is_streaming = True
        self.stop_requested = False

        self.start_btn.configure(state="disabled", fg_color="#1e3a2f")
        self.stop_btn.configure(state="normal", fg_color="#991b1b")
        self.set_status("● Launching AI session...", "#facc15")

        self.worker_thread = threading.Thread(target=self._run_async_worker, args=(self.api_key,), daemon=True)
        self.worker_thread.start()

    def stop_live(self):
        if not self.is_streaming:
            return

        self.set_status("● Stopping session...", "#facc15")
        self.stop_requested = True
        self.is_streaming = False
        self.is_actively_transforming = False

        self.after(500, self._reset_ui_after_stop)

    def _reset_ui_after_stop(self, preserve_error: bool = False):
        self.is_streaming = False
        self.is_actively_transforming = False
        self.stop_requested = False
        self.latest_edited_frame = None
        self.latest_local_frame = None
        self.start_btn.configure(state="normal", fg_color=COLOR_START_BTN)
        self.stop_btn.configure(state="disabled", fg_color=COLOR_STOP_BTN)

        # Keep error visible if one occurred; do not silently wipe it back to 'Ready'
        cur_text = ""
        try:
            cur_text = self.status_lbl.cget("text")
        except Exception:
            pass
        if not preserve_error and not ("Error" in cur_text or "Failed" in cur_text):
            self.set_status("● Ready", COLOR_ACCENT_GREEN)

        try:
            cv2.destroyWindow("DECART LIVE PRO - REALTIME OUTPUT")
        except Exception:
            pass

    def _run_async_worker(self, api_key: str):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        had_error = False

        try:
            self.loop.run_until_complete(self._async_stream_pipeline(api_key))
        except Exception as e:
            had_error = True
            log_app(f"[Worker Fatal Exception]: {e}")
            self.set_status(f"● Error: {e}", COLOR_STOP_TEXT)
        finally:
            self.loop.close()
            self.loop = None
            self.after(0, lambda: self._reset_ui_after_stop(preserve_error=had_error))

    async def _async_stream_pipeline(self, api_key: str):
        log_app("[Pipeline] Creating output window and starting WebRTC engine...")
        # Native widescreen 7:4 format without stretching or distortion
        cv2.namedWindow("DECART LIVE PRO - REALTIME OUTPUT", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("DECART LIVE PRO - REALTIME OUTPUT", 952, 544)

        is_phase_live = False

        def handle_edited_frame(rgb_frame: np.ndarray):
            nonlocal is_phase_live
            bgr = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)
            self.latest_edited_frame = cv2.resize(bgr, (952, 544), interpolation=cv2.INTER_LINEAR)
            if not getattr(self, "is_actively_transforming", False):
                self.is_actively_transforming = True
                log_app("[Pipeline] First AI frame received! Live streaming active.")
                self.set_status("● LIVE STREAMING (30 FPS)", COLOR_ACCENT_GREEN)

        def handle_local_frame(rgb_frame: np.ndarray):
            self.latest_local_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2BGR)

        def handle_state(state):
            nonlocal is_phase_live
            phase = state.phase.value.upper()
            log_app(f"[Pipeline State]: {phase} (error={state.last_error})")
            if state.phase == SessionPhase.LIVE:
                is_phase_live = True
                if self.latest_edited_frame is not None:
                    self.is_actively_transforming = True
                    self.set_status("● LIVE STREAMING (30 FPS)", COLOR_ACCENT_GREEN)
                else:
                    self.set_status("● AI Ready · Initializing frames...", COLOR_ACCENT_GREEN)
            elif state.phase in (SessionPhase.STARTING, SessionPhase.WARMING_UP, SessionPhase.IDLE):
                is_phase_live = False
                if not getattr(self, "is_actively_transforming", False):
                    self.set_status(f"● {phase}... (Warming up AI)", "#facc15")
            elif state.phase == SessionPhase.FAILED:
                is_phase_live = False
                self.is_actively_transforming = False
                err_msg = state.last_error or "Check input image or camera"
                log_app(f"[Pipeline Model Failed]: {err_msg}")
                self.set_status(f"● Model Failed: {err_msg}", COLOR_STOP_TEXT)

                # Render clear error card on output window for 4 seconds so user sees it
                try:
                    err_card = np.zeros((544, 952, 3), dtype=np.uint8)
                    err_card[:] = (18, 15, 24)
                    cv2.rectangle(err_card, (40, 180), (912, 360), (32, 28, 48), -1)
                    cv2.rectangle(err_card, (40, 180), (912, 360), (0, 0, 220), 2)
                    cv2.putText(err_card, "AI MODEL INITIALIZATION FAILED", (80, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2, cv2.LINE_AA)
                    cv2.putText(err_card, str(err_msg)[:75], (80, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
                    cv2.putText(err_card, "Window will close in 4 seconds...", (80, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 140), 1, cv2.LINE_AA)
                    cv2.imshow("DECART LIVE PRO - REALTIME OUTPUT", err_card)
                    cv2.waitKey(4000)
                except Exception:
                    pass

                self.stop_requested = True

        def handle_err(err):
            log_app(f"[Pipeline Command Error]: code={err.code} reason={err.reason}")
            self.set_status(f"● Error: {err.code}", COLOR_STOP_TEXT)

        ref_image = self.ref_image_path if (self.ref_image_path and os.path.exists(self.ref_image_path)) else None
        log_app(f"[Pipeline] Starting session with mode='{self.selected_mode}', ref_image='{ref_image}'")

        start_task = asyncio.create_task(
            self.engine.start_session(
                api_key=api_key,
                reference_image=ref_image,
                editing_type=self.selected_mode,
                zoom_factor=self.zoom_factor,
                on_frame_cb=handle_edited_frame,
                on_local_frame_cb=handle_local_frame,
                on_state_cb=handle_state,
                on_error_cb=handle_err,
            )
        )

        try:
            while not self.stop_requested:
                if start_task.done():
                    exc = start_task.exception()
                    if exc:
                        err_text = str(exc)
                        log_app(f"[Pipeline Task Exception]: {err_text}")
                        if "0 credits" in err_text or "depleted" in err_text:
                            err_display = "● Reactor Error: API Key credits depleted!"
                        elif "Peer connection" in err_text or "session limit" in err_text:
                            err_display = "● Reactor Error: Connection busy or session limit reached."
                        else:
                            err_display = f"● Error: {err_text[:40]}"
                        self.set_status(err_display, COLOR_STOP_TEXT)

                        try:
                            err_card = np.zeros((544, 952, 3), dtype=np.uint8)
                            err_card[:] = (18, 15, 24)
                            cv2.rectangle(err_card, (40, 180), (912, 360), (32, 28, 48), -1)
                            cv2.rectangle(err_card, (40, 180), (912, 360), (0, 0, 220), 2)
                            cv2.putText(err_card, "STREAM CONNECTION ERROR", (80, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (0, 0, 255), 2, cv2.LINE_AA)
                            cv2.putText(err_card, str(err_text)[:75], (80, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)
                            cv2.putText(err_card, "Window will close automatically...", (80, 320), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (140, 140, 140), 1, cv2.LINE_AA)
                            cv2.imshow("DECART LIVE PRO - REALTIME OUTPUT", err_card)
                            cv2.waitKey(4000)
                        except Exception:
                            pass

                        self.stop_requested = True
                        break

                display = None
                if self.latest_edited_frame is not None:
                    display = self.latest_edited_frame.copy()
                    if self.show_pip_var.get() and self.latest_local_frame is not None:
                        pip_h, pip_w = 108, 190
                        pip = cv2.resize(self.latest_local_frame, (pip_w, pip_h))
                        display[-pip_h - 15 : -15, -pip_w - 15 : -15] = pip
                elif self.latest_local_frame is not None:
                    display = cv2.resize(self.latest_local_frame, (952, 544))
                    cv2.rectangle(display, (0, 0), (952, 42), (8, 12, 20), -1)
                    cv2.putText(
                        display,
                        "WARMING UP AI TRANSFORMATION...",
                        (18, 28),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.62,
                        (0, 255, 163),
                        2,
                        cv2.LINE_AA,
                    )
                else:
                    placeholder = np.zeros((544, 952, 3), dtype=np.uint8)
                    cv2.putText(
                        placeholder,
                        "Connecting camera & AI model...",
                        (280, 280),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (100, 116, 139),
                        2,
                        cv2.LINE_AA,
                    )
                    display = placeholder

                cv2.imshow("DECART LIVE PRO - REALTIME OUTPUT", display)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    log_app("[Pipeline] User pressed 'q' to stop.")
                    self.stop_requested = True
                    break

                try:
                    prop = cv2.getWindowProperty("DECART LIVE PRO - REALTIME OUTPUT", cv2.WND_PROP_VISIBLE)
                    if prop < 1:
                        log_app("[Pipeline] Output window closed by user.")
                        self.stop_requested = True
                        break
                except cv2.error:
                    log_app("[Pipeline] Output window destroyed.")
                    self.stop_requested = True
                    break

                await asyncio.sleep(0.01)
        finally:
            cv2.destroyAllWindows()
            if not start_task.done():
                start_task.cancel()
                try:
                    await start_task
                except (asyncio.CancelledError, Exception):
                    pass
            else:
                try:
                    start_task.result()
                except Exception:
                    pass
            await self.engine.stop_session()
            log_app("[Pipeline] Session ended cleanly.")

    # ---------------- Webcam Diagnostics Dialog ----------------

    def _test_webcam_dialog(self):
        info = CameraAspectChecker.test_camera(camera_index=0)
        dialog = ctk.CTkToplevel(self)
        dialog.title("Webcam Diagnostic & Aspect Check")
        dialog.geometry("400x310")
        dialog.configure(fg_color=COLOR_BG)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="WEBCAM DIAGNOSTICS",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=COLOR_ACCENT_GREEN,
        ).pack(pady=(14, 8))

        card = ctk.CTkFrame(dialog, fg_color=COLOR_CARD, border_color=COLOR_CARD_BORDER, border_width=1)
        card.pack(fill="both", expand=True, padx=16, pady=4)

        if not info.get("available"):
            ctk.CTkLabel(card, text=f"Error: {info.get('error')}", text_color=COLOR_STOP_TEXT).pack(pady=20)
            return

        rows = [
            ("Camera Status:", "ONLINE", COLOR_ACCENT_GREEN),
            ("Native Resolution:", f"{info['width']} x {info['height']}", COLOR_TEXT_PRIMARY),
            ("Target Fit Size:", "952 x 544 (Widescreen)", COLOR_BADGE_BLUE_TEXT),
        ]

        for label, val, val_color in rows:
            r = ctk.CTkFrame(card, fg_color="transparent")
            r.pack(fill="x", padx=14, pady=5)
            ctk.CTkLabel(r, text=label, font=ctk.CTkFont(family="Segoe UI", size=11), text_color=COLOR_TEXT_MUTED).pack(side="left")
            ctk.CTkLabel(r, text=val, font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=val_color).pack(side="right")

        ctk.CTkButton(dialog, text="Close", fg_color=COLOR_BTN_SEC, height=34, command=dialog.destroy).pack(pady=10)


if __name__ == "__main__":
    app = DecartLiveProApp()
    app.mainloop()
