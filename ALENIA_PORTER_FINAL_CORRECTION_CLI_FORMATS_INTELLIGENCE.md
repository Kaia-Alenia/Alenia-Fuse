# ALENIA PORTER — FINAL CORRECTION SPECIFICATION
## CLI profesional + formatos inteligentes + conversión confirmada

Esta instrucción corrige la implementación actual de Alenia-Porter. No es una fase cosmética ni una sugerencia. El objetivo es dejar Porter como producto completo y usable.

### 1. PROBLEMAS QUE DEBEN CORREGIRSE

La demostración actual revela:
- `porter` todavía tiene una UX inconsistente.
- Existió un crash de `prompt_toolkit` por fragmentos `HTML` mal utilizados.
- La CLI guiada muestra pocas categorías y depende demasiado de un "Command mode".
- `--help` expone comandos, pero el usuario principal debe descubrirlos dentro de la CLI.
- El catálogo de formatos visibles está reducido artificialmente.
- Aparecen entradas internas como `webp_pipe`.
- Se marcó como exitosa una conversión de imagen con `0 KB`.
- En batch se reutiliza el mismo nombre de salida para archivos distintos.
- Se acepta `input == output`.
- La selección de targets todavía no demuestra compatibilidad específica para el archivo real.

No declarar terminado hasta corregir todos.

### 2. CLI PRINCIPAL

`porter` sin argumentos debe abrir una CLI guiada.

Debe mostrar una lista visible de acciones. Ejemplo:

```text
╭──────────────────────────────────────────────────────╮
│                                                      │
│                     ALENIA PORTER                   │
│                 Multimedia made simple              │
│                                                      │
╰──────────────────────────────────────────────────────╯

¿Qué quieres hacer?

❯ Convertir archivos
  Comprimir archivos
  Editar vídeo
  Editar audio
  Procesar imágenes
  Extraer contenido
  Analizar un archivo
  Configuración
  Ayuda
  Salir

↑ ↓ Navegar   Enter Seleccionar   Esc Atrás
```

Los textos deben usar el idioma activo.

### 3. NAVEGACIÓN REAL

Las teclas deben funcionar realmente:
- ↑
- ↓
- Enter
- Esc

La selección debe ser visible mediante `❯`.

No mostrar instrucciones de teclado que no funcionen.

No crear un menú de impresión estática.

### 4. AUTOCOMPLETADO REAL

TAB debe completar:
- comandos;
- aliases;
- opciones;
- rutas;
- formatos cuando el contexto lo permita.

Ejemplo:

```text
porter › c
❯ convert
  compress
  crop
  cut
  concat
  codecs
  config
```

El autocomplete debe consumir el mismo `CommandRegistry` que la ayuda y la command palette.

### 5. COMMAND PALETTE

Implementar una paleta dentro de la CLI, por ejemplo con `Ctrl+K`.

Debe tener:
- búsqueda;
- flechas;
- Enter;
- Escape;
- descripción;
- comandos reales.

No usar una lista duplicada.

### 6. HISTORIAL

Mantener historial persistente y navegación ↑/↓.

La ruta debe ser multiplataforma y apropiada para datos del usuario.

### 7. MULTILENGUAJE

Mantener un sistema único de i18n.

Idiomas mínimos:
- español;
- inglés;
- portugués;
- francés;
- alemán;
- italiano;
- japonés;
- coreano;
- chino;
- ruso.

No mezclar idiomas accidentalmente.

Toda la UI propia debe utilizar claves de traducción.

### 8. COMMAND MODE

`Command mode (advanced)` no puede ser la interfaz principal.

Debe quedar como modo opcional.

La experiencia guiada debe ser plenamente funcional sin entrar en command mode.

### 9. COMANDOS HUMANOS

Conservar sintaxis sencilla:

```text
convert video.mp4 to webm
compress video.mp4
resize video.mp4 1280x720
trim video.mp4 from 00:01:00 to 00:02:00
extract audio from video.mp4
normalize song.mp3
thumbnail video.mp4
```

No obligar al usuario normal a conocer flags de FFmpeg.

### 10. COMMAND REGISTRY

Crear una única fuente de verdad con:
- name;
- aliases;
- category;
- description;
- syntax;
- examples;
- options;
- completion;
- handler;
- traducciones.

Consumirla desde:
- menú;
- help;
- autocomplete;
- palette;
- sugerencias.

### 11. FORMATOS: REQUISITO FUNDAMENTAL

NO limitar la UI a cuatro formatos por categoría.

La aplicación debe descubrir desde el FFmpeg real los muxers, demuxers, encoders y decoders disponibles.

Pero NO debe mostrar todo `ffmpeg -formats` sin filtrar.

