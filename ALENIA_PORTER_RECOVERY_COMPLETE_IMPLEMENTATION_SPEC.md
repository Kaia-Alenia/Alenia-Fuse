# ALENIA PORTER — RECOVERY / COMPLETE IMPLEMENTATION SPEC

## Propósito

Este documento es un contrato de implementación. No describe un prototipo, un skeleton ni una arquitectura futura. El resultado debe ser una versión funcional de Porter: paquete Python instalable + CLI interactiva moderna + CLI one-shot + motor FFmpeg real + API Python + pruebas reales.

**Regla principal:** no marcar nada como terminado por existir un archivo, clase, comando o interfaz. Se considera implementado únicamente cuando funciona y existe una prueba o evidencia observable apropiada.

**Durante toda esta tarea:** NO hacer `git push`, NO crear release, NO publicar artefactos y, salvo orden posterior del usuario, NO hacer commits.

---

# 1. RESTRICCIONES ABSOLUTAS

## 1.1 Nada simulado

Eliminar cualquier:

- `time.sleep()` usado para simular procesamiento;
- progreso falso;
- output falso;
- `return True` sin haber ejecutado la operación;
- capability registry falsa como fuente de verdad;
- `ffmpeg.bat` ficticio o wrapper dummy;
- dataclasses vacías que pretendan ser la API final;
- handlers que solo impriman “Done”;
- `NotImplementedError` en rutas accesibles por la CLI;
- `pass`, `TODO`, `FIXME` o placeholders en funcionalidades obligatorias.

Un mock puede existir únicamente dentro de un unit test aislado. Nunca para demostrar que la aplicación funciona.

## 1.2 FFmpeg del proyecto es la fuente primaria

Porter ya incluye un FFmpeg completo en `bin/`.

**No descargar otro FFmpeg.** No usar como sustituto `imageio-ffmpeg`, `ffmpeg-python`, gestores de binarios ni descargas automáticas.

Resolver primero el binario distribuido con Porter. Debe verificarse su existencia y ejecutarse `ffmpeg -version`.

## 1.3 FFprobe

Inspeccionar `bin/` y determinar si existe `ffprobe`/`ffprobe.exe`.

- Si existe, resolverlo y usarlo como fuente primaria de probing.
- Si no existe, declararlo explícitamente.
- No descargarlo silenciosamente.
- No inventar sus resultados.
- No presentar como “probe disponible” algo que no lo esté.

Las operaciones que requieren probing deben manejar correctamente esta condición.

## 1.4 Seguridad de subprocess

Nunca utilizar `shell=True` para el funcionamiento normal. Nunca `os.system`. Nunca concatenar comandos como una cadena.

Usar argumentos estructurados:

```python
[ffmpeg_path, "-i", str(input_path), str(output_path)]
```

## 1.5 Compatibilidad

Usar `pathlib`, `platformdirs` cuando sea útil, APIs de terminal multiplataforma y rutas sin hardcodear Windows. Probar rutas con espacios, unicode y caracteres especiales.

---

# 2. RESULTADO FINAL

El producto final debe tener cuatro capas coherentes:

```text
CLI interactiva
      ↓
Command registry / handlers
      ↓
Porter core / operations / planner
      ↓
FFmpeg executor + FFprobe + validator
      ↓
Archivos multimedia reales
```

Y una API Python que use exactamente ese mismo core:

```text
Python API
      ↓
Operations / planner
      ↓
Executor
      ↓
FFmpeg
```

La CLI no puede tener un motor diferente al de la biblioteca.

---

# 3. ESTRUCTURA DEL PROYECTO

La estructura puede adaptarse al repositorio actual, pero las responsabilidades deben quedar separadas:

```text
src/alenia_porter/
├── __init__.py
├── cli/
│   ├── app.py
│   ├── prompt.py
│   ├── palette.py
│   ├── completion.py
│   ├── history.py
│   ├── rendering.py
│   ├── progress.py
│   ├── theme.py
│   ├── errors.py
│   └── commands/
│       ├── registry.py
│       ├── base.py
│       └── ...
├── core/
│   ├── models.py
│   ├── result.py
│   ├── operation.py
│   ├── job.py
│   ├── cancellation.py
│   └── errors.py
├── ffmpeg/
│   ├── resolver.py
│   ├── ffprobe.py
│   ├── executor.py
│   ├── progress.py
│   └── capabilities.py
├── media/
│   ├── media.py
│   ├── video.py
│   ├── audio.py
│   ├── image.py
│   ├── stream.py
│   └── metadata.py
├── operations/
│   ├── convert.py
│   ├── compress.py
│   ├── optimize.py
│   ├── remux.py
│   ├── cut.py
│   ├── trim.py
│   ├── concat.py
│   ├── resize.py
│   ├── crop.py
│   ├── rotate.py
│   ├── fps.py
│   ├── speed.py
│   ├── audio.py
│   ├── normalize.py
│   ├── fade.py
│   ├── frame.py
│   ├── thumbnail.py
│   ├── gif.py
│   ├── subtitle.py
│   └── watermark.py
├── planning/
│   ├── planner.py
│   ├── containers.py
│   ├── codecs.py
│   └── filters.py
├── capabilities/
│   ├── registry.py
│   ├── formats.py
│   ├── encoders.py
│   ├── decoders.py
│   ├── filters.py
│   └── hardware.py
├── config/
│   ├── model.py
│   ├── loader.py
│   └── defaults.py
└── i18n/
    ├── __init__.py
    ├── es.py
    └── en.py
```

No meter toda la lógica en un único `cli.py` o `porter.py` gigante.

---

# 4. DEPENDENCIAS DE LA CLI

Usar:

- `prompt_toolkit` para input, history, completion y key bindings;
- `rich` para paneles, tablas, spinner, progreso, errores y texto coloreado.

