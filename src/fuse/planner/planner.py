"""
Operation Planner — makes real decisions about how to perform an operation
based on media analysis, capabilities, and the requested intent.
"""
import os
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from fuse.ffmpeg.resolver import default_resolver
from fuse.ffmpeg.capabilities import default_registry
from fuse.capabilities.policies import normalize_format, TARGET_BY_ID
from fuse.media.privacy import apply_ffmpeg_privacy


# Maps container format → supported codecs for stream copy
STREAM_COPY_COMPATIBLE = {
    # video → audio that can be stream-copied without re-encoding
    "mp4": {"video": ["h264", "hevc", "h265"], "audio": ["aac", "mp3", "ac3"]},
    "mkv": {"video": ["h264", "hevc", "h265", "vp8", "vp9", "av1"], "audio": ["aac", "mp3", "ac3", "opus", "flac"]},
    "webm": {"video": ["vp8", "vp9", "av1"], "audio": ["vorbis", "opus"]},
    "mov": {"video": ["h264", "hevc", "h265", "prores"], "audio": ["aac", "mp3", "pcm_s16le"]},
    "avi": {"video": ["h264", "mpeg4", "xvid"], "audio": ["mp3", "ac3"]},
}

# Maps target format → recommended video/audio codecs for re-encoding
ENCODE_STRATEGIES = {
    "webm": {"video_codec": "libvpx-vp9", "audio_codec": "libopus", "extra": ["-b:v", "0", "-crf", "30"]},
    "mp4": {"video_codec": "libx264", "audio_codec": "aac", "extra": ["-crf", "23", "-preset", "medium"]},
    "mkv": {"video_codec": "libx264", "audio_codec": "aac", "extra": ["-crf", "23", "-preset", "medium"]},
    "mov": {"video_codec": "libx264", "audio_codec": "aac", "extra": ["-crf", "23", "-preset", "medium"]},
    "avi": {"video_codec": "libx264", "audio_codec": "libmp3lame", "extra": ["-crf", "23"]},
    "ts": {"video_codec": "libx264", "audio_codec": "aac", "extra": ["-crf", "23"]},
    "flv": {"video_codec": "libx264", "audio_codec": "aac", "extra": ["-crf", "23"]},
    "gif": {"video_codec": "gif", "audio_codec": None, "extra": []},
    # Audio formats
    "mp3": {"video_codec": None, "audio_codec": "libmp3lame", "extra": ["-q:a", "2"]},
    "aac": {"video_codec": None, "audio_codec": "aac", "extra": ["-b:a", "192k"]},
    "m4a": {"video_codec": None, "audio_codec": "aac", "extra": ["-b:a", "192k"]},
    "opus": {"video_codec": None, "audio_codec": "libopus", "extra": ["-b:a", "128k"]},
    "flac": {"video_codec": None, "audio_codec": "flac", "extra": []},
    "wav": {"video_codec": None, "audio_codec": "pcm_s16le", "extra": []},
    "ogg": {"video_codec": None, "audio_codec": "libvorbis", "extra": []},
    "wma": {"video_codec": None, "audio_codec": "wmav2", "extra": ["-b:a", "192k"]},
    # Image formats (single frame)
    "png": {"video_codec": "png", "audio_codec": None, "extra": ["-vframes", "1"]},
    "jpg": {"video_codec": "mjpeg", "audio_codec": None, "extra": ["-vframes", "1", "-q:v", "2"]},
    "jpeg": {"video_codec": "mjpeg", "audio_codec": None, "extra": ["-vframes", "1", "-q:v", "2"]},
    "webp": {"video_codec": "libwebp", "audio_codec": None, "extra": ["-vframes", "1"]},
    "bmp": {"video_codec": "bmp", "audio_codec": None, "extra": ["-vframes", "1"]},
    "tiff": {"video_codec": "tiff", "audio_codec": None, "extra": ["-vframes", "1"]},
    "avif": {"video_codec": "libaom-av1", "audio_codec": None, "extra": ["-vframes", "1"]},
    "apng": {"video_codec": "apng", "audio_codec": None, "extra": []},
    "webp_animated": {"video_codec": "libwebp", "audio_codec": None, "extra": ["-loop", "0"]},
}

