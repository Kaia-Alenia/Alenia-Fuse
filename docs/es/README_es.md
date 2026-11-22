# Alenia Fuse

> **Esta es la versión mejorada de Alenia Porter** — reescrita completamente en Python puro, con una API limpia, soporte multiplataforma y publicación en PyPI.
> Alenia Fuse se llamaba anteriormente **Alenia-Porter**. El proyecto fue rebrandeado en la versión 2.0; las instalaciones nuevas usan el paquete `alenia-fuse` y el comando `fuse`.

**Herramienta multimedia profesional — biblioteca Python + CLI interactiva**

Alenia Fuse convierte, edita, comprime e inspecciona audio, video e imágenes. Usa FFmpeg: si ya está instalado en el sistema lo usa, y si no, `fuse setup` descarga un build verificado para tu plataforma a la caché del usuario la primera vez que se necesita.

---

## Inicio rápido

```
pip install alenia-fuse
fuse setup
fuse
```

Eso abre la CLI interactiva. Escribe `/help` para ver todos los comandos.

---

## CLI interactiva

```
  ◈ Alenia Fuse 2.0.7
  Multimedia toolkit
  Type / for commands · Tab for suggestions
fuse ❯
```

### Comandos de sesión

| Comando | Descripción |
| --- | --- |
| `/` | Muestra todos los comandos disponibles |
| `/help` | Ayuda general |
| `/help <comando>` | Ayuda de un comando concreto |
| `/convert` | Convierte un archivo a otro formato |
| `/compress` | Reduce el tamaño de un archivo |
| `/optimize` | Optimiza un archivo |
| `/info` | Inspecciona un archivo |
| `/formats` | Muestra los formatos de salida válidos |
| `/formats <archivo>` | Muestra los destinos válidos para ese archivo |
| `/remux` | Cambia el contenedor sin re-codificar |
| `/lang <código>` | Cambia el idioma de la interfaz (sin reiniciar) |
| `/clear` | Limpia la pantalla |
| `/history clear` | Borra el historial de comandos |
| `/exit` | Sale de Fuse |

### Comandos de shell

```
fuse                        # Abre la sesión interactiva
fuse -h                     # Ayuda
fuse --version              # Versión
fuse setup                  # Descarga y verifica FFmpeg si falta
fuse formats                # Lista todos los formatos de salida
fuse formats video          # Lista formatos de video
fuse formats audio          # Lista formatos de audio
fuse formats image          # Lista formatos de imagen
fuse convert in.mp4 out.webm
```

---

## API Python

```
from fuse import Video, Audio, Image, Media

# Convertir video
result = Video("movie.mp4").convert("webm").output("movie.webm").run()
print(result.success, result.elapsed_seconds)

# Convertir audio
Audio("song.wav").convert("flac").output("song.flac").run()

# Convertir imagen (con Pillow si no hay FFmpeg)
Image("photo.png").convert("webp").output("photo.webp").run()

# Inspeccionar un archivo
info = Media.inspect("movie.mp4")
print(info.duration, info.streams)
```

`run()` devuelve un `OperationResult` con `success`, `operation`, `input_path`, `output_path`, `media`, `elapsed_seconds`, `warnings` y `error`. La API es silenciosa: no imprime nada; los errores se devuelven en `OperationResult` o se lanzan como excepciones.

---

## Formatos de salida

### Video

| Formato | Extensión | Notas |
| --- | --- | --- |
| MP4 | `.mp4` | H.264 / H.265 / AV1 |
| MKV | `.mkv` | Contenedor universal |
| WebM | `.webm` | VP9 / Opus |
| MOV | `.mov` | QuickTime |
| AVI | `.avi` | Legado — soporte limitado |
| MPEG-TS | `.ts` | Transport stream |
| FLV | `.flv` | Legado Flash |

### Audio

| Formato | Extensión | Notas |
| --- | --- | --- |
| MP3 | `.mp3` | libmp3lame |
| FLAC | `.flac` | Sin pérdida |
| AAC | `.aac` `.m4a` | Moderno con pérdida |
| Opus | `.opus` | Mejor relación calidad/tamaño |
| OGG Vorbis | `.ogg` | Formato abierto |
| WAV | `.wav` | PCM sin comprimir |
| WMA | `.wma` | Windows Media Audio |

### Imagen

