# Alenia Fuse

> **Esta es la versión mejorada de Alenia Porter** — reescrita completamente en Python puro, con una API limpia, soporte multiplataforma y publicación en PyPI.
> Alenia Fuse se llamaba anteriormente **Alenia-Porter**. El proyecto fue rebrandeado en la versión 2.0; las instalaciones nuevas usan el paquete `alenia-fuse` y el comando `fuse`.

**Professional multimedia toolkit — Python library + interactive CLI**

[![PyPI](https://img.shields.io/pypi/v/alenia-fuse.svg)](https://pypi.org/project/alenia-fuse/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/alenia-fuse.svg)](https://pypi.org/project/alenia-fuse/)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://python.org)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![CI](https://github.com/Kaia-Alenia/Alenia-Fuse/actions/workflows/lint.yml/badge.svg)](https://github.com/Kaia-Alenia/Alenia-Fuse/actions/workflows/lint.yml)
[![Linux](https://img.shields.io/badge/Linux-x64-blue?logo=linux&logoColor=white)](#supported-platforms)
[![Windows](https://img.shields.io/badge/Windows-x64-blue?logo=windows&logoColor=white)](#supported-platforms)
[![macOS](https://img.shields.io/badge/macOS-arm64-blue?logo=apple&logoColor=white)](#supported-platforms)

Alenia Fuse converts, edits, compresses, and inspects audio, video, and images.
It downloads a verified platform FFmpeg asset on first use when FFmpeg is not already available in the system PATH.

---

## Quick start

```bash
pip install alenia-fuse
fuse
```

That opens the interactive CLI. Type `/help` to see all commands.

---

## Interactive CLI

```
  ◈ Alenia Fuse 2.0.6
  Multimedia toolkit

  Type / for commands · Tab for suggestions

fuse ❯
```

### Session commands

| Command | Description |
|---|---|
| `/` | Show all available commands |
| `/help` | General help |
| `/help <command>` | Help for a specific command |
| `/convert` | Convert media to another format |
| `/compress` | Reduce file size intelligently |
| `/optimize` | Optimize media |
| `/info` | Inspect a media file |
| `/formats` | Browse valid output formats |
| `/formats <file>` | Show valid targets for a specific file |
| `/remux` | Change container without re-encoding |
| `/lang <code>` | Change interface language (no restart needed) |
| `/clear` | Clear the screen |
| `/history clear` | Delete persistent command history |
| `/exit` | Exit Fuse |

### Shell commands

```bash
fuse                        # Open interactive session
fuse -h                     # Help
fuse --version              # Version
fuse formats                # List all output formats
fuse formats video          # List video formats
fuse formats audio          # List audio formats
fuse formats image          # List image formats
```

---

## Python API

```python
from fuse import Video, Audio, Image, Media

# Convert video
result = Video("movie.mp4").convert("webm").output("movie.webm").run()
print(result.success, result.elapsed_seconds)

# Convert audio
Audio("song.wav").convert("flac").output("song.flac").run()

# Convert image
Image("photo.png").convert("webp").output("photo.webp").run()

# Inspect file
info = Media.inspect("movie.mp4")
print(info.duration, info.streams)
```

`run()` returns an `OperationResult` with:

| Field | Type | Description |
|---|---|---|
| `success` | `bool` | Whether the operation succeeded |
| `operation` | `str` | Operation name |
| `input_path` | `Path` | Input file |
| `output_path` | `Path` | Output file |
| `media` | `Media` | Inspected output (FFprobe result) |
| `elapsed_seconds` | `float` | Wall-clock duration |
| `warnings` | `list[str]` | Non-fatal warnings |
| `error` | `str \| None` | Error message if failed |

The API is **silent** — no `print()` calls, no prompts. Errors are raised as exceptions or returned in `OperationResult`.

---

## Supported formats

### Video output

| Format | Extension | Notes |
|---|---|---|
| MP4 | `.mp4` | H.264 / H.265 / AV1 |
| MKV | `.mkv` | Universal container |
| WebM | `.webm` | VP9 / Opus |
| MOV | `.mov` | QuickTime |
| AVI | `.avi` | Legacy — limited support |
| MPEG-TS | `.ts` | Transport stream |
| FLV | `.flv` | Legacy Flash |

### Audio output

| Format | Extension | Notes |
|---|---|---|
| MP3 | `.mp3` | libmp3lame |
| FLAC | `.flac` | Lossless |
| AAC | `.aac` `.m4a` | Modern lossy |
| Opus | `.opus` | Best quality/size ratio |
| OGG Vorbis | `.ogg` | Open format |
| WAV | `.wav` | Uncompressed PCM |
| WMA | `.wma` | Windows Media Audio |

### Image output

| Format | Extension | Notes |
|---|---|---|
| WebP | `.webp` | Modern — recommended |
| JPEG | `.jpg` | Universal |
| PNG | `.png` | Lossless |
| AVIF | `.avif` | Requires libaom-av1 |
| BMP | `.bmp` | Uncompressed |
| TIFF | `.tiff` | High quality |

### Animated

| Format | Extension | Notes |
|---|---|---|
| GIF | `.gif` | Universal animated |
| Animated WebP | `.webp` | Modern animated |

> Fuse only offers formats that the bundled FFmpeg can actually produce.
> Protocols, pipes, devices, manifests, and pseudo-formats are never shown.

---

## Supported platforms

| Platform | Architecture |
|---|---|
| Windows | x64 |
| Linux | x64 |
| macOS | arm64 |

---

## Internationalization

Fuse supports 10 languages:

| Code | Language |
|---|---|
| `en` | English |
| `es` | Spanish |
| `pt` | Portuguese |
| `fr` | French |
| `de` | German |
| `it` | Italian |
| `ja` | Japanese |
| `ko` | Korean |
| `zh` | Chinese |
| `ru` | Russian |

Change language without restarting:

```
fuse ❯ /lang es
```

---

## Architecture

```
CLI ───────────────────┐
                       ▼
                  Shared Core
                       │
              Capability Engine
                       │
                    Planner
                       │
                    Executor
                       │
                   Validator
                       ▲
                       │
Python API ────────────┘
```

- **CLI and API share the same core.** No duplicated logic.
- **Capability Engine** queries the bundled FFmpeg to determine what conversions are actually possible for a given input file.
- **Validator** checks inputs before and outputs after every operation.

---

## Development

```bash
git clone https://github.com/kaia-alenia/alenia-fuse
cd alenia-fuse
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / macOS
pip install -e ".[dev]"
pytest tests/ -v
```

### Build wheel

```bash
python -m build
```

### Test install in clean environment

```bash
python -m venv clean-env
clean-env\Scripts\pip install dist\*.whl
clean-env\Scripts\fuse --version
clean-env\Scripts\fuse -h
```

---

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).

© Alenia Studios — contact.aleniastudios@gmail.com

## Available CLI Commands
- **Convert**: convert, compress, optimize, remux
- **Video**: resize, rotate, fps, speed, trim, mute, extract-audio, cut, concat, subtitle, watermark
- **Audio**: volume, normalize, fade
- **Image**: thumbnail, gif, frame
- **Inspect**: info, formats, codecs, hardware, filters, metadata
- **System**: lang, version
- **Session**: history, clear
