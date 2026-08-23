<div align="center">

# Alenia Porter v2.1

*Universal, high-performance multimedia optimizer — image, video and audio in a single tool.*

> **⚠️ IMPORTANT NOTICE:** The Graphical IDE Edition is still available and can be used indefinitely, but it **will NEVER be updated again** (frozen at v7.0). Moving forward, all new features, updates, and maintenance will be focused **exclusively on the native Go CLI Edition (v2.1+)**.

<a href="https://www.producthunt.com/products/alenia-porter?embed=true&amp;utm_source=badge-featured&amp;utm_medium=badge&amp;utm_campaign=badge-alenia-porter" target="_blank" rel="noopener noreferrer"><img alt="Alenia Porter - Universal multimedia optimizer for image, video &amp; audio. | Product Hunt" width="250" height="54" src="https://api.producthunt.com/widgets/embed-image/v1/featured.svg?post_id=1199433&amp;theme=light&amp;t=1784323367056"></a>

---

**Build and CI**
<br>
[![Build Status](https://github.com/Kaia-Alenia/Alenia-Porter/actions/workflows/build.yml/badge.svg)](https://github.com/Kaia-Alenia/Alenia-Porter/actions/workflows/build.yml)
[![Pages Deploy](https://github.com/Kaia-Alenia/Alenia-Porter/actions/workflows/pages.yml/badge.svg)](https://github.com/Kaia-Alenia/Alenia-Porter/actions/workflows/pages.yml)
[![GitHub release](https://img.shields.io/github/v/release/Kaia-Alenia/Alenia-Porter?include_prereleases&color=6c8ebf&label=latest)](https://github.com/Kaia-Alenia/Alenia-Porter/releases)
[![Downloads](https://img.shields.io/github/downloads/Kaia-Alenia/Alenia-Porter/total?color=4caf50)](https://github.com/Kaia-Alenia/Alenia-Porter/releases)

**License and Stats**
<br>
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Coding time (all-time)](https://devglobe.app/api/badge/Kaia-Alenia/coding-time-all.svg?theme=dark)](https://devglobe.app/developers/Kaia-Alenia)
[![GitGem](https://gitgem.org/api/badge/github/Kaia-Alenia/Alenia-Porter.svg)](https://gitgem.org/github/Kaia-Alenia/Alenia-Porter)

</div>

---

Alenia Porter is a professional, cross-platform, standalone tool that automates the optimization, compression, and preparation of multimedia assets. It includes embedded FFmpeg binaries — no external dependencies, no prior setup.

Originally designed for game engines (Ren'Py, Godot), it has evolved into a **general-purpose multimedia optimizer** for musicians, video editors, web developers, and content creators.

---

## IDE Edition (Graphical User Interface)

<br>

<div align="center">

### Download IDE Edition

| [![Windows](https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/Kaia-Alenia/Alenia-Porter/releases/latest) | [![macOS](https://img.shields.io/badge/macOS-000000?style=for-the-badge&logo=apple&logoColor=white)](https://github.com/Kaia-Alenia/Alenia-Porter/releases/latest) | [![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black)](https://github.com/Kaia-Alenia/Alenia-Porter/releases/latest) |
| :---: | :---: | :---: |
| [Download `.exe`](https://github.com/Kaia-Alenia/Alenia-Porter/releases/latest) | [Download `.dmg`](https://github.com/Kaia-Alenia/Alenia-Porter/releases/latest) | [Download `.AppImage`](https://github.com/Kaia-Alenia/Alenia-Porter/releases/latest) |
| Windows 10 / 11 | macOS 12 Monterey+ | Ubuntu 20.04+ / Arch |

</div>

<br>

**Quick start:**

1. Run the **AleniaPorter** executable.
2. Configure a custom nickname on the first startup (links your local stats anonymously).
3. Choose the preferred output format for audio (OGG or OPUS), video (WebM or MP4), and images (WebP or JPG).
4. Click on **Select Folder** and select the source directory.
5. Processed files are saved in an `Alenia_Optimized/` subfolder, respecting the original directory structure.

---

## CLI Edition (Command Line Interface)

<div align="center">

<img src="docs/images/cli-view-process.gif" alt="Alenia Porter CLI Video" width="860" />

*Main TUI — command palette, session history, and language selector*

</div>

<br>

<div align="center">

<img src="docs/images/cli-optimize.png" alt="Alenia Porter CLI Optimize Flow" width="860" />

*`/optimize` flow — directory scan, format selection, and real-time progress*

</div>

<br>

<div align="center">

<img src="docs/images/cli-complete.png" alt="Alenia Porter CLI Complete Conversion" width="860" />

*Conversion summary — processed files, output paths, elapsed time*

</div>

<br>

The CLI is a self-contained **native Go binary** — no Python, no Node, no runtime. Designed for headless servers, CI/CD pipelines, and automation workflows.

<div align="center">

### Install CLI

| [![Windows](https://img.shields.io/badge/Windows_(PowerShell)-0078D6?style=for-the-badge&logo=powershell&logoColor=white)](#) | [![Linux & macOS](https://img.shields.io/badge/Linux_&_macOS_(Bash)-1f883d?style=for-the-badge&logo=gnubash&logoColor=white)](#) |
| :---: | :---: |
| Open **PowerShell as Administrator** and run: | Open a terminal and run: |
| `irm https://kaia-alenia.github.io/Alenia-Porter/install.ps1 \| iex` | `curl -fsSL https://kaia-alenia.github.io/Alenia-Porter/install.sh \| bash` |
| Installs `porter.exe` in `%LOCALAPPDATA%\Programs\AleniaPorterCLI` | Adds the symlink `porter` to `~/.local/bin` |
| Requires Windows 10 1607+ | Requires `git` and `go` installed |

</div>

<br>

Once installed, type `porter` in any terminal to open the interactive TUI.

**Non-interactive mode** (skips the TUI completely, useful for scripting and CI):

```
porter version
porter optimize <directory> --vformat mp4 --aformat mp3 --iformat webp
```

**Inside the TUI**, commands use the `/` prefix. Type `/` to see autocomplete suggestions:

| Command | Description |
|---------|-------------|
| `/optimize` | Starts a guided conversion — asks for the folder and then formats step by step |
| `/help` | Shows all commands and keyboard shortcuts |
| `/formulas` | Shows the FFmpeg codec reference and common configurations |
| `/lang [code]` | Changes the language (`en`, `es`, `fr`, `ja`, `zh`, `ru`, `pt-br`, `de`, `pt`) |
| `/v-preset [value]` | Sets the video encoding preset (e.g., `slow`, `fast`, `ultrafast`) |
| `/v-crf [value]` | Sets the video quality CRF value (e.g., `17`, `23`, `28`) |
| `/a-bitrate [value]` | Sets the audio bitrate (e.g., `128k`, `192k`, `320k`) |
| `/clear` | Clears the session history |
| `/update` | Runs the project update script |
| `/self-update` | Downloads the latest source code and rebuilds the binary |
| `/exit` | Closes the TUI |


---

## Supported Input Formats

All formats below are **automatically detected** when scanning source directories recursively.

### Audio

| Format | Extension | Notes |
|---------|-----------|-------|
| MP3 | `.mp3` | MPEG Layer 3 |
| WAV | `.wav` | Uncompressed PCM |
| FLAC | `.flac` | Lossless |
| AAC | `.aac` | Advanced Audio Coding |
| OGG Vorbis | `.ogg` | Open, lossy |
| Opus | `.opus` | Modern, ultra-efficient |
| M4A | `.m4a` | AAC in MPEG-4 container |
| WMA | `.wma` | Windows Media Audio |
| AIFF / AIF | `.aiff` `.aif` | Raw Apple audio |
| ALAC | `.alac` | Apple Lossless |
| AMR | `.amr` | Mobile speech codec |
| MIDI | `.mid` `.midi` | Sequenced music |
| MP2 | `.mp2` | MPEG Layer 2 (legacy) |
| MPGA | `.mpga` | MPEG audio stream |
| AU / SND | `.au` `.snd` | Unix audio format |
| RA / RM | `.ra` `.rm` | RealAudio (legacy) |

### Video

| Format | Extension | Notes |
|---------|-----------|-------|
| MP4 | `.mp4` | H.264 / AAC |
| MKV | `.mkv` | Matroska container |
| WebM | `.webm` | VP9 / Opus |
| AVI | `.avi` | Microsoft container (legacy) |
| MOV | `.mov` | Apple QuickTime |
| WMV | `.wmv` | Windows Media Video |
| FLV | `.flv` | Flash Video (legacy) |
| M4V | `.m4v` | Apple iTunes video |
| MPG / MPEG | `.mpg` `.mpeg` `.m2v` | MPEG-1/2 |
| 3GP / 3G2 | `.3gp` `.3g2` | Mobile video |
| TS / M2TS | `.ts` `.m2ts` | Transport Stream |
| VOB | `.vob` | DVD Video Object |
| OGV | `.ogv` | Ogg Theora |
| ASF | `.asf` | Advanced Systems Format |
| DivX | `.divx` | DivX encoded video |

### Images

| Format | Extension | Notes |
|---------|-----------|-------|
| PNG | `.png` | Lossless raster |
| JPEG | `.jpg` `.jpeg` | Lossy, universal |
| WebP | `.webp` | Modern, lossy/lossless |
| BMP | `.bmp` | Uncompressed bitmap |
| TGA | `.tga` | Targa (game textures) |
| TIFF | `.tiff` | High quality for print |
| GIF | `.gif` | Animated / legacy |
| ICO | `.ico` | Windows icon |
| PDF | `.pdf` | Portable Document Format (reading) |
| AVIF | `.avif` | Next-gen image format |

---

## Output Formats (Conversion Targets)

> **Stability:** `Stable` = dedicated code path | `Unstable` = generic FFmpeg fallback, might produce empty or corrupt files | `Broken` = streaming protocol or format without write support

### Audio Output

| Format | Extension | Codec | Stability |
|---------|-----------|-------|-------------|
| OGG Vorbis | `.ogg` | `libvorbis` | Stable |
| Opus | `.opus` | `libopus` | Stable |
| MP3 | `.mp3` | `libmp3lame` | Stable |
| FLAC | `.flac` | `flac` | Stable |
| WAV | `.wav` | `pcm_s16le` | Stable |
| AAC | `.aac` | `aac` | Stable |
| M4A | `.m4a` | `aac` | Stable |
| WMA | `.wma` | `wmav2` | Stable |
| ALAC | `.m4a` | `alac` | Stable |
| AIFF | `.aiff` | `pcm_s16be` | Stable |
| WavPack | `.wv` | `wavpack` | Stable |
| AU | `.au` | `pcm_s16be` | Stable |
| AMR | `.amr` | `amr_nb` (forced 8kHz mono) | Stable |
| AC3 | `.ac3` | `ac3` | Stable |
| DTS | `.dts` | `dca` | Stable |
| CAF | `.caf` | `pcm_s16le` | Stable |

### Video Output

| Format | Extension | Codec | Stability |
|---------|-----------|-------|-------------|
| MP4 | `.mp4` | `libx264` / NVENC / QSV / AMF | Stable |
| WebM | `.webm` | `libvpx-vp9` / vp9_nvenc | Stable |
| MKV | `.mkv` | `libx264` | Stable |
| AVI | `.avi` | `libx264` | Stable |
| MOV | `.mov` | `libx264` | Stable |
| M4V | `.m4v` | `libx264` | Stable |
| FLV | `.flv` | `libx264` | Stable |
| TS | `.ts` | `libx264` | Stable |
| 3GP / 3G2 | `.3gp` `.3g2` | `libx264` | Stable |
| WMV | `.wmv` | `wmv2` | Stable |
| MPEG / MPG / M2V | `.mpeg` `.mpg` `.m2v` | `mpeg2video` | Stable |
| OGV | `.ogv` | `libtheora` | Stable |
| GIF | `.gif` | `gif` encoder (15fps, max 640px) | Stable |
| VOB | `.vob` | Generic fallback — no assigned encoder | Unstable |
| ASF | `.asf` | Generic fallback — no assigned encoder | Unstable |
| RM / RealMedia | `.rm` | Generic fallback — no assigned encoder | Unstable |
| AVIF (video) | `.avif` | Generic fallback — requires build with `libavif` | Unstable |
| MXF | `.mxf` | Generic fallback | Unstable |
| NUT | `.nut` | Generic fallback (experimental container) | Unstable |
| ADTS | `.adts` | Audio demuxer only — not a video container | Broken |
| ASF Stream | `.asf_stream` | Streaming protocol — cannot write to file | Broken |
| FITS | `.fits` | Astronomy image format — not a video container | Broken |
| RTP / MPEG-TS | `.rtp_mpegts` | Streaming protocol — cannot write to file | Broken |
| RTSP | `.rtsp` | Streaming protocol — cannot write to file | Broken |
| WebM Chunk | `.webm_chunk` | Streaming fragment — not an independent file | Broken |
| WebM DASH Manifest | `.webm_dash_manifest` | Metadata manifest only | Broken |
| YUV4MPEG Pipe | `.yuv4mpegpipe` | Raw pipe format — not a file container | Broken |

### Image Output

| Format | Extension | Notes | Stability |
|---------|-----------|-------|-------------|
| WebP | `.webp` | `libwebp`, quality controlled via `-q:v` | Stable |
| JPEG / JPG | `.jpg` `.jpeg` | Quality mapped to FFmpeg `-q:v` scale | Stable |
| PNG | `.png` | Lossless | Stable |
| BMP | `.bmp` | Uncompressed | Stable |
| TIFF | `.tiff` | Archive quality | Stable |
| TGA | `.tga` | Game textures | Stable |
| ICO | `.ico` | Auto-scaled to max 256×256, forced `rgba` pixel format | Stable |
| PDF | `.pdf` | Via Pillow (not FFmpeg), converts to RGB first | Stable |
| GIF (from image) | `.gif` | FFmpeg applies 15fps filter + scales to static image — produces a 1-frame GIF; may look corrupt in some viewers | Unstable |
| AVIF | `.avif` | Falls back to generic handler — requires FFmpeg build with `libavif` | Unstable |
| APNG | `.apng` | Falls back to generic handler — unreliable animated PNG muxer in standard builds | Unstable |
| MJPEG | `.mjpeg` | FFmpeg demuxer, not an image output format | Broken |
| MPJPEG | `.mpjpeg` | Multipart JPEG stream — not a file format | Broken |
| SMJPEG | `.smjpeg` | Loki game format — no write support in FFmpeg | Broken |

---

## Todo / Known Issues

| Format | Context | Root Cause |
|---------|----------|------------|
| AVIF Output | Image + Video | No dedicated handler — falls back to generic FFmpeg; requires `libavif` compilation flag |
| APNG Output | Image | No dedicated handler — animated PNG muxer produces inconsistent results |
| GIF as image output | Image | The engine applies a video filter (15fps, 480px) to static images — a 1-frame GIF is created which may look corrupt |
| MJPEG / MPJPEG / SMJPEG | Image output | These are demuxers or streaming formats, not file containers — selecting them as targets yields corrupt or empty files |
| VOB / ASF / RM Output | Video | No explicit encoder assigned — falls back to generic handler, results vary depending on source format |
| ADTS / RTSP / RTP / WebM Chunk / DASH Manifest / YUV4MPEG | Video | Streaming protocols or pipe formats — cannot be used as standalone file destinations |
| `.wv` Input (folder mode) | IDE Edition | WavPack is in the GUI file selector filter but **missing from the audio extensions in `media_engine.py`** — it won't be detected when scanning a folder |
| HEIC / HEIF | Any | No FFmpeg encoder without a commercial codec — not planned |
| MIDI as audio output | Audio | Sequenced format, not PCM — cannot be re-encoded |
| RA / RM as audio output | Audio | RealMedia codec not available in standard FFmpeg distributions |
| RA / RM Output | Unsupported | RealMedia codec not available in FFmpeg distributions |

---

## Architecture

| Component | Technology | Description |
|------------|------------|-------------|
| **IDE Edition** | Python + Nuitka + pywebview | Standalone executable with integrated React UI |
| **Frontend UI** | React 19 + TypeScript + Vite | Rendered in system WebView (no browser window) |
| **Media Engine** | Python + FFmpeg (embedded) | Concurrent processing via `ThreadPoolExecutor` |
| **CLI Edition** | Go 1.25.11 + Bubble Tea | Native TUI binary, zero dependencies |
| **CI/CD** | GitHub Actions | Builds + smoke tests on Windows, macOS, Linux |
| **GPU Acceleration** | NVENC / QSV / AMF (auto-detection) | Used for MP4 and WebM encoding when available |

---

## How It Works

1. **Efficient Scan** — Recursively scans directories by extension, grouping audio, video, and image files.
2. **Concurrent Processing** — Uses `ThreadPoolExecutor` with `(CPU count - 1)` workers. Each FFmpeg subprocess is forced to a single thread to avoid contention on low-end hardware.
3. **Smart Deduplication** — A SHA-256 cache (`.alenia_cache.json`) skips already optimized files in subsequent runs.
4. **GPU Auto-detection** — Queries the FFmpeg encoders list at runtime and selects NVIDIA NVENC, Intel QSV, or AMD AMF when available, falling back to software encoders.
5. **Fail-Safe Resiliency** — If FFmpeg fails, it automatically retries in safe mode (software-only). Generates timestamped crash dumps for diagnostics.

---

## Telemetry and Privacy

Alenia Porter includes a lightweight, **completely anonymous**, and asynchronous telemetry system.

- **No personal data is collected** — no filenames, no real names, no passwords, no disk contents.
- **What is sent:** Anonymous UUID, chosen nickname, OS type, run mode (GUI/CLI), output format extension (e.g., `webp`), file count, and elapsed time.
- **Purpose:** Public benchmarks to measure performance across different platforms and hardware configurations.

---

## CLI vs IDE Edition

| Feature | IDE Edition (GUI) | CLI Edition |
|----------------|-------------------|-------------|
| **Target Audience** | Content creators, editors, designers | DevOps, backend devs, CI/CD automation |
| **Interface** | React UI with dynamic themes | Minimalist TUI with Bubble Tea |
| **Architecture** | Python + pywebview + integrated FFmpeg | Native Go binary, zero dependencies |
| **Integration** | Standalone desktop application | Shell scripts, GitHub Actions, Makefiles |
| **GPU Acceleration** | Auto (NVENC / QSV / AMF) | Auto (same FFmpeg backend) |
| **Batch Processing** | By folder with live progress | Directory or file list via flags |
| **Performance** | High | Ultra-high (minimal overhead) |

---

<div align="center">

**License:** GNU General Public License v3 (GPL v3).

**Assets and Music License:** Standard Licensing: Alenia Studios Standard (CC BY 4.0 + Additional Terms).
- **Attribution**: Required to Alenia Studios.
- **No Resale**: Standalone redistribution or resale is prohibited.
- **No AI**: Usage for AI training or dataset creation is prohibited.
- **Commercial Use**: Allowed for games, videos, and projects.
*Designed to be free, transparent, and accessible to the entire developer and creator community.*

**Official Alenia Studios Email:** contact.aleniastudios@gmail.com

**Developed and translated by Kaia-Alenia Studios**
🇺🇸 US &nbsp; 🇪🇸 ES &nbsp; 🇫🇷 FR &nbsp; 🇯🇵 JP &nbsp; 🇨🇳 CN &nbsp; 🇷🇺 RU &nbsp; 🇧🇷 BR &nbsp; 🇩🇪 DE

</div>
