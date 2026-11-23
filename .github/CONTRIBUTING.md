# Contributing to Alenia Fuse

Thank you for your interest in contributing to Alenia Fuse! This is an open-source project designed for the indie developer community and we are happy to receive your contributions.

## What Alenia Fuse is

Pure-Python multimedia toolkit (Python 3.11+): a `fuse` CLI built with `rich` + `prompt_toolkit`, and a Python API (`Video`, `Audio`, `Image`, `Media`). It converts, edits, compresses and inspects audio, video and images using FFmpeg — system FFmpeg when present, otherwise a platform build downloaded by `fuse setup` into the user cache. Still images can also convert via Pillow when FFmpeg is unavailable. There is no Go code, no Nuitka build, no React GUI and no automatic GPU acceleration in this codebase; please do not document or reintroduce them as if they existed.

## Getting Started
1. Fork this repository.
2. Clone your fork locally: `git clone https://github.com/YOUR-USERNAME/alenia-fuse.git`
3. Set up a virtual environment and install in editable mode with dev dependencies: `pip install -e ".[dev]"`
4. Make your changes in a descriptive branch: `git checkout -b fix/my-fix` or `git checkout -b feat/new-feature`

## Code Structure
- **`src/fuse/`**: the whole package.
  - **`api/`**: public Python API — `Video`, `Audio`, `Image`, `Media`, `OperationResult`.
  - **`capabilities/`**: product-level target catalog (`policies.py`) and the engine that asks FFmpeg what it can really do.
  - **`cli/`**: the `fuse` entry point, argument parser, interactive session and `cli/commands/` (convert, video, audio, image, inspect, system, session, media).
  - **`ffmpeg/`**: `resolver.py` (finds ffmpeg/ffprobe, triggers the download), `downloader.py` (downloads the platform FFmpeg build), `backend.py`, `probe.py`, `capabilities.py`, `diagnostics.py`.
  - **`planner/`**: builds the FFmpeg command line for a conversion/operation.
  - **`operations/`**: `convert`, `compress`, `image` (Pillow fallback for still images), `audio`, `video`.
  - **`media/`**: `Media` model and ffprobe-based inspection (with a Pillow fallback for still images).
  - **`i18n/`**: interface translations (10 languages).
  - **`jobs/`**: job/progress handling.
- **`tests/`**: pytest suite. `tests/test_no_ffmpeg.py` covers the no-FFmpeg path: `fuse setup` failing with a useful reason, image conversion via Pillow, and `ffprobe` missing.
- **`scripts/`**: helper scripts; `scripts/download_ffmpeg.py` is a thin CLI wrapper around `fuse.ffmpeg.downloader`.

## Contribution Guidelines
- **Security first**: ensure your code does not introduce vulnerabilities.
- **Testing**: any major PR must include tests (pytest). If you touch the FFmpeg path, add or update a test in `tests/test_no_ffmpeg.py` — the no-FFmpeg path must keep working.
- **Errors must say why**: never swallow an exception into a bare `return False` or a generic "not available" message. Record the cause on the resolver (`unavailable_reason`) and surface it in CLI/API errors.
- **Formatting**: run the linter and maintain visual consistency of the code.
- **Compatibility**: the tool must run on Windows, Linux, and macOS seamlessly.

## Submitting a Pull Request
- Detail the changes you have made in your PR description.
- Ensure that GitHub Actions (build and lint) pass successfully.
- An Alenia Studios maintainer will review and merge your code.

Thank you for supporting the indie ecosystem!