| Formato | Extensión | Notas |
| --- | --- | --- |
| WebP | `.webp` | Moderno — recomendado |
| JPEG | `.jpg` | Universal |
| PNG | `.png` | Sin pérdida |
| AVIF | `.avif` | Requiere libaom-av1 (solo con FFmpeg) |
| BMP | `.bmp` | Sin comprimir |
| TIFF | `.tiff` | Alta calidad |

### Animado

| Formato | Extensión | Notas |
| --- | --- | --- |
| GIF | `.gif` | Animado universal |
| WebP animado | `.webp` | Animado moderno |

> Fuse solo ofrece los formatos que el FFmpeg disponible puede producir. Las imágenes fijas (PNG/JPG/WebP/BMP/TIFF) también se convierten con Pillow cuando no hay FFmpeg; GIF animado y AVIF sí necesitan FFmpeg.

---

## Plataformas

| Plataforma | Arquitectura |
| --- | --- |
| Windows | x64 |
| Linux | x64 |
| macOS | arm64 |

## Idiomas

Fuse tiene interfaz en 10 idiomas: `en`, `es`, `pt`, `fr`, `de`, `it`, `ja`, `ko`, `zh`, `ru`. Cambia el idioma sin reiniciar:

```
fuse ❯ /lang es
```

## FFmpeg: cómo se consigue

1. Si `ffmpeg` y `ffprobe` ya están en el PATH del sistema, Fuse los usa.
2. Si no, `fuse setup` (o la primera conversión que lo necesite) descarga el build de tu plataforma — Windows/Linux desde BtbN FFmpeg-Builds, macOS desde evermeet.cx — a la caché del usuario (`~/.cache/alenia-fuse/ffmpeg` en Linux/macOS, `%LOCALAPPDATA%\AleniaFuse\ffmpeg` en Windows) y verifica que los binarios descargados realmente ejecutan `ffmpeg -version` / `ffprobe -version` antes de aceptarlos.
3. También puedes apuntar a tu propio FFmpeg con la variable `FUSE_FFMPEG_DIR`, o desactivar la descarga automática con `FUSE_DISABLE_FFMPEG_DOWNLOAD=1`.

Si la descarga falla, `fuse setup` muestra la causa real (sin red, URL cambiada, arquitectura no soportada) en vez de un error genérico. Sin FFmpeg, las conversiones de video y audio no pueden correr; las de imágenes fijas sí, con Pillow.

## Arquitectura

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

- **CLI y API comparten el mismo núcleo.** Sin lógica duplicada.
- **Capability Engine** consulta el FFmpeg disponible para saber qué conversiones son realmente posibles para un archivo dado.
- **Validator** revisa las entradas antes y las salidas después de cada operación.
- El código es **Python puro** (`rich` + `prompt_toolkit` para la CLI, `Pillow` para imágenes y PDF). No hay Go, ni Nuitka, ni interfaz React, ni ejecutable compilado aparte.

## Qué NO hace Fuse (todavía)

Para no prometer lo que no existe:

- **No hay aceleración GPU automática.** Los encoders son por software (`libx264`, `libvpx-vp9`, `aac`, `libopus`...). `fuse hardware` solo lista los encoders de hardware que el FFmpeg disponible trae, no los usa.
- **No hay edición IDE / interfaz gráfica.** Solo existe la CLI (`fuse`) y la API Python.
- **No hay caché de archivos ya convertidos** ni reintento automático "a prueba de fallos": si FFmpeg falla, la operación devuelve el error.
- **No hay build de macOS x86_64** en la descarga automática: el build de macOS es para arm64 (el binario de evermeet.cx es x86_64 y corre en Apple Silicon vía Rosetta 2; no está verificado en hardware real por Alenia todavía).

## Desarrollo

```
git clone https://github.com/kaia-alenia/alenia-fuse
cd alenia-fuse
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux / macOS
pip install -e ".[dev]"
pytest tests/ -v
```

### Construir el wheel

```
python -m build
```

### Probar la instalación en un entorno limpio

```
python -m venv clean-env
clean-env\Scripts\pip install dist\*.whl
clean-env\Scripts\fuse --version
clean-env\Scripts\fuse -h
```

---

## Licencia

GNU General Public License v3.0 — ver `LICENSE`.

© Alenia Studios — contact.aleniastudios@gmail.com
