# Alenia-Porter — Plan Maestro de Migración y Limpieza Total

## ESTADO DE ESTE DOCUMENTO

**Tipo:** Instrucción de ejecución obligatoria para una IA local.  
**Objetivo:** Migrar Alenia-Porter a una arquitectura **100 % Python**, eliminar completamente las arquitecturas antiguas y dejar el repositorio limpio, coherente, rápido, comprobable y mantenible.

---

# 1. AUTORIDAD Y REGLAS DE EJECUCIÓN

## 1.1. Regla principal

La IA ejecutora **NO debe tomar decisiones arquitectónicas propias**.

Este documento define la arquitectura objetivo.

La IA debe:

1. inspeccionar el estado actual del repositorio;
2. aplicar las instrucciones de este documento;
3. migrar únicamente lo necesario;
4. eliminar únicamente lo indicado;
5. corregir referencias rotas producidas por la migración;
6. validar el resultado completo;
7. detenerse únicamente cuando el repositorio cumpla los criterios de aceptación.

Si encuentra una ambigüedad real que impida continuar sin inventar comportamiento, debe:

- conservar el comportamiento existente cuando sea posible;
- elegir la solución más pequeña y compatible con esta especificación;
- documentar exactamente la ambigüedad y la solución aplicada;
- **NO introducir una nueva arquitectura, framework o lenguaje por iniciativa propia**.

---

## 1.2. Decisión arquitectónica definitiva

La arquitectura final será:

> **PYTHON PURO COMO ÚNICO LENGUAJE DE IMPLEMENTACIÓN DEL PRODUCTO.**

No se mantendrá una arquitectura híbrida.

La estructura final no debe depender de:

- Go;
- módulos Go;
- binarios Go;
- Node.js;
- npm;
- React;
- frontend del IDE antiguo;
- `legacy`;
- IDLE como producto o arquitectura;
- launchers que busquen implementaciones antiguas.

La única excepción temporal durante la ejecución es que código antiguo puede permanecer mientras se migra funcionalidad. Al finalizar el trabajo, las excepciones temporales deben desaparecer.

---

# 2. OBJETIVO FINAL

Al finalizar, Alenia-Porter debe tener una sola fuente de verdad:

```text
Python
│
├── Motor multimedia
│   └── FFmpeg
│
├── Lógica de aplicación
│
├── CLI / TUI
│
├── Sistema de comandos
│
├── Configuración
│
├── Internacionalización
│
├── Actualizaciones
│
└── Tests
```

No debe existir una segunda aplicación implementando la misma lógica.

La regla es:

> **Un producto; un lenguaje; un runtime principal; una arquitectura; una fuente de verdad.**

---

# 3. PRINCIPIOS OBLIGATORIOS

## 3.1. Python primero

Toda funcionalidad que forme parte del producto debe implementarse en Python.

No crear:

- nuevos archivos `.go`;
- nuevos módulos Go;
- wrappers Go;
- procesos auxiliares Go;
- binarios Go requeridos para ejecutar Alenia-Porter.

---

## 3.2. El motor sigue siendo Python

El motor existente basado en Python debe conservarse como base funcional.

La migración no debe reescribir innecesariamente el motor multimedia si ya funciona.

Primero:

1. identificar la lógica existente;
2. conservar el comportamiento correcto;
3. reorganizar;
4. eliminar duplicaciones;
5. mejorar la interfaz alrededor del motor.

No reescribir por gusto.

---

## 3.3. No duplicar lógica

Una funcionalidad debe tener una única implementación.

Ejemplos:

- una única configuración;
- un único sistema de idiomas;
- un único sistema de comandos;
- un único motor de procesamiento;
- un único sistema de detección de formatos;
- un único sistema de actualización.

No crear versiones Python de código Go manteniendo ambas.

La migración debe terminar con **una sola implementación Python**.

---

## 3.4. No conservar código muerto

No crear carpetas como:

```text
old/
legacy/
archive/
deprecated/
backup/
backup_old/
```

Git ya conserva el historial.

El código eliminado debe eliminarse del árbol activo del repositorio.

---

# 4. ELIMINACIONES OBLIGATORIAS

## 4.1. Eliminar completamente `legacy/`

Eliminar la carpeta completa:

```text
legacy/
```

Incluyendo todos sus contenidos.

Esto incluye explícitamente:

```text
legacy/ide/
legacy/ide/gui_web.py
legacy/ide/frontend/
legacy/ide/frontend/dist/
legacy/ide/frontend/node_modules/     # si existe en el repositorio
legacy/__init__.py
```

No mover estos archivos a otra carpeta.

No renombrarlos.

No conservarlos como compatibilidad.

No dejar imports hacia ellos.

---

## 4.2. Eliminar el IDE antiguo

Eliminar todos los componentes pertenecientes al IDE antiguo, incluyendo cualquier combinación de:

- Python GUI antigua;
- webview usado exclusivamente por el IDE antiguo;
- React;
- JavaScript del IDE;
- TypeScript del IDE;
- HTML/CSS/JS perteneciente exclusivamente al IDE;
- builds frontend;
- scripts de desarrollo del IDE.

Antes de borrar, verificar si un archivo es usado por el producto actual.

Si es exclusivamente del IDE antiguo, eliminarlo.

Si contiene lógica reutilizable necesaria para el producto actual, extraer únicamente esa lógica hacia Python limpio antes de eliminar el archivo antiguo.

---

## 4.3. Eliminar Go después de migrar su funcionalidad necesaria

La arquitectura final no debe contener:

```text
cmd/ap/
go.mod
go.sum
```

Tampoco deben quedar:

- archivos `.go`;
- imports Go;
- comandos `go build`;
- comandos `go test`;
- workflows Go;
- scripts de release Go;
- referencias a binarios Go;
- documentación que diga que Go forma parte de la arquitectura final.

### Regla crítica

Antes de borrar `cmd/ap/`, identificar todas las funcionalidades reales que aporta.

Migrar únicamente las funcionalidades útiles al sistema Python.

Después:

1. comprobar que Python cubre dichas funcionalidades;
2. probarlas;
3. eliminar `cmd/ap/`;
4. eliminar `go.mod`;
5. eliminar `go.sum`;
6. eliminar referencias restantes.

---

## 4.4. Eliminar binarios compilados que no deban vivir en Git

Inspeccionar archivos como:

```text
ap_bin
```

y cualquier otro ejecutable/binario compilado.

Si es un artefacto generado y no código fuente obligatorio:

- eliminarlo del repositorio;
- añadir una regla apropiada a `.gitignore`;
- distribuir binarios mediante releases o artefactos de CI cuando corresponda.

No conservar binarios generados en la raíz como parte del código fuente.

---

# 5. LIMPIEZA DE REFERENCIAS

Después de eliminar `legacy` y Go, realizar una búsqueda global obligatoria.

Buscar referencias a:

```text
legacy
legacy/ide
gui_web
frontend
npm
node
node_modules
react
go.mod
go.sum
go build
go test
cmd/ap
ap_bin
```

También buscar referencias a rutas antiguas en:

```text
.github/
docs/
README.md
CONTRIBUTING.md
launch.sh
Makefile
scripts/
pyproject.toml
.gitignore
dependabot.yml
workflows/
```

Cada referencia encontrada debe:

- eliminarse si apunta a código eliminado;
- actualizarse si apunta a una ruta que cambió;
- mantenerse únicamente si sigue siendo funcional y pertenece a la arquitectura final.

Al finalizar:

> No debe existir ninguna referencia activa al IDE eliminado ni a la arquitectura Go eliminada.

---

# 6. WORKFLOWS DE GITHUB

Los workflows deben quedar orientados exclusivamente a Python.

## 6.1. CI obligatorio

El workflow principal debe:

1. hacer checkout;
2. instalar la versión de Python definida por el proyecto;
3. instalar dependencias;
4. instalar dependencias de desarrollo;
5. ejecutar validaciones estáticas;
6. ejecutar tests;
7. generar coverage cuando esté configurado;
8. fallar ante errores.

No instalar:

- Go;
- Node;
- npm;

salvo que exista una dependencia completamente independiente y explícitamente necesaria para documentación. Si no existe una razón real, no usar ninguno.

---

## 6.2. Dependabot

Eliminar configuraciones Dependabot que apunten exclusivamente a:

```text
/legacy/ide/frontend
```

Eliminar ecosistemas que ya no existan.

Mantener únicamente configuraciones correspondientes a dependencias activas del proyecto final.

---

## 6.3. Releases

Los releases deben construir únicamente el producto Python.

No deben ejecutar:

```text
go build
```

No deben requerir Go.

La estrategia de empaquetado debe definirse según el sistema de distribución ya existente en el proyecto.

No inventar un segundo sistema de empaquetado si el actual funciona.

---

# 7. ARQUITECTURA PYTHON OBJETIVO

La IA debe reorganizar progresivamente el código para separar responsabilidades.

La estructura exacta puede adaptarse al contenido real, pero debe respetar esta separación:

```text
src/alenia_porter/
│
├── __init__.py
│
├── engine/
│   ├── __init__.py
│   ├── ffmpeg.py
│   ├── media.py
│   ├── optimizer.py
│   └── progress.py
│
├── application/
│   ├── __init__.py
│   ├── config.py
│   ├── commands.py
│   ├── formats.py
│   ├── updates.py
│   └── i18n.py
│
├── cli/
│   ├── __init__.py
│   ├── main.py
│   ├── parser.py
│   ├── completion.py
│   └── renderer.py
│
└── ...
```

### Importante

Esta estructura es un objetivo de responsabilidades, no una orden de crear archivos vacíos.

No crear módulos artificiales.

Solo crear módulos cuando exista código real que corresponda a esa responsabilidad.

---

# 8. MIGRACIÓN DE FUNCIONALIDADES DE GO

Antes de eliminar Go, auditar `cmd/ap/`.

Crear un inventario interno de cada funcionalidad.

Para cada una, decidir únicamente entre:

```text
CONSERVAR Y MIGRAR A PYTHON
```

o:

```text
ELIMINAR POR NO SER NECESARIA
```

No existe una tercera opción de mantenerla en Go.

Las funcionalidades útiles identificadas incluyen potencialmente:

- historial de comandos;
- sugerencias;
- autocompletado;
- selección de formatos;
- progreso;
- configuración;
- internacionalización;
- ayuda;
- actualización;
- escaneo de medios;
- cancelación de procesos.

Migrarlas al sistema Python sin copiar literalmente la arquitectura Go.

Python debe integrarlas en una API coherente.

---

# 9. NUEVO SISTEMA DE CLI

La CLI Python será la interfaz oficial.

Debe ser rápida.

Debe iniciar sin procesos secundarios innecesarios.

Debe evitar bloqueos.

Debe tener responsabilidades separadas:

```text
Input
   ↓
Parser
   ↓
Command Dispatcher
   ↓
Application / Engine
   ↓
Progress / Output
```

No mezclar toda la aplicación dentro de un único archivo gigantesco.

---

# 10. COMANDOS — REGLAS GENERALES

Todos los comandos deben tener:

1. nombre principal;
2. aliases cuando aporten valor;
3. validación;
4. ayuda específica;
5. mensajes de error claros;
6. comportamiento consistente;
7. código de salida apropiado cuando se ejecuten en modo no interactivo.

La sintaxis debe ser coherente.

No mezclar arbitrariamente:

```text
/comando
```

con:

```text
comando
```

La CLI debe elegir una convención principal.

## Decisión obligatoria

La CLI debe usar comandos normales sin `/` como interfaz principal:

```text
optimize
convert
info
formats
config
lang
help
clear
exit
```

Los comandos con `/` pueden mantenerse temporalmente como aliases de compatibilidad si actualmente son importantes, pero:

- no deben aparecer como interfaz principal;
- no deben duplicar implementaciones;
- deben llamar al mismo handler Python.

---

# 11. COMANDOS OBLIGATORIOS A MEJORAR

## 11.1. `help`

Debe soportar:

```text
help
help optimize
help convert
```

Debe mostrar:

- descripción;
- sintaxis;
- argumentos;
- ejemplos;
- aliases.

---

## 11.2. `optimize`

Debe:

1. validar la ruta;
2. detectar medios compatibles;
3. informar qué encontró;
4. solicitar o aceptar opciones;
5. ejecutar el motor;
6. mostrar progreso;
7. informar resultados;
8. informar errores individualmente;
9. no bloquear innecesariamente la interfaz.

Debe aceptar argumentos de forma consistente.

---

## 11.3. `formats`

Debe mostrar formatos disponibles organizados por categoría:

```text
Video
Audio
Imagen
```

No duplicar listas de formatos en múltiples módulos.

La fuente de formatos debe ser única.

---

## 11.4. `info`

Debe permitir inspeccionar un archivo multimedia y mostrar información útil.

Debe validar:

- existencia;
- tipo;
- acceso.

Los errores deben ser claros.

---

## 11.5. `config`

Debe centralizar la configuración.

La configuración no debe estar duplicada entre:

- CLI;
- engine;
- archivos antiguos.

Debe permitir consultar y modificar valores de forma controlada.

---

## 11.6. `lang`

Debe utilizar el sistema único de internacionalización.

Cambiar idioma debe afectar inmediatamente a la interfaz correspondiente.

No dejar cadenas importantes hardcodeadas si el proyecto ya soporta i18n.

---

## 11.7. `clear`

Debe limpiar únicamente la salida/historial visual de la sesión.

No debe borrar configuración ni historial persistente accidentalmente.

---

## 11.8. `exit` y `quit`

Ambos deben cerrar correctamente.

Si existe un proceso activo:

- cancelar o finalizar correctamente según el sistema de procesos;
- no dejar procesos FFmpeg huérfanos;
- limpiar recursos.

---

# 12. ALIASES

Implementar aliases de forma centralizada.

Ejemplos:

```text
help     -> ?
quit     -> exit
opt      -> optimize
conv     -> convert
```

Los aliases no deben tener implementaciones separadas.

Debe existir:

```text
alias
    ↓
resolver
    ↓
comando canónico
    ↓
handler único
```

---

# 13. AUTOCOMPLETADO Y SUGERENCIAS

La CLI debe mejorar la experiencia de comandos.

## Autocompletado

Debe sugerir:

- comandos;
- aliases;
- argumentos conocidos cuando sea posible;
- formatos.

## Errores tipográficos

Cuando el usuario escriba un comando desconocido:

```text
optmize
```

