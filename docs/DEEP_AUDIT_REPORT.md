# Auditoría Destructiva de Alenia-Porter (Post-Migración)

## 1. Arquitectura y Estructura Actual
Al revisar la base de código actual bajo `src/alenia_porter/` se constató que la arquitectura es puramente simulada y superficial:
- Existen archivos como `cli/main.py`, `ffmpeg/resolver.py`, `ffmpeg/capabilities.py`, `planner/planner.py`, pero la mayoría contiene código esqueleto o implementaciones simuladas (mocks).
- No existe una integración profunda con un motor real de FFmpeg. Las operaciones no están implementando transformaciones reales de medios, sino que se comportan como `stubs` que simplemente imprimen que la operación fue "exitosa" o usan `time.sleep` para simular trabajo, violando flagrantemente la restricción absoluta 1.1 ("Nada simulado") del documento maestro.

## 2. Motor FFmpeg y FFprobe
- **Binarios en `bin/`:** Los ejecutables `ffmpeg.bat` y `ffprobe.bat` presentes en el directorio `bin/` son **ficticios**. Son scripts dummy de Windows (`@echo off`) creados explícitamente para saltarse las validaciones de existencia, violando la regla 1.2 ("No FFmpeg dummy o wrapper dummy").
- **Subprocess y Ejecución:** Al no haber binarios reales, las llamadas a `subprocess` fallarán si se intentan utilizar para conversiones reales. La resolución del binario es un espejismo para engañar a las pruebas unitarias.

## 3. Comandos y Operaciones (CLI)
- **Implementación de Comandos:** Comandos como `convert` están implementados con código "dummy" que no procesa el input real usando un command registry verdadero.
- **Validaciones:** No existe validación de existencia de streams (FFprobe), no se analizan codecs reales y el `CapabilityRegistry` está hardcodeado y es falso.
- **CLI Framework:** Se incluyeron llamadas a librerías (`rich`, `prompt_toolkit`), pero el flujo de la CLI interactiva (`porter`) no cumple con los lineamientos de comandos reales definidos en el Spec. Es puramente visual.

## 4. Archivos Legados y Limpieza
- Se eliminó el código en Go (`cmd/ap/`, `go.mod`), y scripts antiguos de la interfaz. Esto sí se cumplió.

## 5. Pruebas (Tests)
Las pruebas bajo `tests/` (`test_cli.py`, `test_ffmpeg.py`, `test_media.py`) pasan, pero son **pruebas triviales** que no validan comportamiento, sino la mera existencia de atributos o que el resolver dummy de FFmpeg devuelva `True`. No hay pruebas de integración que consuman archivos de video o audio y apliquen validación destructiva sobre los outputs.

## CONCLUSIÓN FINAL DEL ESTADO
La migración actual es un **fraude arquitectónico**. El sistema **NO** cumple la especificación maestra y se encuentra en un estado **incompleto y simulado**. 

Se requiere **purgar los mocks**, descargar o incorporar un binario FFmpeg real en `bin/` y reconstruir el Core y el Planner para que consuman `subprocess` con argumentos reales y validen el formato mediante `ffprobe` (JSON parser).

*No he realizado cambios en el código para respetar la regla "NO HAGAS MÁS CAMBIOS TODAVÍA".*
