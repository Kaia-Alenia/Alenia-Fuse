import sys
import os
from pathlib import Path

# Fix path to import alenia_porter
sys.path.insert(0, str(Path(__file__).parent / "src"))

from alenia_porter.media.models import Media, Stream
from alenia_porter.cli.interactive import select_format_for_type, scan_directory, detect_media_type
from alenia_porter.ffmpeg.capabilities import default_registry as caps
from alenia_porter.planner.planner import OperationPlanner

def demo_intelligence():
    caps.load_from_ffmpeg()
    planner = OperationPlanner()

    print("="*60)
    print("DEMOSTRACIÓN DE INTELIGENCIA: TARGETS CONTEXTUALES")
    print("="*60)
    
    # 1. Video
    print("\n[1] INPUT: Video MP4 (H264 + AAC)")
    video = Media(path="video.mp4", container="mp4", duration=10, size=100)
    video.streams.append(Stream(index=0, codec_type="video", codec_name="h264"))
    video.streams.append(Stream(index=1, codec_type="audio", codec_name="aac"))
    
    valid_video = []
    for m in caps.get_muxers_by_category("video"):
        if planner.plan_convert(video, m.name, f"dummy.{m.name}").is_valid:
            valid_video.append(m.name)
    print(f"Targets válidos (Video): {len(valid_video)} encontrados.")
    print(f"Ejemplos: {', '.join(valid_video[:10])}...")
    
    # 2. Audio
    print("\n[2] INPUT: Audio WAV")
    audio = Media(path="song.wav", container="wav", duration=10, size=100)
    audio.streams.append(Stream(index=0, codec_type="audio", codec_name="pcm_s16le"))
    
    valid_audio = []
    for m in caps.get_muxers_by_category("audio"):
        if planner.plan_convert(audio, m.name, f"dummy.{m.name}").is_valid:
            valid_audio.append(m.name)
    print(f"Targets válidos (Audio): {len(valid_audio)} encontrados.")
    print(f"Ejemplos: {', '.join(valid_audio[:10])}...")

    # 3. Imagen RGBA (Semántica Correcta)
    print("\n[3] INPUT: Imagen PNG con Transparencia (RGBA)")
    image = Media(path="transparent.png", container="png", duration=0, size=100)
    vs = Stream(index=0, codec_type="video", codec_name="png")
    vs.pix_fmt = "rgba"
    image.streams.append(vs)
    
    valid_img = []
    for m in caps.get_muxers_by_category("image"):
        if planner.plan_convert(image, m.name, f"dummy.{m.name}").is_valid:
            valid_img.append(m.name)
    print(f"Targets válidos (Image): {len(valid_img)} encontrados.")
    
    # Comprobar exclusión de JPEG
    plan_jpg = planner.plan_convert(image, "jpeg", "dummy.jpeg")
    print(f"¿Es posible convertir RGBA a JPEG directamente? {'SÍ' if plan_jpg.is_valid else 'NO'}")
    if not plan_jpg.is_valid:
        print(f"Razón: {plan_jpg.error_reason}")

    # 4. Exclusión de _pipe
    print("\n[4] DEMOSTRACIÓN NEGATIVA: Exclusión de Entradas Internas (Pipes)")
    all_formats = caps.formats.keys()
    pipes = [f for f in all_formats if "pipe" in f]
    print(f"Formatos 'pipe' encontrados en la lista pública: {len(pipes)}")
    if len(pipes) == 0:
        print("ÉXITO: Entradas como 'webp_pipe' están correctamente filtradas.")

    print("\n" + "="*60)

if __name__ == "__main__":
    demo_intelligence()
