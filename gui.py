"""
gui.py — Main application window built with customtkinter.

Layout (top to bottom):
  1. Timer display (Elapsed / Remaining)
  2. Record button (Start / Stop toggle) + Status label
  3. Scrollable editable text box
  4. Bottom bar: Copy · Clear · Undo · [Change API Key]
     API key/provider entry rows expand/collapse inline below the buttons.
"""

import customtkinter as ctk

from config_manager import load_config, save_config
from recorder import Recorder
from transcriber import transcribe

MAX_SECONDS = 12 * 60  # 12 minutes


class App(ctk.CTk):
    """Main application window."""

    def __init__(self) -> None:
        super().__init__()

        # ── Window setup ─────────────────────────────────────────────
        self.title("AI Transcriber")
        self.geometry("620x520")
        self.minsize(500, 400)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # ── State ────────────────────────────────────────────────────
        self._recorder = Recorder()
        self._elapsed = 0          # seconds elapsed while recording
        self._timer_id: str | None = None
        self._undo_stack: list[str] = []
        self._config = load_config()
        self._show_key = False
        self._api_key_expanded = False
        self._api_provider = self._config.get("api_provider", "OpenAI")

        # ── Build UI ─────────────────────────────────────────────────
        # Pack order: top sections first, bottom bar anchored to bottom,
        # then the text box fills the remaining middle space.
        self._build_timer_section()
        self._build_controls_section()
        self._build_bottom_bar()       # Anchored to bottom
        self._build_text_section()     # Fills remaining middle space

        # If no API key saved yet, auto-expand the key entry
        if not self._config.get("api_key"):
            self._expand_api_key()

    # ==================================================================
    # UI construction
    # ==================================================================

    def _build_timer_section(self) -> None:
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=16, pady=(12, 4))

        self._elapsed_label = ctk.CTkLabel(
            frame, text="Elapsed: 0:00", font=("", 15, "bold")
        )
        self._elapsed_label.pack(side="left", padx=20, pady=8)

        self._remaining_label = ctk.CTkLabel(
            frame, text="Remaining: 12:00", font=("", 15, "bold")
        )
        self._remaining_label.pack(side="right", padx=20, pady=8)

    def _build_controls_section(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="x", padx=16, pady=(8, 4))

        self._record_btn = ctk.CTkButton(
            frame,
            text="🎙  Start Recording",
            width=200,
            height=42,
            font=("", 15, "bold"),
            fg_color="#2ea44f",
            hover_color="#238636",
            command=self._toggle_recording,
        )
        self._record_btn.pack(side="left", padx=(0, 16))

        self._status_label = ctk.CTkLabel(
            frame, text="Status: Idle", font=("", 13)
        )
        self._status_label.pack(side="left")

    def _build_bottom_bar(self) -> None:
        """Bottom section: action buttons + collapsible API key/provider rows."""
        self._bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._bottom_frame.pack(side="bottom", fill="x", padx=16, pady=(4, 10))

        # ── Row 1: Action buttons ────────────────────────────────────
        btn_row = ctk.CTkFrame(self._bottom_frame, fg_color="transparent")
        btn_row.pack(fill="x", pady=(0, 0))

        self._copy_btn = ctk.CTkButton(
            btn_row, text="📋  Copy to Clipboard", width=160, command=self._copy
        )
        self._copy_btn.pack(side="left", padx=(0, 8))

        self._clear_btn = ctk.CTkButton(
            btn_row, text="🗑  Clear", width=100, command=self._clear
        )
        self._clear_btn.pack(side="left", padx=(0, 8))

        self._undo_btn = ctk.CTkButton(
            btn_row, text="↩  Undo Clear", width=120, command=self._undo
        )
        self._undo_btn.pack(side="left", padx=(0, 8))

        # "Change API Key" toggle button — pushed to the right
        self._api_key_toggle_btn = ctk.CTkButton(
            btn_row,
            text="🔑 Change API Key",
            width=140,
            fg_color="gray30",
            hover_color="gray40",
            command=self._toggle_api_key_section,
        )
        self._api_key_toggle_btn.pack(side="right")

        # ── Row 2: API provider selector (hidden by default) ──────────
        self._api_provider_row = ctk.CTkFrame(self._bottom_frame, fg_color="transparent")
        # NOT packed yet — starts collapsed

        ctk.CTkLabel(self._api_provider_row, text="Provider:", font=("", 12)).pack(
            side="left", padx=(0, 6)
        )

        self._provider_var = ctk.StringVar(value=self._api_provider)
        self._provider_dropdown = ctk.CTkOptionMenu(
            self._api_provider_row,
            values=["OpenAI", "OpenRouter"],
            variable=self._provider_var,
            width=140,
            font=("", 12),
            command=self._on_provider_changed,
        )
        self._provider_dropdown.pack(side="left", padx=(0, 6))

        # ── Row 3: API key entry (hidden by default) ─────────────────
        self._api_key_row = ctk.CTkFrame(self._bottom_frame, fg_color="transparent")
        # NOT packed yet — starts collapsed

        ctk.CTkLabel(self._api_key_row, text="API Key:", font=("", 12)).pack(
            side="left", padx=(0, 6)
        )

        self._api_key_entry = ctk.CTkEntry(
            self._api_key_row, width=280, show="•", font=("", 12)
        )
        self._api_key_entry.pack(side="left", padx=(0, 6))

        # Pre-populate from config
        if self._config.get("api_key"):
            self._api_key_entry.insert(0, self._config["api_key"])

        self._toggle_key_btn = ctk.CTkButton(
            self._api_key_row, text="Show", width=50, font=("", 11),
            command=self._toggle_key_visibility
        )
        self._toggle_key_btn.pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            self._api_key_row, text="Save", width=60, font=("", 11),
            command=self._save_api_key
        ).pack(side="left")

    def _build_text_section(self) -> None:
        """Packed AFTER the bottom bar so it fills remaining middle space."""
        self._textbox = ctk.CTkTextbox(
            self, wrap="word", font=("", 14), height=260
        )
        self._textbox.pack(fill="both", expand=True, padx=16, pady=(8, 4))

    # ==================================================================
    # API key helpers
    # ==================================================================

    def _toggle_api_key_section(self) -> None:
        """Expand or collapse the API key entry row."""
        if self._api_key_expanded:
            self._collapse_api_key()
        else:
            self._expand_api_key()

    def _expand_api_key(self) -> None:
        self._api_provider_row.pack(fill="x", pady=(6, 0))
        self._api_key_row.pack(fill="x", pady=(6, 0))
        self._api_key_expanded = True
        self._api_key_toggle_btn.configure(text="🔑 Hide API Key")

    def _collapse_api_key(self) -> None:
        self._api_provider_row.pack_forget()
        self._api_key_row.pack_forget()
        self._api_key_expanded = False
        self._api_key_toggle_btn.configure(text="🔑 Change API Key")

    def _on_provider_changed(self, choice: str) -> None:
        """Called when the user picks a different provider from the dropdown."""
        self._api_provider = choice

    def _toggle_key_visibility(self) -> None:
        self._show_key = not self._show_key
        if self._show_key:
            self._api_key_entry.configure(show="")
            self._toggle_key_btn.configure(text="Hide")
        else:
            self._api_key_entry.configure(show="•")
            self._toggle_key_btn.configure(text="Show")

    def _save_api_key(self) -> None:
        key = self._api_key_entry.get().strip()
        self._config["api_key"] = key
        self._config["api_provider"] = self._api_provider
        save_config(self._config)
        self._set_status(f"API key saved ✓ (Provider: {self._api_provider})")
        # Collapse the API key section after saving
        self._collapse_api_key()

    def _get_api_key(self) -> str:
        return self._api_key_entry.get().strip()

    # ==================================================================
    # Recording
    # ==================================================================

    def _toggle_recording(self) -> None:
        if self._recorder.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        api_key = self._get_api_key()
        if not api_key:
            self._set_status(f"⚠ Enter your {self._api_provider} API key first!")
            self._expand_api_key()
            return

        self._recorder.start()
        self._elapsed = 0
        self._update_timer_display()
        self._tick()

        self._record_btn.configure(
            text="⏹  Stop Recording",
            fg_color="#d73a49",
            hover_color="#b31d28",
        )
        self._set_status("🔴 Recording…")

    def _stop_recording(self) -> None:
        # Cancel the timer
        if self._timer_id is not None:
            self.after_cancel(self._timer_id)
            self._timer_id = None

        self._set_status("Saving audio…")
        wav_path = self._recorder.stop()

        self._record_btn.configure(
            text="🎙  Start Recording",
            fg_color="#2ea44f",
            hover_color="#238636",
        )

        if wav_path is None:
            self._set_status("⚠ No audio captured.")
            return

        self._set_status("Transcribing…")
        transcribe(
            file_path=wav_path,
            api_key=self._get_api_key(),
            on_success=self._on_transcription_success,
            on_error=self._on_transcription_error,
            api_provider=self._api_provider,
        )

    # ==================================================================
    # Timer
    # ==================================================================

    def _tick(self) -> None:
        """Called every second while recording."""
        if not self._recorder.is_recording:
            return

        self._elapsed += 1
        self._update_timer_display()

        if self._elapsed >= MAX_SECONDS:
            self._set_status("⏱ Time limit reached — stopping…")
            self._stop_recording()
            return

        self._timer_id = self.after(1000, self._tick)

    def _update_timer_display(self) -> None:
        remaining = max(0, MAX_SECONDS - self._elapsed)

        e_min, e_sec = divmod(self._elapsed, 60)
        r_min, r_sec = divmod(remaining, 60)

        self._elapsed_label.configure(text=f"Elapsed: {e_min}:{e_sec:02d}")
        self._remaining_label.configure(text=f"Remaining: {r_min}:{r_sec:02d}")

    # ==================================================================
    # Transcription callbacks  (called from background thread)
    # ==================================================================

    def _on_transcription_success(self, text: str) -> None:
        # Schedule UI update on the main thread
        self.after(0, self._append_text, text)
        self.after(0, self._set_status, "✅ Transcription complete")

    def _on_transcription_error(self, error_msg: str) -> None:
        self.after(0, self._set_status, f"❌ {error_msg}")

    # ==================================================================
    # Text box actions
    # ==================================================================

    def _append_text(self, text: str) -> None:
        """Append transcribed text to the text box."""
        current = self._textbox.get("1.0", "end").strip()
        if current:
            self._textbox.insert("end", "\n\n" + text)
        else:
            self._textbox.insert("end", text)
        # Scroll to the bottom
        self._textbox.see("end")

    def _copy(self) -> None:
        """Copy all text to the system clipboard."""
        text = self._textbox.get("1.0", "end").strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            self._set_status("📋 Copied to clipboard!")
        else:
            self._set_status("Nothing to copy.")

    def _clear(self) -> None:
        """Clear the text box, pushing current content to the undo stack."""
        text = self._textbox.get("1.0", "end").strip()
        if text:
            self._undo_stack.append(text)
        self._textbox.delete("1.0", "end")
        self._set_status("Text cleared.")

    def _undo(self) -> None:
        """Restore the last cleared text from the undo stack."""
        if not self._undo_stack:
            self._set_status("Nothing to undo.")
            return
        restored = self._undo_stack.pop()
        self._textbox.delete("1.0", "end")
        self._textbox.insert("1.0", restored)
        self._set_status("↩ Undo successful.")

    # ==================================================================
    # Helpers
    # ==================================================================

    def _set_status(self, msg: str) -> None:
        self._status_label.configure(text=f"Status: {msg}")
