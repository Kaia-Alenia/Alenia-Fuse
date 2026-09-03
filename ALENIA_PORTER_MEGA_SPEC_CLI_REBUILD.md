# ALENIA PORTER — MEGA SPEC DE CORRECCIÓN FINAL
## Reconstrucción definitiva de la experiencia CLI, arquitectura de interacción, comandos y formatos inteligentes

**Estado:** INSTRUCCIÓN OBLIGATORIA DE IMPLEMENTACIÓN  
**Base:** rama `migration-phase-a`  
**Objetivo:** corregir Porter sin volver a crear una aplicación falsa, una TUI forzada o una colección de menús.  
**Regla principal:** la IA implementadora NO toma decisiones de producto. Este documento define el comportamiento esperado.

---

# 0. CONTEXTO Y DIAGNÓSTICO

La migración a Python consiguió partes importantes del motor:

- paquete Python;
- backend real de FFmpeg;
- uso de FFprobe;
- operaciones reales en varias áreas;
- instalación mediante `pip`;
- comando `porter`;
- internacionalización parcial;
- estructura de librería + CLI.

Sin embargo, la experiencia actual tiene problemas graves.

## 0.1 Problema principal: Porter dejó de sentirse como una CLI

La implementación actual está empujando al usuario hacia una interfaz de menús/TUI.

Eso **NO es el objetivo**.

Porter debe sentirse como herramientas modernas tales como:

- Codex CLI;
- Gemini CLI;
- Claude Code;
- OpenCode;
- Aider.

Es decir:

```text
terminal normal
      ↓
porter
      ↓
prompt persistente
      ↓
usuario escribe
      ↓
Porter entiende
      ↓
autocomplete + sugerencias + comandos simples
      ↓
resultado
      ↓
vuelve al prompt
```

NO:

```text
porter
      ↓
gran menú
      ↓
flechas
      ↓
submenú
      ↓
más submenús
      ↓
el usuario queda atrapado en una TUI
```

La CLI es la interfaz principal.

---

# 1. DECISIÓN DE PRODUCTO DEFINITIVA

## 1.1 `porter` abre una CLI interactiva

Al ejecutar:

```powershell
porter
```

debe abrirse la sesión interactiva principal.

Ejemplo conceptual:

```text
                  ◈ ALENIA PORTER
              multimedia, made simple

  Type /help to explore commands.

porter ❯
```

El usuario debe poder escribir inmediatamente.

No debe estar obligado a elegir:

```text
Convert files
Compress files
Edit video
Edit audio
...
```

antes de poder usar Porter.

---

## 1.2 La CLI debe ser prompt-first

La interacción principal es:

```text
porter ❯ convert movie.mp4 to webm
```

o:

```text
porter ❯ /convert movie.mp4 to webm
```

o, si el parser humano lo soporta:

```text
porter ❯ make movie.mp4 smaller
```

Porter debe funcionar principalmente escribiendo.

Las interfaces visuales deben complementar la CLI, no reemplazarla.

---

## 1.3 Las flechas NO deben ser la experiencia principal

Las flechas pueden utilizarse para:

- seleccionar una sugerencia;
- navegar resultados de autocomplete;
- navegar historial;
- seleccionar una opción cuando una operación necesita una decisión.

Pero no deben ser obligatorias para usar Porter.

---

# 2. QUÉ DEBE EXISTIR FUERA DE LA SESIÓN INTERACTIVA

La shell externa debe mantenerse pequeña y limpia.

## 2.1 Comandos externos permitidos

Fuera de la sesión interactiva:

```powershell
porter
porter -h
porter --help
porter --version
porter version
porter formats
```

Opcionalmente:

```powershell
porter formats video
porter formats audio
porter formats image
```

si la implementación lo mantiene como consulta rápida.

---

## 2.2 TODO LO DEMÁS VIVE DENTRO DE PORTER

Operaciones como:

```text
convert
compress
optimize
trim
cut
concat
resize
crop
rotate
fps
speed
mute
extract-audio
volume
normalize
fade
frame
thumbnail
gif
subtitle
watermark
metadata
info
codecs
filters
hardware
config
lang
help
clear
exit
```

