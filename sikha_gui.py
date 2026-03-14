from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from assistant.runtime import SikhaRuntime


BG = "#0f172a"
PANEL = "#1e293b"
PANEL_ALT = "#172033"
ACCENT = "#38bdf8"
TEXT = "#e2e8f0"
TEXT_MUTED = "#94a3b8"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
USER_BUBBLE = "#0f2740"
ASSISTANT_BUBBLE = "#132238"
FONT_UI = ("Segoe UI", 10)
FONT_TITLE = ("Segoe UI Semibold", 20)
FONT_BODY = ("Segoe UI", 11)
FONT_MONO = ("Consolas", 10)


class SikhaGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sikha Desktop")
        self.root.geometry("1360x860")
        self.root.minsize(1120, 700)
        self.root.configure(bg=BG)

        self.assistant = SikhaRuntime(enable_voice_input=True, enable_voice_output=True)
        self.command_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Assistant ready")
        self.model_var = tk.StringVar(value="Checking model...")
        self.history_empty_var = tk.StringVar(value="No history yet.")
        self.active_sidebar = tk.StringVar(value="History")

        self.selected_file: Path | None = None
        self.listening = False
        self._listening_job: str | None = None
        self._wave_phase = 0

        self._build_ui()
        self._refresh_status()
        self._refresh_history()
        greeting = self.assistant.greeting()
        self._append_message("assistant", greeting)
        self._speak_async(greeting)

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        self._build_top_bar()
        self._build_sidebar()
        self._build_main_workspace()
        self._build_utility_panel()
        self._build_command_bar()

    def _build_top_bar(self) -> None:
        frame = tk.Frame(self.root, bg=BG, height=68)
        frame.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=18, pady=(16, 10))
        frame.grid_columnconfigure(1, weight=1)

        title = tk.Label(frame, text="Sikha", font=FONT_TITLE, bg=BG, fg=TEXT)
        title.grid(row=0, column=0, sticky="w")

        center = tk.Frame(frame, bg=BG)
        center.grid(row=0, column=1)

        self._status_chip(center, "AI", SUCCESS, self.status_var).pack(side="left", padx=6)
        self._status_chip(center, "Mode", ACCENT, tk.StringVar(value="Online")).pack(side="left", padx=6)
        self._status_chip(center, "Model", ACCENT, self.model_var).pack(side="left", padx=6)

        self.mic_button = tk.Button(
            frame,
            text="Mic",
            command=self._toggle_voice_capture,
            bg=ACCENT,
            fg=BG,
            activebackground="#7dd3fc",
            activeforeground=BG,
            relief="flat",
            padx=18,
            pady=10,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        )
        self.mic_button.grid(row=0, column=2, sticky="e")

    def _build_sidebar(self) -> None:
        frame = tk.Frame(self.root, bg=PANEL, width=260, highlightthickness=1, highlightbackground="#243247")
        frame.grid(row=1, column=0, rowspan=2, sticky="nsew", padx=(18, 10), pady=(0, 18))
        frame.grid_propagate(False)

        tk.Label(frame, text="Workspace", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 12)).pack(
            anchor="w", padx=16, pady=(16, 10)
        )

        for section in ("History", "Files", "Memory", "Tools", "Settings"):
            self._sidebar_button(frame, section).pack(fill="x", padx=12, pady=4)

        tk.Label(frame, text="Recent commands", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(
            anchor="w", padx=16, pady=(18, 8)
        )

        self.history_list = tk.Listbox(
            frame,
            bg=PANEL_ALT,
            fg=TEXT,
            selectbackground="#1d4f6b",
            selectforeground=TEXT,
            borderwidth=0,
            highlightthickness=0,
            activestyle="none",
            font=("Segoe UI", 10),
        )
        self.history_list.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.history_list.bind("<<ListboxSelect>>", self._reuse_history_item)

    def _build_main_workspace(self) -> None:
        workspace = tk.Frame(self.root, bg=BG)
        workspace.grid(row=1, column=1, sticky="nsew", pady=(0, 10))
        workspace.grid_rowconfigure(1, weight=1)
        workspace.grid_columnconfigure(0, weight=1)

        hero = tk.Frame(workspace, bg=PANEL, highlightthickness=1, highlightbackground="#243247")
        hero.grid(row=0, column=0, sticky="ew")
        hero.grid_columnconfigure(0, weight=1)

        tk.Label(
            hero,
            text="A lightweight Jarvis-style copilot for voice, tasks, and normal AI chat.",
            bg=PANEL,
            fg=TEXT,
            font=("Segoe UI", 13),
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="w", padx=18, pady=(16, 6))

        tk.Label(
            hero,
            text="Use normal commands, slash commands like /model or /clear, or attach a file for quick summaries.",
            bg=PANEL,
            fg=TEXT_MUTED,
            font=FONT_UI,
            anchor="w",
        ).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))

        self.voice_banner = tk.Frame(hero, bg="#0f2740", highlightthickness=1, highlightbackground="#1f5371")
        self.voice_banner.grid(row=0, column=1, rowspan=2, sticky="e", padx=16)
        self.voice_banner.grid_remove()

        self.voice_label = tk.Label(
            self.voice_banner,
            text="Listening...",
            bg="#0f2740",
            fg=ACCENT,
            font=("Segoe UI Semibold", 11),
        )
        self.voice_label.pack(anchor="w", padx=14, pady=(10, 2))

        self.wave_canvas = tk.Canvas(
            self.voice_banner,
            width=180,
            height=44,
            bg="#0f2740",
            highlightthickness=0,
        )
        self.wave_canvas.pack(padx=12, pady=(0, 10))

        conversation = tk.Frame(workspace, bg=BG)
        conversation.grid(row=1, column=0, sticky="nsew", pady=(14, 0))
        conversation.grid_rowconfigure(1, weight=1)
        conversation.grid_columnconfigure(0, weight=1)

        chips = tk.Frame(conversation, bg=BG)
        chips.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for label, prompt in (
            ("Ask AI", "What can you help me with today?"),
            ("Open YouTube", "open youtube"),
            ("Summarize File", "summarize the attached file"),
            ("Generate Code", "/model Write a Python function to read a CSV file."),
        ):
            tk.Button(
                chips,
                text=label,
                command=lambda value=prompt: self._submit_command(value),
                bg=PANEL,
                fg=TEXT,
                activebackground="#25364f",
                activeforeground=TEXT,
                relief="flat",
                padx=12,
                pady=8,
                font=("Segoe UI", 9),
                cursor="hand2",
            ).pack(side="left", padx=(0, 8))

        chat_shell = tk.Frame(conversation, bg=PANEL, highlightthickness=1, highlightbackground="#243247")
        chat_shell.grid(row=1, column=0, sticky="nsew")
        chat_shell.grid_rowconfigure(0, weight=1)
        chat_shell.grid_columnconfigure(0, weight=1)

        self.chat_canvas = tk.Canvas(chat_shell, bg=PANEL, highlightthickness=0)
        self.chat_canvas.grid(row=0, column=0, sticky="nsew")

        scrollbar = tk.Scrollbar(chat_shell, orient="vertical", command=self.chat_canvas.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_frame = tk.Frame(self.chat_canvas, bg=PANEL)
        self.chat_window = self.chat_canvas.create_window((0, 0), window=self.chat_frame, anchor="nw")
        self.chat_frame.bind("<Configure>", self._on_chat_frame_configure)
        self.chat_canvas.bind("<Configure>", self._on_chat_canvas_configure)

    def _build_utility_panel(self) -> None:
        frame = tk.Frame(self.root, bg=PANEL, width=280, highlightthickness=1, highlightbackground="#243247")
        frame.grid(row=1, column=2, rowspan=2, sticky="nsew", padx=(10, 18), pady=(0, 18))
        frame.grid_propagate(False)

        tk.Label(frame, text="Quick Tools", bg=PANEL, fg=TEXT, font=("Segoe UI Semibold", 12)).pack(
            anchor="w", padx=16, pady=(16, 12)
        )

        self._tool_card(
            frame,
            "Code Generator",
            "Use /model followed by your coding prompt.",
            lambda: self._submit_command("/model Write a Python script to rename files in a folder."),
        ).pack(fill="x", padx=12, pady=6)

        self._tool_card(
            frame,
            "File Summarizer",
            "Attach a text file and ask for a summary.",
            self._attach_file,
        ).pack(fill="x", padx=12, pady=6)

        self._tool_card(
            frame,
            "Task Automation",
            "Run system and browser commands through the assistant.",
            lambda: self._submit_command("open chrome"),
        ).pack(fill="x", padx=12, pady=6)

        self._tool_card(
            frame,
            "AI Suggestions",
            "Get prompt ideas for work, code, or daily commands.",
            lambda: self._submit_command("/help"),
        ).pack(fill="x", padx=12, pady=6)

        tk.Label(frame, text="Selected file", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(
            anchor="w", padx=16, pady=(18, 6)
        )
        self.file_label = tk.Label(
            frame,
            text="No file attached",
            bg=PANEL_ALT,
            fg=TEXT,
            anchor="w",
            justify="left",
            wraplength=220,
            padx=12,
            pady=12,
        )
        self.file_label.pack(fill="x", padx=12)

    def _build_command_bar(self) -> None:
        frame = tk.Frame(self.root, bg=PANEL, highlightthickness=1, highlightbackground="#243247")
        frame.grid(row=2, column=1, sticky="ew", pady=(0, 18))
        frame.grid_columnconfigure(1, weight=1)

        tk.Button(
            frame,
            text="Attach",
            command=self._attach_file,
            bg=PANEL_ALT,
            fg=TEXT,
            activebackground="#25364f",
            activeforeground=TEXT,
            relief="flat",
            padx=16,
            pady=12,
            cursor="hand2",
        ).grid(row=0, column=0, padx=12, pady=12)

        entry = tk.Entry(
            frame,
            textvariable=self.command_var,
            bg="#0b1220",
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            font=FONT_BODY,
        )
        entry.grid(row=0, column=1, sticky="ew", padx=(0, 10), pady=12, ipady=12)
        entry.bind("<Return>", lambda _event: self._submit_command())
        entry.focus_set()

        tk.Button(
            frame,
            text="Voice",
            command=self._toggle_voice_capture,
            bg=PANEL_ALT,
            fg=TEXT,
            activebackground="#25364f",
            activeforeground=TEXT,
            relief="flat",
            padx=16,
            pady=12,
            cursor="hand2",
        ).grid(row=0, column=2, padx=(0, 10), pady=12)

        tk.Button(
            frame,
            text="Send",
            command=self._submit_command,
            bg=ACCENT,
            fg=BG,
            activebackground="#7dd3fc",
            activeforeground=BG,
            relief="flat",
            padx=18,
            pady=12,
            font=("Segoe UI Semibold", 10),
            cursor="hand2",
        ).grid(row=0, column=3, padx=(0, 12), pady=12)

    def _status_chip(self, parent: tk.Widget, label: str, dot_color: str, variable: tk.StringVar) -> tk.Frame:
        chip = tk.Frame(parent, bg=PANEL, padx=10, pady=8)
        dot = tk.Canvas(chip, width=10, height=10, bg=PANEL, highlightthickness=0)
        dot.create_oval(2, 2, 8, 8, fill=dot_color, outline=dot_color)
        dot.pack(side="left", padx=(0, 8))
        tk.Label(chip, text=f"{label}:", bg=PANEL, fg=TEXT_MUTED, font=("Segoe UI", 9)).pack(side="left")
        tk.Label(chip, textvariable=variable, bg=PANEL, fg=TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(4, 0))
        return chip

    def _sidebar_button(self, parent: tk.Widget, title: str) -> tk.Button:
        return tk.Button(
            parent,
            text=title,
            command=lambda value=title: self._select_sidebar(value),
            bg=PANEL_ALT,
            fg=TEXT,
            activebackground="#25364f",
            activeforeground=TEXT,
            relief="flat",
            anchor="w",
            padx=14,
            pady=10,
            font=("Segoe UI", 10),
            cursor="hand2",
        )

    def _tool_card(self, parent: tk.Widget, title: str, description: str, command) -> tk.Frame:
        card = tk.Frame(parent, bg=PANEL_ALT, padx=12, pady=12)
        tk.Label(card, text=title, bg=PANEL_ALT, fg=TEXT, font=("Segoe UI Semibold", 10)).pack(anchor="w")
        tk.Label(
            card,
            text=description,
            bg=PANEL_ALT,
            fg=TEXT_MUTED,
            font=("Segoe UI", 9),
            wraplength=220,
            justify="left",
        ).pack(anchor="w", pady=(6, 10))
        tk.Button(
            card,
            text="Open",
            command=command,
            bg=ACCENT,
            fg=BG,
            activebackground="#7dd3fc",
            activeforeground=BG,
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
        ).pack(anchor="w")
        return card

    def _append_message(self, role: str, message: str) -> None:
        outer = tk.Frame(self.chat_frame, bg=PANEL)
        outer.pack(fill="x", padx=16, pady=8, anchor="e" if role == "user" else "w")

        bubble = tk.Frame(
            outer,
            bg=USER_BUBBLE if role == "user" else ASSISTANT_BUBBLE,
            padx=14,
            pady=12,
        )
        bubble.pack(anchor="e" if role == "user" else "w")

        label = tk.Label(
            bubble,
            text=("You\n" if role == "user" else "Sikha\n") + message,
            bg=bubble["bg"],
            fg=TEXT,
            justify="left",
            wraplength=680,
            font=FONT_BODY if "```" not in message else FONT_MONO,
        )
        label.pack(anchor="w")
        self.root.after(20, lambda: self.chat_canvas.yview_moveto(1.0))

    def _submit_command(self, forced_text: str | None = None) -> None:
        text = forced_text or self.command_var.get().strip()
        if not text:
            return
        self.command_var.set("")
        self._append_message("user", text)

        if text.startswith("/"):
            self.root.after(10, lambda: self._run_slash_command(text))
            return

        self.root.after(10, lambda: self._run_command(text))

    def _run_slash_command(self, command: str) -> None:
        parts = command.split(maxsplit=1)
        name = parts[0].lower()
        payload = parts[1] if len(parts) > 1 else ""

        if name == "/clear":
            for child in self.chat_frame.winfo_children():
                child.destroy()
            response = "Conversation cleared."
            self._append_message("assistant", response)
            self._speak_async(response)
            return
        if name == "/help":
            response = (
                "Slash commands:\n/model <prompt>\n/clear\n/help\n\n"
                "Attach a file, then ask for a summary or use /model for free-form AI chat."
            )
            self._append_message("assistant", response)
            self._speak_async("You can use model, clear, and help commands.")
            return
        if name == "/model":
            if not payload:
                response = "Use /model followed by your prompt."
                self._append_message("assistant", response)
                self._speak_async(response)
                return
            thread = threading.Thread(target=self._run_model_prompt, args=(payload,), daemon=True)
            thread.start()
            return

        response = f"Unknown slash command: {name}"
        self._append_message("assistant", response)
        self._speak_async(response)

    def _run_command(self, text: str) -> None:
        if self.selected_file and any(word in text.lower() for word in ("summarize", "analyse", "analyze", "review")):
            thread = threading.Thread(target=self._summarize_selected_file, args=(text,), daemon=True)
            thread.start()
            return

        result = self.assistant.process_text(text)
        self._append_message("assistant", result.response)
        self._speak_async(result.response)
        self._refresh_history()

    def _run_model_prompt(self, prompt: str) -> None:
        response = self.assistant.ask_model(prompt)
        self.root.after(0, lambda: self._append_message("assistant", response))
        self.root.after(0, lambda: self._speak_async(response))
        self.root.after(0, self._refresh_status)

    def _summarize_selected_file(self, instruction: str) -> None:
        assert self.selected_file is not None
        try:
            content = self.selected_file.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self.root.after(0, lambda: self._append_message("assistant", f"Could not read file: {exc}"))
            self.root.after(0, lambda: self._speak_async("I could not read the selected file."))
            return

        prompt = (
            f"{instruction}\n\n"
            f"Filename: {self.selected_file.name}\n\n"
            "Content:\n"
            f"{content[:7000]}"
        )
        response = self.assistant.ask_model(
            prompt,
            system_prompt="You are Sikha. Summarize files clearly, extract useful points, and keep the answer practical.",
        )
        self.root.after(0, lambda: self._append_message("assistant", response))
        self.root.after(0, lambda: self._speak_async(response))

    def _attach_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Attach a file",
            filetypes=[
                ("Text and code files", "*.txt *.md *.py *.json *.csv *.log"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        self.selected_file = Path(path)
        self.file_label.configure(text=self.selected_file.name)
        response = f"Attached file: {self.selected_file.name}. Ask me to summarize or analyze it."
        self._append_message("assistant", response)
        self._speak_async(f"Attached file {self.selected_file.name}.")

    def _toggle_voice_capture(self) -> None:
        if self.listening:
            return
        self.listening = True
        self.mic_button.configure(text="Listening", bg=WARNING)
        self.voice_banner.grid()
        self._animate_wave()
        thread = threading.Thread(target=self._capture_voice, daemon=True)
        thread.start()

    def _capture_voice(self) -> None:
        spoken = self.assistant.listen_for_voice()
        self.root.after(0, lambda: self._finish_voice_capture(spoken))

    def _finish_voice_capture(self, spoken: str | None) -> None:
        self.listening = False
        self.mic_button.configure(text="Mic", bg=ACCENT)
        self.voice_banner.grid_remove()
        if self._listening_job is not None:
            self.root.after_cancel(self._listening_job)
            self._listening_job = None

        if not spoken:
            response = "Voice was not recognized. Type a command and try again."
            self._append_message("assistant", response)
            self._speak_async(response)
            return

        self.command_var.set(spoken)
        self._append_message("user", spoken)
        self.root.after(10, lambda: self._run_command(spoken))

    def _animate_wave(self) -> None:
        if not self.listening:
            self.wave_canvas.delete("all")
            return

        self.wave_canvas.delete("all")
        base_y = 22
        for index in range(10):
            phase = (self._wave_phase + index) % 6
            height = 8 + (phase * 4)
            x = 12 + index * 16
            self.wave_canvas.create_line(x, base_y - height, x, base_y + height, fill=ACCENT, width=4, capstyle="round")

        self._wave_phase = (self._wave_phase + 1) % 6
        self._listening_job = self.root.after(120, self._animate_wave)

    def _refresh_status(self) -> None:
        status = self.assistant.llm_status()
        provider = status.get("provider", "unknown")
        model = status.get("model", "none")
        available = status.get("available", "false")

        self.status_var.set("Ready" if available == "true" else "Limited")
        self.model_var.set(f"{provider}/{model}")

    def _refresh_history(self) -> None:
        self.history_list.delete(0, "end")
        try:
            rows = self.assistant.memory.list_command_history(limit=20)
        except Exception:
            rows = []

        if not rows:
            self.history_list.insert("end", self.history_empty_var.get())
            return

        for text, intent, _created_at in rows:
            label = f"{intent}: {text[:42]}"
            self.history_list.insert("end", label)

    def _reuse_history_item(self, _event) -> None:
        selection = self.history_list.curselection()
        if not selection:
            return
        value = self.history_list.get(selection[0])
        if value == self.history_empty_var.get():
            return
        prompt = value.split(": ", 1)[-1]
        self.command_var.set(prompt)

    def _select_sidebar(self, name: str) -> None:
        self.active_sidebar.set(name)
        helper_messages = {
            "History": "Pick an earlier command from the left list to reuse it.",
            "Files": "Attach a text or code file, then ask me to summarize or analyze it.",
            "Memory": "I keep lightweight command history and notes without changing the assistant core.",
            "Tools": "Use quick tools on the right for code generation, file review, and task automation.",
            "Settings": "Model provider and runtime behavior still come from your existing environment variables.",
        }
        response = helper_messages.get(name, f"{name} opened.")
        self._append_message("assistant", response)
        self._speak_async(response)

    def _speak_async(self, message: str) -> None:
        if not message.strip():
            return
        threading.Thread(target=self.assistant.speak, args=(message,), daemon=True).start()

    def _on_chat_frame_configure(self, _event) -> None:
        self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all"))

    def _on_chat_canvas_configure(self, event) -> None:
        self.chat_canvas.itemconfigure(self.chat_window, width=event.width)


def main() -> None:
    root = tk.Tk()
    SikhaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
