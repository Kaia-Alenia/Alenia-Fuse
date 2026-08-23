__license__ = "GNU General Public License v3 (GPL v3)"
import os
import sys
import webview
import json
import threading
import glob
import base64
import urllib.parse

# Ensure the 'src' directory is in the path to allow 'alenia_porter' imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from alenia_porter import porter
from alenia_porter import updater
from alenia_porter.media_engine import convert_media, stream_files


def load_themes():
    themes_dict = {}
    with porter.resource_path(os.path.join("assets", "themes")) as themes_path:
        if os.path.exists(themes_path):
            for file in glob.glob(os.path.join(themes_path, "*.json")):
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        name = data.get("name", os.path.basename(file))
                        themes_dict[name] = data
                except Exception:
                    pass
    if not themes_dict:
        themes_dict["Default Theme"] = {
            "name": "Default Theme",
            "bg_main": "#1e1e1e",
            "fg_main": "#ffffff",
            "fg_dim": "#a3a3a3",
            "accent": "#8b5cf6",
            "accent_hover": "#a78bfa",
            "link": "#F96854",
            "success": "#4ade80",
            "error": "#f87171",
            "warning": "#fbbf24",
            "char_sprite": "assets/images/kaia_default.png"
        }
    return themes_dict

def image_to_base64(path):
    if not path: return None
    with porter.resource_path(path) as full_path:
        if not os.path.exists(full_path): return None
        try:
            with open(full_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                ext = path.split('.')[-1].lower()
                mime = "image/png"
                if ext in ["jpg", "jpeg"]: mime = "image/jpeg"
                elif ext == "gif": mime = "image/gif"
                return f"data:{mime};base64,{encoded_string}"
        except Exception:
            return None

class Api:
    CURRENT_VERSION = "v7.1"

    def __init__(self, window):
        self.window = window
        self.configuration_data = self.load_user_configuration()
        self.available_themes = load_themes()
        self.theme_names = list(self.available_themes.keys())
        
        self.appearance_mode = self.configuration_data.get("appearance_mode", "system")
        self.custom_light_theme = self.configuration_data.get("custom_light_theme", {
            "preset": "Default Theme",
            "bg_main": None,
            "fg_main": None,
            "accent": None
        })
        self.custom_dark_theme = self.configuration_data.get("custom_dark_theme", {
            "preset": "Default Theme",
            "bg_main": None,
            "fg_main": None,
            "accent": None
        })
            
        self.languages_dictionary = porter.load_locales()
        self.current_language_code = self.configuration_data.get("lang", "es")
        if self.current_language_code not in self.languages_dictionary:
            self.current_language_code = "en"

    def load_user_configuration(self):
        config_path = porter.get_config_file_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {}

    def save_user_configuration(self):
        config_path = porter.get_config_file_path()
        try:
            import json, os
            current_config = {}
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    current_config = json.load(f)
            current_config.update(self.configuration_data)
            self.configuration_data = current_config
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.configuration_data, f, indent=4)
        except: pass

    def get_initial_data(self):
        # Determine current theme preset name for legacy image fetching
        preset_name = self.custom_dark_theme["preset"] if self.appearance_mode == "dark" else self.custom_light_theme["preset"]
        if preset_name not in self.available_themes:
            preset_name = self.theme_names[0]
            
        theme_data = self.available_themes[preset_name]
        
        images = {
            "default": image_to_base64(theme_data.get("char_sprite", "assets/images/kaia_default.png")),
            "success": image_to_base64(theme_data.get("char_success", "assets/images/kaia_success.png")),
            "info": image_to_base64("assets/images/kaia_info.png"),
            "support": image_to_base64("assets/images/kaia_support.png")
        }
        
        return {
            "nickname": porter.get_local_nickname(),
            "uuid": porter.get_local_uuid(),
            "translations": self.languages_dictionary.get(self.current_language_code, {}),
            "theme": theme_data, # Legacy theme format for backward compatibility (temporarily)
            "appearance": {
                "mode": self.appearance_mode,
                "light": self.custom_light_theme,
                "dark": self.custom_dark_theme
            },
            "available_themes": self.available_themes,
            "images": images,
            "langCode": self.current_language_code,
            "languages": list(self.languages_dictionary.keys()),
            "is_first_run": porter.is_first_run()
        }

    def save_appearance_settings(self, settings):
        self.appearance_mode = settings.get("mode", self.appearance_mode)
        self.custom_light_theme = settings.get("light", self.custom_light_theme)
        self.custom_dark_theme = settings.get("dark", self.custom_dark_theme)
        
        self.configuration_data["appearance_mode"] = self.appearance_mode
        self.configuration_data["custom_light_theme"] = self.custom_light_theme
        self.configuration_data["custom_dark_theme"] = self.custom_dark_theme
        
        self.save_user_configuration()
        return self.get_initial_data()

    def mark_first_run_done(self):
        return porter.mark_first_run_done()

    def get_me_info(self):
        return {
            "uuid": porter.get_local_uuid(),
            "nickname": porter.get_local_nickname(),
            "telemetry_enabled": porter.get_telemetry_status()
        }

    def set_language(self, lang_code):
        if lang_code in self.languages_dictionary:
            self.current_language_code = lang_code
            self.configuration_data["lang"] = lang_code
            self.save_user_configuration()
        return self.get_initial_data()

    def select_files(self):
        file_types = (
            'Multimedia (*.mp4;*.webm;*.avi;*.mkv;*.mov;*.wmv;*.flv;*.m4v;*.ogv;*.3gp;*.mpeg;*.ts;*.divx;'
            '*.mp3;*.wav;*.flac;*.ogg;*.opus;*.m4a;*.aac;*.wma;*.aiff;*.amr;*.wv;*.ac3;*.dts;*.caf;'
            '*.jpg;*.jpeg;*.png;*.webp;*.gif;*.bmp;*.tiff;*.tga;*.ico;*.avif;*.apng;*.pdf)',
            'All files (*.*)'
        )

        file_paths = self.window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=file_types
        )
        if file_paths:
            return [{"path": f, "size": os.path.getsize(f)} for f in file_paths if os.path.exists(f)]
        return []

    def select_folder(self):
        folder_paths = self.window.create_file_dialog(
            webview.FileDialog.FOLDER,
            allow_multiple=False
        )
        if folder_paths and len(folder_paths) > 0:
            return folder_paths[0]
        return None

    def scan_directory(self, directory_path):
        audio_extensions = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus", ".aac", ".wma", ".aiff", ".aif", ".alac", ".amr", ".mid", ".midi", ".mp2", ".mpga", ".au", ".snd", ".ra", ".rm", ".wv", ".ac3", ".dts", ".caf")
        video_extensions = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".m2v", ".3gp", ".3g2", ".ts", ".m2ts", ".vob", ".ogv", ".asf", ".divx", ".gif")
        image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".webp", ".tiff", ".ico", ".pdf", ".avif", ".apng")
        
        audio_count = 0
        video_count = 0
        image_count = 0
        total_size = 0
        
        if os.path.exists(directory_path) and os.path.isdir(directory_path):
            file_list = list(stream_files(directory_path, directory_path, audio_extensions, video_extensions, image_extensions, recursive=True))
            for f_path, r_path, m_type in file_list:
                if m_type == "audio": audio_count += 1
                elif m_type == "video": video_count += 1
                elif m_type == "image": image_count += 1
                try:
                    total_size += os.path.getsize(f_path)
                except:
                    pass
                
        return {
            "audio": audio_count,
            "video": video_count,
            "image": image_count,
            "total_size": total_size
        }

    def get_file_sizes(self, paths):
        result = {}
        for p in paths:
            try:
                result[p] = os.path.getsize(p)
            except:
                result[p] = 0
        return result

    def resolve_dropped_paths(self, raw_uris):
        import urllib.parse
        audio_extensions = (".wav", ".mp3", ".flac", ".m4a", ".ogg", ".opus", ".aac", ".wma", ".aiff", ".aif", ".alac", ".amr", ".mid", ".midi", ".mp2", ".mpga", ".au", ".snd", ".ra", ".rm")
        video_extensions = (".mp4", ".mkv", ".webm", ".avi", ".mov", ".wmv", ".flv", ".m4v", ".mpg", ".mpeg", ".m2v", ".3gp", ".3g2", ".ts", ".m2ts", ".vob", ".ogv", ".asf", ".divx", ".gif")
        image_extensions = (".png", ".jpg", ".jpeg", ".bmp", ".tga", ".webp", ".tiff", ".ico", ".pdf", ".avif", ".apng")
        all_media_exts = audio_extensions + video_extensions + image_extensions

        resolved = []
        for raw in (raw_uris or []):
            raw = raw.strip()
            if not raw or raw.startswith("#"):
                continue
            path = raw
            try:
                if raw.startswith("file://"):
                    parsed = urllib.parse.urlparse(raw)
                    path = urllib.parse.unquote(parsed.path)
                    if os.name == "nt" and path.startswith("/") and len(path) > 2 and path[2] == ":":
                        path = path[1:]
                elif raw.startswith("file:"):
                    path = urllib.parse.unquote(raw[5:])
                    if path.startswith("//"):
                        path = path[2:]
                else:
                    path = urllib.parse.unquote(raw)
            except Exception:
                pass

            if not os.path.exists(path):
                continue

            if os.path.isdir(path):
                scan = self.scan_directory(path)
                total = scan["audio"] + scan["video"] + scan["image"]
                resolved.append({
                    "path": path,
                    "name": os.path.basename(path),
                    "isDirectory": True,
                    "size": scan["total_size"],
                    "mediaCount": total,
                    "audio": scan["audio"],
                    "video": scan["video"],
                    "image": scan["image"],
                    "mediaType": "video"
                })
            elif os.path.isfile(path):
                name_lower = os.path.basename(path).lower()
                if not name_lower.endswith(all_media_exts):
                    continue
                if name_lower.endswith(video_extensions):
                    mtype = "video"
                elif name_lower.endswith(audio_extensions):
                    mtype = "audio"
                else:
                    mtype = "image"
                try:
                    size = os.path.getsize(path)
                except Exception:
                    size = 0
                resolved.append({
                    "path": path,
                    "name": os.path.basename(path),
                    "isDirectory": False,
                    "size": size,
                    "mediaType": mtype
                })
        return resolved

    def get_telemetry_status(self):
        return porter.get_telemetry_status()

    def set_telemetry_status(self, value):
        self.configuration_data["telemetry_enabled"] = value
        self.save_user_configuration()
        porter.set_telemetry_status(value)
        return value

    def set_nickname(self, nickname):
        porter.set_local_nickname(nickname)
        return nickname

    def check_update(self):
        has_update, new_ver, dl_url = updater.check_for_updates(self.CURRENT_VERSION)
        return {
            "has_update": has_update,
            "new_ver": new_ver,
            "dl_url": dl_url
        }

    def open_in_browser(self, url):
        import webbrowser
        try:
            webbrowser.open(url)
            return True
        except:
            return False

    def download_update(self, dl_url):
        def _do_update():
            last_percent = -1
            def progress_cb(percent):
                nonlocal last_percent
                if percent != last_percent:
                    last_percent = percent
                    try:
                        self.window.evaluate_js(f'window.updateProgress({int(percent)})')
                    except Exception:
                        pass

            def ready_cb():
                try:
                    self.window.evaluate_js('window.updateReadyToRestart()')
                except Exception:
                    pass

            try:
                updater.download_and_apply_update(dl_url, progress_cb, ready_cb)
            except Exception as e:
                try:
                    self.window.evaluate_js(f'window.updateFailed({json.dumps(str(e))})')
                except Exception:
                    pass

        thread = threading.Thread(target=_do_update, daemon=True)
        thread.start()
        return True

    def explain_command(self, command):
        """Genera una explicación local y determinista de un comando FFmpeg."""
        explanation = "Comando de FFmpeg para procesar medios:\\n\\n"
        if "-i " in command:
            explanation += "- Define el archivo de entrada.\\n"
        if "-vcodec copy" in command or "-c:v copy" in command:
            explanation += "- Copia el video original sin recodificar (rápido).\\n"
        elif "-vcodec libx264" in command or "-c:v libx264" in command:
            explanation += "- Codifica el video en formato H.264 (alta compatibilidad).\\n"
        elif "-vcodec libx265" in command or "-c:v libx265" in command:
            explanation += "- Codifica el video en formato H.265/HEVC (mejor compresión).\\n"
        
        if "-acodec copy" in command or "-c:a copy" in command:
            explanation += "- Copia el audio original sin recodificar.\\n"
        elif "-acodec aac" in command or "-c:a aac" in command:
            explanation += "- Codifica el audio en formato AAC.\\n"
        
        if "-crf" in command:
            explanation += "- Aplica un factor de tasa constante (CRF) para controlar la calidad de compresión.\\n"
        
        if "-vf scale=" in command:
            explanation += "- Escala la resolución del video.\\n"
            
        if "-hwaccel" in command or "h264_nvenc" in command or "hevc_nvenc" in command:
            explanation += "- Utiliza aceleración por hardware de la tarjeta de video (muy rápido).\\n"
            
        explanation += "\\nEste comando optimiza y convierte tus archivos según las preferencias seleccionadas."
        return explanation


    def start_conversion(self, params):
        cancel_flag_path = porter.get_cancel_flag_path()
        if os.path.exists(cancel_flag_path):
            try: os.remove(cancel_flag_path)
            except: pass

        thread = threading.Thread(target=self._run_conversion, args=(params,))
        thread.start()
        return True

    def _run_conversion(self, params):
        print(f"[Backend] Params recibidos: {params}")
        input_directory = params.get("inputDirectory")
        input_files = []
        if not input_directory:
            raw_files = params.get("files", [])
            raw_input = params.get("input")
            if raw_files:
                input_files = [f for f in raw_files if f]
            elif raw_input:
                input_files = [raw_input]

        if not input_files and not input_directory:
            self.window.evaluate_js('window.conversionComplete(false)')
            return

        is_folder_mode = bool(input_directory)
        media_type = params.get("mediaType", "video")

        video_fmt = params.get("videoFormat") or params.get("format", "mp4") or "mp4"
        audio_fmt = params.get("audioFormat") or (params.get("format", "mp3") if media_type == "audio" else "mp3") or "mp3"
        image_fmt = params.get("imageFormat") or (params.get("format", "jpg") if media_type == "image" else "jpg") or "jpg"

        audio_enabled = True
        video_enabled = True
        image_enabled = True

        audio_bitrate = f"{params.get('audioBitrate', 192)}k"
        video_crf = str(params.get("quality", 23))
        video_preset = params.get("preset", "fast")
        image_quality = str(params.get("quality", 80))

        # If the user used a custom formula -> force reconversion even if the file exists
        custom_args = params.get("customArgs", "") or ""
        force_overwrite = bool(custom_args.strip())

        def progress_cb(current=0, total=0, file_name="", *args, **kwargs):
            percent = int((current / total) * 100) if total > 0 else 0
            self._update_progress(percent)

        def status_cb(msg="", *args, **kwargs):
            pass

        def completion_cb(processed=0, out_dir="", orig_size=0, final_size=0, *args, **kwargs):
            self._update_progress(100)
            out_dir_safe = json.dumps(str(out_dir))
            self.window.evaluate_js(f'window.conversionComplete(true, {orig_size}, {final_size}, {out_dir_safe})')

        def error_cb(msg="", *args, **kwargs):
            self.window.evaluate_js('window.conversionComplete(false)')

        try:
            self._update_progress(5)
            convert_media(
                input_directory=input_directory,
                target_audio_format=audio_fmt,
                target_video_format=video_fmt,
                target_image_format=image_fmt,
                recursive=params.get("recursive", True),
                preserve_structure=True,
                audio_bitrate=audio_bitrate,
                video_crf=video_crf,
                video_preset=video_preset,
                image_quality=image_quality,
                audio_enabled=audio_enabled,
                video_enabled=video_enabled,
                image_enabled=image_enabled,
                progress_update_callback=progress_cb,
                status_update_callback=status_cb,
                completion_callback=completion_cb,
                error_callback=error_cb,
                lang_code=self.current_language_code,
                headless=True,
                safe_mode=False,
                input_files=input_files,
                force_overwrite=force_overwrite
            )
        except Exception as e:
            print(f"Error during conversion: {e}")
            self.window.evaluate_js('window.conversionComplete(false)')

    def cancel_conversion(self):
        cancel_flag_path = porter.get_cancel_flag_path()
        try:
            with open(cancel_flag_path, 'w') as f:
                f.write('1')
        except:
            pass
        return True

    def _update_progress(self, percent):
        self.window.evaluate_js(f'window.updateProgress({percent})')

