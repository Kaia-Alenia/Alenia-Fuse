# ALENIA PORTER — MASTER EXECUTION SPECIFICATION

## 0. PROPÓSITO

Este documento es el **contrato de ejecución** para reconstruir Alenia-Porter como producto nuevo sobre la base funcional existente.

La IA local debe seguir estas instrucciones literalmente.

No debe decidir una arquitectura alternativa.

No debe detenerse después de "hacer que compile".

No debe declarar el trabajo terminado porque algunos tests pasen.

El objetivo es terminar con un producto usable:

```text
pip install alenia-porter
        ↓
porter
        ↓
CLI interactiva profesional
        ↓
Python Library
        ↓
Operation Planner
        ↓
FFmpeg / FFprobe / Pillow
```

---

# 1. DECISIÓN ARQUITECTÓNICA FINAL

## 1.1. Una sola arquitectura

La arquitectura final es:

```text
Python
│
├── Public Python API
│
├── Media Models
│
├── Operation Layer
│
├── Capability Detection
│
├── Operation Planner
│
├── Job / Process Manager
│
├── CLI / TUI
│
├── Config
│
└── i18n
      │
      ├── FFmpeg
      ├── FFprobe
      └── Pillow
```

No mantener arquitecturas paralelas.

## 1.2. Lenguajes

El producto final debe utilizar:

```text
Python
```

como lenguaje de implementación.

Go no forma parte del producto final.

React/Node/npm no forman parte del runtime ni del build del producto final.

---

# 2. PRODUCTO FINAL

Porter será simultáneamente:

```text
1. Librería Python instalable por pip.
2. CLI interactiva.
3. CLI one-shot para scripts.
```

Las tres interfaces deben usar el mismo núcleo.

```text
             Porter Core
                 │
       ┌─────────┼─────────┐
       │         │         │
      API       CLI       TUI
```

La CLI nunca debe contener lógica multimedia duplicada.

---

# 3. REGLA ABSOLUTA: CORE FIRST

Antes de hacer una CLI bonita, debe existir un core Python estable.

La dependencia es:

```text
Core
  ↓
API
  ↓
CLI
```

Nunca:

```text
CLI
  ↓
lógica propia
  ↓
FFmpeg
```

---

# 4. PUNTO DE PARTIDA Y SEGURIDAD

Antes de modificar código:

1. detectar rama actual;
2. crear una rama de trabajo;
3. registrar SHA inicial;
4. ejecutar tests existentes;
5. registrar qué funciona y qué está roto;
6. guardar el resultado en un informe de migración.

No borrar código antes de conocer sus dependencias.

El repositorio debe poder compararse antes/después.

---

# 5. FASE 0 — INVENTARIO OBLIGATORIO

Antes de implementar:

### Inspeccionar

```text
src/
cmd/
legacy/
tests/
docs/
.github/
scripts/
pyproject.toml
Makefile
README.md
launchers
installers
```

### Buscar

```text
.go
Go
go.mod
go.sum
cmd/ap
legacy
legacy/ide
React
npm
node
tkinter
IDLE
gui_web
FFmpeg
FFprobe
Pillow
subprocess
```

### Entregar

Crear:

```text
docs/MIGRATION_AUDIT.md
```

con:

```text
archivo
responsabilidad
dependencias
estado
migrar/eliminar/conservar
razón
```

No inventar funcionalidad que no exista.

---

# 5A. DECISIÓN CERRADA — FFMPEG INCLUIDO POR PORTER

Esta decisión es obligatoria y no queda abierta a interpretación.

## 5A.1. Fuente oficial de FFmpeg

Porter **ya distribuye actualmente un FFmpeg completo dentro del proyecto**.

La nueva arquitectura debe continuar utilizando el binario proporcionado por Porter.

Ruta conceptual obligatoria:

```text
Alenia-Porter/
└── bin/
    ├── ffmpeg
    └── ffprobe   # si está incluido actualmente
```

La IA local debe inspeccionar el árbol real y conservar la ubicación actual de los binarios.

## 5A.2. Regla de prioridad

El orden obligatorio para resolver FFmpeg es:

```text
1. FFmpeg incluido con Porter;
2. FFprobe incluido con Porter;
3. configuración explícita del usuario, únicamente como mecanismo de diagnóstico/override si el producto ya lo necesita;
4. PATH del sistema solamente como fallback explícito y controlado;
5. si no existe una capacidad válida:
       error claro;
       no ejecutar la operación.
```