No añadir React, Node, Tkinter, una webview ni Textual para esta CLI.

---

# 5. IDENTIDAD VISUAL EXACTA

## 5.1 Tema

Tema oscuro por defecto. La apariencia debe ser técnica, limpia y moderna; no parecer un script académico.

## 5.2 Paleta obligatoria

```text
Background:          #020617
Panel:               #111827
Panel secondary:     #0F172A
Border:              #334155
Primary/Brand:       #7C5CFF
Primary bright:      #9A84FF
Secondary/Cyan:      #22D3EE
Success:             #22C55E
Warning:             #F59E0B
Error:               #EF4444
Info:                #38BDF8
Text primary:        #F8FAFC
Text secondary:      #CBD5E1
Text muted:          #94A3B8
Text disabled:       #64748B
White:               #FFFFFF
Black:               #000000
```

Reglas:

- morado = identidad/acción principal;
- cyan = información técnica;
- verde = éxito;
- amarillo = advertencia;
- rojo = error;
- grises = contenido secundario.

No usar colores aleatorios. No pintar cada línea con un color distinto. No usar rojo como decoración.

## 5.3 Prompt exacto

```text
porter › 
```

`porter` en `#7C5CFF`, `›` en `#94A3B8`, entrada del usuario en `#F8FAFC`.

No usar `>>>`, `$` o `C:\>` como identidad principal.

## 5.4 Logo

Al iniciar el modo interactivo debe aparecer un logo ASCII compacto y consistente con Porter. Debe caber en una terminal de aproximadamente 80 columnas.

Después del logo:

```text
Porter 7.x · Python media toolkit
Type "help" for commands.
```

No imprimir un muro de texto.

---

# 6. ARRANQUE DE `porter`

## Sin argumentos

```bash
porter
```

Abre el loop interactivo.

## Con comando

```bash
porter convert input.mp4 output.webm
```

Ejecuta el comando directamente y termina con un exit code apropiado.

## Opciones globales obligatorias

```text
--help
--version
--json
--quiet
--no-color
--verbose
--debug
--non-interactive
--dry-run
```

`--dry-run` es la única simulación permitida: debe construir el plan y mostrar el argv que se ejecutaría, sin ejecutar FFmpeg.

---

# 7. INPUT INTERACTIVO

La CLI debe:

1. aceptar espacios correctamente;
2. aceptar rutas entre comillas;
3. completar comandos con Tab;
4. completar opciones con Tab;
5. completar rutas locales;
6. recordar history entre sesiones;
7. soportar navegación arriba/abajo;
8. usar Ctrl+R para búsqueda de historial cuando el backend lo permita;
9. volver al prompt después de cada comando;
10. no salir ante errores normales de usuario.

Presionar Enter en una línea vacía = nuevo prompt, sin error.

---

# 8. HISTORIAL

Guardar en una ubicación multiplataforma equivalente a:

```text
~/.alenia/porter/history
```

En Windows usar la ubicación apropiada de datos de usuario, preferentemente mediante `platformdirs`.

No almacenar secretos.

---

# 9. COMMAND PALETTE

Debe existir una paleta real, recomendablemente con `Ctrl+K`.

Debe permitir búsqueda y navegación con teclado.

Vista objetivo:

```text
╭─ Command Palette ───────────────────────────────╮
│ Search commands...                              │
│                                                 │
│ › convert      Convert media                   │
│   compress     Reduce file size                │
│   info         Show media information          │
│   metadata     Show detailed metadata          │
╰─────────────────────────────────────────────────╯
```

`Enter` ejecuta; `Esc` cierra.

La paleta debe usar el registry central, no una lista duplicada.

---

# 10. COMMAND REGISTRY

Cada comando debe registrar:

```text
name
aliases
category
description
syntax
examples
options
completion
handler
```

El mismo registry alimenta:

- `help`;
- `help <command>`;
- autocomplete;
- command palette;
- sugerencias.

Prohibido duplicar la lista de comandos en cuatro archivos distintos.

---

# 11. AYUDA

`help` debe presentar grupos visuales:

```text
MEDIA
  convert
  compress
  optimize
  remux
  cut
  trim
  concat

VIDEO
  resize
  crop
  rotate
  fps
  speed
  mute
  frame
  thumbnail
  gif
  watermark
  subtitle

AUDIO
  extract-audio
  volume
  normalize
  fade

INSPECTION
  info
  metadata
  formats
  codecs
  filters
  hardware
  diagnostics

SYSTEM
  config
  lang
  clear
  help
  exit
```

`help convert` debe mostrar sintaxis, opciones, ejemplos, restricciones y errores frecuentes.

---

# 12. COMANDOS OBLIGATORIOS

Todos deben realizar trabajo real cuando su operación sea aplicable.

## `convert`

```bash
porter convert input.mp4 output.webm
```

Debe detectar input, output, codecs disponibles, construir plan, ejecutar FFmpeg, mostrar progreso y validar output.

Opciones mínimas:

```text
--overwrite
--video-codec
--audio-codec
--bitrate
--crf
--preset
--fps
--resolution
--audio-bitrate
```

## `compress`

```bash
porter compress input.mp4 output.mp4
```

Debe recodificar/optimizar de forma real y reportar tamaño real:

```text
Original: 18.4 MB
Output:   11.2 MB
Saved:    7.2 MB
Reduction: 39.1%
```

Si el archivo aumenta, decirlo correctamente; jamás afirmar ahorro falso.

## `optimize`

```bash
porter optimize input.mp4 output.mp4
```

Debe aplicar una estrategia explícita y documentada. No prometer una “optimización universal”.

## `remux`

```bash
porter remux input.mkv output.mp4
```

Debe preferir stream copy cuando sea técnicamente compatible. Si no, informar que requiere re-encode o fallar de forma explicada según la política del comando.