### 12. CLASIFICACIÓN DE FORMATO

Cada entrada debe clasificarse como:
- container;
- audio;
- video;
- image;
- raw;
- input-only;
- output-only;
- input+output;
- protocol;
- pipe;
- device;
- special.

Solo los destinos de archivo válidos deben aparecer como targets normales.

### 13. NO MOSTRAR ENTRADAS INTERNAS

Ejemplo:

`webp_pipe` no debe convertirse en una opción de archivo llamada simplemente `WebP` si representa un pipe.

El usuario debe ver el formato de archivo WebP real, no una entrada interna del backend.

### 14. "TODOS LOS FORMATOS" SIGNIFICA ESTO

Debe ofrecerse todo destino de archivo que:
1. el FFmpeg bundled realmente pueda generar;
2. Porter pueda usar mediante sus operaciones;
3. no requiera software de terceros;
4. sea válido para el tipo de medio;
5. pueda producir un archivo verificable.

No incluir:
- protocolos;
- dispositivos;
- pipes;
- entradas especiales;
- formatos que solo sirven como input;
- destinos que no puedan validarse.

### 15. EJEMPLOS DE FORMATOS

No hardcodear estas listas como fuente de verdad, pero comprobar que formatos comunes adicionales aparezcan cuando estén disponibles.

Video/container potenciales:
`mp4`, `mkv`, `webm`, `mov`, `avi`, `flv`, `mpeg`, `mpg`, `m4v`, `ts`, `m2ts`, `mts`, `3gp`, `3g2`, `ogv`, `f4v`, `asf`, `wmv`, `vob`, `mxf`, `nut`.

Audio potenciales:
`mp3`, `wav`, `flac`, `aac`, `m4a`, `opus`, `ogg`, `oga`, `wma`, `ac3`, `eac3`, `mka`, `aiff`, `aif`, `alac`, `amr`, `au`.

Imagen potenciales:
`png`, `jpg`, `jpeg`, `webp`, `bmp`, `tiff`, `tif`, `gif`, `ico`, `ppm`, `pgm`, `pbm`, `pam`, `tga`, `pcx`, `sgi`, `jp2`, `j2k`, `jpf`, `jpx`, `avif`, `exr`.

Solo mostrar los realmente disponibles y válidos.

### 16. TARGETS CONTEXTUALES

No mostrar la misma lista para todo.

Para un audio:
mostrar targets de audio.

Para una imagen:
mostrar targets de imagen.

Para un video:
mostrar containers/video targets válidos.

Además consultar los streams reales.

### 17. INPUT REAL

Antes de mostrar destinos, analizar el archivo con FFprobe.

Obtener, cuando exista:
- container;
- streams;
- codecs;
- width;
- height;
- fps;
- pixel format;
- color space;
- alpha;
- bit depth;
- sample rate;
- channels;
- duration;
- bitrate.

### 18. COMPATIBILIDAD

No considerar suficiente:

```text
muxer exists
```

La decisión debe considerar:

```text
input
+
streams
+
decoder
+
encoder
+
container
+
required pixel/audio properties
+
operation semantics
```

### 19. STREAMS

Ejemplo:

`movie.mp4` puede contener:
- video H.264;
- audio AAC;
- subtitles.

El target debe determinar qué streams puede conservar y cuáles requieren conversión.

### 20. CODEC COMPATIBILITY

Si WebM es el destino, no intentar poner H.264 + AAC simplemente porque existen.

Elegir codecs válidos como VP8/VP9/AV1 + Opus/Vorbis cuando estén disponibles.

Las capacidades deben venir del FFmpeg real.

### 21. IMAGE SEMANTICS

No todas las conversiones técnicamente posibles son apropiadas.

Separar:
- técnicamente posible;
- apropiado para la operación.

Por ejemplo, una imagen estática puede técnicamente producir un GIF de un frame, pero no debe mostrarse como target normal de conversión de imagen. Debe pertenecer a una operación de animación o sección avanzada.

### 22. RGBA / ALPHA

Analizar transparencia.

Si el input es RGBA y el destino no soporta alpha:
- advertir;
- pedir background cuando corresponda;
- o exigir una decisión explícita.

No perder transparencia silenciosamente.

### 23. JPEG

Para RGBA → JPEG:

```text
JPEG does not support transparency.

Choose a background color or cancel.
```

No hacer una conversión silenciosa con pérdida semántica.

### 24. BMP

BMP debe aparecer si:
- FFmpeg tiene encoder/muxer;
- el input es compatible;
- Porter puede producir un BMP verificable.

No excluirlo por ser menos común.

### 25. OTHER FORMATS

La lista principal puede mostrar los targets recomendados.

Debe existir:

```text
Other formats...
```

