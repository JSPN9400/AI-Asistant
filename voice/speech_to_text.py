import audioop
import json
import os
import queue
import threading
import time
from pathlib import Path

import pyaudio
from vosk import KaldiRecognizer, Model, SetLogLevel

from assistant.paths import app_root, resource_path


class SpeechToText:
    """
    Offline speech-to-text using Vosk.
    To support Hindi + English, download a suitable Vosk model, e.g.
    - https://alphacephei.com/vosk/models
    and place it under `models/vosk-hindi-en/`.
    """

    def __init__(
        self,
        model_path: Path | None = None,
        sample_rate: int = 16000,
        energy_threshold: int = 350,
        require_wake_word: bool | None = None,
    ):
        SetLogLevel(-1)
        model_dir = model_path or self._resolve_model_path()
        if not model_dir.exists():
            raise RuntimeError(
                f"Vosk model not found at {model_dir}. "
                "Download a Vosk Hindi/English model and extract it there."
            )

        self.model = Model(str(model_dir))
        self.sample_rate = sample_rate
        self.recognizer = KaldiRecognizer(self.model, sample_rate)
        self.recognizer.SetWords(True)
        self.energy_threshold = int(os.getenv("ASSISTANT_ENERGY_THRESHOLD", energy_threshold))
        self.debug = os.getenv("ASSISTANT_STT_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}
        default_require_wake_word = os.getenv("ASSISTANT_REQUIRE_WAKE_WORD", "0").strip().lower()
        self.require_wake_word = (
            require_wake_word
            if require_wake_word is not None
            else default_require_wake_word in {"1", "true", "yes", "on"}
        )
        self.wake_words = ("sikha", "shikha", "sikhaa")
        self._last_debug_rms = 0.0

        self.audio = pyaudio.PyAudio()
        self._queue: queue.Queue[bytes] = queue.Queue()
        self._stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=4000,
            stream_callback=self._callback,
        )
        self._debug(
            f"SpeechToText ready: model='{model_dir.name}', sample_rate={self.sample_rate}, "
            f"energy_threshold={self.energy_threshold}, wake_word_required={self.require_wake_word}"
        )

    @staticmethod
    def _resolve_model_path() -> Path:
        preferred_model = os.getenv("ASSISTANT_STT_MODEL", "").strip()
        models_root = resource_path("models")
        search_roots = [models_root, app_root() / "models"]

        if preferred_model:
            candidates = [root / preferred_model for root in search_roots]
        else:
            candidates = [
                root / "vosk-hindi-en" for root in search_roots
            ] + [
                root / "vosk-model-small-en-us-0.15" for root in search_roots
            ] + [
                root / "vosk-model-small-hi-0.22" for root in search_roots
            ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

        return candidates[0]

    def _callback(self, in_data, frame_count, time_info, status):
        self._queue.put(in_data)
        return (None, pyaudio.paContinue)

    def listen(self, timeout: float = 5, phrase_time_limit: float = 20) -> str | None:
        mode = "wake word required" if self.require_wake_word else "direct command"
        print(f"Listening (offline Vosk, {mode})...")
        self._debug(f"listen() started: timeout={timeout}, phrase_time_limit={phrase_time_limit}")

        result_text: list[str] = []
        done = threading.Event()
        start_time = time.monotonic()
        voice_started = threading.Event()

        def worker():
            nonlocal result_text
            while not done.is_set():
                if not voice_started.is_set() and (time.monotonic() - start_time) > timeout:
                    break
                try:
                    data = self._queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if not self._is_foreground_audio(data):
                    continue
                voice_started.set()
                if self.recognizer.AcceptWaveform(data):
                    res = json.loads(self.recognizer.Result())
                    text = res.get("text", "")
                    if text:
                        result_text.append(text)
                        break

        t = threading.Thread(target=worker, daemon=True)
        t.start()
        t.join(timeout=phrase_time_limit)
        done.set()

        if not result_text:
            final_res = json.loads(self.recognizer.FinalResult())
            final_text = final_res.get("text", "").strip()
            if final_text:
                result_text.append(final_text)

        if not result_text:
            self._debug("listen() ended without recognized speech")
            print("Could not understand focused speech.")
            return None

        text = " ".join(result_text)
        self._debug(f"recognized raw text: {text}")
        if self.require_wake_word and not self._has_wake_word(text):
            self._debug("wake word missing in recognized text")
            print("Wake word not detected, ignoring background speech.")
            return None

        text = self._strip_wake_word(text)
        if not text:
            self._debug("wake word detected but command content was empty")
            print("Wake word detected, waiting for a command.")
            return None

        print(f"You said: {text}")
        return text

    def _is_foreground_audio(self, data: bytes) -> bool:
        try:
            rms = audioop.rms(data, 2)
            if self.debug and rms != self._last_debug_rms:
                self._last_debug_rms = rms
                print(f"[STT debug] audio rms={rms} threshold={self.energy_threshold}")
            return rms >= self.energy_threshold
        except Exception:
            return True

    def _has_wake_word(self, text: str) -> bool:
        lowered = text.lower()
        return any(word in lowered.split() for word in self.wake_words)

    def _strip_wake_word(self, text: str) -> str:
        words = [word for word in text.split() if word.lower() not in self.wake_words]
        return " ".join(words).strip()

    def _debug(self, message: str) -> None:
        if self.debug:
            print(f"[STT debug] {message}")

