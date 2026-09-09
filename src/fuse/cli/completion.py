"""
Completion engine for Alenia Fuse interactive CLI (§7, §8).

Architecture (§7):
    CompletionEngine  — knows completion types: command, alias, path, option,
                        enum, language, format, codec, hardware.
    FuseCompleter   — prompt_toolkit Completer that delegates to CompletionEngine.

FuseCompleter must NOT use PathCompleter as a universal fallback (§7).
Format autocomplete must consult the Capability Engine and FFprobe (§8).
"""
from __future__ import annotations

import shlex
from collections.abc import Iterable
from pathlib import Path

from prompt_toolkit.completion import Completer, Completion, PathCompleter
from prompt_toolkit.document import Document

from fuse.cli.registry import registry
from fuse.i18n.manager import t

# ---------------------------------------------------------------------------
# Completion types (§7)
# ---------------------------------------------------------------------------
_SUPPORTED_TYPES = {
    "command", "alias", "path", "option",
    "enum", "language", "format", "codec", "hardware",
}

_SUPPORTED_LANGUAGES = [
    "en", "es", "pt", "fr", "de", "it", "ja", "ko", "zh", "ru",
]


class CompletionEngine:
    """
    Core completion logic.  Returns raw (text, display_meta) tuples so that
    FuseCompleter can wrap them in Completion objects.
    """

    def __init__(self):
        self._path_completer = PathCompleter(expanduser=True)

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def complete(
        self,
        completion_type: str,
        prefix: str,
        context: dict | None = None,
    ) -> list[tuple[str, str]]:
        """
        Return list of (text, meta) tuples matching prefix for the given type.
        context may carry 'input_path', 'cmd_name', etc.
        """
        context = context or {}
        if completion_type == "command":
            return self._complete_commands(prefix)
        if completion_type == "alias":
            return self._complete_aliases(prefix)
        if completion_type == "path":
            return []   # delegated to PathCompleter at the prompt level
        if completion_type == "option":
            return self._complete_options(prefix, context.get("cmd_name", ""))
        if completion_type == "language":
            return self._complete_language(prefix)
        if completion_type == "format":
            return self._complete_format(prefix, context.get("input_path"))
        if completion_type == "codec":
            return self._complete_codec(prefix)
        if completion_type == "hardware":
            return self._complete_hardware(prefix)
        return []

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _complete_commands(self, prefix: str) -> list[tuple[str, str]]:
        results = []
        for cmd in registry.get_all():
            if cmd.name.startswith(prefix):
                results.append((cmd.name, t(cmd.description_key)))
        return results

    def _complete_aliases(self, prefix: str) -> list[tuple[str, str]]:
        results = []
        for cmd in registry.get_all():
            for alias in cmd.aliases:
                if alias.startswith(prefix):
                    results.append((alias, f"→ {cmd.name}"))
        return results

    # ------------------------------------------------------------------
    # Options
    # ------------------------------------------------------------------

    def _complete_options(self, prefix: str, cmd_name: str) -> list[tuple[str, str]]:
        cmd = registry.get(cmd_name)
        if not cmd:
            return []
        results = []
        for arg in cmd.arguments:
            if arg.name.startswith("--") and arg.name.startswith(prefix):
                results.append((arg.name, t(arg.help_key)))
        return results

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------

    def _complete_language(self, prefix: str) -> list[tuple[str, str]]:
        return [
            (lang, "")
            for lang in _SUPPORTED_LANGUAGES
            if lang.startswith(prefix)
        ]

    # ------------------------------------------------------------------
    # Formats — consults Capability Engine and FFprobe (§8)
    # ------------------------------------------------------------------

    def _complete_format(
        self, prefix: str, input_path: str | None
    ) -> list[tuple[str, str]]:
        """
        Returns valid target formats for input_path (§8).
        If input_path is not available or not analysable, falls back to the
        product catalog without source-specific filtering.
        """
        from fuse.capabilities.policies import ALL_TARGETS

        if input_path and Path(input_path).is_file():
            try:
                from fuse.capabilities.engine import get_valid_targets
                from fuse.media.models import Media
                media = Media.inspect(input_path)
                caps = get_valid_targets(media)
                results = []
                for cap in caps:
                    if cap.target_extension.lstrip(".").startswith(prefix):
                        meta = f"{cap.target_id}"
                        results.append((cap.target_extension.lstrip("."), meta))
                return results
            except Exception:
                pass  # fall through to catalog

        # Fallback: product catalog (no source-specific filtering)
        results = []
        for target in ALL_TARGETS:
            ext = target.extensions[0].lstrip(".")
            if ext.startswith(prefix):
                results.append((ext, target.display_name))
        return results

    # ------------------------------------------------------------------
    # Codecs
    # ------------------------------------------------------------------

    def _complete_codec(self, prefix: str) -> list[tuple[str, str]]:
        try:
            from fuse.ffmpeg.capabilities import default_registry
            if default_registry.load_status == "not_loaded":
                default_registry.load_from_ffmpeg()
            return [
                (enc, "encoder")
                for enc in sorted(default_registry.encoders)
                if enc.startswith(prefix)
            ]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Hardware encoders
    # ------------------------------------------------------------------

    def _complete_hardware(self, prefix: str) -> list[tuple[str, str]]:
        hw_encoders = [
            "h264_nvenc", "hevc_nvenc", "h264_amf", "hevc_amf",
            "h264_qsv", "hevc_qsv", "h264_videotoolbox",
        ]
        return [(e, "hw encoder") for e in hw_encoders if e.startswith(prefix)]