para acceder a TODOS los demás destinos válidos para ese archivo.

### 26. SEARCH FORMAT

Cuando haya muchos destinos, implementar:

```text
Search format...
```

La búsqueda debe operar sobre el catálogo dinámico real.

### 27. PREFLIGHT

Cuando la compatibilidad no pueda demostrarse de manera fiable mediante análisis estático, hacer un preflight real.

Flujo:

```text
analizar input
↓
crear plan
↓
ejecutar una pequeña prueba real
↓
validar output
↓
eliminar temporal
↓
ejecutar conversión completa
```

El preflight usa FFmpeg real.

No es una simulación.

### 28. NO PREFLIGHT INNECESARIO

Si ya existe evidencia suficientemente fuerte y cacheada para la combinación de:
- versión FFmpeg;
- container;
- codec;
- propiedades relevantes;
- operación;

se puede evitar el preflight.

Si existe incertidumbre, no adivinar.

### 29. OUTPUT VALIDATION

Después de cualquier operación:

1. return code == 0;
2. output existe;
3. output size > 0;
4. output es legible;
5. FFprobe puede leerlo cuando corresponda;
6. container esperado;
7. streams esperados;
8. codec esperado;
9. efecto solicitado.

### 30. CERO BYTES = ERROR

Absoluto:

```text
0 bytes → FAILURE
```

Nunca:

```text
Conversion complete.
Size: 0 KB
```

### 31. `webp_pipe` = NO ÉXITO

Si el resultado termina en una entidad tipo:

```text
webp_pipe
```

que no corresponde a un archivo WebP válido, la operación debe fallar.

### 32. IMAGE REGRESSION TEST

Crear un test que reproduzca:

```text
PNG → WebP
```

y garantice:
- output > 0;
- output legible;
- formato correcto;
- no `webp_pipe`;
- no éxito falso.

### 33. INPUT == OUTPUT

Debe rechazarse:

```text
convert a.mp4 a.mp4
```

con un mensaje claro.

### 34. BATCH COLLISIONS

El log actual muestra:

```text
sample_video.avi → sample_video.mp4
sample_video.mkv → sample_video.mp4
sample_video.mov → sample_video.mp4
sample_video.mp4 → sample_video.mp4
```

Esto es incorrecto.

La estrategia debe garantizar nombres únicos, por ejemplo:

```text
sample_video.mp4
sample_video_1.mp4
sample_video_2.mp4
```

o una estrategia equivalente.

Nunca destruir outputs anteriores por colisión.

### 35. BATCH SUMMARY

Al finalizar:

```text
Batch complete

Succeeded: 13
Failed:     1
Skipped:    2
```

Los fallos deben aparecer con razón.

### 36. OVERWRITE

No sobrescribir por defecto.

Si existe un output:

```text
Output already exists.

❯ Overwrite
  Choose another name
  Cancel
```

o exigir `--overwrite` en modo no interactivo.

### 37. PROGRESS

El progreso debe provenir de ejecución real.

No usar `time.sleep()` para animarlo.

Si existe:
- duración;
- `out_time`;
- speed;

calcular progreso real.

No inventar ETA.

### 38. VELOCIDAD

Si se muestra:

```text
Speed: 3.0x
```

debe derivarse de FFmpeg.

### 39. CANCELACIÓN

Ctrl+C debe:
- cancelar;
- terminar FFmpeg;
- limpiar temporales;
- no dejar output corrupto;
- regresar al prompt.

### 40. COLORES

Tema oscuro.

Paleta:

```text
Background       #020617
Panel            #111827
Panel secondary  #0F172A
Border           #334155
Primary          #7C5CFF
Primary bright   #9A84FF
Cyan             #22D3EE
Success          #22C55E
Warning          #F59E0B
Error            #EF4444
Info             #38BDF8
Text             #F8FAFC
Secondary text   #CBD5E1
Muted            #94A3B8
Disabled         #64748B
```

Uso:

```text
morado = branding/selección
cyan = información
verde = éxito
amarillo = warning
rojo = error
gris = secundario
```

No usar colores arbitrarios.

### 41. ESTILO VISUAL

Debe parecer una herramienta profesional para desarrolladores.

No:
- script académico;
- aplicación DOS;
- menú viejo;
- arcoíris;
- exceso de cajas.

### 42. LOGO

Mantener logo compacto.

No gastar la mayor parte de la pantalla en ASCII.

### 43. AYUDA

`help` dentro de la CLI debe ser la principal ayuda para usuarios interactivos.

`porter -h` queda como ayuda de shell/CLI one-shot.

La lista interna debe mostrar las operaciones existentes, agrupadas.

### 44. DISEÑO DE OPERACIONES

