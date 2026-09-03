import json
import os
import platform
import locale
from pathlib import Path
from typing import Dict, Any
from alenia_porter.config.manager import config

class I18nManager:
    def __init__(self):
        self.current_lang = "en"
        self.translations: Dict[str, Any] = {}
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

    def load_language(self, lang: str):
        file_path = self.locales_dir / f"{lang}.json"
        if not file_path.exists():
            file_path = self.locales_dir / "en.json" # fallback
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                self.translations = json.load(f)
            self.current_lang = lang
        except Exception:
            self.translations = {}

    def get(self, key: str, **kwargs) -> str:
        keys = key.split('.')
        val = self.translations
        for k in keys:
            if isinstance(val, dict):
                val = val.get(k, key)
            else:
                val = key
                break
        
        if not isinstance(val, str):
            val = key
            
        if kwargs and isinstance(val, str):
            try:
                val = val.format(**kwargs)
            except KeyError:
                pass
        return val

i18n = I18nManager()
def t(key: str, **kwargs) -> str:
    return i18n.get(key, **kwargs)
