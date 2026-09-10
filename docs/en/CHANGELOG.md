# Changelog

## 2.0.6

- Route `convert image.png output.pdf` through the built-in image-to-PDF exporter.
- Produce broadly compatible MP4 output for animated images.

## [2.0.1] — FFmpeg release assets

### Changed

- Added verified, cached FFmpeg downloads from GitHub Release assets.
- Added the `fuse setup` command for explicit media-engine setup.
- Kept FFmpeg binaries out of the PyPI package and Git repository.

## [2.0.0] — Alenia Fuse rebrand

Alenia Fuse starts a new product line with a clean public identity and a focused multimedia workflow.

### Changed

- Renamed the Python package to `fuse`.
- Renamed the distribution to `alenia-fuse`.
- Standardized the executable command as `fuse`.
- Removed the former external backend and deployment files.
- Reset the public version line to 2.0.
- Preserved the interactive CLI, Python API, FFmpeg capabilities, and localization system.

### Migration note

Alenia Fuse was previously known as Alenia-Porter. New installations should use `pip install alenia-fuse` and run `fuse`.