la CLI debe sugerir:

```text
Did you mean: optimize?
```

No ejecutar automáticamente una sugerencia sin confirmación.

---

# 14. VALIDACIÓN DE ARGUMENTOS

Nunca pasar argumentos inválidos directamente al motor.

Cada comando debe validar antes de ejecutar.

Ejemplos:

- rutas existentes;
- formatos soportados;
- valores numéricos;
- opciones incompatibles.

Los errores deben indicar:

1. qué está mal;
2. qué se esperaba;
3. cómo corregirlo.

---

# 15. PROGRESO

El progreso debe venir de una fuente controlada.

No mezclar directamente:

- prints del motor;
- prints de subprocess;
- UI;
- lógica de negocio.

Crear una interfaz clara para eventos/progreso.

Ejemplo conceptual:

```text
Engine
   ↓ event
Progress Layer
   ↓
CLI Renderer
```

La interfaz debe poder mostrar:

- archivo actual;
- cantidad procesada;
- errores;
- finalización.

---

# 16. PROCESOS Y FFmpeg

La CLI no debe congelarse mientras FFmpeg procesa.

Los procesos deben:

- ejecutarse de forma controlada;
- poder reportar progreso;
- manejar errores;
- limpiarse correctamente;
- evitar procesos huérfanos.

No introducir concurrencia compleja sin necesidad.

La solución debe ser simple, comprobable y compatible con el motor existente.

---

# 17. CONFIGURACIÓN

Debe existir una única fuente de verdad.

No duplicar:

- idioma;
- preferencias;
- telemetry;
- presets;
- configuración de usuario.

La configuración debe:

- cargarse de forma segura;
- tener defaults;
- sobrevivir archivos incompletos cuando sea posible;
- validar datos;
- no corromperse fácilmente.

---

# 18. INTERNACIONALIZACIÓN

Auditar las cadenas existentes.

Eliminar sistemas duplicados.

Debe existir un único sistema de traducciones activo.

Buscar especialmente cadenas hardcodeadas en:

- CLI;
- errores;
- ayuda;
- comandos;
- progreso.

No es obligatorio traducir absolutamente todo en una sola migración si el sistema actual tiene cobertura parcial, pero no deben crearse nuevas cadenas importantes fuera del sistema elegido.

---

# 19. TKINTER Y VESTIGIOS DEL IDE

No confundir:

```text
IDLE / IDE antiguo
```

con:

```text
Tkinter utilizado por funcionalidades actuales
```

La IA debe auditar cada uso de Tkinter.

### Si pertenece exclusivamente al IDE antiguo:

Eliminarlo.

### Si pertenece a la aplicación actual:

Evaluar si es necesario para la arquitectura CLI final.

Para una CLI pura, no usar cuadros gráficos como solución normal.

Por ejemplo:

```text
messagebox
filedialog
```

no deben ser obligatorios para usar la CLI.

Si actualmente existen como fallback de errores, reemplazarlos por manejo adecuado de errores en terminal cuando sea posible.

El objetivo es:

> La CLI oficial debe funcionar completamente sin GUI.

---

# 20. `pyproject.toml`

Auditar completamente `pyproject.toml`.

Corregir información incorrecta.

La descripción del proyecto debe representar realmente Alenia-Porter.

Eliminar dependencias no utilizadas.

No mantener dependencias heredadas solo porque estaban instaladas.

Verificar cada dependencia.

Mantener únicamente dependencias necesarias para:

- el producto;
- la CLI;
- el motor;
- tests/desarrollo.

También verificar:

- backend de build;
- scripts;
- paquetes;
- package-data;
- versión mínima de Python.

---

# 21. DEPENDENCIAS

Después de la migración:

1. listar dependencias;
2. identificar quién las usa;
3. eliminar dependencias sin uso;
4. ejecutar tests;
5. confirmar que no existan imports rotos.

No eliminar una dependencia únicamente porque parece antigua: comprobar primero su uso real.

---

# 22. DOCUMENTACIÓN

Actualizar:

- `README.md`;
- documentación de instalación;
- documentación de ejecución;
- contributing;
- changelog cuando corresponda.

La documentación final no debe decir que el producto depende de:

- Go;
- React;
- Node;
- npm;
- legacy IDE.

La documentación debe reflejar la arquitectura real.

---

# 23. TESTS

Antes de eliminar código, identificar tests existentes.

Después de la migración, crear o actualizar tests para cubrir como mínimo:

## Motor

- detección de medios;
- validación;
- ejecución controlada cuando sea posible.

## CLI

- parser;
- aliases;
- comandos válidos;
- comandos inválidos;
- ayuda;
- validación de argumentos.

## Configuración

- defaults;
- carga;
- datos inválidos.

## Migración

- confirmar que no existan imports hacia `legacy`;
- confirmar que no exista dependencia Go en la ejecución Python.

---

# 24. BÚSQUEDA FINAL DE VESTIGIOS

Antes de considerar terminado el trabajo, ejecutar búsquedas globales.

Buscar:

```text
legacy
legacy/
legacy/ide
gui_web
frontend
React
npm
node_modules
go.mod
go.sum
package main
cmd/ap
go build
go test
ap_bin
```

También buscar extensiones:

```text
*.go
```

El resultado final no debe contener código Go.

Si aparece una coincidencia documental histórica, eliminarla o actualizarla según corresponda.

No aceptar referencias activas rotas.

---

# 25. REGLAS DE CALIDAD

El resultado final debe cumplir:

- sin código muerto conocido;
- sin arquitecturas duplicadas;
- sin imports rotos;
- sin rutas antiguas;
- sin workflows apuntando a componentes eliminados;
- sin dependencias innecesarias conocidas;
- sin procesos Go requeridos;
- sin Node requerido para ejecutar el producto;
- sin IDE legacy;
- CLI funcional;
- motor funcional;
- tests ejecutables.

---

# 26. PROHIBICIONES

La IA ejecutora NO debe:

- mantener Go "por si acaso";
- mantener `legacy` "por historial";
- crear una carpeta archive;
- crear una carpeta backup;
- inventar una nueva aplicación;
- reemplazar el motor funcional sin motivo;
- introducir microservicios;
- introducir comunicación RPC innecesaria;
- añadir Docker si no es necesario para el objetivo;
- añadir bases de datos;
- añadir telemetría nueva;
- cambiar el objetivo del producto;
- crear dependencias pesadas sin justificación;
- mezclar dos sistemas de CLI;
- duplicar comandos;
- dejar compatibilidad permanente con el IDE antiguo.

---

# 27. ORDEN OBLIGATORIO DE EJECUCIÓN

La IA debe seguir este orden.

## PASO 1 — Inventario

Inspeccionar:

- árbol completo;
- dependencias;
- workflows;
- scripts;
- puntos de entrada;
- Python;
- Go;
- legacy.

No modificar todavía hasta entender referencias importantes.

---

## PASO 2 — Identificar funcionalidades Go

Inventariar qué hace `cmd/ap/`.

Clasificar cada función:

```text
MIGRAR
```

o:

```text
ELIMINAR
```

---

## PASO 3 — Consolidar Python

Crear o mejorar la implementación Python necesaria.

Mantener el motor como fuente funcional principal.

---

## PASO 4 — Migrar CLI

La CLI Python debe absorber las funcionalidades útiles de Go.

