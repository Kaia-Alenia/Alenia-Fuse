"""
Target catalog — explicit product-level conversion targets (§11).

Fuse offers these targets to end users. FFmpeg may list many more formats,
but Fuse is a product layer — not a pass-through for every FFmpeg muxer (§10).
"""
from fuse.capabilities.models import TargetDefinition

# ---------------------------------------------------------------------------
# Video targets
# ---------------------------------------------------------------------------
VIDEO_TARGETS: list[TargetDefinition] = [
    TargetDefinition(
        id="mp4",
        display_name="MP4",
        extensions=[".mp4"],
        kind="video",
        muxer="mp4",
        video_encoders=["libx264", "libx265", "libsvtav1"],
        audio_encoders=["aac", "libopus"],
    ),
    TargetDefinition(
        id="mkv",
        display_name="MKV",
        extensions=[".mkv"],
        kind="video",
        muxer="matroska",
        video_encoders=["libx264", "libx265", "libvpx-vp9", "libsvtav1"],
        audio_encoders=["aac", "libopus", "libvorbis", "flac"],
    ),
    TargetDefinition(
        id="webm",
        display_name="WebM",
        extensions=[".webm"],
        kind="video",
        muxer="webm",
        video_encoders=["libvpx-vp9", "libvpx"],
        audio_encoders=["libopus", "libvorbis"],
    ),
    TargetDefinition(
        id="mov",
        display_name="MOV",
        extensions=[".mov"],
        kind="video",
        muxer="mov",
        video_encoders=["libx264", "libx265"],
        audio_encoders=["aac"],
    ),
    TargetDefinition(
        id="avi",
        display_name="AVI",
        extensions=[".avi"],
        kind="video",
        muxer="avi",
        video_encoders=["libx264", "mpeg4"],
        audio_encoders=["mp3", "pcm_s16le"],
        limitations=["Limited browser support"],
    ),
    TargetDefinition(
        id="ts",
        display_name="MPEG-TS",
        extensions=[".ts", ".m2ts"],
        kind="video",
        muxer="mpegts",
        video_encoders=["libx264", "libx265", "mpeg2video"],
        audio_encoders=["aac", "mp3"],
    ),
    TargetDefinition(
        id="flv",
        display_name="FLV",
        extensions=[".flv"],
        kind="video",
        muxer="flv",
        video_encoders=["libx264"],
        audio_encoders=["aac"],
        limitations=["Legacy format — limited modern support"],
    ),
]

# ---------------------------------------------------------------------------
# Audio targets
# ---------------------------------------------------------------------------
AUDIO_TARGETS: list[TargetDefinition] = [
    TargetDefinition(
        id="mp3",
        display_name="MP3",
        extensions=[".mp3"],
        kind="audio",
        muxer="mp3",
        audio_encoders=["libmp3lame"],
    ),
    TargetDefinition(
        id="flac",
        display_name="FLAC",
        extensions=[".flac"],
        kind="audio",
        muxer="flac",
        audio_encoders=["flac"],
    ),
    TargetDefinition(
        id="aac",
        display_name="AAC",
        extensions=[".aac", ".m4a"],
        kind="audio",
        muxer="adts",
        audio_encoders=["aac"],
    ),
    TargetDefinition(
        id="m4a",
        display_name="M4A",
        extensions=[".m4a"],
        kind="audio",
        muxer="mp4",
        audio_encoders=["aac"],
    ),
    TargetDefinition(
        id="opus",
        display_name="Opus",
        extensions=[".opus"],
        kind="audio",
        muxer="ogg",
        audio_encoders=["libopus"],
    ),
    TargetDefinition(
        id="ogg",
        display_name="OGG Vorbis",
        extensions=[".ogg"],
        kind="audio",
        muxer="ogg",
        audio_encoders=["libvorbis"],
    ),
    TargetDefinition(
        id="wav",
        display_name="WAV",
        extensions=[".wav"],
        kind="audio",
        muxer="wav",
        audio_encoders=["pcm_s16le", "pcm_s24le", "pcm_f32le"],
    ),
    TargetDefinition(
        id="wma",
        display_name="WMA",
        extensions=[".wma"],
        kind="audio",
        muxer="asf",
        audio_encoders=["wmav2"],
        limitations=["Windows Media Audio — limited cross-platform support"],
    ),
]