El FFmpeg incluido por Porter es la **fuente de verdad principal**.

No sustituirlo silenciosamente por:

```text
apt ffmpeg
brew ffmpeg
winget ffmpeg
choco ffmpeg
PATH del sistema
```

cuando el binario distribuido por Porter está disponible y es válido.

## 5A.3. No descargar FFmpeg

Porter no debe descargar FFmpeg automáticamente durante la ejecución.

No añadir:

```text
download manager
auto-installer
remote binary fetcher
```

como solución a una instalación incompleta.

La distribución de Porter debe contener el binario requerido según la plataforma objetivo.

## 5A.4. FFmpeg debe permanecer completo

La IA **NO debe reemplazar, recortar o recompilar el FFmpeg existente simplemente para reducir tamaño**.

El FFmpeg distribuido actualmente se considera una dependencia funcional importante.

Debe conservar sus capacidades salvo que una versión posterior explícitamente aprobada lo sustituya.

No eliminar codecs, encoders, decoders, muxers, demuxers, filters o aceleración hardware únicamente porque Porter no los use todavía.

## 5A.5. FFprobe

La IA debe inspeccionar `bin/` y determinar si actualmente existe:

```text
ffprobe
ffprobe.exe
```

según plataforma.

### Si ya existe

Debe conservarse y utilizarse como fuente oficial para inspección de medios.

### Si no existe

NO descargarlo automáticamente.

En ese caso, la IA debe documentar la ausencia y utilizar una estrategia explícita y estable aprobada para la versión final; no inventar un mecanismo durante la migración.

## 5A.6. FFmpegResolver

Crear o consolidar:

```text
FFmpegResolver
```

Responsabilidades:

```text
locate ffmpeg included by Porter
locate ffprobe included by Porter
verify executable availability
read version
read capabilities
expose absolute paths
```

La aplicación no debe tener rutas hardcodeadas repetidas en diferentes módulos.

## 5A.7. Capability Detection

Todas las capacidades deben descubrirse desde **el FFmpeg que realmente está usando Porter**.

No utilizar como fuente principal:

```text
internet
Wikipedia
listas estáticas copiadas
FFmpeg instalado en otra ruta
```

El flujo obligatorio es:

```text
Porter bundled FFmpeg
        ↓
FFmpegResolver
        ↓
version/capability discovery
        ↓
CapabilityRegistry
        ↓
OperationPlanner
```

## 5A.8. Mostrar el origen en diagnóstico

`porter info --environment` debe poder indicar:

```text
FFmpeg:
  source: bundled
  path: ...
  version: ...

FFprobe:
  source: bundled
  path: ...
  version: ...
```

Esto facilita diagnosticar instalaciones.

## 5A.9. Integridad del binario

Porter debe comprobar que el binario existe y puede ejecutarse.

Si la distribución soporta una validación adicional de integridad, puede utilizarse; pero no inventar un sistema criptográfico complejo sin necesidad.

Una ausencia o fallo del binario debe producir un error claramente diagnosticable.

## 5A.10. Empaquetado

La migración debe garantizar que los binarios de `bin/` lleguen al usuario final cuando corresponda a la plataforma de distribución.

No basta con que existan en el repositorio.

Debe probarse:

```text
source repository
      ↓
build/package
      ↓
clean environment
      ↓
install
      ↓
bundled FFmpeg found
      ↓
real operation succeeds
```

## 5A.11. Licencias

Como Porter distribuye FFmpeg, conservar y revisar los avisos/licencias correspondientes al binario incluido.

La IA no debe eliminar archivos de licencia o atribución asociados a FFmpeg.

No asumir que mover el binario dentro del paquete elimina obligaciones de distribución.

---

# 6. FASE 1 — CONSTRUIR EL CORE PYTHON

Crear una arquitectura limpia.

Objetivo conceptual:

```text
alenia_porter/
│
├── api/
├── media/
├── operations/
├── ffmpeg/
├── planner/
├── jobs/
├── cli/
├── config/
├── i18n/
└── errors/
```

No crear módulos vacíos.

Cada módulo debe tener responsabilidad real.

---

# 7. MEDIA MODEL

