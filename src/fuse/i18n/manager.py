import json
import locale
from pathlib import Path
from typing import Any

from fuse.config.manager import config

# Compatibility map for command metadata that predates the locale-key system.
# It keeps old plugins usable while their help text is migrated to JSON keys.
_LEGACY_KEYS = {
    "Input file": "commands.args.input",
    "Input audio file": "commands.args.audio_input",
    "Input video file": "commands.args.video_input",
    "Media file to inspect": "commands.args.inspect_input",
    "Output file": "commands.args.output",
    "Output file path": "commands.args.output_path",
    "Output file with desired extension": "commands.args.output_extension",
    "Output audio file": "commands.args.audio_output",
    "Output image file": "commands.args.image_output",
    "Output video file": "commands.args.video_output",
    "Title tag": "commands.args.title",
    "Artist tag": "commands.args.artist",
    "Album tag": "commands.args.album",
    "Year tag": "commands.args.year",
    "Quality: balanced, high, max (default: balanced)": "commands.args.quality",
    "Target size": "commands.args.target_size",
    "Target size, e.g. 20MB": "commands.args.target_size_mb",
    "Target size, e.g. 1280x720": "commands.args.video_size",
    "Degrees: 90, 180, 270": "commands.args.degrees",
    "Target FPS, e.g. 60": "commands.args.target_fps",
    "Speed factor, e.g. 2x or 0.5": "commands.args.speed_factor",
    "Start time, e.g. 00:01:00": "commands.args.start_time",
    "End time, e.g. 00:02:00": "commands.args.end_time",
    "Duration, e.g. 60": "commands.args.duration",
    "Timestamp (default: 00:00:05)": "commands.args.thumbnail_time",
    "Timestamp (default: 00:00:00)": "commands.args.frame_time",
    "Start time (default: 00:00:00)": "commands.args.start_time_default",
    "Duration in seconds (default: 5)": "commands.args.gif_duration",
    "Frames per second (default: 10)": "commands.args.gif_fps",
    "Width in pixels (default: 480)": "commands.args.gif_width",
    "Output GIF file": "commands.args.gif_output",
    "Volume change: +20%, -10%, 1.5": "commands.args.volume",
    "in or out": "commands.args.fade_type",
    "Fade duration in seconds": "commands.args.fade_duration",
    "Encoding preset: ultrafast/medium/slow (default: medium)": "commands.args.preset",
    "CRF quality 0-51 (default: 23)": "commands.args.crf",
    "Subtitle file (.srt, .ass)": "commands.args.subtitle",
    "Watermark image file": "commands.args.watermark",
    "Position: topleft, topright, bottomleft, bottomright, center": "commands.args.position",
    "Input files separated by spaces": "commands.args.input_files",
    "Filter name to search for": "commands.args.filter_search",
    "Optional: category (video/audio/image) or media file path": "commands.args.category",
}

class I18nManager:
    def __init__(self):
        self.current_lang = "en"
        self.requested_lang = "en"
        self.resolved_lang = "en"
        self.translations: dict[str, Any] = {}
        self.fallback_translations: dict[str, Any] = {}
        self.locales_dir = Path(__file__).parent / "locales"
        
        saved_lang = config.get("language")
        if saved_lang:
            self.current_lang = saved_lang
        else:
            self._detect_system_language()
            
        self.load_language(self.current_lang)

    def _detect_system_language(self):
        try:
            sys_loc = locale.getdefaultlocale()[0]
            if sys_loc:
                lang = sys_loc.split('_')[0].lower()
                if (self.locales_dir / f"{lang}.json").exists():
                    self.current_lang = lang
        except Exception:
            pass

    def _read_locale(self, lang: str) -> dict[str, Any]:
        path = self.locales_dir / f"{lang}.json"
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}

    def load_language(self, lang: str):
        """Load a locale while retaining English as a per-key fallback."""
        normalized = str(lang or "en").strip().lower().replace("-", "_")
        normalized = normalized.split("_")[0]
        self.requested_lang = normalized
        self.fallback_translations = self._read_locale("en")

        candidate = self._read_locale(normalized)
        if candidate:
            self.translations = candidate
            self.resolved_lang = normalized
        else:
            self.translations = self.fallback_translations.copy()
            self.resolved_lang = "en"
        self.current_lang = self.resolved_lang

    def set_language(self, lang: str, persist: bool = True) -> bool:
        """Switch language immediately and optionally persist it for next runs."""
        self.load_language(lang)
        if self.resolved_lang != self.requested_lang:
            return False
        if persist:
            config.set("language", self.resolved_lang)
        return True

    def get(self, key: str, **kwargs) -> str:
        key = _LEGACY_KEYS.get(key, key)
        keys = key.split('.')
        val = self.translations
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k)
            else:
                val = None
                break

        if not isinstance(val, str):
            val = self._get_from(self.fallback_translations, keys)
        if not isinstance(val, str):
            val = key
            
        if kwargs and isinstance(val, str):
            try:
                val = val.format(**kwargs)
            except KeyError:
                pass
        return val

    @staticmethod
    def _get_from(source: dict[str, Any], keys: list[str]) -> Any:
        value: Any = source
        for key in keys:
            if not isinstance(value, dict) or key not in value:
                return None
            value = value[key]
        return value

i18n = I18nManager()
def t(key: str, **kwargs) -> str:
    return i18n.get(key, **kwargs)