## `cut`

```bash
porter cut input.mp4 output.mp4 --start 00:01:10 --duration 00:00:20
```

Debe generar el segmento solicitado y validar duración/streams cuando sea razonable.

## `trim`

```bash
porter trim input.mp4 output.mp4 --start 00:00:10 --end 00:00:30
```

Debe tener semántica definida; no crear dos comandos idénticos sin motivo técnico.

## `concat`

```bash
porter concat a.mp4 b.mp4 c.mp4 output.mp4
```

Debe validar compatibilidad de streams y elegir copy/re-encode según corresponda.

No inventar `merge` como duplicado de `concat`.

## `resize`

```bash
porter resize input.mp4 output.mp4 --width 1280 --height 720
```

Debe preservar aspect ratio cuando se solicite y validar dimensiones reales.

## `crop`

```bash
porter crop input.mp4 output.mp4 --width 800 --height 600 --x 20 --y 10
```

Validar geometría antes de ejecutar.

## `rotate`

Admitir al menos `90`, `180`, `270`.

## `fps`

```bash
porter fps input.mp4 output.mp4 --fps 30
```

## `speed`

```bash
porter speed input.mp4 output.mp4 --factor 1.5
```

Debe ajustar audio cuando exista y cuando técnicamente corresponda.

## `mute`

```bash
porter mute input.mp4 output.mp4
```

Después de validar debe haber cero streams de audio.

## `extract-audio`

```bash
porter extract-audio video.mp4 audio.mp3
```

Debe localizar el stream de audio real.

## `volume`

```bash
porter volume audio.mp3 output.mp3 --factor 1.5
```

Debe usar un filtro real.

## `normalize`

Debe implementar normalización real, por ejemplo mediante `loudnorm` u otra estrategia compatible con el plan.

## `fade`

```bash
porter fade input.mp4 output.mp4 --in 2 --out 3
```

Debe aplicar filtros reales.

## `frame`

```bash
porter frame video.mp4 frame.png --at 00:00:05
```

Debe extraer un frame real.

## `thumbnail`

```bash
porter thumbnail video.mp4 thumb.jpg
```

Debe crear una miniatura real y permitir timestamp cuando corresponda.

## `gif`

```bash
porter gif input.mp4 output.gif
```

Utilizar una estrategia razonable; palettegen/paletteuse puede usarse cuando sea apropiado.

## `subtitle`

Debe implementar las capacidades reales soportadas por FFmpeg para:

- inspeccionar streams de subtítulos;
- extraerlos cuando sea posible;
- incorporar subtítulo externo;
- burn-in cuando sea compatible.

No prometer un flujo que el binario real no pueda ejecutar.

## `watermark`

```bash
porter watermark input.mp4 logo.png output.mp4
```

Debe utilizar overlay real y permitir posición.

---

# 13. INSPECCIÓN

## `info`

Debe ser breve y humano. Ejemplo:

```text
╭─ Video ───────────────────────────────────────╮
│ File       sample.mp4                         │
│ Duration   01:23.481                          │
│ Size       42.8 MB                            │
│ Resolution 1920×1080                          │
│ Video      H.264 / 29.97 fps                 │
│ Audio      AAC / 48 kHz / Stereo             │
╰────────────────────────────────────────────────╯
```

Todos los valores deben proceder del archivo real.

## `metadata`

Debe exponer información detallada. Con `--json`, JSON estable y sin ANSI.

Debe poder devolver:

- container/format;
- duration;
- size;
- bitrate;
- streams;
- codec;
- resolution;
- fps;
- sample rate;
- channels;
- language;
- tags/metadata.

## `formats`

No tratar toda la salida de `ffmpeg -formats` como extensiones de salida. Clasificar:

```text
Normal file target
Advanced file target
Input-only / special
Streaming / protocol
Device / pipe
```

La lista técnica procede del FFmpeg real.

## `codecs`

Usar `-encoders` y `-decoders` reales. Separar video/audio y encoder/decoder.

## `filters`

Usar la lista real de `ffmpeg -filters`.

## `hardware`

Detectar realmente hwaccels/encoders disponibles. No confundir “FFmpeg compilado con NVENC” con “GPU NVIDIA usable en esta máquina”.

## `diagnostics`

Debe mostrar como mínimo:

```text
Porter version
Python version
OS
Bundled FFmpeg path
FFmpeg version
FFprobe path/version or NOT BUNDLED
Capability counts
Hardware detection summary
Configuration path
```

---

# 14. SISTEMA DE EJECUCIÓN FFmpeg

## Resolver

`FFmpegResolver` debe:

1. localizar el binario bundled;
2. verificar existencia;
3. verificar que pueda ejecutarse;
4. ejecutar `-version`;
5. extraer versión;
6. devolver un objeto de información estructurado.

`FFprobeResolver` debe ser independiente.

## Executor

Crear `FFmpegExecutor`/`ProcessExecutor` central. Debe manejar:

- argv estructurado;
- process start;
- stdout/stderr;
- progress estructurado;
- cancelación;
- exit code;
- duración;
- logs.

No dejar `Popen` disperso por los comandos.

## `-nostdin`

Considerar/usar `-nostdin` para evitar que FFmpeg consuma accidentalmente la entrada de la terminal.

---

# 15. PROGRESO Y SPINNER

## Spinner

Para operaciones no triviales pero cortas:

```text
⠋ Inspecting media...
```

Usar Rich. No escribir bucles de animación con `sleep`.

## Progress

Para operaciones largas usar preferentemente:

```text
-progress pipe:1
```

u otro formato estructurado equivalente.

Nunca generar porcentajes sintéticos.

Vista objetivo:

```text
╭─ Converting ───────────────────────────────────╮
│ input.mp4 → output.webm                       │
│                                                │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 72%               │
│ Elapsed 00:04 · 00:02 remaining               │
╰────────────────────────────────────────────────╯
```

Si ETA no es fiable, ocultarla.

---

# 16. CANCELACIÓN

Ctrl+C debe:

1. detectar cancelación;
2. terminar el proceso FFmpeg;
3. esperar su cierre;
4. borrar temporal;
5. no dejar output corrupto;
6. mostrar:

```text
⚠ Operation cancelled.
```

No mostrar un traceback de `KeyboardInterrupt` como respuesta normal.

---

# 17. OUTPUT ATÓMICO Y VALIDACIÓN

No escribir directamente al destino final cuando la operación pueda fallar.

Flujo obligatorio:

```text
input
  ↓
plan
  ↓
temporary output
  ↓
FFmpeg
  ↓
validator
  ↓
os.replace / rename
  ↓
final output
```

Validar:

- return code 0;
- existe;
- tamaño > 0;
- probe válido cuando esté disponible;
- streams esperados;
- container legible;
- efecto solicitado.

Ejemplos:

```text
mute      -> audio streams == 0
resize    -> dimensiones esperadas
fps       -> fps real compatible con tolerancia
frame     -> imagen válida
extract   -> audio stream presente
```

---

# 18. FFPROBE / MEDIA PROBER

Preferir JSON:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
```

Crear modelos para:

```text
Media
Video
Audio
Image
Stream
Metadata
```

`Media` debe poder representar, cuando exista:

```text
path
format
duration
size
streams
metadata
```

`Stream` debe representar, cuando exista:

```text
index
type
codec
language
duration
bitrate
metadata
```

No usar únicamente parsing textual de stderr de FFmpeg cuando JSON de FFprobe esté disponible.

---

# 19. CAPABILITY REGISTRY REAL

Descubrir desde el ejecutable bundled:

```text
ffmpeg -formats
ffmpeg -encoders
ffmpeg -decoders
ffmpeg -filters
ffmpeg -protocols
ffmpeg -hwaccels
```

Cachear por versión/ruta.

Invalidar si cambia el ejecutable o se pide refresh.

La registry debe distinguir:

```text
input
output
input+output
codec encoder
codec decoder
filter
protocol
special/device
```

Una lista estática solo puede servir para clasificación UX (“common”), nunca como verdad técnica.

---

# 20. PLANNER

Crear `OperationPlanner` que decida según input, output y capabilities:

- container;
- video codec;
- audio codec;
- stream copy;
- re-encode;
- filters;
- mapping;
- quality;
- bitrate;
- hardware acceleration cuando sea realmente usable.

Debe existir una representación del plan, por ejemplo:

```python
OperationPlan(
    input=...,
    output=...,
    container="webm",
    video_codec="libvpx-vp9",
    audio_codec="libopus",
    video_filters=[],
    audio_filters=[],
    stream_copy=False,
)
```

El plan no puede asumir codecs que no existan.

---

# 21. STREAM COPY

Priorizar copy cuando sea técnicamente correcto.

Ejemplo:

```text
H.264 + AAC → MP4
```

debe poder usar stream copy si el contenedor y streams son compatibles.

Si el destino no soporta el stream, debe:

- re-encode si el comando lo permite;
- o explicar claramente por qué no puede hacer copy.

Nunca decir “sin recodificar” si realmente se recodificó.

---

# 22. API PYTHON

Debe existir una API de alto nivel, simple y coherente.

Ejemplo conceptual:

```python
from alenia_porter import Video

result = Video("input.mp4").convert("output.webm").run()
```

También deben existir conceptos equivalentes para `Audio`, `Image`, `Media`, `Stream` y `Operation` cuando corresponda.

La API no debe llamar `sys.exit()`.

Los errores de dominio deben ser excepciones específicas.

---

# 23. RESULTADO DE OPERACIONES

No devolver simplemente `True`.

Debe existir un resultado estructurado que pueda contener:

```text
success
operation
input_path
output_path
input_size
output_size
duration
elapsed
command
validation
cancelled
```

En CLI se transforma en UI; en API queda disponible al programador.

---

# 24. EXCEPCIONES DE DOMINIO

Crear, como mínimo cuando sean necesarias:

```text
PorterError
FFmpegNotFoundError
FFprobeNotFoundError
InvalidMediaError
UnsupportedFormatError
UnsupportedCodecError
OperationError
ValidationError
CancelledError
ConfigurationError
```

Los errores de usuario no deben imprimir tracebacks por defecto. `--debug` sí puede mostrar diagnóstico detallado.

---

# 25. CONFIGURACIÓN

Configurar persistentemente, al menos:

```text
language
color_enabled
theme
overwrite
ffmpeg_path (override explícito)
ffprobe_path (override explícito)
log_level
history_enabled
```

El override de FFmpeg nunca debe romper la prioridad del bundled por defecto.

No guardar configuración en el repositorio del usuario.

---

# 26. LOCALIZACIÓN

Idiomas iniciales:

```text
es
en
```

Toda la UI propia debe obtener sus textos de una capa de localización.

No mezclar accidentalmente:

```text
Conversión fallida
Use --overwrite
```

El inglés de ayuda y errores propios debe estar completo.

---

# 27. ONE-SHOT / SCRIPTING

Todas las operaciones deben poder utilizarse fuera del loop:

```bash
porter info file.mp4
porter metadata file.mp4 --json
porter convert input.mp4 output.webm
porter resize input.mp4 output.mp4 --width 1280 --height 720
```

Debe existir un contrato de exit codes. Como guía:

```text
0    success
1    operation failure
2    invalid arguments
3    dependency unavailable
4    output validation failure
130  cancelled
```

No usar `sys.exit()` desde la API; sí desde el entrypoint CLI.

---

# 28. JSON / QUIET / NO-COLOR

## `--json`

No ANSI. No texto humano mezclado. El resultado debe ser parseable.

## `--quiet`

Mostrar solo información esencial y errores.

## `--no-color`

Cero secuencias ANSI.

Si stdout no es TTY, adaptar colores/progreso para que no rompan pipelines.

---

# 29. DRY RUN / EXPLAIN

`--dry-run`:

```text
Dry run