deben funcionar dentro de:

```text
porter ❯
```

No se debe convertir `porter --help` en una enorme lista de todas las operaciones.

---

# 3. AYUDA EXTERNA LIMPIA

`porter -h` debe mostrar solamente la estructura esencial.

Ejemplo:

```text
ALENIA PORTER
Professional multimedia toolkit

Usage:
  porter                 Start interactive Porter CLI
  porter formats         Browse supported output formats
  porter --version       Show version
  porter --help          Show this help

Interactive commands:
  Start Porter and type /help

Examples:
  porter
  porter formats
  porter formats video
```

NO mostrar una página gigantesca con 30 comandos.

La documentación de comandos vive dentro de Porter.

---

# 4. DISEÑO VISUAL DE LA CLI

## 4.1 Porter NO debe parecer un menú antiguo

Eliminar la sensación de:

- menú de consola;
- lista de opciones permanente;
- aplicación DOS;
- instalador;
- herramienta académica;
- TUI de administración.

Debe parecer una CLI moderna.

---

## 4.2 Pantalla de inicio

Al iniciar, mostrar algo compacto.

Ejemplo de dirección visual:

```text

                     ◈
              ALENIA PORTER
            multimedia toolkit

       Convert • edit • optimize media

       Type /help for commands

porter ❯
```

No usar un banner gigante.

No usar múltiples cajas decorativas.

No desperdiciar la pantalla.

---

## 4.3 Branding ASCII

Crear un logo ASCII/Unicode propio, compacto y elegante.

Debe funcionar correctamente en:

- Windows Terminal;
- PowerShell;
- CMD cuando sea posible;
- Linux terminals;
- macOS Terminal/iTerm.

No depender de caracteres que rompan encoding.

Si se usan caracteres Unicode, tener fallback ASCII.

---

## 4.4 Paleta visual

Tema oscuro moderno.

Colores:

```text
Primary          #8B5CF6
Primary bright   #A78BFA

Cyan             #22D3EE

Success          #22C55E
Warning          #F59E0B
Error            #EF4444

Text             #F8FAFC
Secondary        #CBD5E1
Muted            #94A3B8
Dim              #64748B
```

Uso:

- morado → identidad y prompt;
- cyan → rutas, información técnica y datos;
- verde → éxito;
- amarillo → advertencias;
- rojo → errores;
- gris → información secundaria.

No colorear cada línea.

---

# 5. EL PROMPT

El prompt debe ser reconocible.

Ejemplo recomendado:

```text
porter ❯
```

Alternativa:

```text
porter ›
```

Elegir UNO y usarlo consistentemente.

Recomendación final:

```text
porter ❯
```

El prompt debe:

- funcionar en todos los idiomas;
- no cambiar innecesariamente;
- mantenerse visible;
- volver después de cada operación.

---

# 6. COMANDOS CON `/`

## 6.1 Porter debe tener comandos discoverables

Al escribir:

```text
/
```

debe aparecer una lista de comandos.

Ejemplo:

```text
porter ❯ /

  /convert        Convert media files
  /compress       Reduce file size
  /edit           Video and audio editing
  /extract        Extract media content
  /info           Analyze a file
  /formats        Browse output formats
  /config         Porter settings
  /help           Show all commands
```

La lista debe aparecer como sugerencias/autocomplete.

No como un menú permanente.

---

## 6.2 Selección

Cuando la lista está abierta:

- ↑ mueve arriba;
- ↓ mueve abajo;
- Tab completa;
- Enter selecciona/ejecuta según contexto;
- Esc cierra sugerencias.

La CLI debe seguir siendo CLI.

---

# 7. NO IMPLEMENTAR UNA COMMAND PALETTE REDUNDANTE

La actual idea de una `Command Palette` separada no tiene sentido si:

- `/` ya descubre comandos;
- autocomplete ya busca comandos;
- `/help` ya explica comandos.

Por lo tanto:

## DECISIÓN

Eliminar la command palette separada si duplica funcionalidad.

NO implementar:

```text
Ctrl+K → ventana especial → buscar comando
```

si el mismo problema se resuelve naturalmente mediante:

```text
/
```

y autocomplete contextual.

Menos interfaces duplicadas.

Una sola experiencia coherente.

---

# 8. AUTOCOMPLETADO REAL

El autocomplete es obligatorio.

## 8.1 Debe completar comandos

```text
porter ❯ con<TAB>
```

Resultado:

```text
porter ❯ convert
```

---

## 8.2 Debe sugerir mientras se escribe

```text
porter ❯ c
```

Debe sugerir:

```text
convert
compress
crop
cut
concat
codecs
config
```

ordenado por relevancia.

---

## 8.3 Debe ser contextual

Después de:

```text
porter ❯ convert file.mp4 to
```

las sugerencias deben ser targets válidos para `file.mp4`.

NO:

```text
todos los formatos del mundo
```

---

## 8.4 Debe completar rutas

Después de un argumento que espera archivo:

```text
porter ❯ convert C:\vid
```

debe sugerir rutas reales.

---

## 8.5 Debe completar opciones

Ejemplo:

```text
porter ❯ compress movie.mp4 --
```

debe sugerir:

```text
--quality
--target-size
--preset
--overwrite
```

solo las opciones válidas para ese comando.

---

# 9. SINTAXIS HUMANA

Porter debe ocultar la complejidad de FFmpeg.

## 9.1 Ejemplos principales

```text
convert movie.mp4 to webm
convert song.wav to flac
convert photo.png to bmp

compress movie.mp4
make movie.mp4 smaller

trim movie.mp4 from 00:01:00 to 00:02:00

resize movie.mp4 to 1920x1080

extract audio from movie.mp4

thumbnail movie.mp4 at 00:00:10

speed movie.mp4 2x

normalize song.mp3

rotate movie.mp4 90
```

---

## 9.2 Los aliases deben ser inteligentes

Ejemplo:

```text
make smaller
```

puede resolver a:

```text
compress
```

pero los aliases no deben convertirse en comandos duplicados.

El `CommandRegistry` debe resolverlos.

---

# 10. HELP INTERNO

Dentro de Porter:

```text
porter ❯ /help
```

debe mostrar ayuda organizada.

Ejemplo:

```text
Commands

  CONVERT
    /convert       Convert files
    /compress      Reduce size
    /optimize      Optimize for common use

  VIDEO
    /trim          Trim media
    /cut           Cut segments
    /concat        Join files
    /resize        Change dimensions
    /crop          Crop video
    /rotate        Rotate media
    /fps           Change frame rate
    /speed         Change playback speed

  AUDIO
    /mute
    /extract-audio
    /volume
    /normalize
    /fade

  EXTRACT
    /frame
    /thumbnail
    /gif

  INFORMATION
    /info
    /formats
    /codecs
    /filters
    /hardware

  PORTER
    /config
    /lang
    /clear
    /help
    /exit
```

Debe ser compacto.

---

# 11. `HELP <COMMAND>`

Ejemplo:

```text
porter ❯ /help convert
```

Debe explicar:

```text
CONVERT

Convert a media file to a compatible output format.

Usage:
  convert <input> to <format>
  convert <input> <output>

Examples:
  convert movie.mp4 to webm
  convert song.wav to flac

Options:
  --quality
  --codec
  --overwrite
```

No imprimir documentación de FFmpeg.

---

# 12. OPERACIONES COMPLETAS

La implementación actual sigue incompleta respecto a Porter.

El catálogo objetivo debe cubrir, como mínimo:

## CONVERSIÓN

```text
convert
remux
```

## COMPRESIÓN / OPTIMIZACIÓN

```text
compress
optimize
```

## VIDEO

```text
trim
cut
concat
resize
crop
rotate
fps
speed
mute
```

## AUDIO

```text
extract-audio
volume
normalize
fade
speed
trim
```

## IMAGEN / FRAMES

