# Contribuir a Alenia Fuse

¡Gracias por tu interés en contribuir a Alenia Fuse! Este es un proyecto open-source diseñado para la comunidad de desarrolladores indie y estamos felices de recibir tus aportes.

## Cómo empezar
1. Haz un fork de este repositorio.
2. Clona tu fork localmente: `git clone https://github.com/TU-USUARIO/alenia-fuse.git`
3. Instala las dependencias y crea tu entorno local (preferimos `uv`).
4. Haz tus cambios en una rama descriptiva: `git checkout -b fix/mi-mejora` o `git checkout -b feat/nueva-funcion`

## Estructura del Código
- **`src/fuse/media_engine.py`**: El motor puro que envuelve a FFmpeg y maneja el procesamiento de los medios, Smart Caching y Aceleración por Hardware.
- **`src/fuse/`**: Lógica principal, utilidades y procesamiento multimedia.
- **`src/fuse/cli.py`**: El punto de entrada para la GUI (Tkinter) de la aplicación.
- **`src/fuse/cli/`**: La implementación de la CLI y sus comandos públicos.

## Reglas de Contribución
- **Seguridad primero**: Asegúrate de que tu código no introduce vulnerabilidades. Usamos Snyk en nuestro CI/CD.
- **Testing**: Todo PR importante debe incluir pruebas (pytest).
- **Formato**: Ejecuta linter y mantén la consistencia visual del código.
- **Compatibilidad**: La herramienta debe poder correr en Windows, Linux y macOS sin problemas.

## Enviar un Pull Request
- Detalla los cambios que has realizado en la descripción de tu PR.
- Asegúrate de que las GitHub Actions (build y snyk) pasan exitosamente.
- Un mantenedor de Alenia Studios revisará y fusionará tu código.

¡Gracias por apoyar el ecosistema indie!
