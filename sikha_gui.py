from __future__ import annotations

import threading
import tkinter as tk
from tkinter import scrolledtext, ttk

from assistant.runtime import SikhaRuntime


class SikhaGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sikha Assistant")
        self.root.geometry("960x700")
        self.root.minsize(840, 620)

        self.assistant = SikhaRuntime(enable_voice_input=True, enable_voice_output=False)

        self.status_var = tk.StringVar()
        self.command_var = tk.StringVar()
        self.model_var = tk.StringVar()

        self._build_ui()
        self._refresh_status()
        self._append_assistant(self.assistant.greeting())

    def _build_ui(self) -> None:
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        self.root.configure(bg="#f5efe4")

        frame = ttk.Frame(self.root, padding=14)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 12))

        ttk.Label(
            header,
            text="Sikha",
            font=("Segoe UI Semibold", 22),
        ).pack(side="left")

        ttk.Label(
            header,
            textvariable=self.status_var,
            font=("Segoe UI", 10),
        ).pack(side="right")

        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True)

        command_tab = ttk.Frame(notebook, padding=12)
        model_tab = ttk.Frame(notebook, padding=12)
        notebook.add(command_tab, text="Assistant")
        notebook.add(model_tab, text="Model Chat")

        self.chat_log = scrolledtext.ScrolledText(
            command_tab,
            wrap="word",
            height=24,
            font=("Consolas", 11),
            bg="#fffdf8",
        )
        self.chat_log.pack(fill="both", expand=True)
        self.chat_log.configure(state="disabled")

        quick_row = ttk.Frame(command_tab)
        quick_row.pack(fill="x", pady=(10, 8))
        for label, command in (
            ("Open Chrome", "open chrome"),
            ("Open YouTube", "open youtube"),
            ("Show Tasks", "show tasks"),
            ("Take Screenshot", "take screenshot"),
        ):
            ttk.Button(
                quick_row,
                text=label,
                command=lambda value=command: self._submit_command(value),
            ).pack(side="left", padx=(0, 8))

        input_row = ttk.Frame(command_tab)
        input_row.pack(fill="x")
        entry = ttk.Entry(input_row, textvariable=self.command_var, font=("Segoe UI", 11))
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _event: self._submit_command())

        ttk.Button(input_row, text="Send", command=self._submit_command).pack(side="left", padx=8)
        ttk.Button(input_row, text="Speak", command=self._start_voice_capture).pack(side="left")

        ttk.Label(
            command_tab,
            text="Use typed commands or press Speak. Voice falls back to typed input if recognition fails.",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(8, 0))

        self.model_log = scrolledtext.ScrolledText(
            model_tab,
            wrap="word",
            height=24,
            font=("Consolas", 11),
            bg="#fbfbff",
        )
        self.model_log.pack(fill="both", expand=True)
        self.model_log.configure(state="disabled")

        model_controls = ttk.Frame(model_tab)
        model_controls.pack(fill="x", pady=(10, 0))
        model_entry = ttk.Entry(model_controls, textvariable=self.model_var, font=("Segoe UI", 11))
        model_entry.pack(side="left", fill="x", expand=True)
        model_entry.bind("<Return>", lambda _event: self._ask_model())

        ttk.Button(model_controls, text="Ask Model", command=self._ask_model).pack(side="left", padx=8)
        ttk.Button(model_controls, text="Refresh Status", command=self._refresh_status).pack(side="left")

        ttk.Label(
            model_tab,
            text="Set ASSISTANT_LLM_PROVIDER=ollama and OLLAMA_MODEL=phi3 to use local Phi-3 through Ollama.",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(8, 0))

    def _refresh_status(self) -> None:
        status = self.assistant.llm_status()
        provider = status.get("provider", "unknown")
        model = status.get("model", "")
        available = status.get("available", "false")
        message = status.get("message", "")
        self.status_var.set(f"LLM: {provider}/{model} | ready={available} | {message}")

    def _append_chat(self, prefix: str, message: str, *, model_log: bool = False) -> None:
        widget = self.model_log if model_log else self.chat_log
        widget.configure(state="normal")
        widget.insert("end", f"{prefix}: {message}\n\n")
        widget.see("end")
        widget.configure(state="disabled")

    def _append_user(self, message: str) -> None:
        self._append_chat("You", message)

    def _append_assistant(self, message: str) -> None:
        self._append_chat("Sikha", message)

    def _append_model(self, prefix: str, message: str) -> None:
        self._append_chat(prefix, message, model_log=True)

    def _submit_command(self, forced_text: str | None = None) -> None:
        text = forced_text or self.command_var.get().strip()
        if not text:
            return
        self.command_var.set("")
        self._append_user(text)
        self.root.after(10, lambda: self._run_command(text))

    def _run_command(self, text: str) -> None:
        result = self.assistant.process_text(text)
        self._append_assistant(result.response)

    def _start_voice_capture(self) -> None:
        thread = threading.Thread(target=self._capture_voice, daemon=True)
        thread.start()

    def _capture_voice(self) -> None:
        spoken = self.assistant.listen_for_voice()
        if not spoken:
            self.root.after(0, lambda: self._append_assistant("Voice was not recognized. Type a command and try again."))
            return
        self.root.after(0, lambda: self._append_user(spoken))
        self.root.after(10, lambda: self._run_command(spoken))

    def _ask_model(self) -> None:
        prompt = self.model_var.get().strip()
        if not prompt:
            return
        self.model_var.set("")
        self._append_model("You", prompt)

        thread = threading.Thread(target=self._run_model_prompt, args=(prompt,), daemon=True)
        thread.start()

    def _run_model_prompt(self, prompt: str) -> None:
        response = self.assistant.ask_model(prompt)
        self.root.after(0, lambda: self._append_model("Model", response))


def main() -> None:
    root = tk.Tk()
    app = SikhaGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
