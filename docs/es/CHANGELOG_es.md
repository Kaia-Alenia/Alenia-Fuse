# Changelog

## [2.0.1] — Assets de FFmpeg

### Cambios

- Se añadieron descargas verificadas y en caché de FFmpeg desde los assets de GitHub Releases.
- Se añadió el comando `fuse setup` para preparar explícitamente el motor multimedia.
- Los binarios de FFmpeg permanecen fuera de PyPI y del repositorio Git.

## [2.0.0] — Rebranding de Alenia Fuse

Alenia Fuse inicia una nueva línea de producto con una identidad pública renovada y un flujo multimedia enfocado.

### Cambios

- El paquete Python ahora se llama `fuse`.
- La distribución ahora se llama `alenia-fuse`.
- El comando oficial ahora es `fuse`.
- Se eliminaron el backend externo y sus archivos de despliegue heredados.
- La línea pública de versiones se reinició en 2.0.
- Se conservaron el CLI interactivo, la API Python, las capacidades de FFmpeg y el sistema de idiomas.

### Nota de migración

Alenia Fuse se llamaba anteriormente Alenia-Porter. Las instalaciones nuevas deben usar `pip install alenia-fuse` y ejecutar `fuse`.
