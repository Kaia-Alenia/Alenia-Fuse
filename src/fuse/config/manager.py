import json
from pathlib import Path
import os
import platform

class ConfigManager:
    def __init__(self):
        self.app_name = "fuse"
        self.config_dir = self._get_config_dir()
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_dir()
        self.settings = self._load()

    def _get_config_dir(self) -> Path:
        system = platform.system()
        if system == "Windows":
            base = os.environ.get("APPDATA")
            return Path(base) / self.app_name if base else Path.home() / f".{self.app_name}"
        elif system == "Darwin":
            return Path.home() / "Library" / "Application Support" / self.app_name
        else:
            base = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
            return Path(base) / self.app_name

    def _ensure_config_dir(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save(self):
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save()

config = ConfigManager()