# ---------------------------------------------------------------------------
# Image targets
# ---------------------------------------------------------------------------
IMAGE_TARGETS: list[TargetDefinition] = [
    TargetDefinition(
        id="webp",
        display_name="WebP",
        extensions=[".webp"],
        kind="image",
        muxer="webp",
        video_encoders=["libwebp"],
    ),
    TargetDefinition(
        id="jpg",
        display_name="JPEG",
        extensions=[".jpg", ".jpeg"],
        kind="image",
        muxer="image2",
        supports_alpha=False,
        video_encoders=["mjpeg"],
    ),
    TargetDefinition(
        id="png",
        display_name="PNG",
        extensions=[".png"],
        kind="image",
        muxer="image2",
        video_encoders=["png"],
    ),
    TargetDefinition(
        id="avif",
        display_name="AVIF",
        extensions=[".avif"],
        kind="image",
        muxer="avif",
        video_encoders=["libaom-av1"],
        requirements=["libaom-av1 encoder"],
    ),
    TargetDefinition(
        id="bmp",
        display_name="BMP",
        extensions=[".bmp"],
        kind="image",
        muxer="image2",
        video_encoders=["bmp"],
    ),
    TargetDefinition(
        id="tiff",
        display_name="TIFF",
        extensions=[".tiff", ".tif"],
        kind="image",
        muxer="image2",
        video_encoders=["tiff"],
    ),
]

# ---------------------------------------------------------------------------
# Animated image targets
# ---------------------------------------------------------------------------
ANIMATED_TARGETS: list[TargetDefinition] = [
    TargetDefinition(
        id="gif",
        display_name="GIF",
        extensions=[".gif"],
        kind="animated_image",
        muxer="gif",
        video_encoders=["gif"],
    ),
    TargetDefinition(
        id="webp_animated",
        display_name="Animated WebP",
        extensions=[".webp"],
        kind="animated_image",
        muxer="webp",
        video_encoders=["libwebp_anim"],
    ),
    TargetDefinition(
        id="apng",
        display_name="APNG",
        extensions=[".apng", ".png"],
        kind="animated_image",
        muxer="apng",
        video_encoders=["apng"],
    ),
]

# PDF is deliberately handled by Pillow, not by a generic FFmpeg muxer.
PDF_TARGETS: list[TargetDefinition] = [
    TargetDefinition(
        id="pdf",
        display_name="PDF",
        extensions=[".pdf"],
        kind="image",
        muxer="pillow",
        requirements=["Pillow"],
    ),
]

# Single flat catalog for engine lookups
ALL_TARGETS: list[TargetDefinition] = (
    VIDEO_TARGETS + AUDIO_TARGETS + IMAGE_TARGETS + ANIMATED_TARGETS + PDF_TARGETS
)
TARGET_BY_ID: dict[str, TargetDefinition] = {t.id: t for t in ALL_TARGETS}

# User-facing aliases accepted by the API and CLI. The planner always works
# with canonical target IDs so extension spelling cannot create fake targets.
FORMAT_ALIASES: dict[str, str] = {
    "jpeg": "jpg",
    "jpe": "jpg",
    "m2ts": "ts",
    "mpegts": "ts",
    "tif": "tiff",
}


def normalize_format(value: str) -> str:
    """Return the canonical Fuse target ID for a format or extension."""
    normalized = str(value or "").strip().lower().lstrip(".")
    if normalized in TARGET_BY_ID:
        return normalized
    return FORMAT_ALIASES.get(normalized, normalized)