ffmpeg
  -i input.mp4
  -c:v libx264
  -crf 23
  output.mp4
```

No ejecutar.

`--explain`, si se implementa, debe explicar el plan real:

```text
Input codec: h264
Output container: webm
Selected video codec: libvpx-vp9
Reason: requested container supports VP9 and current FFmpeg exposes the encoder.
```

---

# 30. OPTIONS Y PARSING

Validar antes de lanzar FFmpeg:

- `--fps` numérico;
- `--factor` numérico y razonable;
- `--resolution` `WIDTHxHEIGHT`;
- `--start`, `--end`, `--duration` como segundos o timestamps válidos;
- bitrate con unidades (`128k`, `1M`);
- rutas existentes;
- output distinto de input salvo una política explícita.

No usar `split(" ")` para parsing interactivo.

---

# 31. GLOB Y RUTAS

En Windows no depender de globbing del shell.

Expandir patrones mediante Python cuando una operación por lotes lo necesite.

Aceptar:

```text
"C:\My Videos\clip one.mp4"
/home/user/video.mp4
./relative/path.mp4
```

---

# 32. OVERWRITE

Por defecto:

```text
✗ Output already exists: output.mp4

Use --overwrite to replace it.
```

No sobrescribir silenciosamente.

---

# 33. UI DE ÉXITO / WARNING / ERROR

Éxito:

```text
✓ Converted successfully

output.webm
2.4 MB · 00:08.21
```

Warning:

```text
⚠ Stream copy was not possible.
  Re-encoding was required.
```

Error:

```text
✗ Conversion failed

Reason
  No suitable video encoder is available.

Try
  porter codecs
```

Usar los colores exactos definidos arriba.

---

# 34. NO SPAM

No imprimir cada segundo:

```text
Starting...
Loading...
Running...
Executing...
Processing...
Almost done...
```

Una operación debe tener una sola representación de estado que se actualice.

---

# 35. DISEÑO DE LA SESSION

Después de una operación interactiva:

```text
resultado
porter ›
```

No reiniciar la aplicación.

El estado de sesión puede conservar idioma, tema, opciones visuales e historial. No conservar rutas peligrosas o secretos sin necesidad.

---

# 36. COMMAND UNKNOWN / SUGGESTIONS

Ejemplo:

```text
porter › convertt

✗ Unknown command: convertt

Did you mean:
  convert