Probar cada funcionalidad migrada.

---

## PASO 5 — Eliminar Go

Solo después de comprobar la migración:

- eliminar `cmd/ap`;
- eliminar `.go`;
- eliminar `go.mod`;
- eliminar `go.sum`;
- eliminar scripts y workflows Go;
- eliminar binarios generados.

---

## PASO 6 — Eliminar Legacy

Eliminar:

```text
legacy/
```

completamente.

---

## PASO 7 — Limpiar referencias

Actualizar:

- launchers;
- workflows;
- Dependabot;
- documentación;
- scripts;
- ignores.

---

## PASO 8 — Limpiar dependencias

Auditar `pyproject.toml`.

Eliminar dependencias sin uso.

---

## PASO 9 — Mejorar comandos

Implementar:

- comandos canónicos;
- aliases;
- help por comando;
- sugerencias;
- validación;
- autocompletado cuando corresponda;
- errores claros;
- progreso controlado;
- cancelación segura.

---

## PASO 10 — Tests

Ejecutar y corregir.

No considerar terminado mientras existan fallos relacionados con la migración.

---

## PASO 11 — Auditoría final

Confirmar que:

```text
Python = arquitectura final
```

y que no quedan vestigios activos.

---

# 28. CRITERIOS DE ACEPTACIÓN FINALES

El trabajo estará terminado únicamente cuando se cumpla TODO lo siguiente:

### Arquitectura

- [ ] Python es el único lenguaje de implementación principal.
- [ ] No existen archivos `.go`.
- [ ] No existe `go.mod`.
- [ ] No existe `go.sum`.
- [ ] No existe `cmd/ap/`.
- [ ] No existe `legacy/`.
- [ ] No existe el frontend del IDE antiguo.

### Ejecución

- [ ] La aplicación funciona sin Go.
- [ ] La aplicación funciona sin Node.
- [ ] La CLI Python funciona.
- [ ] El motor multimedia funciona.
- [ ] FFmpeg se ejecuta correctamente mediante la arquitectura Python.

### CLI

- [ ] `help` funciona.
- [ ] `help <comando>` funciona.
- [ ] aliases funcionan.
- [ ] comandos inválidos muestran sugerencias.
- [ ] argumentos inválidos muestran errores claros.
- [ ] progreso funciona.
- [ ] cancelación es segura.
- [ ] `exit` limpia procesos.

### Repositorio

- [ ] Workflows actualizados.
- [ ] Dependabot actualizado.
- [ ] Documentación actualizada.
- [ ] Dependencias auditadas.
- [ ] No existen referencias activas a legacy.
- [ ] No existen referencias activas a Go.
- [ ] No existen rutas rotas.

### Calidad

- [ ] Tests ejecutados.
- [ ] Errores corregidos.
- [ ] Imports validados.
- [ ] No existe código duplicado evidente entre arquitecturas antiguas.

---

# 29. RESULTADO ESPERADO

El resultado final debe sentirse como un proyecto que siempre fue diseñado así:

```text
Alenia-Porter
│
├── src/
│   └── alenia_porter/
│       ├── engine
│       ├── application
│       ├── cli
│       └── recursos necesarios
│
├── tests/
├── docs/
├── .github/
│
├── pyproject.toml
├── README.md
└── LICENSE
```

La arquitectura debe ser simple.

La velocidad debe venir de:

- menos procesos;
- menos capas;
- menos comunicación entre lenguajes;
- menos código duplicado;
- menos dependencias;
- responsabilidades claras.

No de añadir complejidad.

---

# 30. INSTRUCCIÓN FINAL PARA LA IA EJECUTORA

Ejecuta esta migración de principio a fin.

No mantengas las arquitecturas antiguas por precaución.

No dejes código legacy dentro del árbol activo.

No conserves Go como segunda implementación.

No introduzcas decisiones arquitectónicas alternativas.

Primero migra las funcionalidades necesarias.

Después elimina completamente las implementaciones antiguas.

Finalmente valida el repositorio completo.

La arquitectura final obligatoria es:

> **ALENIA-PORTER = PYTHON PURO + MOTOR PYTHON + CLI PYTHON + UNA ÚNICA FUENTE DE VERDAD.**


---

# 31. ESPECIFICACIÓN DE PRODUCTO: ALENIA-PORTER COMO HERRAMIENTA MULTIMEDIA GENERAL

Esta sección tiene prioridad sobre cualquier comportamiento antiguo que contradiga estas reglas.

Alenia-Porter deja de ser únicamente un "optimizador por carpetas".

Debe convertirse en una **CLI multimedia general, sencilla de usar**, construida sobre FFmpeg pero sin obligar al usuario a memorizar sintaxis de FFmpeg.

Objetivo:

```text
Usuario
  ↓
comando sencillo de Porter
  ↓
parser/validador Python
  ↓
plan de operación
  ↓
FFmpeg / FFprobe
  ↓
resultado
```

Porter debe ocultar la complejidad de FFmpeg, pero no limitar innecesariamente sus capacidades.

---

# 32. REGLA FUNDAMENTAL DE FFmpeg

**NO asumir que porque FFmpeg reconoce una extensión, esa extensión es un destino de salida válido.**

Antes de ofrecer cualquier formato como salida, Porter debe comprobar:

1. que existe un muxer/container de salida válido;
2. que existe un encoder compatible para el stream requerido;
3. que el codec puede escribirse dentro del container seleccionado;
4. que la compilación concreta de FFmpeg incluida con Porter soporta esa combinación;
5. que el resultado puede guardarse como archivo normal;
6. que no corresponde a un protocolo de streaming, pipe, demuxer o formato de entrada únicamente.

Por tanto:

```text
FFmpeg "conoce" el formato
≠
Porter puede ofrecerlo como salida
```

Esta regla elimina el problema actual de ofrecer destinos que producen archivos vacíos, corruptos o que requieren circunstancias especiales.

---

# 33. SISTEMA DE CAPACIDADES DE FFmpeg

Porter debe detectar las capacidades de la instancia real de FFmpeg al arrancar o bajo demanda.

Utilizar FFmpeg/FFprobe para descubrir:

```text
formats
demuxers
muxers
encoders
decoders
codecs
filters
protocols
hwaccels
pixel formats
sample formats
```

No mantener una lista gigante completamente desconectada de la instalación real.

Debe existir una capa Python de capacidades:

```text
FFmpegCapabilities
```

que pueda responder consultas equivalentes a:

```text
has_encoder("libx264")
has_encoder("libx265")
has_encoder("libvpx-vp9")
has_encoder("libopus")
has_encoder("libmp3lame")

has_muxer("mp4")
has_muxer("webm")
has_muxer("mkv")

has_filter("scale")
has_filter("crop")
has_filter("fps")
has_filter("volume")
has_filter("atempo")
has_filter("subtitles")

has_hwaccel(...)
```

La aplicación debe degradar correctamente cuando una capacidad no está disponible.

---

# 34. CLASIFICACIÓN OBLIGATORIA DE FORMATOS

Porter debe clasificar formatos en:

```text
SUPPORTED_INPUT
SUPPORTED_OUTPUT
INPUT_ONLY
STREAMING_ONLY
PIPE_ONLY
METADATA_ONLY
UNSUPPORTED
```

Además, los formatos de salida deben tener una segunda clasificación:

```text
STABLE
EXPERIMENTAL
```

### STABLE

Un destino debe aparecer como estable únicamente cuando Porter tenga una ruta de ejecución conocida, validada y testeada.

### EXPERIMENTAL

Solo aparecer si la capacidad real de FFmpeg existe pero Porter no tiene todavía una ruta especializada y robusta.

### INPUT_ONLY

No debe aparecer en el menú normal de destinos.

### STREAMING_ONLY / PIPE_ONLY / METADATA_ONLY

No deben aparecer como destinos de archivos normales.

---

# 35. FORMATOS PRINCIPALES QUE PORTER DEBE PRIORIZAR

No se trata de mostrar una lista gigantesca.

Se debe priorizar aquello que un usuario común realmente necesita.

## Video

Prioridad:

```text
MP4
MKV
WebM
MOV
AVI
GIF
M4V
TS
MPEG/MPG
WMV
```

La lista final depende de las capacidades reales detectadas.

## Audio

Prioridad:

```text
MP3
M4A/AAC
WAV
FLAC
OGG
OPUS
AIFF
WMA
AC3
```

## Imagen

Prioridad:

```text
PNG
JPG/JPEG
WebP
BMP
TIFF
TGA
GIF
```

Los destinos restantes que sean técnicos, raros o especializados deben estar disponibles únicamente mediante modo avanzado o no ofrecerse.

---

# 36. PERFILES DE USO EN LUGAR DE OPCIONES TÉCNICAS

Porter debe traducir opciones complejas a perfiles sencillos.

Ejemplo:

```text
video convert input.mp4 output.webm
```

puede tener internamente:

```text
codec = seleccionado automáticamente
quality = automático
audio = Opus apropiado
```

El usuario no debería necesitar conocer:

```text
-c:v
-c:a
-b:v
-b:a
-preset
-profile:v
-pix_fmt
-movflags
```

Sin embargo, esas capacidades deben permanecer disponibles mediante opciones avanzadas.

---

# 37. COMANDOS OFICIALES DE PORTER

La CLI final debe implementar como mínimo:

```text
porter help
porter version
porter info <archivo>

porter convert <entrada> <salida>
porter optimize <entrada>
porter compress <entrada>
porter resize <entrada> <dimensiones>
porter crop <entrada> <área>
porter rotate <entrada> <ángulo>

porter trim <entrada> <inicio> <fin>
porter cut <entrada> <inicio> <duración>

porter merge <entradas...> <salida>
porter concat <entradas...> <salida>

porter extract-audio <video> <salida>
porter mute <video> <salida>
porter audio-extract <video> <salida>

porter volume <audio> <factor> <salida>
porter normalize <audio> <salida>
porter fade <audio> <salida>

porter speed <entrada> <factor> <salida>
porter fps <video> <fps> <salida>

porter frame <video> <tiempo> <imagen>
porter thumbnail <video> <imagen>
porter gif <video> <gif>

porter subtitle <video> <subtitulos> <salida>
porter watermark <entrada> <imagen> <salida>

porter metadata <archivo>
porter remux <entrada> <salida>

porter formats
porter codecs
porter filters
porter hardware

porter config
porter lang
porter clear
porter exit
```

Los nombres pueden tener aliases, pero debe existir un único handler por comando.

---

# 38. COMANDOS DE VIDEO

## `convert`

Convierte entre formatos soportados.

Ejemplo:

```text
porter convert video.mov video.mp4
```

Debe:

1. detectar automáticamente el tipo de entrada;
2. inferir el tipo de salida por extensión;
3. determinar codecs apropiados;
4. comprobar compatibilidad;
5. usar una configuración segura;
6. evitar pérdida innecesaria de calidad;
7. preservar audio cuando sea compatible;
8. advertir si alguna pista debe ser convertida o descartada.

No utilizar un comando FFmpeg genérico ciego para todo.

---

# 39. `compress`

Debe ser un comando de alto nivel.

Ejemplos:

```text
porter compress video.mp4
porter compress video.mp4 --quality medium
porter compress video.mp4 --quality high
porter compress video.mp4 --quality small
```

Perfiles mínimos:

```text
small
balanced
high
lossless
```

Los perfiles deben estar definidos en Python y documentados.

No depender exclusivamente de CRF.

Para video:

- considerar codec;
- resolución;
- bitrate;
- preset;
- audio;
- hardware disponible.

Para audio:

- bitrate;
- sample rate;
- canales;
- codec.

---

# 40. `optimize`

`optimize` es el comando inteligente.

Debe seleccionar automáticamente una estrategia apropiada según:

```text
tipo de archivo
codec actual
container actual
resolución
bitrate
tamaño
hardware
objetivo
```

No debe re-encodear un archivo si una operación de remux/stream-copy es suficiente.

No debe comprimir una imagen PNG a JPEG únicamente para ahorrar espacio sin una orden explícita que permita pérdida.

No debe cambiar audio sin razón.

---

# 41. `resize`

Ejemplos:

```text
porter resize video.mp4 1920x1080 output.mp4
porter resize image.png 50% output.webp
porter resize video.mp4 720p output.mp4
```

Debe validar:

- dimensiones;
- relación de aspecto;
- orientación;
- límites razonables.

Opciones sencillas:

```text
--fit contain
--fit cover
--fit stretch
```

Por defecto:

```text
preservar relación de aspecto
```

---

# 42. `crop`

Ejemplos:

```text
porter crop video.mp4 1280x720+0+0 output.mp4
porter crop image.png 500x500+10+10 output.png
```

Debe validar que el área esté dentro de los límites.

Añadir una forma sencilla basada en presets cuando sea posible:

```text
--center 16:9
--square
--vertical
```

---

# 43. `rotate`

Debe soportar como mínimo:

```text
90
180
270
```

Opcionalmente:

```text
clockwise
counterclockwise
```

No aceptar ángulos arbitrarios en el comando básico si requieren filtros complejos.

La funcionalidad avanzada puede existir mediante opciones avanzadas.

---

# 44. `trim` Y `cut`

Diferencia obligatoria:

```text
trim = seleccionar un intervalo
cut = seleccionar inicio + duración
```

Ejemplos:

```text
porter trim video.mp4 00:01:30 00:03:45 clip.mp4
porter cut video.mp4 00:01:30 00:00:20 clip.mp4
```

Porter debe elegir automáticamente entre:

```text
stream copy
```

y:

```text
re-encode
```

según precisión requerida.

### Regla

Si el corte puede realizarse correctamente sin recodificar, preferirlo por velocidad.

Si el usuario requiere precisión por frame, utilizar recodificación.

La CLI debe explicar el método si existe una diferencia importante.

---

# 45. `merge` Y `concat`

Ejemplo:

```text
porter merge a.mp4 b.mp4 c.mp4 output.mp4
```

Debe comprobar:

- codec;
- resolución;
- FPS;
- streams;
- audio;
- timebase;
- container.

Si los archivos son compatibles, utilizar la estrategia rápida.

Si no son compatibles:

- normalizar;
- re-encodear;
- o rechazar con un error explicativo.

Nunca producir un archivo corrupto silenciosamente.

---

# 46. AUDIO DESDE VIDEO

Comandos:

```text
porter extract-audio video.mp4 audio.mp3
porter audio-extract video.mp4 audio.flac
```

