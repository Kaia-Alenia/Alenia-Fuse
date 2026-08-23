import os
import re
import subprocess
import time
import datetime
import concurrent.futures
import hashlib
import json
import traceback
import threading
import shlex

# Import dependencies from porter.py
from alenia_porter import porter
import tempfile

VIDEO_SEMAPHORE = threading.Semaphore(max(1, os.cpu_count() // 3))
_CACHE_LOCK = threading.Lock()

_AMR_CODEC_AVAILABLE = None  # lazy check: None = not yet tested

def _check_amr_available(ffmpeg_path):
    """Return True only if amr_nb encoder is present in this FFmpeg build."""
    global _AMR_CODEC_AVAILABLE
    if _AMR_CODEC_AVAILABLE is None:
        try:
            r = subprocess.run([ffmpeg_path, "-encoders"],
                               capture_output=True, text=True, timeout=5)
            _AMR_CODEC_AVAILABLE = "amr_nb" in r.stdout
        except Exception:
            _AMR_CODEC_AVAILABLE = False
    return _AMR_CODEC_AVAILABLE

def stream_files(directory, base_directory, audio_exts, video_exts, image_exts, recursive=True, audio_enabled=True, video_enabled=True, image_enabled=True):
    try:
        for entry in os.scandir(directory):
            if entry.is_dir():
                if entry.name != "Alenia_Optimized" and recursive:
                    yield from stream_files(entry.path, base_directory, audio_exts, video_exts, image_exts, recursive=recursive, audio_enabled=audio_enabled, video_enabled=video_enabled, image_enabled=image_enabled)
            elif entry.is_file():
                name_lower = entry.name.lower()
                if audio_enabled and name_lower.endswith(audio_exts):
                    rel = os.path.relpath(entry.path, base_directory)
                    yield (entry.path, rel, "audio")
                elif video_enabled and name_lower.endswith(video_exts):
                    rel = os.path.relpath(entry.path, base_directory)
                    yield (entry.path, rel, "video")
                elif image_enabled and name_lower.endswith(image_exts):
                    rel = os.path.relpath(entry.path, base_directory)
                    yield (entry.path, rel, "image")
    except Exception:
        pass

def get_file_hash(file_path):
    hash_sha = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hash_sha.update(chunk)
        return hash_sha.hexdigest()
    except Exception:
        return None

def load_cache(output_dir):
    cache_path = os.path.join(output_dir, ".alenia_cache.json")
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_cache(output_dir, cache_dict):
    cache_path = os.path.join(output_dir, ".alenia_cache.json")
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_dict, f, indent=2)
    except: pass

def _test_encoder(ffmpeg_executable_path, encoder):
    try:
        test_cmd = [
            ffmpeg_executable_path, "-y",
            "-f", "lavfi", "-i", "color=c=black:s=16x16:d=0.1:r=1",
            "-frames:v", "1",
            "-c:v", encoder,
            "-f", "null", "-"
        ]
        result = subprocess.run(test_cmd, capture_output=True, timeout=10)
        return result.returncode == 0
    except Exception:
        return False

def get_best_video_encoder(ffmpeg_executable_path, target_codec):
    try:
        res = subprocess.run([ffmpeg_executable_path, "-encoders"], capture_output=True, text=True, timeout=5)
        encoders = res.stdout.lower()
        if target_codec == "mp4":
            for hw_encoder in ("h264_nvenc", "h264_qsv", "h264_amf"):
                if hw_encoder in encoders and _test_encoder(ffmpeg_executable_path, hw_encoder):
                    return hw_encoder
            return "libx264"
        elif target_codec == "webm":
            for hw_encoder in ("vp9_nvenc", "vp9_qsv"):
                if hw_encoder in encoders and _test_encoder(ffmpeg_executable_path, hw_encoder):
                    return hw_encoder
            return "libvpx-vp9"
    except Exception:
        pass
    return "libx264" if target_codec == "mp4" else "libvpx-vp9"

def process_single_file_top_level(file_info, target_audio_format, target_video_format, target_image_format, audio_output_directory, video_output_directory, image_output_directory, ffmpeg_executable_path, subprocess_creation_flags, preserve_structure=False, audio_bitrate="192k", video_crf="23", video_preset="veryfast", image_quality="80", safe_mode=False, cache_dict=None, force_overwrite=False, video_extra_args="", audio_extra_args="", image_extra_args="", existing_files_cache=None):
    absolute_path, relative_path, media_type = file_info
    base_name = os.path.splitext(os.path.basename(relative_path))[0]
    orig_ext = os.path.splitext(os.path.basename(absolute_path))[1].lstrip('.').lower()
    cleaned_base_name = re.sub(r'[^a-zA-Z0-9_]', '_', base_name).lower()
    # No longer appending original extension to avoid file_mp3.ogg filenames
    output_file_name = f"{cleaned_base_name}.tmp"
    
    target_audio_format = target_audio_format.lower()
    target_video_format = target_video_format.lower()
    target_image_format = target_image_format.lower()
    
    if cache_dict is None:
        cache_dict = {}

    orig_size = os.path.getsize(absolute_path)
    file_hash = get_file_hash(absolute_path)
    
    def _ensure_dir(path):
        try:
            os.makedirs(path, exist_ok=True)
        except Exception:
            pass

    if media_type == "video":
        ext_map = {"asf_stream": "asf", "yuv4mpegpipe": "y4m"}
        actual_ext = ext_map.get(target_video_format, target_video_format)
        output_file_name = f"{cleaned_base_name}.{actual_ext}"
        if preserve_structure:
            parts = relative_path.replace('\\', '/').split('/')
            if len(parts) > 1 and parts[0].lower() in ("video", "videos"):
                rel_subdir = os.path.dirname("/".join(parts[1:]))
            else:
                rel_subdir = os.path.dirname(relative_path)
            dest_dir = os.path.join(video_output_directory, rel_subdir) if rel_subdir else video_output_directory
        else:
            dest_dir = video_output_directory
    elif media_type == "image":
        output_file_name = f"{cleaned_base_name}.{'jpg' if target_image_format in ('jpg', 'jpeg') else target_image_format}"
        if preserve_structure:
            parts = relative_path.replace('\\', '/').split('/')
            if len(parts) > 1 and parts[0].lower() in ("image", "images", "imagen", "imagenes", "img", "imgen"):
                rel_subdir = os.path.dirname("/".join(parts[1:]))
            else:
                rel_subdir = os.path.dirname(relative_path)
            dest_dir = os.path.join(image_output_directory, rel_subdir) if rel_subdir else image_output_directory
        else:
            dest_dir = image_output_directory
    else:
        actual_ext = "m4a" if target_audio_format == "alac" else target_audio_format
        output_file_name = f"{cleaned_base_name}.{actual_ext}"
        if preserve_structure:
            parts = relative_path.replace('\\', '/').split('/')
            if len(parts) > 1 and parts[0].lower() in ("audio", "audios", "sound", "sounds", "sonido", "sonidos", "audio"):
                rel_subdir = os.path.dirname("/".join(parts[1:]))
            else:
                rel_subdir = os.path.dirname(relative_path)
            dest_dir = os.path.join(audio_output_directory, rel_subdir) if rel_subdir else audio_output_directory
        else:
            dest_dir = audio_output_directory

    _ensure_dir(dest_dir)
    output_file_path = os.path.join(dest_dir, output_file_name)

    # --- Smart deduplication logic ---
    # Scan dest_dir for any existing file with the same cleaned base name (regardless of extension)
    # Skip this entirely if force_overwrite is True (e.g. user applied a custom formula)
    if not force_overwrite:
        existing_same_base = None
        if existing_files_cache is not None:
            norm_dest = os.path.normpath(dest_dir)
            with _CACHE_LOCK:
                if norm_dest not in existing_files_cache:
                    existing_files_cache[norm_dest] = {}
                    if os.path.isdir(dest_dir):
                        for existing_entry in os.scandir(dest_dir):
                            if existing_entry.is_file():
                                existing_files_cache[norm_dest][os.path.splitext(existing_entry.name)[0].lower()] = existing_entry.path
            existing_same_base = existing_files_cache[norm_dest].get(cleaned_base_name)
        else:
            if os.path.isdir(dest_dir):
                for existing_entry in os.scandir(dest_dir):
                    if not existing_entry.is_file():
                        continue
                    existing_base = os.path.splitext(existing_entry.name)[0].lower()
                    if existing_base == cleaned_base_name:
                        existing_same_base = existing_entry.path
                        break

        if existing_same_base is not None:
            if existing_same_base.lower() == output_file_path.lower():
                if os.path.getsize(existing_same_base) > 0:
                    cached_hash = cache_dict.get(relative_path) if cache_dict else None
                    if cached_hash and cached_hash == file_hash:
                        return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, os.path.getsize(existing_same_base), True, None, file_hash, True)
                else:
                    try:
                        os.remove(existing_same_base)
                    except Exception:
                        pass
            else:
                try:
                    os.remove(existing_same_base)
                except Exception:
                    pass

    # Special handling for PDF image conversion using Pillow (FFmpeg lacks PDF muxer)
    if media_type == "image" and target_image_format == "pdf":
        try:
            from PIL import Image
            with Image.open(absolute_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img.save(output_file_path, "PDF", resolution=100.0)
            final_size = os.path.getsize(output_file_path)
            return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, final_size, True, None, file_hash, False)
        except Exception as e:
            error_details = str(e)
            porter.log_error_to_file(f"PIL PDF generation failed for {absolute_path}: {error_details}")
            return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, 0, False, error_details, file_hash, False)

    def get_safe_audio_bitrate(requested_bitrate, is_opus):
        if not is_opus: return str(requested_bitrate)
        try:
            val_str = str(requested_bitrate).lower().replace("k", "").strip()
            if int(val_str) > 256:
                return "256k"
        except: pass
        return str(requested_bitrate)

    ffmpeg_command = []

    if media_type == "video":
        encoder_map = {
            "mp4": "libx264", "mkv": "libx264", "avi": "libx264",
            "mov": "libx264", "m4v": "libx264", "flv": "libx264",
            "ogv": "libtheora", "ts": "libx264", "3gp": "libx264",
            "wmv": "wmv2", "mpeg": "mpeg2video", "mpg": "mpeg2video", "gif": "gif",
            "webm": "libvpx-vp9"
        }
        encoder = encoder_map.get(target_video_format, None)
        if target_video_format in ("mp4", "webm"):
            if safe_mode:
                encoder = "libx264" if target_video_format == "mp4" else "libvpx-vp9"
            else:
                encoder = get_best_video_encoder(ffmpeg_executable_path, "mp4" if target_video_format == "mp4" else "webm")
            
        if encoder == "gif":
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-filter_complex", "fps=15,scale='min(iw,640)':-2:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0", "-an", "-threads", "1", output_file_path
            ]
        elif encoder in ("wmv2", "mpeg4", "mpeg2video"):
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-c:v", encoder, "-q:v", "2",
                "-c:a", "wmav2" if encoder == "wmv2" else "mp3", "-b:a", str(audio_bitrate),
                "-threads", "1", output_file_path
            ]
            if encoder == "mpeg2video":
                # Insert -r 30 before -threads
                idx = ffmpeg_command.index("-threads")
                ffmpeg_command.insert(idx, "-r")
                ffmpeg_command.insert(idx + 1, "30")
        elif encoder == "libx264" or (encoder and ("nvenc" in encoder or "qsv" in encoder or "amf" in encoder)):
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-c:v", encoder, "-crf", str(video_crf), "-preset", video_preset,
                "-c:a", "aac", "-b:a", str(audio_bitrate),
                "-threads", "1", output_file_path
            ]
        elif encoder == "libvpx-vp9" or (encoder and ("vp9" in encoder)):
            vp9_preset_map = {
                "ultrafast": ("8", "realtime"), "superfast": ("6", "realtime"), "veryfast": ("4", "realtime"),
                "faster": ("4", "good"), "fast": ("3", "good"), "medium": ("1", "good"), "slow": ("0", "good")
            }
            cpu_used_val, deadline_val = vp9_preset_map.get(video_preset, ("0", "good"))
            
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-c:v", encoder, "-crf", str(video_crf), "-b:v", "0",
                "-cpu-used", cpu_used_val, "-deadline", deadline_val, "-row-mt", "1",
                "-c:a", "libopus", "-b:a", get_safe_audio_bitrate(audio_bitrate, True),
                "-threads", "1", output_file_path
            ]
        elif encoder == "libtheora":
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-c:v", "libtheora", "-q:v", "7",
                "-c:a", "libvorbis", "-b:a", str(audio_bitrate),
                "-threads", "1", output_file_path
            ]
        elif encoder:
            # Generic fallback with explicit codec
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-c:v", encoder, "-q:v", "2",
                "-b:a", str(audio_bitrate),
                "-threads", "1", output_file_path
            ]
        else:
            # No encoder known — let FFmpeg decide (may fail for exotic formats)
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-q:v", "2",
                "-b:a", str(audio_bitrate),
                "-threads", "1", output_file_path
            ]
            
    elif media_type == "image":
        if target_image_format in ("jpg", "jpeg"):
            try:
                q = int(image_quality)
                qv = max(2, min(31, int(31 - (q / 100.0) * 29)))
            except Exception:
                qv = 4
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-q:v", str(qv), "-threads", "1", output_file_path
            ]
        elif target_image_format == "ico":
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-vf", "scale='min(256,iw)':'min(256,ih)':force_original_aspect_ratio=decrease,format=rgba",
                "-threads", "1", output_file_path
            ]
        elif target_image_format in ("png", "bmp", "tiff", "tga"):
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-threads", "1", output_file_path
            ]
        elif target_image_format == "gif":
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-filter_complex", "scale='if(gt(iw,480),480,iw)':-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0", "-threads", "1", output_file_path
            ]
        elif target_image_format == "webp":
            try:
                wq = int(image_quality)
                wq = max(0, min(100, wq))
            except Exception:
                wq = 80
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-c:v", "libwebp", "-q:v", str(wq),
                "-threads", "1", output_file_path
            ]
        else:
            # Generic fallback for unknown image formats
            ffmpeg_command = [
                ffmpeg_executable_path, "-y", "-i", absolute_path,
                "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
                "-threads", "1", output_file_path
            ]
    else:
        codec = {
            "ogg": "libvorbis", "mp3": "libmp3lame", "flac": "flac",
            "wav": "pcm_s16le", "aac": "aac", "m4a": "aac",
            "wma": "wmav2", "alac": "alac", "aiff": "pcm_s16be",
            "wv": "wavpack", "au": "pcm_s16be", "amr": "amr_nb",
            "ac3": "ac3", "dts": "dca", "caf": "pcm_s16le",
            "opus": "libopus"
        }.get(target_audio_format, "libopus")
        ffmpeg_command = [
            ffmpeg_executable_path, "-y", "-i", absolute_path,
            "-map_metadata", "-1", "-metadata", "software=Optimized in Alenia Porter",
            "-vn",
            "-c:a", codec, "-threads", "1"
        ]
        if codec == "flac":
            ffmpeg_command.extend(["-sample_fmt", "s16"])
        elif codec == "amr_nb":
            if not _check_amr_available(ffmpeg_executable_path):
                return (
                    relative_path, media_type, cleaned_base_name, output_file_name,
                    orig_size, 0, False,
                    "AMR output requires the amr_nb encoder, which is not available in "
                    "this FFmpeg build. On Ubuntu/Debian install libavcodec-extra and "
                    "rebuild, or replace the embedded FFmpeg with a static build that "
                    "includes libopencore-amrnb.",
                    file_hash, False
                )
            ffmpeg_command.extend(["-ar", "8000", "-ac", "1", "-b:a", "12.2k"])
        elif codec not in ("pcm_s16le", "alac"):
            ffmpeg_command.extend(["-b:a", get_safe_audio_bitrate(audio_bitrate, codec == "libopus")])
            
        if codec in ("dca", "aac"):
            ffmpeg_command.extend(["-strict", "-2"])
            
        ffmpeg_command.append(output_file_path)

    if safe_mode and media_type != "audio" and not (media_type == "video" and target_video_format == "gif"):
        ffmpeg_command.insert(1, "-hwaccel")
        ffmpeg_command.insert(2, "none")

    extra_args_str = ""
    if media_type == "video":
        extra_args_str = video_extra_args
    elif media_type == "audio":
        extra_args_str = audio_extra_args
    elif media_type == "image":
        extra_args_str = image_extra_args
        
    if extra_args_str:
        try:
            extra_args = shlex.split(extra_args_str)
            if output_file_path in ffmpeg_command:
                idx = ffmpeg_command.index(output_file_path)
                ffmpeg_command = ffmpeg_command[:idx] + extra_args + ffmpeg_command[idx:]
            else:
                ffmpeg_command.extend(extra_args)
        except Exception:
            pass

    try:
        cancel_flag_path = porter.get_cancel_flag_path()
        if os.path.exists(cancel_flag_path):
            return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, 0, False, "Cancelled by user", file_hash, False)

        acquired_semaphore = False
        if media_type == "video":
            VIDEO_SEMAPHORE.acquire()
            acquired_semaphore = True

        try:
            with tempfile.TemporaryFile() as stderr_file:
                process_handle = subprocess.Popen(
                    ffmpeg_command,
                    stdout=subprocess.DEVNULL,
                    stderr=stderr_file,
                    creationflags=subprocess_creation_flags
                )
                
                while process_handle.poll() is None:
                    if os.path.exists(cancel_flag_path):
                        try: process_handle.kill()
                        except: pass
                        return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, 0, False, "Cancelled by user", file_hash, False)
                    time.sleep(0.5)

                stderr_file.seek(0)
                stderr_data = stderr_file.read()
        finally:
            if acquired_semaphore:
                VIDEO_SEMAPHORE.release()
        
        if process_handle.returncode != 0:
            error_details = stderr_data.decode('utf-8', errors='ignore')
            porter.log_error_to_file(f"FFmpeg failed with return code {process_handle.returncode} for file {absolute_path}")
            
            log_dir = os.path.dirname(porter.get_config_file_path())
            os.makedirs(log_dir, exist_ok=True)
            dump_file = os.path.join(log_dir, f"CRASH_DUMP_{int(time.time())}_{cleaned_base_name[:10]}.txt")
            with open(dump_file, "w", encoding="utf-8") as df:
                df.write(f"--- ALENIA PORTER CRASH DUMP ---\nTimestamp: {datetime.datetime.now()}\nFile: {absolute_path}\nCommand: {' '.join(ffmpeg_command)}\nSafe Mode: {safe_mode}\n--- FFmpeg Stderr ---\n{error_details}")

            if not safe_mode and media_type == "video":
                return process_single_file_top_level(file_info, target_audio_format, target_video_format, target_image_format, audio_output_directory, video_output_directory, image_output_directory, ffmpeg_executable_path, subprocess_creation_flags, preserve_structure, audio_bitrate, video_crf, video_preset, image_quality, safe_mode=True, cache_dict=cache_dict, force_overwrite=force_overwrite, video_extra_args=video_extra_args, audio_extra_args=audio_extra_args, image_extra_args=image_extra_args)

            return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, 0, False, f"FFmpeg error. Logged to {dump_file}", file_hash, False)

        final_size = os.path.getsize(output_file_path) if os.path.exists(output_file_path) else 0
        if final_size == 0:
            error_msg = f"FFmpeg produced an empty file (0 bytes) for {absolute_path}"
            porter.log_error_to_file(error_msg)
            if not safe_mode and media_type == "video":
                return process_single_file_top_level(file_info, target_audio_format, target_video_format, target_image_format, audio_output_directory, video_output_directory, image_output_directory, ffmpeg_executable_path, subprocess_creation_flags, preserve_structure, audio_bitrate, video_crf, video_preset, image_quality, safe_mode=True, cache_dict=cache_dict, force_overwrite=force_overwrite, video_extra_args=video_extra_args, audio_extra_args=audio_extra_args, image_extra_args=image_extra_args)
            return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, 0, False, error_msg, file_hash, False)
        return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, final_size, True, None, file_hash, False)
    except Exception as e:
        porter.log_error_to_file(f"Exception processing file {absolute_path}: {str(e)}")
        return (relative_path, media_type, cleaned_base_name, output_file_name, orig_size, 0, False, str(e), file_hash, False)