Crear objetos para representar medios.

Como mínimo:

```text
Media
Video
Audio
Image
Stream
Format
Codec
```

El modelo debe permitir consultar:

```text
path
container
streams
duration
size
video codec
audio codec
width
height
fps
sample rate
channels
bitrate
metadata
```

La información debe venir de FFprobe cuando corresponda.

---

# 8. CAPABILITY SYSTEM

Crear un sistema de capacidades real.

Debe consultar la instalación concreta de FFmpeg.

Debe detectar:

```text
muxers
demuxers
encoders
decoders
filters
protocols
hwaccels
```

No usar listas estáticas como única fuente de verdad.

---

# 9. FORMAT CLASSIFICATION

Cada formato/capacidad debe poder clasificarse:

```text
INPUT
OUTPUT
INPUT_AND_OUTPUT
STREAMING
PIPE
METADATA
UNSUPPORTED
```

Y:

```text
COMMON
ADVANCED
HIDDEN
```

La interfaz común no debe mostrar formatos técnicos que no sean destinos de archivo normales.

Regla absoluta:

```text
FFmpeg reconoce algo
≠
Porter puede producirlo como archivo
```

---

# 10. OPERATION PLANNER

Crear:

```text
OperationPlanner
```

Debe recibir:

```text
intent
input
target
options
capabilities
```

y producir un plan estructurado.

Ejemplo:

```text
OperationPlan
├── operation
├── backend
├── container
├── video codec
├── audio codec
├── stream copy
├── reencode
├── filters
├── hardware
├── command arguments
├── warnings
└── explanation
```

---

# 11. EXPLICABILIDAD

Cada operación debe poder responder:

```text
¿Qué voy a hacer?
¿Por qué?
¿Por qué ese codec?
¿Por qué ese container?
¿Necesito recodificar?
¿Puedo hacer stream copy?
¿Puedo usar GPU?
¿Por qué no puedo usar una opción?
```

La CLI debe poder mostrar esto.

La API debe exponerlo estructuradamente.

---

# 12. BACKENDS

Crear una abstracción de backend.

Primarios:

```text
FFmpegBackend
FFprobeBackend
PillowBackend
```

No conectar la CLI directamente a `subprocess`.

---

# 13. FFmpeg EXECUTION

Toda ejecución debe:

```text
1. generar argumentos estructurados;
2. no usar shell=True para entrada del usuario;
3. iniciar proceso;
4. capturar stdout/stderr;
5. calcular progreso;
6. soportar cancelación;
7. capturar código de salida;
8. validar el resultado;
9. limpiar temporales.
```

---

# 14. STREAM COPY

Porter debe preferir stream copy cuando sea técnicamente correcto.

Ejemplos:

```text
remux
mute
extract audio cuando el codec sea compatible
cortes rápidos cuando la precisión lo permita
```

No recodificar innecesariamente.

---

# 15. RE-ENCODE

Utilizar recodificación cuando una operación lo requiera:

```text
resize
crop
rotate
filters
speed
fps change
quality compression
```

Las pistas no afectadas deben conservarse como copy cuando sea posible.

---

# 16. VALIDACIÓN DE OUTPUT

Una operación solo es SUCCESS cuando:

```text
process exit = success
AND
file exists
AND
file size > 0
AND
output can be probed
AND
expected streams exist
AND
container is readable
```

No confiar solo en exit code 0.

---

# 17. TEMP FILES

Nunca escribir directamente sobre el archivo final cuando exista riesgo.

Usar:

```text
temporary file
↓
validate
↓
rename
```

En fallo:

```text
temporary file
↓
delete
```

---

# 18. JOB SYSTEM

Crear un modelo:

```text
Job
JobState
JobManager
ProgressEvent
```

Estados:

```text
PLANNING
ANALYZING
RUNNING
FINALIZING
VALIDATING
SUCCESS
FAILED
CANCELLED
```

---

# 19. CLI — PRODUCTO VISIBLE

Ejecutar:

```bash
porter
```

debe abrir la CLI interactiva.

Debe sentirse como una herramienta moderna de terminal.

Características:

```text
prompt
autocomplete
history
suggestions
command palette
spinner
progress
structured output
clean errors
Ctrl+C
```

---

# 20. PROMPT

Usar un prompt reconocible:

```text
porter ›
```

El usuario puede introducir:

```text
convert ...
cut ...
compress ...
```

---

# 21. STARTUP

Al iniciar la CLI mostrar:

```text
ASCII logo
version
FFmpeg availability
optional GPU/capability summary
prompt
```

No imprimir diagnósticos enormes.

Ejemplo:

```text
╭──────────────────────────────╮
│        ALENIA PORTER         │
│      multimedia toolkit      │
╰──────────────────────────────╯

✓ FFmpeg ready
✓ FFprobe ready

porter ›
```

---

# 22. SPINNER

Crear un único sistema de actividad visual.

Estados:

```text
⠋
⠙
⠹
⠸
⠼
⠴
⠦
⠧
⠇
⠏
```

Puede utilizarse otro diseño equivalente, pero debe ser:

```text
estable
limpio
rápido
portable
```

Debe desaparecer siempre al terminar.

Nunca dejar un spinner huérfano.

---

# 23. PROGRESO

Para trabajos largos:

```text
⣾ Processing video.mp4      47%
```

Para operaciones que no permitan progreso exacto:

```text
⣾ Processing video.mp4
```

Nunca inventar porcentajes.

---

# 24. OUTPUT CLEAN

La CLI normal no debe mostrar el stderr completo de FFmpeg.

Mostrar:

```text
acción
estado
progreso
advertencias relevantes
resultado
```

`--verbose` puede mostrar diagnóstico técnico.

---

# 25. COMMAND REGISTRY

Todos los comandos deben registrarse centralmente.

Cada definición debe contener:

```text
name
aliases
description
usage
arguments
options
examples
handler
```

De aquí deben generarse:

```text
help
autocomplete
suggestions
documentation
```

---

# 26. COMANDOS OFICIALES

Implementar como mínimo:

```text
help
version
info
formats
codecs
filters
hardware

convert
optimize
compress
remux

cut
trim
merge
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

config
lang
clear
exit
quit
```

Cada comando debe funcionar realmente.

No crear aliases de funciones inexistentes.

---

# 27. REGLAS PARA COMANDOS

Cada comando debe:

```text
parse
validate
plan
execute
validate output
report
```

Nunca:

```text
parse
→ llamar FFmpeg directamente
```

---

# 28. ALIASES

Implementar:

```text
opt → optimize
conv → convert
quit → exit
? → help
```

Los aliases llaman al handler canónico.

No duplicar implementación.

---

# 29. HELP

Debe funcionar:

```text
help
help convert
help cut
help compress
help optimize
```

Mostrar:

```text
description
syntax
options
examples
notes
```

---

# 30. AUTOCOMPLETADO

Debe sugerir:

```text
commands
aliases
options
formats
files
directories
```

La fuente debe ser el registry.

No copiar listas a mano.

---

# 31. COMMAND PALETTE

La CLI interactiva debe ofrecer descubrimiento visual de comandos.

Debe poder navegarse con:

```text
↑
↓
Tab
Enter
Esc
```

---

# 32. ERRORES INTELIGENTES

Ejemplo:

```text
Unknown command: compres

Did you mean:
  compress
```

Otro:

```text
✗ Cannot create XYZ.

FFmpeg can read this format, but the current build
cannot produce it as a normal file destination.
```

---

# 33. API PYTHON PÚBLICA

La API pública debe ser pequeña y humana.

Ejemplo:

```python
from alenia_porter import Video

Video("input.mp4").convert("output.webm")
```

```python
Video("input.mp4").cut(
    start="00:01:00",
    duration="00:00:20",
).save("clip.mp4")
```

```python
from alenia_porter import Audio

Audio("song.wav").convert("song.mp3")
```

No exponer internals.

---

# 34. OPERACIONES DE VIDEO

Implementar y probar:

```text
convert
compress
optimize
remux
cut
trim
merge
concat
resize
crop
rotate
fps
speed
mute
extract audio
frame
thumbnail
gif
subtitle
watermark
metadata
```

---

# 35. OPERACIONES DE AUDIO

Implementar y probar:

```text
convert
compress
cut
trim
merge
concat
volume
normalize
fade
speed
metadata
```

---

# 36. OPERACIONES DE IMAGEN

Implementar mediante backend adecuado:

```text
convert
compress
resize
crop
rotate
metadata
```