# ---------------------------------------------------------------------------
# FuseCompleter — prompt_toolkit integration
# ---------------------------------------------------------------------------

class ContextualCompleter(Completer):
    """
    prompt_toolkit Completer that delegates to CompletionEngine (§7).
    PathCompleter is used only when the argument's completion type is 'path'.
    It is NOT a universal fallback (§7).
    """

    def __init__(self):
        self._engine = CompletionEngine()
        self._path_completer = PathCompleter(expanduser=True)

    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        text = document.text_before_cursor

        try:
            tokens = shlex.split(text, posix=False)
        except ValueError:
            tokens = text.split()

        is_starting_new_word = not text.endswith(" ")

        # ── 1. First token: command completion ──────────────────────────
        if not tokens or (len(tokens) == 1 and is_starting_new_word):
            word = tokens[0] if tokens else ""
            has_slash = word.startswith("/")
            clean = word.lstrip("/")

            # Gather all entries as (name, meta) tuples — no set() to avoid corruption
            seen: set[str] = set()
            all_entries: list[tuple[str, str]] = []

            for name, meta in self._engine.complete("command", clean):
                if name not in seen:
                    seen.add(name)
                    all_entries.append((name, meta))

            for name, meta in self._engine.complete("alias", clean):
                if name not in seen:
                    seen.add(name)
                    all_entries.append((name, meta))

            # Built-ins that are handled directly in the interactive loop
            for name, key in [
                ("exit",  "commands.exit.description"),
                ("clear", "commands.clear.description"),
                ("help",  "commands.help.description"),
            ]:
                if name.startswith(clean) and name not in seen:
                    seen.add(name)
                    all_entries.append((name, t(key)))

            all_entries.sort(key=lambda x: x[0])

            for name, meta in all_entries:
                display = f"/{name}" if has_slash else name
                yield Completion(
                    display,
                    start_position=-len(word),
                    display=display,
                    display_meta=meta,
                )
            return

        # ── 2. Subsequent tokens: contextual completion ──────────────────
        cmd_name = tokens[0].lstrip("/")
        cmd = registry.get(cmd_name)

        current_word = tokens[-1] if is_starting_new_word else ""

        # Option completion (--flag)
        if current_word.startswith("--"):
            for name, meta in self._engine.complete(
                "option", current_word, {"cmd_name": cmd_name}
            ):
                yield Completion(
                    name,
                    start_position=-len(current_word),
                    display_meta=meta,
                )
            return

        # Language completion for /lang
        if cmd_name == "lang":
            for name, meta in self._engine.complete("language", current_word):
                yield Completion(
                    name,
                    start_position=-len(current_word),
                    display_meta=meta,
                )
            return

        # Format completion after "to" keyword (§8)
        # e.g.: "convert movie.mp4 to <TAB>"
        lower_tokens = [tok.lower().lstrip("/") for tok in tokens]
        if "to" in lower_tokens:
            to_idx = lower_tokens.index("to")
            # input is the token before "to"
            input_path = tokens[to_idx - 1] if to_idx > 0 else None
            for ext, meta in self._engine.complete(
                "format", current_word, {"input_path": input_path}
            ):
                yield Completion(
                    ext,
                    start_position=-len(current_word),
                    display_meta=meta,
                )
            return

        # Determine arg completion type from CommandDefinition
        if cmd:
            # Count how many positional arguments have already been filled
            positional_idx = sum(
                1 for tok in tokens[1:]
                if not tok.startswith("--")
            ) - (1 if is_starting_new_word else 0)

            positional_args = [a for a in cmd.arguments if not a.name.startswith("--")]
            if positional_idx < len(positional_args):
                arg = positional_args[positional_idx]
                ctype = arg.completion or "path"

                if ctype == "format":
                    # Infer input from previous token
                    input_path = tokens[1] if len(tokens) > 1 else None
                    for ext, meta in self._engine.complete(
                        "format", current_word, {"input_path": input_path}
                    ):
                        yield Completion(ext, start_position=-len(current_word), display_meta=meta)
                    return

                if ctype == "language":
                    for name, meta in self._engine.complete("language", current_word):
                        yield Completion(name, start_position=-len(current_word), display_meta=meta)
                    return

                if ctype == "codec":
                    for name, meta in self._engine.complete("codec", current_word):
                        yield Completion(name, start_position=-len(current_word), display_meta=meta)
                    return

                # Default: path completion (explicit, not universal fallback)
                if ctype == "path":
                    yield from self._path_completer.get_completions(document, complete_event)
                    return

        # No matching rule — do not fall back to PathCompleter universally (§7)
