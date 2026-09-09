"""
Conversion Capability Engine (§9, §10, §12, §32).

API:
    get_valid_targets(media) -> list[ConversionCapability]

The engine evaluates the bundled FFmpeg's actual encoder/muxer availability
against the product-level catalog in policies.py. It never silences errors (§32).
"""
from __future__ import annotations

import subprocess

from fuse.capabilities.models import ConversionCapability, TargetDefinition
from fuse.capabilities.policies import ALL_TARGETS

# Load status exposed for diagnostics (§32)
_STATUS: str = "not_loaded"   # 'not_loaded' | 'loaded' | 'failed'
_LOAD_ERROR: str | None = None
_AVAILABLE_ENCODERS: set[str] = set()
_AVAILABLE_MUXERS: set[str] = set()


def _load_ffmpeg_capabilities() -> None:
    """Populate encoder and muxer sets from the bundled FFmpeg binary."""
    global _STATUS, _LOAD_ERROR, _AVAILABLE_ENCODERS, _AVAILABLE_MUXERS

    if _STATUS == "loaded":
        return

    try:
        from fuse.ffmpeg.resolver import default_resolver

        if not default_resolver.is_ffmpeg_available:
            _STATUS = "failed"
            _LOAD_ERROR = "Bundled FFmpeg binary is not available."
            return

        ffmpeg = str(default_resolver.ffmpeg_path)

        # Encoders
        enc_result = subprocess.run(
            [ffmpeg, "-encoders"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True,
        )
        for line in enc_result.stdout.splitlines():
            line = line.strip()
            if len(line) > 8 and line[0] in "VASDTLvasdtl":
                parts = line.split()
                if len(parts) >= 2:
                    _AVAILABLE_ENCODERS.add(parts[1])

        # Muxers
        mux_result = subprocess.run(
            [ffmpeg, "-muxers"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
            check=True,
        )
        for line in mux_result.stdout.splitlines():
            line = line.strip()
            if line.startswith("E"):
                parts = line.split()
                if len(parts) >= 2:
                    name_part = parts[1]
                    # muxers can have comma-separated aliases
                    for name in name_part.split(","):
                        _AVAILABLE_MUXERS.add(name.strip())

        _STATUS = "loaded"
        _LOAD_ERROR = None

    except subprocess.CalledProcessError as exc:
        _STATUS = "failed"
        _LOAD_ERROR = f"FFmpeg subprocess error: {exc}"
        raise RuntimeError(_LOAD_ERROR) from exc
    except Exception as exc:
        _STATUS = "failed"
        _LOAD_ERROR = str(exc)
        raise


def load_status() -> dict:
    """Return the current load status and any error message."""
    return {"status": _STATUS, "error": _LOAD_ERROR}


def _evaluate_target(
    media, target: TargetDefinition
) -> ConversionCapability:
    """
    Check whether a TargetDefinition is achievable from a given source kind.
    Returns a ConversionCapability with available=True/False and a reason.
    """
    # Determine which encoder lists are relevant
    all_required_encoders = (target.video_encoders or []) + (target.audio_encoders or [])

    # Find the first available video encoder (if any required)
    chosen_video_enc = ""
    if target.video_encoders:
        chosen_video_enc = next(
            (e for e in target.video_encoders if e in _AVAILABLE_ENCODERS), ""
        )

    # Find the first available audio encoder (if any required)
    chosen_audio_enc = ""
    if target.audio_encoders:
        chosen_audio_enc = next(
            (e for e in target.audio_encoders if e in _AVAILABLE_ENCODERS), ""
        )

    # Check muxer
    muxer_ok = target.muxer in _AVAILABLE_MUXERS or target.muxer == ""

    # Image targets: video encoder doubles as image encoder

    from fuse.media.models import MediaType
    kind_map = {MediaType.VIDEO: "video", MediaType.AUDIO: "audio", MediaType.IMAGE: "image"}
    source_kind = kind_map.get(media.type, "video")
    
    if target.kind == "image":
        video_ok = bool(chosen_video_enc)
        audio_ok = True  # images have no audio
    elif target.kind == "animated_image":
        video_ok = bool(chosen_video_enc)
        audio_ok = True
    else:
        # Video: must have at least a video encoder if target has video encoders
        video_ok = bool(chosen_video_enc) if target.video_encoders else True
        # Audio: must have at least an audio encoder if target has audio encoders
        audio_ok = bool(chosen_audio_enc) if target.audio_encoders else True

    # Source-kind compatibility rules
    incompatible_reason = _check_source_compatibility(media, target)

    required_encoders = []
    if chosen_video_enc:
        required_encoders.append(chosen_video_enc)
    if chosen_audio_enc:
        required_encoders.append(chosen_audio_enc)

    if incompatible_reason:
        return ConversionCapability(
            source_media_kind=source_kind,
            target_id=target.id,
            target_extension=target.extensions[0],
            target_kind=target.kind,
            available=False,
            reason=incompatible_reason,
            required_encoders=required_encoders,
            required_muxer=target.muxer,
        )

    if not muxer_ok:
        return ConversionCapability(
            source_media_kind=source_kind,
            target_id=target.id,
            target_extension=target.extensions[0],
            target_kind=target.kind,
            available=False,
            reason=f"Muxer '{target.muxer}' not available in bundled FFmpeg.",
            required_muxer=target.muxer,
        )

    if not video_ok:
        missing = ", ".join(target.video_encoders)
        return ConversionCapability(
            source_media_kind=source_kind,
            target_id=target.id,
            target_extension=target.extensions[0],
            target_kind=target.kind,
            available=False,
            reason=f"No suitable video encoder available. Tried: {missing}",
            required_muxer=target.muxer,
        )

    if not audio_ok:
        missing = ", ".join(target.audio_encoders)
        return ConversionCapability(
            source_media_kind=source_kind,
            target_id=target.id,
            target_extension=target.extensions[0],
            target_kind=target.kind,
            available=False,
            reason=f"No suitable audio encoder available. Tried: {missing}",
            required_muxer=target.muxer,
        )

    warnings = []
    has_alpha = False
    for s in media.streams:
        if s.codec_name in ("png", "webp", "gif", "apng") or s.pix_fmt in ("rgba", "yuva420p", "argb"):
            has_alpha = True
            break
            
    if has_alpha and not target.supports_alpha:
        warnings.append(f"Warning: {target.display_name} does not support transparency. Alpha channel will be flattened.")
        
    return ConversionCapability(
        source_media_kind=source_kind,
        target_id=target.id,
        target_extension=target.extensions[0],
        target_kind=target.kind,
        available=True,
        reason="",
        level=target.level,
        warnings=warnings,
        required_encoders=required_encoders,
        required_muxer=target.muxer,
    )


def _check_source_compatibility(media, target: TargetDefinition) -> str:
    """
    Returns a non-empty string if this source/target pair is fundamentally
    incompatible (e.g., audio-only source to a video-only target).
    """
    from fuse.media.models import MediaType
    kind_map = {MediaType.VIDEO: "video", MediaType.AUDIO: "audio", MediaType.IMAGE: "image"}
    source_kind = kind_map.get(media.type, "video")

    if target.id in ("scientific", "rawvideo", "rawaudio"):
        return "UNSUPPORTED_PRODUCT_TARGET: This target requires media characteristics outside Alenia Fuse's supported conversion model."

    if source_kind == "audio" and target.kind == "video":
        return "Cannot convert audio-only source to a video container."

    # Animated sources (GIF, APNG) may target video and animated_image.
    # Detect animated sources by checking if the media has a video stream
    # (GIF/APNG probed via FFprobe expose a video stream with gif/apng codec).
    if source_kind == "image":
        is_animated = any(
            s.codec_name in ("gif", "apng", "webp")
            for s in media.streams
            if s.codec_type == "video"
        )
        if not is_animated and target.kind not in ("image", "animated_image"):
            return "Cannot convert a still image to a video or audio target."
        if is_animated and target.kind == "audio":
            return "Cannot convert an animated image to an audio format."

    if source_kind == "audio" and target.kind in ("image", "animated_image"):
        return "Cannot convert audio to an image format."

    return ""


def get_valid_targets(media) -> list[ConversionCapability]:
    """
    Return all ConversionCapability entries for a given Media object.
    Only returns targets where available=True (§9, §12).

    Raises RuntimeError if FFmpeg capabilities could not be loaded.
    """
    if _STATUS == "not_loaded":
        _load_ffmpeg_capabilities()  # raises on failure — no silent suppression (§32)

    if _STATUS == "failed":
        raise RuntimeError(
            f"Capability engine failed to load: {_LOAD_ERROR}"
        )

    # Determine source kind from media
    from fuse.media.models import MediaType
    kind_map = {
        MediaType.VIDEO: "video",
        MediaType.AUDIO: "audio",
        MediaType.IMAGE: "image",
    }
    source_kind = kind_map.get(media.type, "video")

    results = []
    for target in ALL_TARGETS:
        cap = _evaluate_target(media, target)
        if cap.available:
            results.append(cap)

    return results


def get_all_capabilities(media) -> list[ConversionCapability]:
    """Like get_valid_targets but returns both available and unavailable."""
    if _STATUS == "not_loaded":
        _load_ffmpeg_capabilities()

    if _STATUS == "failed":
        raise RuntimeError(f"Capability engine failed to load: {_LOAD_ERROR}")

    from fuse.media.models import MediaType
    kind_map = {
        MediaType.VIDEO: "video",
        MediaType.AUDIO: "audio",
        MediaType.IMAGE: "image",
    }
    source_kind = kind_map.get(media.type, "video")

    return [_evaluate_target(media, t) for t in ALL_TARGETS]