Usar Pillow cuando sea mejor que FFmpeg.

---

# 37. COMPRESS

Perfiles mínimos:

```text
small
balanced
high
lossless
```

El perfil debe decidir internamente:

```text
codec
quality
preset
audio
resolution
```

No obligar al usuario a conocer CRF.

---

# 38. OPTIMIZE

Diferencia obligatoria:

```text
convert = cambia destino
compress = reduce tamaño
optimize = encuentra la operación válida más eficiente
```

Ejemplo:

```text
MP4 compatible
→ remux/copy
→ no reencode
```

---

# 39. CUT VS TRIM

```text
cut = inicio + duración
trim = inicio + fin
```

Ambos deben permitir operaciones rápidas cuando técnicamente sea posible.

Debe existir modo preciso cuando el usuario lo solicite.

---

# 40. MERGE/CONCAT

Antes de unir:

```text
codec
resolution
fps
audio
streams
timebase
```

Si son compatibles:

```text
fast path
```

Si requieren normalización:

```text
planned transcode
```

Si no es posible:

```text
clear error
```

Nunca generar archivo corrupto.

---

# 41. HARDWARE

Detectar:

```text
NVIDIA
Intel
AMD
```

cuando la instalación lo soporte.

Comando:

```text
hardware
```

Debe mostrar capacidades reales.

No activar GPU solo por existir.

Debe existir fallback software.

---

# 42. FORMATOS ESPECIALES

Nunca ofrecer como destino común:

```text
streaming protocols
pipes
scientific containers sin encoder/muxer compatible
input-only formats
metadata formats
```

No abrir aplicaciones externas automáticamente.

No descargar herramientas externas silenciosamente.

---

# 43. MODO AVANZADO

Debe existir una vía para usuarios expertos.

Ejemplo conceptual:

```text
porter advanced ...
```

o:

```text
porter ffmpeg ...
```

El modo avanzado permite acceder a capacidades que no justifican comandos humanos individuales.

El modo normal sigue siendo seguro y guiado.

---

# 44. BATCH

Soportar:

```text
porter optimize ./videos
```

y operaciones sobre múltiples archivos.

Debe proporcionar:

```text
total
success
failed
skipped
```

Los errores individuales no deben borrar los resultados exitosos.

---

# 45. AUTOMATIZACIÓN

Soportar:

```text
--json
--quiet
--no-color
--non-interactive
--dry-run
--verbose
```

JSON = datos estructurados; sin texto decorativo.

---

# 46. DRY RUN

Ejemplo:

```text
porter --dry-run convert input.mov output.mp4
```

Debe mostrar:

```text
input
output
operation
backend
codec
stream-copy/reencode
hardware
warnings
```

sin ejecutar.

---

# 47. EXPLAIN

Ejemplo:

```text
porter --explain convert input.mov output.mp4
```

Debe explicar las decisiones del planner.

---

# 48. CONFIG

Una sola fuente de configuración.

Debe controlar como mínimo:

```text
language
ffmpeg path
ffprobe path
default output behavior
color
verbosity
hardware preference
```

No duplicar configuración entre CLI y engine.

---

# 49. I18N

Un solo sistema de traducciones.

Debe cubrir:

```text
CLI
errors
help
progress
status
warnings
```

No introducir nuevas cadenas importantes hardcoded.

---

# 50. NO GUI

La librería y la CLI deben funcionar sin GUI.

Eliminar dependencias de:

```text
Tkinter dialogs
webview
React
frontend
IDE
```

si pertenecen al producto antiguo.

No utilizar GUI como requisito para operaciones de terminal.

---

# 51. ELIMINACIÓN DE LEGACY

Eliminar totalmente:

```text
legacy/
```

No renombrar.

No archivar.

No crear backup dentro del repo.

---

# 52. ELIMINACIÓN DE GO

Después de migrar funcionalidades necesarias:

```text
cmd/ap/
go.mod
go.sum
*.go
```

Eliminar.

Luego buscar referencias globales.

---

# 53. ELIMINACIÓN DE FRONTEND ANTIGUO

Eliminar:

```text
React
npm
node_modules
frontend
dist
IDE web
```

cuando pertenezcan al producto eliminado.

---

# 54. WORKFLOWS

Dejar CI/release únicamente con lo necesario.

Pipeline mínimo:

```text
checkout
Python setup
install
lint/type validation
tests
coverage
build
package smoke test
```

No instalar Go ni Node.

---

# 55. RELEASE

Debe poder hacerse:

```text
build
→ install into clean env
→ porter --version
→ porter --help
```

y ejecutar una operación real.

---

# 56. TEST MATRIX

## Instalación

```text
clean venv
pip install
porter --version
porter
```

## CLI

```text
help
help command
autocomplete
aliases
invalid command
suggestion
Ctrl+C
exit
```

## Video

```text
convert
compress
optimize
remux
cut
trim
merge
concat
resize
crop
rotate
fps
speed
mute
extract-audio
frame
thumbnail
gif
subtitle
watermark
metadata
```

## Audio

```text
convert
compress
cut
trim
merge
volume
normalize
fade
speed
metadata
```

## Imagen

```text
convert
compress
resize
crop
rotate
metadata
```

## Negativos

```text
unsupported output
missing encoder
missing muxer
bad path
invalid duration
invalid dimensions
corrupt input
missing FFmpeg
missing FFprobe
```

---

# 57. PRUEBAS DE INTEGRIDAD

Para cada resultado:

```text
exists
size > 0
probe succeeds
expected streams
expected duration
expected container
```

Para imágenes:

```text
Pillow can open
```

---

# 58. PRUEBAS DE CONCURRENCIA

Comprobar:

```text
single job
multiple independent jobs
cancel
failure
retry/fallback
```

No sobrecargar el sistema.

---

# 59. PRUEBA DE STARTUP

Medir y registrar:

```text
startup time
memory baseline
```

No introducir dependencias pesadas sin razón.

---

# 60. REGLA DE VELOCIDAD

Preferencias obligatorias:

```text
stream copy > reencode
```

cuando ambas sean válidas.

No ejecutar procesos auxiliares innecesarios.

No escanear el sistema completo en startup.

Las capacidades pueden cachearse.

---

# 61. REGLA DE ROBUSTEZ

Nunca:

```text
falla FFmpeg
→ marcar success
```

Nunca:

```text
output vacío
→ dejarlo como resultado
```

Nunca:

```text
unsupported
→ intentar a ciegas
```

Nunca:

```text
cancel
→ dejar proceso huérfano
```

---

# 62. FASES DE IMPLEMENTACIÓN

La IA debe seguir estrictamente este orden:

## Fase A — Auditoría

Resultado:

```text
MIGRATION_AUDIT.md
```

## Fase B — Core

Resultado:

```text
Media
Capabilities
Operations
Planner
Backends
Errors
Jobs
```

## Fase C — API

Resultado:

```text
from alenia_porter import Video, Audio, Image
```

## Fase D — CLI mínima funcional

Resultado:

```text
porter
```

con:

```text
help
version
info
convert
```

## Fase E — CLI profesional

Añadir:

```text
autocomplete
history
palette
spinner
progress
suggestions
```

## Fase F — Operaciones

Implementar familias de operaciones.

## Fase G — Intelligent FFmpeg

Implementar:

```text
capability discovery
planner
stream copy
codec selection
format validation
hardware fallback
```

## Fase H — Batch/automation

Implementar:

```text
json
dry-run
explain
batch
non-interactive
```

## Fase I — Purga

Eliminar:

```text
Go
legacy
IDE
Node
React
scripts antiguos
```

## Fase J — Release

Construir e instalar desde cero.

## Fase K — QA final

Ejecutar toda la matriz.

---

# 63. GATES — REGLA CRÍTICA

La IA no puede avanzar a la siguiente fase si la anterior no cumple su gate.

## Gate A

```text
inventory complete
existing behavior recorded
```

## Gate B

```text
core imports
tests pass
ffmpeg detection works
```

## Gate C

```text
public API works
```

## Gate D

```text
porter launches
basic commands work
```

## Gate E

```text
interactive CLI complete
```

## Gate F

```text
common media operations work
```

## Gate G

```text
planner prevents invalid FFmpeg operations
```

## Gate H

```text
automation works
```

## Gate I

```text
legacy/Go/frontend removed
```

## Gate J

```text
clean package installs
```

## Gate K

```text
full test matrix passes
```

---

# 64. NO "DONE" PREMATURO

No declarar:

```text
DONE
COMPLETE
FINISHED
```

mientras exista cualquier:

```text
failing test
broken import
missing command
broken entrypoint
broken release
broken workflow
legacy dependency
Go dependency
invalid FFmpeg output
```

---

# 65. REPORTE FINAL OBLIGATORIO

Al finalizar crear:

```text
docs/FINAL_AUDIT.md
```

Debe contener:

```text
architecture
files deleted
files migrated
files added
commands
API
FFmpeg capabilities
tests
release test
known limitations
```

Debe incluir resultados reales.

No escribir:

```text
"todo funciona"
```

sin pruebas.

---

# 66. LIMPIEZA FINAL

Ejecutar búsquedas globales:

```text
legacy
legacy/ide
gui_web
React
npm
node
cmd/ap
go.mod
go.sum
package main
*.go
ap_bin
```

Cualquier referencia activa encontrada debe corregirse.

---

# 67. CHECKLIST FINAL

```text
[ ] Python only
[ ] package installs through pip
[ ] porter command exists
[ ] interactive CLI works
[ ] autocomplete works
[ ] history works
[ ] command palette works
[ ] spinner works
[ ] progress works
[ ] Ctrl+C works
[ ] public API works
[ ] FFprobe detection works
[ ] FFmpeg capability detection works
[ ] output format validation works
[ ] planner works
[ ] stream copy works
[ ] reencode works
[ ] hardware fallback works
[ ] convert works
[ ] optimize works
[ ] compress works
[ ] cut works
[ ] trim works
[ ] merge/concat works
[ ] resize works
[ ] crop works
[ ] rotate works
[ ] fps works
[ ] speed works
[ ] mute works
[ ] extract-audio works
[ ] volume works
[ ] normalize works
[ ] fade works
[ ] frame works
[ ] thumbnail works
[ ] gif works
[ ] subtitle works
[ ] watermark works
[ ] metadata works
[ ] batch works
[ ] JSON mode works
[ ] dry-run works
[ ] explain works
[ ] clean install works
[ ] bundled FFmpeg is present in the installed package
[ ] bundled FFmpeg is the primary runtime binary
[ ] FFprobe strategy is verified from the actual repository
[ ] release smoke test works
[ ] workflows work
[ ] no Go
[ ] no legacy
[ ] no old IDE
[ ] no old frontend
[ ] no broken references
```

---

# 68. DEFINICIÓN DE "PORTER LISTO"

Porter estará listo cuando una persona que nunca haya usado FFmpeg pueda:

```text
pip install alenia-porter
porter
```

y desde ahí pueda:

```text
descubrir operaciones
elegir una operación
seleccionar archivos
ver qué hará Porter
ver progreso
recibir resultado
```

sin memorizar:

```text
ffmpeg flags
codecs
muxers
filters
CRF
stream maps
timebases
```

Y un programador pueda hacer:

```python
from alenia_porter import Video

Video("input.mp4").cut(
    start="00:01:00",
    duration="00:00:30",
).save("clip.mp4")
```

El mismo core debe encargarse de todo.

---

# 69. FILOSOFÍA DEFINITIVA

```text
FFmpeg = potencia
FFprobe = conocimiento del medio
Pillow = procesamiento de imagen apropiado
Porter = inteligencia, seguridad y experiencia humana
CLI = interfaz
API = plataforma
```

Porter no intenta reemplazar FFmpeg.

Porter debe hacer que usar sus capacidades resulte:

```text
simple
predecible
seguro
rápido
descubrible
extensible
```

---

# 70. INSTRUCCIÓN FINAL A LA IA LOCAL

Implementa exactamente este documento.

No agregues una arquitectura alternativa.

No conviertas la CLI en el núcleo.

No dejes funcionalidades críticas a medias.

No mantengas código antiguo "por si acaso".

No inventes soporte para formatos.

No expongas todos los flags de FFmpeg como comandos humanos.

No elimines comportamiento funcional sin reemplazarlo.

No declares éxito sin ejecutar las validaciones correspondientes.

La salida final debe ser:

```text
ALENIA PORTER
    ↓
Python package
    ↓
Python API
    ↓
Interactive CLI
    ↓
Operation Planner
    ↓
Capability-aware FFmpeg integration
    ↓
Validated media output
```

Ese es el único objetivo de esta migración.
