# API de Python de Alenia Fuse

Alenia Fuse expone un pipeline principal para la CLI y la biblioteca de Python:

`API facade → Media inspection → OperationPlanner → FFmpeg → OperationResult`

El planificador decide si una conversión puede copiar flujos de datos (streams) o si necesita una recodificación real. Las API públicas no llaman a servicios de conversión externos.

## Puntos de entrada públicos

```python
from fuse import Video, Audio, Image, Media

Video("movie.mp4").convert("webm").output("movie.webm").run()
Audio("speech.wav").normalize().output("speech.wav").run()
Image("photo.png").resize(1200, 800).output("photo.webp").run()
Image("photo.png").to_pdf("photo.pdf", dpi=150)
info = Media.inspect("movie.mp4")
```

`Video` maneja la conversión de video y operaciones de video como redimensionar, recortar, rotar, FPS, velocidad, recorte de tiempo, silenciar, extracción de audio, miniaturas, creación de GIF y remux. `Audio` maneja conversión, volumen, normalización, fundidos, velocidad y recorte de tiempo. `Image` maneja la conversión de imágenes, redimensionado, recorte y rotación.

`Media.inspect` lee metadatos técnicos a través de FFprobe. No realiza OCR, ni inventa metadatos, ni llama a servicios de terceros. Las operaciones de metadatos copian o actualizan etiquetas a través de FFmpeg cuando el contenedor seleccionado lo admite.

Todos los archivos multimedia generados utilizan un enfoque de privacidad por defecto: los metadatos globales y los capítulos no se copian automáticamente. Esto elimina campos sensibles comunes como GPS, dispositivo, software, hora de creación y comentarios, mientras preserva los datos técnicos del flujo necesarios para la reproducción. La salida de imagen a PDF se genera sin metadatos de la imagen original.

La conversión de imagen a PDF utiliza Pillow de forma local, corrige la orientación EXIF, compone píxeles transparentes sobre blanco, preserva la calidad de la imagen y admite DPI de página.

## Política de conversión

Fuse solo expone objetivos con una estrategia FFmpeg local. Los objetivos comunes incluyen MP4, WebM, MKV, MOV, AVI, TS, MP3, FLAC, AAC, M4A, Opus, OGG, WAV, WebP, JPEG, PNG, AVIF, BMP, TIFF, GIF y APNG. Los objetivos no compatibles o ambiguos se rechazan antes de la ejecución.

La conversión de video web usa `webm` y produce un archivo `.webm` con VP9/Opus cuando la entrada contiene video/audio. `m4a` es un objetivo de audio separado basado en MP4; no se trata como AAC crudo.

## Distribución de FFmpeg

El paquete de Python no incluye binarios pesados de FFmpeg. Fuse resuelve FFmpeg en este orden: `FUSE_FFMPEG_DIR`, la caché local, binarios de desarrollo y el `PATH` del sistema. Si falta, descarga el asset correspondiente del release de GitHub en el primer uso, verifica su checksum SHA-256 y lo guarda en la caché del usuario. Puedes desactivar la descarga con `FUSE_DISABLE_FFMPEG_DOWNLOAD=1` o ejecutar `fuse setup` manualmente.

Cada operación devuelve un `OperationResult`, incluyendo `success`, `operation`, `input_path`, `output_path`, el `media` opcionalmente inspeccionado, advertencias y un mensaje de error útil.