from pathlib import Path
from datetime import datetime
import traceback

def _main_inner():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    if getattr(sys, 'frozen', False) or '__compiled__' in globals():
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))

    html_path = os.path.join(base_dir, 'legacy', 'ide', 'frontend', 'dist', 'index.html')

    if not os.path.exists(html_path):
        print("Error: No se encontró el build de React. Ejecuta 'npm run build' en la carpeta legacy/ide/frontend.")
        sys.exit(1)

    api = Api(None) # Initialize api without window first

    window = webview.create_window(
        'Alenia Porter',
        url=Path(html_path).as_uri(),
        width=480,
        height=860,
        min_size=(400, 700),
        background_color='#000000',
        resizable=True,
        frameless=False,
        js_api=api
    )
    
    api.window = window

    def on_loaded():
        print("[DND] on_loaded")
        if sys.platform.startswith("linux"):
            # TEMPORARILY DISABLED: native GTK hook for D&D causes total system mouse freeze under WebKitGTK. Reverting to fallback selector.
            print("[DND] Native GTK drag-and-drop deshabilitado en Linux (ver comentario en código). Usa los botones de selección de archivos/carpeta.")
            return
        try:
            from webview.dom import DOMEventHandler
            def on_drop(e):
                raw_paths = []
                try:
                    files = e.get('dataTransfer', {}).get('files', [])
                    for f in files:
                        p = f.get('pywebviewFullPath') or f.get('path')
                        if p:
                            raw_paths.append(p)
                except Exception as ex:
                    print(f"[DND] Error reading DOM drop files: {ex}")
                if raw_paths:
                    resolved = api.resolve_dropped_paths(raw_paths)
                    if resolved:
                        try:
                            window.evaluate_js(f"window.handleNativeDropResolved({json.dumps(resolved)})")
                        except Exception as js_err:
                            print(f"[DND] Error sending resolved drop to JS: {js_err}")
            handler = DOMEventHandler(on_drop, prevent_default=True, stop_propagation=True)
            window.dom.document.events.drop += handler
        except Exception as e:
            print(f"[DND] Error connecting DOM drop handler: {e}")
            try:
                def on_drop_fallback(e):
                    pass
                window.dom.document.events.drop += on_drop_fallback
            except Exception:
                pass

    window.events.loaded += on_loaded

    webview.start(debug=False, http_server=True)

def _handle_fatal_crash():
    crash_text = traceback.format_exc()
    # Write to crash.log
    log_dir = os.path.join(
        os.getenv("LOCALAPPDATA", os.path.expanduser("~")),
        "AleniaStudios", "AleniaPorter"
    )
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "crash.log")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"\n--- {datetime.now().isoformat()} ---\n{crash_text}\n")
    # Show native dialog
    try:
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                0,
                f"Alenia Porter crashed.\nDetails saved to:\n{log_path}",
                "Alenia Porter - Fatal Error",
                0x10  # MB_ICONERROR
            )
        else:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk(); root.withdraw()
            messagebox.showerror("Alenia Porter", f"Crash log: {log_path}")
    except Exception:
        pass

def main():
    try:
        _main_inner()
    except Exception:
        _handle_fatal_crash()

if __name__ == '__main__':
    main()