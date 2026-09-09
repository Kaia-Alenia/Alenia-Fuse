"""
Test i18n live switch (§6): /lang must change the session without restarting Fuse.
"""
import pytest
from fuse.i18n.manager import I18nManager


@pytest.fixture
def mgr():
    """Fresh I18nManager instance for each test."""
    return I18nManager()


def test_initial_language_is_resolved(mgr):
    """Manager starts with a valid resolved language."""
    assert mgr.resolved_lang in ("en", "es", "pt", "fr", "de", "it", "ja", "ko", "zh", "ru")


def test_switch_to_spanish_live(mgr):
    """Switching to Spanish updates translations immediately."""
    mgr.load_language("en")
    en_value = mgr.get("cli.banner_subtitle")

    mgr.load_language("es")
    es_value = mgr.get("cli.banner_subtitle")

    assert mgr.current_lang == "es", "current_lang must update after load_language"
    # Spanish translation should differ from English (if key exists in both)
    # We accept equal values only if both resolve the key to the key itself (missing)
    if en_value != "cli.banner_subtitle" and es_value != "cli.banner_subtitle":
        assert en_value != es_value, (
            "Spanish translation of 'cli.banner_subtitle' should differ from English"
        )


def test_fallback_to_english_on_unknown_lang(mgr):
    """Requesting a non-existent locale falls back to English."""
    mgr.load_language("xx")  # does not exist
    assert mgr.requested_lang == "xx"
    assert mgr.resolved_lang == "en"
    assert mgr.current_lang == "en"


def test_switch_back_to_english(mgr):
    """Can switch back to English after another language."""
    mgr.load_language("es")
    mgr.load_language("en")
    assert mgr.current_lang == "en"
    assert mgr.resolved_lang == "en"


def test_translations_not_empty_after_switch(mgr):
    """Translations dict must not be empty after a valid language switch."""
    mgr.load_language("fr")
    assert mgr.translations, "Translations must not be empty after loading 'fr'"


def test_get_key_returns_string(mgr):
    """t() always returns a string, never None or a dict."""
    mgr.load_language("en")
    result = mgr.get("cli.banner_subtitle")
    assert isinstance(result, str)


def test_missing_spanish_key_falls_back_to_english(mgr):
    """A partially translated locale never leaks a key into the UI."""
    mgr.load_language("es")
    assert mgr.get("commands.hardware.description")
    assert mgr.get("commands.hardware.description") != "commands.hardware.description"


def test_set_language_persists_and_switches(mgr):
    """The public switch API updates the active locale in one operation."""
    assert mgr.set_language("es", persist=False)
    assert mgr.current_lang == "es"
    assert mgr.get("cli.banner_subtitle") == "Convierte • edita • optimiza"


def test_missing_key_returns_key_itself(mgr):
    """A missing key returns the key string (not None or empty string)."""
    mgr.load_language("en")
    result = mgr.get("nonexistent.key.deep")
    assert result == "nonexistent.key.deep"