COMPRESS_STRATEGIES = {
    "balanced": {"crf": 28, "preset": "medium", "audio_bitrate": "128k"},
    "high": {"crf": 23, "preset": "slow", "audio_bitrate": "192k"},
    "max": {"crf": 18, "preset": "slower", "audio_bitrate": "256k"},
    "size": {},  # handled separately
}


class OperationPlan:
    """Result of planning — contains the FFmpeg args list to execute."""
    def __init__(self):
        self.args: List[str] = []
        self.strategy: str = "reencode"
        self.warnings: List[str] = []
        self.is_valid: bool = True
        self.error_reason: Optional[str] = None
        self.needs_preflight: bool = False

    def is_stream_copy(self) -> bool:
        return self.strategy == "stream_copy"


class OperationPlanner:
    def __init__(self, registry=None):
        self.registry = registry or default_registry

    def preflight_check(self, plan: OperationPlan, timeout: float = 5.0) -> bool:
        """
        Executes a real FFmpeg preflight test (fast 1-frame or 1-second segment)
        to definitively prove if the conversion works.
        """
        if not plan.is_valid or not plan.args:
            return False
            
        with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tmp_out:
            tmp_path = tmp_out.name
            
        try:
            # Re-write output path to tmp_path, add -t 1 for speed
            args = plan.args.copy()
            out_idx = len(args) - 1
            args[out_idx] = tmp_path
            
            # Insert -t 1 before output to test just a small slice
            args.insert(out_idx, "-t")
            args.insert(out_idx + 1, "1")
            
            # Avoid overwriting warnings and hide output
            cmd = [str(default_resolver.ffmpeg_path), "-y"] + apply_ffmpeg_privacy(args)
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, timeout=timeout)
            
            if result.returncode == 0 and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                # Need to also check it didn't create a webp_pipe by accident but webp_pipe wouldn't create a real file
                return True
            else:
                plan.is_valid = False
                plan.error_reason = f"Preflight check failed. FFmpeg could not process this format combination."
                return False
        except subprocess.TimeoutExpired:
            # If it takes >5s, it might just be slow, we'll allow it for now
            return True
        except Exception as e:
            plan.is_valid = False
            plan.error_reason = f"Preflight execution failed: {e}"
            return False
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _check_image_semantics(self, media, target_fmt: str, plan: OperationPlan) -> bool:
        """Enforces semantics like RGBA -> JPEG."""
        if not media.main_video:
            return True
            
        pix_fmt = media.main_video.pix_fmt or ""
        has_alpha = "rgba" in pix_fmt or "alpha" in pix_fmt or "yuva" in pix_fmt or "argb" in pix_fmt or "bgra" in pix_fmt
        
        if has_alpha and target_fmt in ("jpg", "jpeg"):
            plan.is_valid = False
            plan.error_reason = "The input image has an alpha channel (transparency). JPEG does not support transparency. Please choose a background color or a different format."
            return False
            
        return True

    def plan_convert(self, media, target_format: str, output_path: str) -> OperationPlan:
        """
        Plan a conversion operation.
        Decides between stream copy (no re-encode) and full re-encode based on
        media streams and target container compatibility.
        """
        plan = OperationPlan()
        fmt = normalize_format(target_format)
        target = TARGET_BY_ID.get(fmt)

        if fmt == "pdf":
            plan.is_valid = False
            plan.error_reason = "PDF is an image-only document operation. Use Image.to_pdf()."
            return plan

        if target is None:
            plan.is_valid = False
            plan.error_reason = f"The target format '{fmt}' is not part of the Fuse conversion catalog."
            return plan

        output_suffix = Path(output_path).suffix.lower()
        allowed_suffixes = {extension.lower() for extension in target.extensions}
        if output_suffix not in allowed_suffixes:
            expected = ", ".join(sorted(allowed_suffixes))
            plan.is_valid = False
            plan.error_reason = (
                f"The output filename must use a valid '{fmt}' extension ({expected}). "
                f"Received '{output_suffix or '[no extension]'}'."
            )
            return plan

        # A target must be representable by the corresponding source stream.
        if target.kind == "video" and not media.main_video:
            plan.is_valid = False
            plan.error_reason = f"The input has no video stream required for '{fmt}'."
            return plan
        if target.kind == "audio" and not media.main_audio:
            plan.is_valid = False
            plan.error_reason = f"The input has no audio stream required for '{fmt}'."
            return plan
        if target.kind in {"image", "animated_image"} and not media.main_video:
            plan.is_valid = False
            plan.error_reason = f"The input has no image/video stream required for '{fmt}'."
            return plan

        # Validate that the format is supported at all
        if not self.registry.supports_format(fmt):
            plan.is_valid = False
            plan.error_reason = (
                f"The target format '{fmt}' cannot represent the required input features, or is not supported."
            )
            return plan
            
        if not self._check_image_semantics(media, fmt, plan):
            return plan

        # Check if stream copy is possible
        can_copy = self._can_stream_copy(media, fmt)

        if can_copy:
            plan.strategy = "stream_copy"
            plan.args = ["-i", media.path, "-c", "copy", output_path]
        else:
            plan.strategy = "reencode"
            strategy = ENCODE_STRATEGIES.get(fmt)

            if strategy is None:
                plan.is_valid = False
                plan.error_reason = f"Fuse has no verified local conversion strategy for '{fmt}'."
                return plan
            else:
                args = ["-i", media.path]

                # Video streams
                if media.main_video and strategy["video_codec"]:
                    if not self.registry.has_encoder(strategy["video_codec"]):
                        plan.is_valid = False
                        plan.error_reason = f"Encoder {strategy['video_codec']} is not available in the bundled FFmpeg."
                        return plan
                    args += ["-c:v", strategy["video_codec"]]
                elif not media.main_video and strategy["video_codec"]:
                    # No video in source — skip video codec
                    pass

                if target.kind == "audio":
                    args += ["-vn"]
                elif target.kind in {"image", "animated_image"}:
                    args += ["-an"]

                # Audio streams
                if media.main_audio and strategy["audio_codec"]:
                    if not self.registry.has_encoder(strategy["audio_codec"]):
                        plan.is_valid = False
                        plan.error_reason = f"Encoder {strategy['audio_codec']} is not available in the bundled FFmpeg."
                        return plan
                    args += ["-c:a", strategy["audio_codec"]]
                elif not media.main_audio and target.kind == "video":
                    args += ["-an"]  # No audio in source

                # Extra codec-specific args
                args += strategy.get("extra", [])
                args.append(output_path)
                plan.args = args

        return plan

    def plan_compress(self, media, output_path: str, quality: str = "balanced",
                      target_size_mb: Optional[float] = None) -> OperationPlan:
        """Plan a compression operation."""
        plan = OperationPlan()

        if not media.main_video:
            # Audio-only compression
            plan.args = ["-i", media.path, "-c:a", "libmp3lame", "-q:a", "4", output_path]
            return plan

        if target_size_mb and media.duration > 0:
            # Two-pass target size encoding
            target_bits = target_size_mb * 1024 * 1024 * 8
            video_bitrate = int((target_bits / media.duration) * 0.9)  # 90% for video
            audio_bitrate = 128000

            plan.strategy = "two_pass"
            plan.args = [
                "-i", media.path,
                "-c:v", "libx264",
                "-b:v", str(video_bitrate),
                "-c:a", "aac",
                "-b:a", str(audio_bitrate),
                output_path
            ]
            return plan

        strategy = COMPRESS_STRATEGIES.get(quality, COMPRESS_STRATEGIES["balanced"])
        plan.args = [
            "-i", media.path,
            "-c:v", "libx264",
            "-crf", str(strategy["crf"]),
            "-preset", strategy["preset"],
            "-c:a", "aac",
            "-b:a", strategy["audio_bitrate"],
            output_path
        ]
        return plan

    def plan_video_op(self, operation: str, media, output_path: str, **kwargs) -> OperationPlan:
        """Plan a video transformation operation."""
        plan = OperationPlan()

        if not media.main_video and operation not in ("metadata",):
            plan.is_valid = False
            plan.error_reason = f"The file does not contain a video stream. Cannot perform '{operation}'."
            return plan

        args = ["-i", media.path]

        if operation == "resize":
            width, height = kwargs.get("width", 0), kwargs.get("height", 0)
            args += ["-vf", f"scale={width}:{height}", "-c:a", "copy", output_path]

        elif operation == "crop":
            w, h = kwargs.get("width", 0), kwargs.get("height", 0)
            x, y = kwargs.get("x", 0), kwargs.get("y", 0)
            args += ["-vf", f"crop={w}:{h}:{x}:{y}", "-c:a", "copy", output_path]

        elif operation == "rotate":
            degrees = kwargs.get("degrees", 90)
            rotation_map = {90: "transpose=1", 180: "transpose=1,transpose=1",
                            270: "transpose=2", -90: "transpose=2"}
            vf = rotation_map.get(int(degrees), f"rotate={degrees}*PI/180")
            args += ["-vf", vf, "-c:a", "copy", output_path]

        elif operation == "fps":
            new_fps = kwargs.get("fps", 30)
            args += ["-vf", f"fps={new_fps}", "-c:a", "copy", output_path]

        elif operation == "speed":
            factor = kwargs.get("factor", 1.0)
            # Speed up or slow down: video filter + audio filter must match
            vf = f"setpts={1.0/factor:.4f}*PTS"
            af = f"atempo={factor:.4f}" if 0.5 <= factor <= 2.0 else (
                f"atempo=2.0,atempo={factor/2.0:.4f}" if factor > 2.0 else
                f"atempo=0.5,atempo={factor*2.0:.4f}"
            )
            args += ["-vf", vf, "-af", af, output_path]

        elif operation == "trim":
            start = kwargs.get("start", "00:00:00")
            end = kwargs.get("end")
            duration = kwargs.get("duration")
            args += ["-ss", str(start)]
            if end:
                args += ["-to", str(end)]
            elif duration:
                args += ["-t", str(duration)]
            args += ["-c", "copy", output_path]

        elif operation == "mute":
            args += ["-c:v", "copy", "-an", output_path]

        elif operation == "extract_audio":
            if not media.main_audio:
                plan.is_valid = False
                plan.error_reason = "The file does not contain an audio stream."
                return plan
            args += ["-vn", "-c:a", "copy", output_path]

        elif operation == "thumbnail":
            timestamp = kwargs.get("timestamp", "00:00:05")
            args += ["-ss", str(timestamp), "-vframes", "1", output_path]

        elif operation == "gif":
            start = kwargs.get("start", "00:00:00")
            dur = kwargs.get("duration", "5")
            fps = kwargs.get("fps", 10)
            width = kwargs.get("width", 480)
            args = [
                "-i", media.path,
                "-ss", str(start),
                "-t", str(dur),
                "-vf", f"fps={fps},scale={width}:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                output_path
            ]

        elif operation == "remux":
            args += ["-c", "copy", output_path]

        elif operation == "cut":
            # Alias for trim — removes a segment, keeps the rest
            start = kwargs.get("start", "00:00:00")
            end = kwargs.get("end")
            duration = kwargs.get("duration")
            args += ["-ss", str(start)]
            if end:
                args += ["-to", str(end)]
            elif duration:
                args += ["-t", str(duration)]
            args += ["-c", "copy", output_path]

        elif operation == "frame":
            # Extract a single frame as an image
            timestamp = kwargs.get("timestamp", "00:00:00")
            args += ["-ss", str(timestamp), "-vframes", "1", output_path]

        elif operation == "optimize":
            # Re-encode with quality settings optimized for size/quality balance
            preset = kwargs.get("preset", "medium")
            crf = kwargs.get("crf", 23)
            args += ["-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                     "-c:a", "aac", "-b:a", "128k", output_path]

        elif operation == "watermark":
            # Overlay an image watermark
            watermark_path = kwargs.get("watermark", "")
            position = kwargs.get("position", "bottomright")
            pos_map = {
                "topleft": "x=10:y=10",
                "topright": "x=W-w-10:y=10",
                "bottomleft": "x=10:y=H-h-10",
                "bottomright": "x=W-w-10:y=H-h-10",
                "center": "x=(W-w)/2:y=(H-h)/2",
            }
            overlay_pos = pos_map.get(position, pos_map["bottomright"])
            if not watermark_path:
                plan.is_valid = False
                plan.error_reason = "Watermark operation requires --watermark <image_path>"
                return plan
            # Build two-input command
            args = [
                "-i", media.path,
                "-i", watermark_path,
                "-filter_complex", f"[0:v][1:v]overlay={overlay_pos}",
                "-c:a", "copy",
                output_path,
            ]

        elif operation == "subtitle":
            # Burn-in subtitles from an external file
            subtitle_path = kwargs.get("subtitle", "")
            if not subtitle_path:
                plan.is_valid = False
                plan.error_reason = "Subtitle operation requires --subtitle <subtitle_file>"
                return plan
            escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")
            args += ["-vf", f"subtitles='{escaped}'", "-c:a", "copy", output_path]

        elif operation == "metadata":
            # Copy file while setting metadata tags
            title = kwargs.get("title", "")
            artist = kwargs.get("artist", "")
            album = kwargs.get("album", "")
            year = kwargs.get("year", "")
            args += ["-c", "copy"]
            if title:
                args += ["-metadata", f"title={title}"]
            if artist:
                args += ["-metadata", f"artist={artist}"]
            if album:
                args += ["-metadata", f"album={album}"]
            if year:
                args += ["-metadata", f"date={year}"]
            args += [output_path]

        else:
            plan.is_valid = False
            plan.error_reason = f"Unknown video operation: {operation}"
            return plan

        plan.args = args
        return plan


    def plan_audio_op(self, operation: str, media, output_path: str, **kwargs) -> OperationPlan:
        """Plan an audio transformation operation."""
        plan = OperationPlan()

        if not media.main_audio:
            plan.is_valid = False
            plan.error_reason = "The file does not contain an audio stream. Cannot perform this operation."
            return plan

        args = ["-i", media.path]

        if operation == "volume":
            # value can be "+20%" or "0.5" or "1.5"
            value = str(kwargs.get("value", "1.0"))
            if value.endswith("%"):
                pct = float(value.rstrip("%")) / 100
                vol_filter = f"volume={1.0 + pct:.4f}"
            else:
                vol_filter = f"volume={value}"
            args += ["-af", vol_filter, "-vn", output_path]

        elif operation == "normalize":
            args += ["-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-vn", output_path]

        elif operation == "fade":
            fade_type = kwargs.get("fade_type", "in")
            duration = kwargs.get("duration", 3.0)
            if fade_type == "in":
                args += ["-af", f"afade=t=in:st=0:d={duration}", "-vn", output_path]
            else:
                if media.duration > 0:
                    start = max(0, media.duration - float(duration))
                    args += ["-af", f"afade=t=out:st={start:.3f}:d={duration}", "-vn", output_path]
                else:
                    args += ["-af", f"afade=t=out:d={duration}", "-vn", output_path]

        elif operation == "trim":
            start = kwargs.get("start", "00:00:00")
            end = kwargs.get("end")
            duration = kwargs.get("duration")
            args += ["-ss", str(start)]
            if end:
                args += ["-to", str(end)]
            elif duration:
                args += ["-t", str(duration)]
            args += ["-vn", "-c:a", "copy", output_path]

        elif operation == "speed":
            factor = float(kwargs.get("factor", 1.0))
            atempo = f"atempo={factor:.4f}" if 0.5 <= factor <= 2.0 else (
                f"atempo=2.0,atempo={factor/2.0:.4f}" if factor > 2.0 else
                f"atempo=0.5,atempo={factor*2.0:.4f}"
            )
            args += ["-af", atempo, "-vn", output_path]

        else:
            plan.is_valid = False
            plan.error_reason = f"Unknown audio operation: {operation}"
            return plan

        plan.args = args
        return plan

    def _can_stream_copy(self, media, target_fmt: str) -> bool:
        """
        Returns True if all streams in the media can be stream-copied
        into the target container without re-encoding.
        """
        compat = STREAM_COPY_COMPATIBLE.get(target_fmt)
        if not compat:
            return False

        if media.main_video:
            if media.main_video.codec_name not in compat.get("video", []):
                return False

        if media.main_audio:
            if media.main_audio.codec_name not in compat.get("audio", []):
                return False

        return True
