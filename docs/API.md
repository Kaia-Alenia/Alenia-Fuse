# Alenia Fuse Python API

Alenia Fuse exposes one core pipeline for the CLI and Python library:

`API facade → Media inspection → OperationPlanner → FFmpeg → OperationResult`

The planner decides whether a conversion can copy streams or needs a real
re-encode. The public APIs do not call external conversion services.

## Public entry points

```python
from fuse import Video, Audio, Image, Media

Video("movie.mp4").convert("webm").output("movie.webm").run()
Audio("speech.wav").normalize().output("speech.wav").run()
Image("photo.png").resize(1200, 800).output("photo.webp").run()
Image("photo.png").to_pdf("photo.pdf", dpi=150)
info = Media.inspect("movie.mp4")
```

`Video` handles video conversion and video operations such as resize, crop,
rotate, FPS, speed, trim, mute, audio extraction, thumbnails, GIF creation
and remuxing. `Audio` handles conversion, volume, normalization, fades, speed
and trim. `Image` handles image conversion, resize, crop and rotation.

`Media.inspect` reads technical metadata through FFprobe. It does not perform
OCR, invent metadata, or call a third-party service. Metadata operations copy
or update tags through FFmpeg when the selected container supports them.

All generated media files use a privacy-first default: global metadata and
chapters are not copied automatically. This removes common sensitive fields
such as GPS, device, software, creation time and comments while preserving
technical stream data required for playback. Image-to-PDF output is generated
without source image metadata.

Image-to-PDF uses Pillow locally, corrects EXIF orientation, composites
transparent pixels on white, preserves image quality and supports page DPI.

## Conversion policy

Fuse only exposes targets with a local FFmpeg strategy. Common targets include
MP4, WebM, MKV, MOV, AVI, TS, MP3, FLAC, AAC, M4A, Opus, OGG, WAV, WebP, JPEG,
PNG, AVIF, BMP, TIFF, GIF and APNG. Unsupported or ambiguous targets are
rejected before execution.

Web video conversion uses `webm` and produces a `.webm` file with VP9/Opus
when the input contains video/audio. `m4a` is a separate MP4-based audio
target; it is not treated as raw AAC.

## FFmpeg distribution

The Python package does not require bundled FFmpeg binaries. Fuse resolves
FFmpeg in this order: `FUSE_FFMPEG_DIR`, an explicitly configured local
cache, packaged development binaries, and the operating-system `PATH`.
Missing FFmpeg returns a clear operation error. Fuse never downloads an
executable during import or silently contacts an external service.

Every operation returns `OperationResult`, including `success`, `operation`,
`input_path`, `output_path`, optional inspected `media`, warnings and a useful
error message.