Mantener operaciones de alto nivel:

```text
convert
compress
optimize
remux
cut
trim
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
formats
codecs
filters
hardware
config
lang
clear
help
exit
```

No todos necesitan estar en la pantalla inicial, pero todos deben ser accesibles desde `help`, palette o categorías.

### 45. ADVANCED

Parámetros técnicos deben permanecer en Advanced:

```text
codec
bitrate
CRF
preset
filters
mapping
pixel format
```

No saturar al usuario normal.

### 46. API

La CLI y la API deben usar exactamente:

```text
same registry
same planner
same operations
same executor
same validator
```

### 47. NO DOS MOTORES

Prohibido tener una ruta especial de CLI que haga cosas distintas de la API.

### 48. FFMPEG

Usar exclusivamente el FFmpeg real bundled por Porter como fuente principal.

No usar:
- dummy;
- wrapper falso;
- `ffmpeg.bat`;
- `imageio-ffmpeg`;
- downloads silenciosos;
- `shell=True`.

### 49. FFPROBE

Usar FFprobe real si está bundled/disponible.

Preferir:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams
```

### 50. CAPABILITIES

Descubrir dinámicamente:
- formats;
- encoders;
- decoders;
- filters;
- protocols;
- hwaccels.

No usar listas fijas como fuente técnica.

### 51. DOMAIN ERRORS

Errores normales deben verse así:

```text
✗ Cannot convert this file.

Reason:
The target format cannot represent the required input features.

No output was created.
```

No mostrar tracebacks salvo `--debug`.

### 52. REGRESSION TESTS OBLIGATORIOS

Agregar pruebas para:
- prompt/interactive no crash;
- menú navegable;
- autocomplete;
- command palette;
- i18n;
- PNG → WebP;
- PNG RGBA → JPEG warning;
- PNG → BMP;
- WAV → FLAC;
- MP4 → MKV;
- input == output;
- batch collision;
- zero-byte output;
- pipe output rejection;
- unsupported codec;
- unsupported target;
- real FFprobe validation.

No reemplazar tests existentes: ampliarlos y corregirlos.

### 53. DEMOSTRACIÓN REAL FINAL

Demostrar en terminal:

```text
porter
```

y:
1. ver menú;
2. mover selección con ↑↓;
3. entrar con Enter;
4. volver con Esc;
5. cambiar idioma;
6. abrir command palette;
7. usar command mode;
8. usar TAB;
9. seleccionar un archivo;
10. analizarlo;
11. ver targets válidos;
12. abrir `Other formats...`;
13. buscar un formato;
14. convertir;
15. ver progreso;
16. validar output;
17. regresar al prompt.

### 54. DEMOSTRACIÓN DE INTELIGENCIA

Usar al menos:
- una imagen RGBA;
- un audio;
- un video;
- un caso incompatible.

Demostrar que los targets cambian según el input.

### 55. DEMOSTRACIÓN NEGATIVA

Comprobar que:
- `webp_pipe` no se ofrece como archivo WebP;
- un target incompatible no aparece normalmente;
- un output 0 bytes falla;
- input == output falla;
- batch no colisiona.

### 56. DEFINICIÓN DE TERMINADO

No declarar terminado hasta que:

```text
[ ] CLI abre sin crash
[ ] menú inicial existe
[ ] ↑↓ funciona
[ ] Enter funciona
[ ] Esc funciona
[ ] autocomplete funciona
[ ] history funciona
[ ] palette funciona
[ ] i18n funciona
[ ] help interno funciona
[ ] command mode funciona
[ ] FFmpeg real funciona
[ ] FFprobe real funciona
[ ] capabilities reales
[ ] formatos completos y clasificados
[ ] targets dinámicos por input
[ ] formatos especiales filtrados
[ ] semántica de imágenes correcta
[ ] alpha detectado
[ ] preflight cuando es necesario
[ ] output validado
[ ] 0-byte rechazado
[ ] pipes rechazados como archivos
[ ] input == output rechazado
[ ] batch sin colisiones
[ ] overwrite seguro
[ ] progreso real
[ ] cancelación real
[ ] API y CLI comparten core
[ ] tests de regresión pasan
[ ] documentación actualizada
```

### 57. REGLA FINAL

NO optimices para que el reporte diga:

```text
35 tests passed
```

Optimiza para que un usuario que nunca ha usado FFmpeg pueda:

```text
abrir Porter
↓
ver qué puede hacer
↓
elegir una operación
↓
seleccionar un archivo
↓
recibir únicamente destinos válidos
↓
convertir
↓
obtener un archivo correcto
```

Porter debe absorber la complejidad de FFmpeg.

El usuario no debe tener que hacerlo.

# FIN