```text
frame
thumbnail
gif
convert
resize
crop
rotate
```

## CONTENIDO

```text
subtitle
watermark
metadata
```

## INFORMACIÓN

```text
info
formats
codecs
filters
hardware
```

## PORTER

```text
config
lang
clear
help
exit
```

---

# 13. CATEGORÍAS SON PARA HELP, NO PARA ATRAPAR AL USUARIO

Las categorías pueden organizar:

- `/help`;
- sugerencias;
- documentación.

NO obligar al usuario a entrar:

```text
Video
 → Edit
   → Resize
```

El usuario debe poder escribir directamente:

```text
resize movie.mp4 1280x720
```

---

# 14. FORMATOS — REQUISITO CRÍTICO

La implementación actual no puede mostrar solamente cuatro formatos por categoría.

Eso es artificial.

---

# 15. `porter formats`

Debe funcionar fuera de la CLI y mostrar información organizada.

Ejemplo:

```text
ALENIA PORTER — OUTPUT FORMATS

Video / Containers
  mp4   mkv   webm   mov   avi   flv   ...
  + 14 more

Audio
  mp3   wav   flac  opus   aac   m4a   ...
  + 10 more

Images
  png   jpg   webp  bmp    tiff  avif  ...
  + 18 more

Use:
  porter formats video
  porter formats audio
  porter formats image

Inside Porter:
  /formats
```

---

# 16. `formats` NO PUEDE SER UNA LISTA FIJA

El catálogo técnico debe venir del FFmpeg bundled real.

Descubrir:

```text
ffmpeg -formats
ffmpeg -muxers
ffmpeg -demuxers
ffmpeg -encoders
ffmpeg -decoders
ffmpeg -filters
ffmpeg -hwaccels
```

La información descubierta debe convertirse a un modelo estructurado.

---

# 17. CLASIFICACIÓN DE FORMATOS

Cada entrada debe tener metadata como:

```python
FormatCapability(
    name=...,
    extensions=[...],
    can_input=True,
    can_output=True,
    category=...,
    is_protocol=False,
    is_pipe=False,
    is_device=False,
)
```

Categorías:

```text
video
audio
image
container
raw
special
protocol
pipe
device
unknown
```

---

# 18. NO USAR `KNOWN_VIDEO` COMO FUENTE DE VERDAD

Las listas manuales pueden existir solamente como:

```text
metadata complementaria
```

Nunca como el mecanismo que decide qué soporta Porter.

FFmpeg real es la fuente técnica.

---

# 19. FILTRADO DE ENTRADAS INTERNAS

No ofrecer como formato de usuario:

```text
webp_pipe
image2pipe
pipe
rtsp
http
udp
alsa
dshow
```

cuando no representan un archivo output normal.

Separar:

```text
backend capability
```

de:

```text
user-selectable file format
```

---

# 20. TODOS LOS TARGETS VÁLIDOS

Porter debe ser amplio.

Pero amplio NO significa irresponsable.

Un target aparece solamente si:

1. FFmpeg bundled puede producirlo;
2. existe una ruta de codificación/muxing válida;
3. corresponde al tipo de operación;
4. es un archivo normal;
5. Porter puede validar el resultado.

---

# 21. TARGETS CONTEXTUALES

Nunca mostrar exactamente la misma lista para todos los inputs.

Primero:

```text
FFprobe
```

Luego analizar:

```text
streams
codecs
dimensions
pixel format
alpha
bit depth
sample rate
channels
duration
```

Después calcular:

```text
valid targets
recommended targets
other valid targets
```

---

# 22. VIDEO INTELIGENTE

Para video, evaluar:

```text
video stream
audio stream
subtitle stream
target container
available encoders
container compatibility
```

Ejemplo:

```text
MP4 → WebM
```

No copiar automáticamente:

```text
H.264 + AAC
```

si el target WebM no lo acepta.

Seleccionar una estrategia válida usando capacidades reales.

---

# 23. STREAM COPY

El planner debe decidir:

```text
stream copy
```

solamente cuando:

```text
input codec compatible
+
target container compatible
+
operación no requiere reencode
```

---

# 24. REENCODE

Cuando sea necesario:

```text
decoder disponible
+
encoder disponible
+
target muxer disponible
```

Seleccionar una estrategia real.

---

# 25. AUDIO

Para audio, targets válidos dependen de:

- codec;
- encoder;
- container;
- canales;
- sample rate cuando corresponda.

Ejemplo:

```text
WAV → FLAC
```

debe aparecer si el backend bundled lo soporta.

---

# 26. IMÁGENES

Las imágenes necesitan reglas semánticas.

No basta con preguntar:

```text
¿FFmpeg puede producir algo?
```

---

# 27. ALPHA / RGBA

Detectar:

```text
alpha
rgba
yuva
transparency
```

Si el target pierde transparencia:

```text
Warning:
JPEG does not support transparency.

Choose:
  flatten on white
  flatten on black
  choose custom background
  cancel
```

No perder alpha silenciosamente.

---

# 28. GIF

Una imagen estática puede producir técnicamente un GIF de un frame.

Pero no debe recomendarse como conversión normal.

Diferenciar:

```text
normal format conversion
```

de:

```text
animation operation
```

---

# 29. BMP

BMP debe aparecer si es realmente soportado y válido.

No ocultar formatos solo porque sean menos modernos.

---

# 30. OTHER FORMATS

Después de los formatos recomendados:

```text
Other compatible formats...
```

Debe permitir explorar el resto.

No limitar el catálogo a cuatro.

---

# 31. SEARCH DE FORMATOS

Dentro de una selección contextual:

```text
Search formats: av
```

debe encontrar:

```text
AVIF
AVI
...
```

según los targets realmente válidos.

---

# 32. PREFLIGHT REAL

Cuando la compatibilidad no pueda demostrarse estáticamente:

```text
analyze input
      ↓
build plan
      ↓
small real FFmpeg preflight
      ↓
validate with FFprobe
      ↓
cache capability result
      ↓
perform full operation
```

---

# 33. PREFLIGHT NO ES ÉXITO POR `returncode == 0`

Éxito requiere:

```text
return code == 0
output exists
size > 0
FFprobe readable
expected format
expected streams
expected semantic properties
```

---

# 34. VALIDACIÓN FINAL OBLIGATORIA

Después de cada operación:

## Nivel 1

```text
FFmpeg return code == 0
```

## Nivel 2

```text
output exists
output size > 0
```

## Nivel 3

```text
FFprobe can read output
```

## Nivel 4

Validar:

```text
container
streams
codec
dimensions
audio properties
```

## Nivel 5

Validar el efecto solicitado.

Ejemplos:

```text
resize → dimensions changed
trim → duration approximately expected
mute → no audio stream
extract-audio → audio output exists
rotate → intended transform applied
```

---

# 35. CERO BYTES ES FALLO ABSOLUTO

Esto está prohibido:

```text
✓ Conversion complete
Size: 0 KB
```

Debe ser:

```text
✗ Conversion failed

The output file is empty and was rejected.
```

---

# 36. `webp_pipe` Y EQUIVALENTES

Una entrada interna como:

```text
webp_pipe
```

NO es automáticamente:

```text
WebP file output
```

La capa de capacidades debe saber diferenciarlo.

---

# 37. INPUT == OUTPUT

Rechazar:

```text
convert movie.mp4 movie.mp4
```

a menos que una operación explícita de in-place exista y sea segura.

Mensaje:

```text
Input and output cannot be the same file.
```

---

# 38. BATCH

El batch actual debe corregirse completamente.

Nunca:

```text
a.avi → a.mp4
a.mkv → a.mp4
a.mov → a.mp4
```

sobrescribiendo.

---

# 39. NOMBRES ÚNICOS

Usar estrategia segura:

```text
sample.mp4
sample_1.mp4
sample_2.mp4
```

o preservar carpetas relativas.

La estrategia debe ser determinista.

---

# 40. OVERWRITE

Por defecto:

```text
NO overwrite
```

Si existe:

```text
Output already exists.

Overwrite? [y/N]
```

En CLI no interactiva:

```text
--overwrite
```

para autorizar.

---

# 41. PROGRESO

El progreso debe provenir de datos reales de FFmpeg.

Mostrar, cuando esté disponible:

```text
Converting movie.mp4 → movie.webm

  ████████████████████░░░░░  78%
  00:01:34 / 00:02:00   2.4x
```

No inventar porcentajes.

---

# 42. RESULTADO FINAL DE OPERACIÓN

Al terminar:

```text
✓ Done

  Output    movie.webm
  Format    WebM
  Video     VP9
  Audio     Opus
  Size      18.4 MB
```

Solo mostrar información que realmente fue validada.

---

# 43. ERRORES

Errores normales:

```text
✗ Conversion failed

WebM cannot be produced with the requested stream configuration.

Try:
  • Let Porter choose compatible codecs
  • Choose another output format
```

No mostrar traceback.

`--debug` puede mostrar detalles técnicos.

---

# 44. ARQUITECTURA ÚNICA

Debe existir una sola ruta:

```text
CLI
 ↓
Command Registry
 ↓
Parser
 ↓
Operation
 ↓
Planner
 ↓
Job
 ↓
FFmpeg Backend
 ↓
Validator
```

La API Python debe usar exactamente el mismo core.

---

# 45. PROHIBIDO DUPLICAR LÓGICA

NO:

```text
CLI conversion logic
API conversion logic
```

por separado.

Sí:

```text
shared operation engine
```

---

# 46. API PYTHON

Mantener una API simple:

```python
from alenia_porter import Video

result = (
    Video("movie.mp4")
    .convert("webm")
    .output("movie.webm")
    .run()
)
```

Pero la API debe usar el mismo:

```text
planner
executor
validator
```

que la CLI.

---

# 47. LIMPIEZA DE LA IMPLEMENTACIÓN ACTUAL

Eliminar o corregir:

- menús que fuerzan navegación;
- command palette redundante;
- TODOs de autocomplete;
- listas artificiales de cuatro formatos;
- clasificación manual como fuente de verdad;
- falsos éxitos;
- outputs de 0 bytes aceptados;
- pipes expuestos como formatos;
- colisiones batch;
- ayuda externa gigantesca;
- UX inconsistente entre shell e interactivo.

---

# 48. AUDITORÍA DE TODO

Antes de declarar terminado, revisar:

```text
src/alenia_porter/cli/
src/alenia_porter/ffmpeg/
src/alenia_porter/planner/
src/alenia_porter/operations/
src/alenia_porter/jobs/
src/alenia_porter/api/
src/alenia_porter/i18n/
tests/
pyproject.toml
.github/
scripts/
README.md
```

Buscar:

```text
TODO
FIXME
pass
NotImplemented
mock
dummy
simulation
time.sleep
shell=True
hardcoded capabilities
```

Cada resultado debe:

- eliminarse;
- implementarse;
- o justificarse técnicamente.

---

# 49. TESTS OBLIGATORIOS

## CLI

```text
[ ] porter opens interactive prompt
[ ] /help works
[ ] / shows command suggestions
[ ] autocomplete works
[ ] Tab completion works
[ ] history works
[ ] Esc closes suggestions
[ ] errors do not crash prompt_toolkit
```

## HELP

```text
[ ] porter -h is concise
[ ] porter -h does not dump all internal commands
[ ] /help contains command catalog
[ ] /help <command> works
```

## FORMATS

```text
[ ] real FFmpeg capabilities discovered
[ ] protocols excluded
[ ] devices excluded
[ ] pipes excluded
[ ] input-only targets excluded
[ ] contextual targets differ by media type
[ ] other compatible formats available
```

## REAL MEDIA

```text
[ ] MP4 → WebM
[ ] MP4 → MKV
[ ] WAV → FLAC
[ ] WAV → MP3
[ ] PNG → WebP
[ ] PNG → BMP
[ ] RGBA PNG → JPEG requires alpha decision
```

