import os
import subprocess
from pathlib import Path
from urllib.parse import quote

from assistant.paths import data_dir, resource_path


class TextToSpeech:
    def __init__(self, rate: int = 180, voice_index: int | None = None):
        self._disabled_reason: str | None = None
        self._preferred_gender = self._get_preferred_gender()
        self._speaker = self._build_pyttsx3_speaker(rate, voice_index)
        if self._speaker is not None:
            return

        self._speaker = self._build_powershell_speaker(rate)
        if self._speaker is not None:
            return

        self._speaker = self._build_browser_speaker(rate)
        if self._speaker is None:
            if self._disabled_reason:
                print(f"Voice output disabled: {self._disabled_reason}")
            else:
                print("Voice output disabled: no working TTS backend was found.")

    def speak(self, text: str) -> None:
        print(f"Assistant: {text}")
        if self._speaker is None:
            return
        try:
            self._speaker(text)
        except Exception as exc:
            self._disabled_reason = self._summarize_error(str(exc))
            print(f"Voice output disabled: {self._disabled_reason}")
            self._speaker = None

    def _build_pyttsx3_speaker(self, rate: int, voice_index: int | None):
        try:
            import pyttsx3

            engine = pyttsx3.init()
            engine.setProperty("rate", rate)
            voices = engine.getProperty("voices")

            selected_voice = None
            if voice_index is not None and 0 <= voice_index < len(voices):
                selected_voice = voices[voice_index]
            else:
                selected_voice = self._pick_voice(voices, self._preferred_gender)

            if selected_voice is not None:
                engine.setProperty("voice", selected_voice.id)

            def speak_with_pyttsx3(text: str) -> None:
                engine.say(text)
                engine.runAndWait()

            return speak_with_pyttsx3
        except Exception as exc:
            self._disabled_reason = self._summarize_error(str(exc))
            return None

    def _build_powershell_speaker(self, rate: int):
        probe_script = """
try {
    Add-Type -AssemblyName System.Speech -ErrorAction Stop
    $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $voices = $s.GetInstalledVoices()
    if ($voices -and $voices.Count -gt 0) {
        $null = $s.SpeakAsyncCancelAll()
        exit 0
    }
} catch {}
try {
    $null = New-Object -ComObject SAPI.SpVoice
    $null.Rate = 0
    exit 0
} catch {}
exit 1
""".strip()
        try:
            probe = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", probe_script],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if probe.returncode != 0:
                self._disabled_reason = "Windows blocked text-to-speech access for this process."
                return None
        except Exception as exc:
            self._disabled_reason = self._summarize_error(str(exc))
            return None

        def speak_with_powershell(text: str) -> None:
            escaped_text = text.replace("'", "''")
            script = f"""
try {{
    Add-Type -AssemblyName System.Speech -ErrorAction Stop
    $s = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $s.Rate = {self._rate_to_sapi(rate)}
    $preferred = $s.GetInstalledVoices() | Where-Object {{
        $_.VoiceInfo.Name -match '{self._voice_match_pattern()}'
    }} | Select-Object -First 1
    if ($preferred) {{ $s.SelectVoice($preferred.VoiceInfo.Name) }}
    $s.Speak('{escaped_text}')
    exit 0
}} catch {{}}
$sapi = New-Object -ComObject SAPI.SpVoice
$sapi.Rate = {self._rate_to_sapi(rate)}
[void]$sapi.Speak('{escaped_text}')
""".strip()
            completed = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", script],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if completed.returncode != 0:
                stderr = completed.stderr.strip() or "PowerShell speech failed"
                raise RuntimeError(stderr)

        return speak_with_powershell

    def _build_browser_speaker(self, rate: int):
        browser_path = self._find_browser_executable()
        if browser_path is None:
            return None

        page_path = self._ensure_browser_tts_page()
        base_url = page_path.resolve().as_uri()

        def speak_with_browser(text: str) -> None:
            url = f"{base_url}#text={quote(text)}&rate={rate}&gender={quote(self._preferred_gender)}"
            subprocess.Popen(
                [browser_path, "--new-window", f"--app={url}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

        self._disabled_reason = None
        return speak_with_browser

    @staticmethod
    def _find_browser_executable() -> str | None:
        candidates = [
            Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return str(candidate)
        return None

    @staticmethod
    def _ensure_browser_tts_page() -> Path:
        bundled_page = resource_path("voice", "browser_tts.html")
        if bundled_page.exists():
            return bundled_page

        page_path = data_dir() / "browser_tts.html"
        if page_path.exists():
            return page_path

        page_path.write_text(
            """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Sikha Voice</title>
</head>
<body>
  <script>
    const params = new URLSearchParams(location.hash.slice(1));
    const text = params.get("text") || "";
    const rate = Number(params.get("rate") || "180");
    const gender = (params.get("gender") || "female").toLowerCase();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = Math.max(0.7, Math.min(1.4, rate / 180));
    utterance.lang = /[\u0900-\u097F]/.test(text) ? "hi-IN" : "en-US";
    const genderHints = {
      female: ["female", "zira", "hazel", "heera", "susan", "eva", "aria"],
      male: ["male", "david", "mark", "george", "guy", "ravi"]
    };
    const hints = genderHints[gender] || genderHints.female;
    const selectVoice = () => {
      const voices = speechSynthesis.getVoices();
      const match = voices.find((voice) => {
        const label = `${voice.name} ${voice.voiceURI}`.toLowerCase();
        return hints.some((hint) => label.includes(hint));
      });
      if (match) {
        utterance.voice = match;
      }
    };
    selectVoice();
    speechSynthesis.onvoiceschanged = selectVoice;
    utterance.onend = () => setTimeout(() => window.close(), 300);
    speechSynthesis.cancel();
    speechSynthesis.speak(utterance);
    setTimeout(() => window.close(), 12000);
  </script>
</body>
</html>
""",
            encoding="utf-8",
        )
        return page_path

    @staticmethod
    def _summarize_error(message: str) -> str:
        lowered = message.lower()
        if "access is denied" in lowered or "e_accessdenied" in lowered:
            return "Windows blocked text-to-speech access for this process."
        if "wrong version" in lowered:
            return "The installed speech COM bindings are mismatched."
        return message.splitlines()[0].strip()

    @staticmethod
    def _get_preferred_gender() -> str:
        preferred_gender = os.getenv("ASSISTANT_VOICE_GENDER", "female").strip().lower()
        if preferred_gender in {"male", "female"}:
            return preferred_gender
        return "female"

    @staticmethod
    def _pick_voice(voices, preferred_gender: str):
        markers = {
            "female": ("female", "zira", "hazel", "heera", "susan", "eva", "aria"),
            "male": ("male", "david", "mark", "george", "guy", "ravi"),
        }
        preferred_markers = markers.get(preferred_gender, markers["female"])
        for voice in voices:
            voice_text = f"{getattr(voice, 'name', '')} {getattr(voice, 'id', '')}".lower()
            if any(marker in voice_text for marker in preferred_markers):
                return voice
        return voices[0] if voices else None

    def _voice_match_pattern(self) -> str:
        patterns = {
            "female": "Zira|Hazel|Heera|Female|Susan|Eva|Aria",
            "male": "David|Mark|George|Male|Guy|Ravi",
        }
        return patterns.get(self._preferred_gender, patterns["female"])

    @staticmethod
    def _rate_to_sapi(rate: int) -> int:
        if rate <= 140:
            return -2
        if rate <= 170:
            return -1
        if rate <= 200:
            return 0
        if rate <= 230:
            return 1
        return 2
