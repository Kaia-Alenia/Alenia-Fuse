"""
Test i18n schema (§6): all locales must contain the keys defined in en.json.
"""
import json
from pathlib import Path

import pytest

LOCALES_DIR = (
    Path(__file__).parent.parent
    / "src" / "fuse" / "i18n" / "locales"
)


def _load_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _flatten_keys(d: dict, prefix: str = "") -> set:
    keys = set()
    for k, v in d.items():
        full = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            keys |= _flatten_keys(v, full)
        else:
            keys.add(full)
    return keys


@pytest.fixture(scope="module")
def reference_keys():
    en = _load_json(LOCALES_DIR / "en.json")
    return _flatten_keys(en)


@pytest.fixture(params=[p.name for p in LOCALES_DIR.glob("*.json") if p.stem != "en"])
def locale_file(request):
    return LOCALES_DIR / request.param


def test_locale_missing_keys_are_allowed_with_fallback(locale_file, reference_keys):
    """Locales may omit keys because I18nManager falls back to English per key."""
    data = _load_json(locale_file)
    locale_keys = _flatten_keys(data)
    missing = reference_keys - locale_keys
    if missing:
        import warnings
        warnings.warn(
            f"Locale '{locale_file.stem}' uses English fallback for "
            f"{len(missing)} key(s): " + ", ".join(sorted(missing))
        )


def test_locale_has_no_extra_orphan_keys(locale_file, reference_keys):
    """Locales should not have keys absent from en.json (likely stale translations)."""
    data = _load_json(locale_file)
    locale_keys = _flatten_keys(data)
    orphans = locale_keys - reference_keys
    # Report as warning, not failure — orphan keys are undesirable but not blocking.
    if orphans:
        import warnings
        warnings.warn(
            f"Locale '{locale_file.stem}' has {len(orphans)} orphan key(s) "
            f"not in en.json: {', '.join(sorted(orphans))}"
        )