## VALIDATION

```text
[ ] zero-byte output rejected
[ ] invalid output rejected
[ ] pipe mistaken for file rejected
[ ] expected container verified
[ ] expected streams verified
```

## SAFETY

```text
[ ] input == output rejected
[ ] overwrite protected
[ ] batch collisions prevented
[ ] Ctrl+C cleanup works
```

---

# 50. DEMOSTRACIÓN FINAL OBLIGATORIA

No declarar terminado solo con:

```text
pytest passed
```

Demostrar visualmente y funcionalmente:

## Inicio

```powershell
porter
```

Debe abrir una CLI moderna.

## Discoverability

```text
porter ❯ /
```

Debe mostrar comandos.

## Help

```text
porter ❯ /help
```

## Autocomplete

Escribir parcialmente un comando y demostrar sugerencias.

## Human syntax

```text
porter ❯ convert test.mp4 to webm
```

## Contextual formats

Seleccionar:

- video;
- audio;
- imagen RGBA.

Demostrar que los targets cambian.

## Conversion

Realizar conversión.

## Validation

Ejecutar:

```text
/info output
```

y demostrar formato real.

## Negative cases

Demostrar:

```text
input == output → rejected
zero byte → rejected
invalid target → rejected
batch collision → prevented
```

---

# 51. CRITERIO FINAL DE EXPERIENCIA

Un usuario que nunca ha usado FFmpeg debe poder:

```text
abrir Porter
↓
escribir una intención simple
↓
recibir sugerencias
↓
descubrir comandos con /
↓
pedir ayuda
↓
seleccionar un archivo
↓
ver solamente opciones razonables
↓
convertir
↓
obtener un archivo validado
```

Sin:

- memorizar comandos complejos de FFmpeg;
- aprender codecs;
- conocer muxers;
- entender pipes;
- saber pixel formats;
- saber cuándo hacer stream copy.

Porter debe hacer eso internamente.

---

# 52. DEFINICIÓN ABSOLUTA DE TERMINADO

NO usar la palabra:

```text
DONE
COMPLETE
100%
FINISHED
```

hasta cumplir:

```text
[ ] Porter parece una CLI moderna
[ ] No obliga a usar una TUI
[ ] Prompt-first UX
[ ] / descubre comandos
[ ] autocomplete real
[ ] TAB real
[ ] history real
[ ] help interno completo
[ ] help externo compacto
[ ] command palette redundante eliminada
[ ] todos los comandos objetivo implementados o documentados con alcance claro
[ ] capabilities reales de FFmpeg
[ ] formatos no limitados artificialmente
[ ] protocolos filtrados
[ ] pipes filtrados
[ ] targets contextuales
[ ] video inteligente
[ ] audio inteligente
[ ] imágenes semánticamente correctas
[ ] alpha manejado explícitamente
[ ] preflight real cuando hace falta
[ ] output validado
[ ] 0 bytes rechazado
[ ] input == output rechazado
[ ] batch seguro
[ ] overwrite seguro
[ ] progreso real
[ ] cancelación real
[ ] API comparte core
[ ] i18n coherente
[ ] tests de regresión
[ ] demostración manual real
[ ] documentación actualizada
```

---

# 53. INSTRUCCIÓN FINAL PARA LA IA IMPLEMENTADORA

No crear otra capa visual por crearla.

No reemplazar una CLI con una TUI.

No limitar artificialmente funcionalidades para que la interfaz parezca simple.

No hardcodear cuatro formatos.

No declarar una conversión exitosa porque FFmpeg devolvió código 0.

No confiar en listas manuales como fuente técnica.

No mostrar capacidades internas de FFmpeg como opciones de usuario.

No duplicar motores entre CLI y API.

No marcar el trabajo terminado hasta ejecutar pruebas reales con archivos reales.

**La prioridad es una CLI elegante, rápida, moderna y natural que esconda la complejidad de FFmpeg sin esconder capacidades reales.**

# FIN DE LA ESPECIFICACIÓN