def convert_media(input_directory, target_audio_format, target_video_format, target_image_format, recursive, preserve_structure, audio_bitrate, video_crf, video_preset, image_quality, audio_enabled, video_enabled, image_enabled, progress_update_callback, status_update_callback, completion_callback, error_callback, lang_code="es", headless=False, safe_mode=False, input_files=None, force_overwrite=False, video_extra_args="", audio_extra_args="", image_extra_args=""):
    start_time = time.time()
    try:
        cancel_flag_path = porter.get_cancel_flag_path()
        if os.path.exists(cancel_flag_path):
            try: os.remove(cancel_flag_path)
            except: pass

        audio_extensions = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus", ".aac", ".wma", ".aiff", ".aif", ".alac", ".amr", ".mid", ".midi", ".mp2", ".mpga", ".au", ".snd", ".ra", ".rm")
        video_extensions = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".m2v", ".3gp", ".3g2", ".ts", ".m2ts", ".vob", ".ogv", ".asf", ".divx", ".gif")
        image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".webp", ".tiff", ".ico", ".pdf", ".avif", ".apng")
        
        if input_files and len(input_files) > 0:
            file_list = []
            for file_path in input_files:
                if not os.path.isfile(file_path): continue
                name_lower = os.path.basename(file_path).lower()
                rel = os.path.basename(file_path)
                if audio_enabled and name_lower.endswith(audio_extensions): file_list.append((file_path, rel, "audio"))
                elif video_enabled and name_lower.endswith(video_extensions): file_list.append((file_path, rel, "video"))
                elif image_enabled and name_lower.endswith(image_extensions): file_list.append((file_path, rel, "image"))
            
            if input_directory is None or not os.path.isdir(str(input_directory)):
                input_directory = os.path.dirname(os.path.abspath(input_files[0]))
        else:
            file_list = list(stream_files(input_directory, input_directory, audio_extensions, video_extensions, image_extensions, recursive=recursive, audio_enabled=audio_enabled, video_enabled=video_enabled, image_enabled=image_enabled))
            
        total_files_count = len(file_list)

        if total_files_count == 0:
            completion_callback(0, input_directory or "", 0, 0)
            return

        target_folder_name = "Alenia_Optimized"
        output_directory_path = os.path.join(str(input_directory), target_folder_name)
        audio_output_directory = os.path.join(output_directory_path, "audio")
        video_output_directory = os.path.join(output_directory_path, "video")
        image_output_directory = os.path.join(output_directory_path, "images")

        for _d in (output_directory_path,):
            try: os.makedirs(_d, exist_ok=True)
            except: pass

        cache_dict = load_cache(output_directory_path)
        new_cache = cache_dict.copy()

        ffmpeg_executable_path = porter.get_ffmpeg_path()
        subprocess_creation_flags = 0
        if os.name == "nt": subprocess_creation_flags = 0x08000000

        audio_count, video_count, image_count = 0, 0, 0
        total_original_size, total_final_size = 0, 0
        processed_files_count = 0
        
        existing_files_cache = {}

        max_workers = max(1, os.cpu_count() - 1)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(
                    process_single_file_top_level,
                    file_info, target_audio_format, target_video_format, target_image_format,
                    audio_output_directory, video_output_directory, image_output_directory,
                    ffmpeg_executable_path, subprocess_creation_flags, preserve_structure,
                    audio_bitrate, video_crf, video_preset, image_quality, safe_mode, cache_dict, force_overwrite,
                    video_extra_args, audio_extra_args, image_extra_args, existing_files_cache
                ): file_info for file_info in file_list
            }

            for future in concurrent.futures.as_completed(futures):
                relative_path, media_type, cleaned_base_name, output_file_name, orig_size, final_size, success, error_msg, file_hash, skipped = future.result()
                if success:
                    total_original_size += orig_size
                    total_final_size += final_size
                    if media_type == "video": video_count += 1
                    elif media_type == "image": image_count += 1
                    else: audio_count += 1
                    if file_hash:
                        new_cache[relative_path] = file_hash
                else:
                    if error_msg: porter.log_error_to_file(error_msg)

                processed_files_count += 1
                progress_update_callback(processed_files_count, total_files_count)

        save_cache(output_directory_path, new_cache)

        duration_seconds = time.time() - start_time
        if audio_count > 0: porter.update_telemetry_stats("audio", audio_count, duration_seconds, headless)
        if video_count > 0: porter.update_telemetry_stats("video", video_count, duration_seconds, headless)
        if image_count > 0: porter.update_telemetry_stats("image", image_count, duration_seconds, headless)

        completion_callback(processed_files_count, output_directory_path, total_original_size, total_final_size)

    except Exception as conversion_exception:
        exception_traceback = traceback.format_exc()
        porter.log_error_to_file(exception_traceback)
        try: porter.send_crash_report("CONVERSION_ERROR", str(conversion_exception), exception_traceback)
        except: pass
        error_callback(str(conversion_exception))