```

Usar fuzzy matching razonable. No inventar comandos.

---

# 37. CLEAR / EXIT

`clear` limpia terminal de forma multiplataforma.

`exit` termina la sesión.

`quit` puede ser alias.

Ctrl+D debe salir limpiamente donde la terminal lo soporte.

---

# 38. LEGACY CLEANUP

Buscar y eliminar/actualizar referencias a:

```text
Go
go.mod
go.sum
cmd/ap
React
package.json
node_modules
legacy/ide
Tkinter
gui_web.py
old launchers
old CLI references
old GUI references
```

No borrar ciegamente: buscar referencias primero.

El resultado final no debe requerir Node/Go/Tkinter para la CLI actual.

---

# 39. SCRIPTS Y WORKFLOWS

Revisar:

```text
.github/workflows/*
Makefile
build_releases.sh
install.sh
install.ps1
launch.sh
```

Eliminar referencias a `go build`, Node, React o el IDE antiguo.

CI debe ejecutar Python, lint, tests y packaging.

FFmpeg/FFprobe deben ser dependencias explícitas del entorno de test cuando un test los necesite.

---

# 40. PACKAGE / PYPROJECT

`pyproject.toml` debe tener:

- metadata correcta;
- Python mínimo real;
- dependencias actuales;
- console script correcto:

```text
porter = <nuevo entrypoint Python>
```

- package data para los assets/binaries que se distribuyan.

No dejar un entrypoint apuntando al CLI viejo.

---

# 41. INSTALACIÓN LIMPIA

Probar en un entorno limpio:

```bash
python -m venv .venv-test
```

Activar e instalar:

```bash
pip install .
```

Después:

```bash
porter --version
porter --help
```

Debe funcionar sin depender de imports del checkout que no formen parte del paquete.

---

# 42. WHEEL / SDIST

Construir:

```bash
python -m build
```

Inspeccionar el wheel y verificar que contiene todos los assets que Porter necesita.

Probar la instalación del wheel en otro entorno limpio.

---

# 43. FFmpeg EN EL PAQUETE

Si `bin/ffmpeg` forma parte del producto distribuido, comprobar que el mecanismo de packaging lo incluye realmente.

No asumir que “está en el repo” significa “está en el wheel”.

Documentar versión/procedencia/licencia del binario.

---

# 44. LICENCIAS

No reemplazar ni modificar accidentalmente archivos de licencia del FFmpeg incluido.

Documentar correctamente las obligaciones de distribución de los componentes bundled.

---

# 45. TEST FIXTURES

Crear fixtures muy pequeños. Preferiblemente generarlos con FFmpeg:

```text
5 segundos
1280x720
video sintético
audio sine
```

Fixtures adicionales:

```text
fixture_audio.wav
fixture_image.png
fixture_subtitle.srt
```

Evitar archivos grandes innecesarios.

---

# 46. TESTS UNITARIOS

Probar como mínimo:

- FFmpeg resolver;
- FFprobe resolver;
- capability parser;
- registry;
- planner;
- time parser;
- resolution parser;
- command registry;
- metadata parser;
- result validator;
- config loader;
- error mapping.

---

# 47. TESTS DE INTEGRACIÓN

Deben ejecutar FFmpeg real. Mínimo:

```text
info
convert
remux cuando sea aplicable
compress
resize
mute
extract-audio
frame
thumbnail
```

El test de integración no debe mockear FFmpeg.

---

# 48. TEST CONTRA SIMULACIÓN

Debe existir una prueba que falle si una operación vuelve a hacer solamente:

```python
time.sleep(...)
return True
```

El test debe comprobar una transformación real del archivo: formato, streams, dimensiones, duración, metadata o equivalente.

---

# 49. TEST DE VALIDACIÓN

Crear intencionalmente una condición inválida o output vacío/corrupto y verificar que Porter NO diga “success”.

---

# 50. TEST DE CANCELACIÓN

Verificar que cancelar una operación:

- termina el proceso;
- elimina temporal;
- evita declarar éxito;
- no deja output final corrupto.

---

# 51. TEST DE CLI

Automatizar al menos:

```bash
porter --version
porter --help
porter info fixture.mp4
porter metadata fixture.mp4 --json
porter convert fixture.mp4 fixture.webm
porter resize fixture.mp4 fixture-small.mp4 --width 640 --height 360
porter mute fixture.mp4 fixture-muted.mp4
porter thumbnail fixture.mp4 thumb.jpg
```

---

# 52. TEST DE UX MANUAL

La IA local debe arrancar:

```bash
porter
```

y comprobar físicamente:

1. logo;
2. colores;
3. prompt;
4. Tab completion;
5. history;
6. Ctrl+K;
7. help;
8. info real;
9. operación real con progreso;
10. cancelación Ctrl+C;
11. retorno al prompt;
12. exit.

No basta con compilar.

---

# 53. FORMATO DE TERMINAL

La interfaz debe conservar buen aspecto con aproximadamente:

```text
80 columnas
100 columnas
120 columnas
```

No crear tablas que exploten horizontalmente.

La información secundaria puede truncarse de manera elegante.

---

# 54. PERFORMANCE

`porter --version` no debe inicializar capacidades completas si no son necesarias.

El prompt no debe ejecutar `ffmpeg -formats`, `-encoders`, `-filters` etc. en cada Enter.

Usar cache durante la sesión.

---

# 55. COMMAND COMPLETION DINÁMICO

Completion debe venir del registry y, cuando sea útil, de capabilities reales.

Ejemplos:

```text
convert --<TAB>
convert --video-codec <TAB>
convert input.mp4 <TAB>
```

Nunca hardcodear una lista de codec que contradiga al FFmpeg instalado.

---

# 56. METADATA

Definir una política clara para conservar/cambiar metadata.

No eliminar tags o artwork accidentalmente sin explicación.

Para audio con artwork, evitar romperlo sin razón técnica.

---

# 57. SUBTÍTULOS

Distinguir claramente:

```text
subtitle stream
external subtitle
burn-in subtitle
```

No tratarlos como la misma operación.

---

# 58. HARDWARE

Mostrar al usuario algo parecido a:

```text
Hardware acceleration

Compiled support
  NVENC      yes
  QSV        yes

Detected / usable
  NVIDIA GPU no
  Intel QSV  yes
```

La terminología debe ser honesta. El encoder compilado no garantiza que la máquina tenga la GPU correspondiente.

---

# 59. COMMON VS COMPLETE FORMAT LIST

La UX puede presentar “Common formats”, pero esa lista es solo de conveniencia.

La fuente completa de capabilities debe ser el FFmpeg real.

No convertir protocolos, dispositivos, pipes o formatos científicos en “targets normales” del comando `convert` sin una razón de producto.

---

# 60. IMAGE OPERATIONS

`Image` debe cubrir solo operaciones que Porter pueda realizar de forma fiable, incluyendo cuando corresponda:

- convert;
- resize;
- crop;
- rotate;
- metadata.

No prometer edición avanzada inexistente.

---

# 61. ADVANCED FFmpeg ESCAPE HATCH

Debe existir una forma avanzada de pasar opciones FFmpeg cuando sea necesario, pero siempre a través del executor seguro y de argv estructurado.

No exigir envolver manualmente cada flag existente de FFmpeg como comando humano.

La CLI amigable cubre operaciones comunes; el escape hatch cubre casos avanzados.

---

# 62. EXPLAINABILIDAD DEL PLAN

Cuando una operación es no trivial, Porter debe poder explicar:

```text
Stream copy: yes/no
Video encoder: ...
Audio encoder: ...
Container: ...
Reason: ...
```

No revelar toda la complejidad interna por defecto.

---

# 63. LOG FILE

`--log-file` puede ser añadido como opción global o config.

Los logs de debug deben ir a una ubicación de usuario adecuada.

No mezclar logs internos con JSON.

---

# 64. EXCEPCIONES EN INTERACTIVE MODE

Un error de un comando no debe matar el proceso interactivo completo.

Ejemplo:

```text
porter › convert missing.mp4 output.mp4
✗ Input file does not exist.
porter ›
```

Solo un fallo catastrófico interno puede terminar la aplicación, y debe registrarse.

---

# 65. OPERACIONES IDEMPOTENTES / DESTRUCTIVAS

No modificar el input durante operaciones normales.

Si el usuario intenta usar el mismo path para input/output, detectar la situación y aplicar una política explícita en vez de corromper el archivo.

---

# 66. OUTPUT STATS

Después de una operación que produzca archivo, cuando sea significativo mostrar:

```text
Output path
Output size
Elapsed
Reduction / increase when relevant
```

Datos reales, nunca estimados como hechos.

---

# 67. CONVERSIÓN Y CODEC DEFAULTS

Los defaults deben estar definidos por una política central del planner.

No permitir que cada command module invente sus propios defaults.

Documentar los defaults.

---

# 68. NORMALIZACIÓN DE NOMBRES

Mostrar nombres humanos cuando ayuden, por ejemplo:

```text
H.264 (libx264)
H.265 / HEVC (libx265)
VP9 (libvpx-vp9)
```

Pero solo si el encoder existe realmente.

---

# 69. CONVERSIONES DE AUDIO

Para audio validar:

- codec de entrada;
- codec de salida;
- sample rate;
- channels;
- metadata/artwork cuando aplique.

No asumir que todos los codecs soportan las mismas opciones.

---

# 70. TIME / FPS / BITRATE

Internamente normalizar tiempos a segundos.

Aceptar:

```text
10
10.5
00:01:10
01:02:03.500
```

Aceptar resolutions como:

```text
1280x720
1920x1080
```

Validar bitrate antes del proceso.

---

# 71. MAPPING DE STREAMS

El planner debe usar mapping explícito cuando una operación lo requiera.

No asumir que el auto-selection de FFmpeg siempre producirá exactamente el resultado pretendido por Porter.

---

# 72. CONSTRAINTS DE CONCAT

Antes de concat, comprobar compatibilidad relevante:

- codecs;
- resolución;
- fps;
- sample rate;
- canales;
- número/tipo de streams;
- timebase/container cuando corresponda.

Si no son compatibles, aplicar una estrategia real o devolver un diagnóstico claro.

---

# 73. VALIDACIÓN ESPECÍFICA POR COMANDO

Cada operación debe declarar qué significa “validado”.

Ejemplos:

```text
convert       output readable + expected streams
remux         container changed + streams preserved when promised
compress      output exists + size measured
resize        dimensions correct
crop          dimensions/geometry correct
rotate        orientation/geometry correct when probe can verify
fps           frame-rate result within expected tolerance
speed         duration changes as expected
mute          no audio stream
extract-audio audio stream present
frame         valid image
thumbnail     valid image and expected dimensions when specified
gif           output animation/image valid
watermark     output valid; visual effect may require fixture-specific check
```

---

# 74. CLI INTERACTIVA NO ES OBLIGATORIAMENTE UN TUI

No convertir la herramienta en una aplicación de bloques permanentes.

Debe sentirse como una CLI moderna:

- prompt limpio;
- rich feedback;
- keyboard interaction;
- command discovery;
- useful output;
- minimal clutter.

---

# 75. BARRA DE ESTADO

No crear una barra persistente gigante ocupando la terminal.

La sesión debe quedar legible cuando el usuario haya ejecutado muchos comandos.

---

# 76. COLOR EN HELP

Aplicar:

- títulos: `#7C5CFF`;
- comandos: `#F8FAFC`/primary;
- descripciones: `#CBD5E1`;
- warnings: `#F59E0B`;
- ejemplos técnicos: `#22D3EE`.

No convertir toda la pantalla en morado.

---

# 77. ERROR FORMAT

Los errores deben responder estas preguntas:

```text
Qué falló?
Dónde?
Por qué?
Qué puede hacer el usuario?
```

Ejemplo:

```text
✗ Conversion failed

Input
  video.mov

Reason
  FFmpeg has no available encoder for the requested output.

Try
  porter codecs
  porter convert video.mov video.mp4 --video-codec libx264
```

---

# 78. NO DATOS INVENTADOS

Nunca inventar:

- codec;
- duración;
- tamaño;
- capability;
- hardware;
- progreso;
- versión;
- éxito.

Si no se puede saber, decir que no se pudo determinar.

---

# 79. AUDITORÍA DE CÓDIGO FINAL

Buscar en todo el proyecto:

```text
TODO
FIXME
pass
NotImplementedError
time.sleep
shell=True
os.system
dummy
fake
stub
simulation
simulated
placeholder
legacy
go build
npm
node
react
tkinter
```

Cada match debe ser revisado manualmente. No ignorar automáticamente ninguno.

---

# 80. AUDITORÍA DE ENTRYPOINTS

Comprobar:

```text
porter
python -m alenia_porter
pip install .
wheel install
launch scripts
```

Todos deben apuntar a la arquitectura nueva o eliminarse si están obsoletos.

---

# 81. AUDITORÍA DE DOCUMENTACIÓN

README/docs no pueden describir:

- Go CLI antigua;
- Tkinter GUI;
- React IDE;
- paths de `legacy/ide`;
- comandos inexistentes;
- opciones inexistentes.

Cada ejemplo de documentación debe corresponder a un comando que realmente funcione.

---

# 82. ORDEN DE IMPLEMENTACIÓN

## Fase A — Inventario

1. inspeccionar repo real;
2. localizar FFmpeg bundled;
3. localizar FFprobe;
4. identificar restos legacy;
5. identificar entrypoints y scripts.

## Fase B — CLI real

Implementar y probar antes de expandir comandos:

```text
logo
prompt
theme
history
completion
palette
help
clear
exit
```

No aceptar “CLI lista” si solo imprime un prompt.

## Fase C — Runtime real

Implementar:

```text
FFmpegResolver
FFprobeResolver
Executor
Job
Progress
Cancellation
Validator
```

## Fase D — Capabilities

Implementar descubrimiento real y cache.

## Fase E — Media/API

Implementar modelos y API pública.

## Fase F — Planner

Implementar decisiones de container/codecs/copy/re-encode.

## Fase G — Primeros comandos reales

```text
info
convert
remux
compress
resize
```

Deben pasar antes de continuar.

## Fase H — Resto de comandos

Implementar la matriz completa.

## Fase I — Tests

Unit + integration + CLI + manual UX.

## Fase J — Packaging

Wheel + sdist + clean install.

## Fase K — Audit final

Código + UX + commands + package + workflows + docs.

---

# 83. GATES

Cada fase tiene que pasar antes de continuar.

## Gate CLI

Debe poder arrancarse `porter` y usar:

```text
Tab
history
Ctrl+K
help
clear
exit
```

## Gate runtime

`info` y `convert` deben ejecutar FFmpeg/FFprobe reales cuando corresponda.

## Gate command matrix

Todos los comandos obligatorios deben ser reales o estar marcados como no soportados por la capacidad concreta de FFmpeg; nunca simulados.

## Gate packaging

`pip install .` y wheel limpio deben funcionar.

## Gate final

Todas las casillas del checklist final deben ser PASS.

---

# 84. MATRIZ FINAL DE COMANDOS

La auditoría debe entregar una tabla con esta estructura:

| Comando | Existe | Ejecuta motor real | Validation | Test | Estado |
|---|---:|---:|---:|---:|---|
| convert | | | | | |
| compress | | | | | |
| optimize | | | | | |
| remux | | | | | |
| cut | | | | | |
| trim | | | | | |
| concat | | | | | |
| resize | | | | | |
| crop | | | | | |
| rotate | | | | | |
| fps | | | | | |
| speed | | | | | |
| mute | | | | | |
| extract-audio | | | | | |
| volume | | | | | |
| normalize | | | | | |
| fade | | | | | |
| frame | | | | | |
| thumbnail | | | | | |
| gif | | | | | |
| subtitle | | | | | |
| watermark | | | | | |
| info | | | | | |
| metadata | | | | | |
| formats | | | | | |
| codecs | | | | | |
| filters | | | | | |
| hardware | | | | | |
| diagnostics | | | | | |
| config | | | | | |
| lang | | | | | |
| clear | | | | | |
| help | | | | | |
| exit | | | | | |

Una celda vacía en algo obligatorio = no terminado.

---

# 85. MATRIZ FINAL DE UX

| Elemento | PASS/FAIL |
|---|---|
| Tema oscuro | |
| Paleta exacta | |
| Logo | |
| Prompt `porter ›` | |
| Completion | |
| History persistente | |
| Ctrl+K palette | |
| Help | |
| Spinner real | |
| Progress real | |
| Ctrl+C | |
| Error rendering | |
| JSON | |
| Quiet | |
| No-color | |
| Verbose | |
| Debug | |
| Non-interactive | |
| Dry-run | |
| Exit codes | |

---

# 86. MATRIZ FINAL DE MOTOR

| Componente | PASS/FAIL |
|---|---|
| Bundled FFmpeg detected | |
| FFmpeg version detected | |
| Bundled FFprobe detected / absent explicitly | |
| Safe subprocess | |
| Structured argv | |
| Progress parser | |
| Cancellation | |
| Temp output | |
| Atomic replace | |
| Output validation | |
| Capability registry real | |
| Capability cache | |
| Planner real | |
| Stream mapping | |
| Hardware detection | |

---

# 87. REPORTE FINAL OBLIGATORIO

Al terminar, la IA local debe escribir un reporte con:

## Architecture
Qué existe realmente.

## CLI
Qué funciona realmente y cómo se probó.

## FFmpeg
Ruta exacta, versión y origen bundled.

## FFprobe
Ruta/versión o `NOT BUNDLED`.

## Commands
Matriz PASS/FAIL.

## Tests
Comandos ejecutados + resultados.

## Packaging
Wheel/sdist + clean install.

## Legacy cleanup
Qué fue eliminado/actualizado.

## Known issues
Cualquier limitación real.

## Git state
Mostrar `git status`.

Indicar expresamente:

```text
NO PUSH REALIZADO
```

---

# 88. DEFINICIÓN DE DONE

Porter está terminado cuando:

```bash
pip install .
porter
```

abre una CLI profesional y funcional, con prompt, completion, history, palette, help y feedback visual; y cuando:

```bash
porter convert input.mp4 output.webm
```

ejecuta el FFmpeg bundled real, produce un WebM real y lo valida.

Además, la API Python puede realizar la misma operación sin pasar por la CLI.

---

# 89. DEFINICIÓN DE NOT DONE

Cualquiera de estos estados significa que el trabajo sigue incompleto:

```text
porter abre pero no hace nada
convert simula con sleep
ffmpeg apunta a dummy
capabilities son hardcoded como fuente primaria
Video/Audio/Image son contenedores vacíos
help existe pero comandos no
no hay completion
no hay history
no hay command palette
no hay pruebas reales
output no se valida
Ctrl+C deja temporales corruptos
pip install limpio falla
wheel no incluye assets requeridos
quedan referencias a Go/React/Tkinter/legacy
workflows siguen usando Go/Node
README documenta comportamiento inexistente
```

---

# 90. INSTRUCCIÓN FINAL A LA IA IMPLEMENTADORA

Ejecuta este documento como un contrato, no como una lluvia de ideas.

No reduzcas el alcance porque haya carpetas creadas. No declares “done” porque las clases existan. No sustituyas trabajo real por mock. No cambies el FFmpeg bundled. No descargues otro. No hagas push.

Primero consigue una CLI que ya tenga aspecto de producto terminado. Después conéctala al runtime real. Después implementa cada operación. Después prueba cada una. Después prueba packaging limpio. Finalmente audita el repositorio completo.

Cuando una capacidad no exista en el FFmpeg real, reporta:

```text
UNSUPPORTED BY CURRENT FFMPEG
```

Cuando FFprobe no exista en el paquete:

```text
FFPROBE NOT BUNDLED
```

Cuando algo no esté implementado:

```text
NOT IMPLEMENTED
```

Nunca simular una respuesta para evitar reportar una ausencia.

**El criterio de éxito es comportamiento observable y verificable.**

**NO PUSH.**