Porter debe detectar si puede usar:

```text
stream copy
```

antes de recodificar.

Ejemplo conceptual:

```text
video.mp4
   │
   └── audio AAC
          │
          └── output.m4a
             stream copy
```

Esto debe ser mucho más rápido que convertir innecesariamente.

---

# 47. `mute`

Ejemplo:

```text
porter mute video.mp4 muted.mp4
```

Debe eliminar el stream de audio sin recodificar el video cuando sea posible.

---

# 48. `volume`

Ejemplos:

```text
porter volume audio.mp3 +3dB output.mp3
porter volume audio.mp3 -6dB output.mp3
```

Soportar también factores sencillos:

```text
0.5x
1.5x
2x
```

Validar valores.

---

# 49. `normalize`

Implementar normalización de audio mediante una estrategia controlada.

Debe distinguir:

```text
normalización de loudness
```

de:

```text
simple peak normalization
```

El modo predeterminado debe ser el adecuado para uso general.

No aplicar normalización destructiva sin recodificación cuando no sea posible.

---

# 50. `fade`

Ejemplos:

```text
porter fade audio.mp3 --in 2 --out 3 output.mp3
porter fade video.mp4 --in 2 --out 3 output.mp4
```

Debe poder aplicar fade de audio sin afectar video cuando el usuario lo solicite.

---

# 51. `speed`

Ejemplos:

```text
porter speed video.mp4 1.5x output.mp4
porter speed audio.mp3 0.75x output.mp3
```

Valores fuera de los límites admitidos deben rechazarse con un mensaje claro.

No construir automáticamente filtros inválidos.

---

# 52. `fps`

Ejemplos:

```text
porter fps video.mp4 30 output.mp4
porter fps video.mp4 60 output.mp4
```

Debe explicar cuando cambiar FPS implique recodificación.

---

# 53. `frame` Y `thumbnail`

Ejemplos:

```text
porter frame video.mp4 00:00:05 frame.png
porter thumbnail video.mp4 thumb.jpg
```

`thumbnail` debe seleccionar automáticamente un frame representativo, evitando normalmente un frame negro o de transición inicial.

---

# 54. `gif`

Ejemplo:

```text
porter gif video.mp4 output.gif
```

Debe usar una estrategia adecuada de GIF:

1. seleccionar intervalo;
2. reducir FPS;
3. limitar dimensiones razonables;
4. generar una paleta adecuada;
5. aplicar la paleta;
6. escribir GIF.

No utilizar una conversión ingenua que produzca GIFs de baja calidad.

Opciones:

```text
--start
--duration
--fps
--width
--height
```

---

# 55. SUBTÍTULOS

Ejemplo:

```text
porter subtitle video.mp4 subtitles.srt output.mp4
```

Debe diferenciar:

```text
hard-subtitle
```

de:

```text
mux subtitle stream
```

No asumir que todas las fuentes o containers permiten ambas estrategias.

---

# 56. WATERMARK

Ejemplo:

```text
porter watermark video.mp4 logo.png output.mp4
```

Posiciones sencillas:

```text
top-left
top-right
center
bottom-left
bottom-right
```

No obligar al usuario a escribir expresiones de `overlay`.

---

# 57. `remux`

Este comando existe específicamente para cambiar container sin recodificar cuando sea compatible.

Ejemplo:

```text
porter remux video.mkv video.mp4
```

Antes de ejecutar:

1. comprobar codecs;
2. comprobar compatibilidad;
3. usar stream-copy;
4. rechazar si el resultado no sería válido.

Este comando debe ser especialmente rápido.

---

# 58. `metadata`

Debe permitir consultar metadatos usando FFprobe.

Ejemplo:

```text
porter metadata video.mp4
```

Mostrar:

```text
duration
format
size
bitrate
video codec
audio codec
resolution
fps
sample rate
channels
streams
```

No mostrar todo el output bruto de FFprobe por defecto.

Añadir:

```text
--json
```

para automatización.

---

# 59. MODOS DE USO

Porter debe tener tres niveles.

## NIVEL 1 — Fácil

```text
porter compress video.mp4
porter convert video.mov video.mp4
porter cut video.mp4 00:00:10 00:00:20 clip.mp4
```

## NIVEL 2 — Opciones útiles

```text
--quality
--codec
--bitrate
--preset
--fps
--resolution
--audio
--overwrite
--output
```

## NIVEL 3 — Avanzado

Debe existir un mecanismo explícito para usuarios expertos.

Ejemplo conceptual:

```text
porter advanced ...
```

o:

```text
porter ffmpeg ...
```

Debe quedar claro que:

> El modo avanzado expone capacidades directamente asociadas a FFmpeg y no recibe las mismas garantías simplificadas de los comandos de alto nivel.

No duplicar internamente cada posible opción de FFmpeg.

Esto permite acceso completo sin convertir la CLI normal en una copia de la documentación de FFmpeg.

---

# 60. REGLA: NO EXPONER TODAS LAS OPCIONES DE FFmpeg EN LA CLI NORMAL

FFmpeg posee una cantidad enorme de opciones especializadas.

Porter NO debe convertir:

```text
porter
```

en:

```text
ffmpeg
```

copiando todos los flags.

El objetivo es:

```text
FFmpeg = motor
Porter = interfaz humana
```

Los comandos comunes deben ser fáciles.

Las capacidades avanzadas deben permanecer accesibles mediante el modo avanzado.

---

# 61. RESOLUCIÓN AUTOMÁTICA DE CODECS

Porter debe tener una política por defecto.

Ejemplo conceptual:

```text
MP4
→ H.264 + AAC
```

```text
WebM
→ VP9 + Opus
```

```text
MKV
→ codec apropiado según contenido
```

```text
MP3
→ libmp3lame
```

```text
OGG
→ libvorbis
```

```text
Opus
→ libopus
```

No seleccionar simplemente el primer encoder que FFmpeg devuelve.

Debe existir una tabla de políticas:

```text
ContainerPolicy
CodecPolicy
AudioPolicy
VideoPolicy
```

con fallback controlado.

---

# 62. HARDWARE ACCELERATION

Porter debe detectar:

```text
NVIDIA
Intel
AMD
```

cuando FFmpeg exponga la capacidad correspondiente.

Debe existir:

```text
porter hardware
```

que muestre:

```text
GPU detectada
aceleradores disponibles
encoders hardware disponibles
```

La aceleración automática debe ser conservadora.

### Regla importante

No usar GPU simplemente porque existe.

Usarla cuando:

- el codec;
- container;
- hardware;
- operación;
- calidad;
- compilación FFmpeg

sean compatibles.

Si la ruta hardware falla:

```text
hardware
   ↓ falla
software
```

con un fallback controlado.

No reintentar infinitamente.

---

# 63. FALLBACK DE FFmpeg

Toda ejecución debe tener estados claros:

```text
PLANNED
RUNNING
SUCCESS
FAILED
CANCELLED
```

Cuando FFmpeg falla:

1. capturar stderr;
2. identificar el motivo;
3. decidir si existe fallback seguro;
4. intentar como máximo el número de fallbacks definido;
5. informar el resultado.

No convertir automáticamente cada error en otra estrategia.

---

# 64. ARCHIVOS DE SALIDA

Por defecto:

- no sobrescribir archivos sin permiso;
- generar nombre seguro;
- preservar extensión correcta;
- evitar colisiones;
- permitir `--overwrite`.

Ejemplo:

```text
video.mp4
→ video_optimized.mp4
```

o:

```text
--output output.mp4
```

El comportamiento debe documentarse y ser consistente.

---

# 65. PROTECCIÓN CONTRA ARCHIVOS CORRUPTOS

Nunca escribir directamente sobre el archivo final si existe riesgo de corrupción.

Usar estrategia temporal:

```text
input
  ↓
temporary output
  ↓
validación
  ↓
rename/move atómico
  ↓
final
```

Si FFmpeg falla:

```text
temporary file
→ eliminar
```

El usuario no debe terminar con un archivo parcialmente escrito presentado como resultado exitoso.

---

# 66. VALIDACIÓN POST-PROCESAMIENTO

Después de operaciones importantes:

1. comprobar existencia;
2. comprobar tamaño > 0;
3. consultar FFprobe;
4. confirmar que el container es válido;
5. confirmar streams esperados;
6. confirmar duración razonable cuando corresponda.

Un proceso FFmpeg que termina con código 0 no debe ser la única señal de éxito.

---

# 67. OPTIMIZACIÓN Y SMART CACHE

Mantener el concepto de cache inteligente cuando sea correcto.

El cache debe incluir suficiente información para evitar resultados incorrectos.

Como mínimo considerar:

```text
input hash
size
mtime
operation
profile
output format
relevant options
Porter version
```

No reutilizar automáticamente un resultado obtenido con una configuración diferente.

---

# 68. PROCESAMIENTO POR LOTES

Los comandos deben aceptar múltiples entradas cuando tenga sentido.

Ejemplo:

```text
porter convert *.mov --to mp4
```

o una carpeta:

```text
porter optimize ./videos
```

El procesamiento por lotes debe:

- mostrar progreso;
- continuar con archivos independientes cuando sea seguro;
- registrar fallos por archivo;
- entregar resumen final.

Ejemplo:

```text
Processed: 48
Succeeded: 45
Failed: 3
Skipped: 7
```

---

# 69. SALIDAS PARA AUTOMATIZACIÓN

Todo comando debe poder usarse desde scripts.

Añadir modos como:

```text
--quiet
--json
--no-color
--non-interactive
```

El modo JSON no debe contener texto decorativo.

Ejemplo conceptual:

```json
{
  "success": true,
  "input": "...",
  "output": "...",
  "duration": 12.4,
  "operation": "convert"
}
```

Los códigos de salida deben ser consistentes:

```text
0 = éxito
1 = error de uso
2 = archivo inválido/no encontrado
3 = error de procesamiento
4 = cancelado
5 = dependencia/capacidad no disponible
```

---

# 70. CLI INTERACTIVA

La TUI Python debe usar los mismos handlers que la CLI normal.

No crear:

```text
handler_go
handler_python
```

Debe existir:

```text
CommandRegistry
    ↓
CommandHandler
    ↓
Application
```

La TUI solo debe ser otra forma de introducir comandos y visualizar resultados.

---

# 71. COMMAND REGISTRY

Todos los comandos deben registrarse centralmente.

Cada comando debe definir:

```text
name
aliases
description
usage
arguments
options
handler
examples
```

Esto permitirá generar automáticamente:

```text
help
autocomplete
suggestions
documentation
```

sin duplicar información.

---

# 72. ERRORES DE CLI

Errores como:

```text
unknown command
```

deben indicar la solución.

Ejemplo:

```text
Unknown command: compres

Did you mean:
  compress
```

Errores de formato:

```text
Output format "rtsp" cannot be used as a normal file destination.
```

Nunca:

```text
Conversion failed.
```

sin información útil.

---

# 73. SISTEMA DE AYUDA

Debe existir:

```text
porter help
porter help convert
porter help optimize
porter help cut
porter help normalize
```

La ayuda debe incluir ejemplos sencillos.

La referencia técnica de FFmpeg no debe aparecer como documentación principal.

Porter debe explicar:

```text
qué hace
cómo usarlo
ejemplo
opciones importantes
```

---

# 74. `formats`, `codecs`, `filters`, `hardware`

Estos comandos deben mostrar capacidades reales de la instalación.

## `formats`

Mostrar únicamente:

```text
input/output
```

y separar claramente:

```text
Common
Advanced
Unsupported as output
```

## `codecs`

Mostrar codecs útiles.

## `filters`

Mostrar filtros disponibles, preferentemente agrupados.

## `hardware`

Mostrar aceleración detectada.

Nunca mostrar una capacidad como disponible si la instancia real de FFmpeg no la posee.

---

# 75. DETECCIÓN DE EXTENSIONES

No basarse solamente en extensión.

Porter debe utilizar:

```text
FFprobe
```

para identificar realmente el archivo cuando sea posible.

La extensión sirve para:

- selección inicial;
- inferencia del destino;
- UI.

FFprobe sirve para:

- confirmación;
- streams;
- codec;
- container;
- duración.

---

# 76. IMÁGENES

Para imágenes, utilizar la mejor herramienta según operación.

Regla:

```text
FFmpeg cuando sea adecuado;
Pillow cuando sea mejor para la operación;
```

No utilizar FFmpeg para una operación simplemente porque puede hacerlo.

Especialmente revisar:

- PNG;
- JPEG;
- WebP;
- TIFF;
- BMP;
- TGA;
- ICO;
- GIF.

Para imágenes especializadas que Porter no pueda producir de forma fiable:

```text
no ofrecer como salida normal
```

---

# 77. PDF

PDF no debe considerarse automáticamente un formato multimedia de FFmpeg.

Si se mantiene soporte PDF:

- debe ser una capacidad separada;
- utilizar la herramienta adecuada;
- documentarlo claramente;
- no presentarlo como un encoder normal de FFmpeg.

---

# 78. MIDI

MIDI no debe tratarse como audio PCM convencional.

No ofrecer:

```text
MIDI → MP3
```

como una conversión directa de FFmpeg si requiere un sintetizador/renderizador externo.

Si no existe un sistema de renderizado MIDI explícito:

```text
MIDI = input especializado
```

y no mostrarlo como destino de audio.

---

# 79. FORMATOS QUE REQUIEREN APLICACIONES EXTERNAS

Porter no debe fingir compatibilidad.

Si un formato:

- requiere software externo;
- requiere plugin;
- requiere compilación especial;
- no puede escribirse con el FFmpeg embebido;

debe aparecer como:

```text
External / Unsupported
```

o no aparecer como destino normal.

No descargar software silenciosamente.

No abrir aplicaciones externas automáticamente.

No crear asociaciones de archivos.

---

# 80. NO ABRIR APLICACIONES DEL SISTEMA AUTOMÁTICAMENTE

Porter procesa archivos.

No debe ejecutar automáticamente:

```text
notepad
Photoshop
VLC
Windows Media Player
QuickTime
navegador
```

para completar una conversión.

El resultado debe ser un archivo.

Si en el futuro existe:

```text
porter open output.mp4
```

debe ser una acción explícita del usuario y separada de la conversión.

---

# 81. RENDIMIENTO

Priorizar:

1. evitar re-encoding innecesario;
2. stream copy cuando sea correcto;
3. utilizar hardware cuando aporte beneficio real;
4. evitar procesos Python extra;
5. evitar duplicar datos grandes en memoria;
6. procesar archivos en streaming;
7. limitar concurrencia al hardware disponible.

No usar `ThreadPoolExecutor` con una fórmula fija sin considerar el tipo de operación.

El número de procesos concurrentes debe depender de:

```text
CPU
RAM
GPU
tamaño de archivos
operación
codec
```

y tener límites seguros.

---

# 82. CANCELACIÓN

Todo trabajo debe poder cancelarse.

Al cancelar:

1. marcar operación como CANCELLED;
2. terminar FFmpeg de forma controlada;
3. esperar a su salida;
4. eliminar temporales;
5. no marcar el archivo como exitoso;
6. dejar la CLI en estado consistente.

---

# 83. THREADS Y PROCESOS

No ejecutar un nuevo proceso FFmpeg por cada operación sin límites.

Crear un gestor de trabajos.

Conceptualmente:

```text
JobManager
    │
    ├── Queue
    ├── Worker limit
    ├── Cancellation
    └── Progress
```

No sobrecargar CPU ejecutando demasiadas instancias FFmpeg.

---

# 84. TEST MATRIX OBLIGATORIA

Crear tests para operaciones comunes.

### Video

```text
MP4 → MP4
MOV → MP4
MKV → MP4
MP4 → WebM
MP4 → GIF
cut
trim
merge
resize
crop
rotate
mute
extract-audio
thumbnail
subtitle
```

### Audio

```text
WAV → MP3
FLAC → MP3
MP3 → OGG
MP3 → OPUS
trim
merge
volume
normalize
fade
speed
```

### Imagen

```text
PNG → JPG
PNG → WebP
JPG → WebP
WebP → PNG
resize
crop
```

Cada operación debe comprobar resultado mediante FFprobe/Pillow según corresponda.

---

# 85. TESTS DE FORMATOS INVALIDOS

Debe existir una matriz de negativos.

Probar explícitamente destinos como:

```text
RTSP
RTP
YUV4MPEG pipe
DASH manifest
demuxers sin muxer
codecs inexistentes
formatos sin encoder
```

El comportamiento correcto es:

```text
rechazar antes de generar un archivo corrupto
```

No intentar ciegamente.

---

# 86. TESTS DE HARDWARE

Ejecutar dos escenarios conceptuales:

```text
hardware disponible
hardware no disponible
```

El segundo debe funcionar usando software cuando sea posible.

No considerar fallo la ausencia de una GPU.

---

# 87. TESTS DE INSTALACIÓN LIMPIA

La validación final debe hacerse en un entorno limpio.

Probar:

```text
crear venv limpio
instalar paquete
ejecutar porter
porter version
porter help
porter formats
porter info sample
porter convert sample
```

No depender de imports provenientes del checkout.

---

# 88. TESTS DE RELEASE

El pipeline debe verificar el artefacto distribuible.

Comprobar:

```text
package install
entry point
resources
FFmpeg packaged/located correctly
locales
tests
```

No aceptar:

```text
works only from repository root
```

---

# 89. DOCUMENTACIÓN DEL NUEVO PRODUCTO

El README debe presentar Porter como:

> herramienta multimedia CLI/TUI para convertir, comprimir, cortar, editar, inspeccionar y procesar archivos de audio, video e imagen usando un motor FFmpeg controlado por Python.

No describir dos productos distintos.

No presentar una edición Go.

No presentar el IDE antiguo.

No utilizar como arquitectura final la frase:

```text
Python + Go
```

La documentación debe mostrar una sola aplicación.

---

# 90. MIGRACIÓN COMPLETA: CRITERIO EXTRA DE ACEPTACIÓN

Antes de cerrar la migración, la IA debe demostrar que estas afirmaciones son verdaderas:

```text
[ ] porter funciona sin Go;
[ ] porter funciona sin Node;
[ ] porter funciona sin legacy;
[ ] porter funciona sin el IDE antiguo;
[ ] porter funciona desde instalación limpia;
[ ] la CLI Python es la interfaz oficial;
[ ] la TUI Python y la CLI normal usan los mismos handlers;
[ ] FFmpeg se descubre y valida dinámicamente;
[ ] Porter no ofrece falsos formatos de salida;
[ ] operaciones comunes no requieren conocer FFmpeg;
[ ] existe modo avanzado para usuarios expertos;
[ ] conversiones simples funcionan;
[ ] cortes funcionan;
[ ] merge/concat funciona o rechaza incompatibilidades;
[ ] extracción de audio funciona;
[ ] compresión funciona;
[ ] resize/crop/rotate funcionan;
[ ] metadata funciona;
[ ] thumbnails/frames funcionan;
[ ] GIF funciona con una ruta adecuada;
[ ] audio processing funciona;
[ ] hardware acceleration tiene fallback;
[ ] cancelación funciona;
[ ] archivos corruptos no se presentan como éxitos;
[ ] batch processing funciona;
[ ] JSON/non-interactive funciona;
[ ] tests pasan;
[ ] release install funciona;
[ ] no quedan vestigios activos de la arquitectura antigua.
```

---

# 91. DEFINICIÓN FINAL DE ALENIA-PORTER

La IA ejecutora debe considerar que el objetivo final no es simplemente:

```text
"quitar Go"
```

ni:

```text
"arreglar la CLI"
```

El objetivo es producir:

```text
                ALENIA PORTER
                      │
               PYTHON PURO
                      │
          ┌───────────┴───────────┐
          │                       │
       CLI/TUI                 ENGINE
          │                       │
     CommandRegistry           FFmpeg
          │                     FFprobe
          │                       │
          └───────────┬───────────┘
                      │
               Multimedia
                      │
       ┌──────────────┼──────────────┐
       │              │              │
      Video         Audio          Image
       │              │              │
     Convert        Convert       Convert
     Compress       Trim          Resize
     Cut            Merge         Crop
     Merge          Volume        Optimize
     Resize         Normalize     ...
     Crop           Fade
     GIF            Speed
     Subtitle       ...
     ...
```

La filosofía de Porter debe ser:

> **“Hazlo fácil para el usuario; hazlo correctamente por debajo.”**

El usuario no debe aprender FFmpeg para utilizar Porter.

FFmpeg sigue siendo el motor poderoso.

Porter es la capa que convierte ese poder en comandos humanos, seguros y fáciles.

---

# 92. INSTRUCCIÓN FINAL DE EJECUCIÓN

Durante toda la implementación:

1. no crear una segunda arquitectura;
2. no preservar Go;
3. no preservar el IDE;
4. no preservar `legacy`;
5. no crear wrappers duplicados;
6. no ofrecer falsos formatos;
7. no ejecutar FFmpeg de forma ciega;
8. no considerar código de salida 0 como única validación;
9. no sobrescribir archivos accidentalmente;
10. no producir resultados parciales presentados como exitosos;
11. no introducir dependencias innecesarias;
12. no hacer que las funciones nuevas dependan de la TUI;
13. no hacer que el motor dependa de la interfaz;
14. no esconder errores;
15. no sacrificar robustez para conseguir una implementación más corta.

La implementación final debe ser:

```text
simple por fuera;
correcta por dentro;
Python de extremo a extremo;
FFmpeg como motor;
Porter como capa humana.
```
