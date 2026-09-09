import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from fuse.ffmpeg.capabilities import default_registry as caps
from fuse.media.models import Media, Stream
from fuse.planner.planner import OperationPlanner


def demo_intelligence():
    caps.load_from_ffmpeg()
    planner = OperationPlanner()

    print("="*60)
    print("INTELLIGENCE DEMONSTRATION: CONTEXTUAL TARGETS")
    print("="*60)
    
    print("\n[1] INPUT: Video MP4 (H264 + AAC)")
    video = Media(path="video.mp4", container="mp4", duration=10, size=100)
    video.streams.append(Stream(index=0, codec_type="video", codec_name="h264"))
    video.streams.append(Stream(index=1, codec_type="audio", codec_name="aac"))
    
    valid_video = []
    for m in caps.get_muxers_by_category("video"):
        if planner.plan_convert(video, m.name, f"dummy.{m.name}").is_valid:
            valid_video.append(m.name)
    print(f"Valid targets (Video): {len(valid_video)} found.")
    print(f"Examples: {', '.join(valid_video[:10])}...")
    
    print("\n[2] INPUT: Audio WAV")
    audio = Media(path="song.wav", container="wav", duration=10, size=100)
    audio.streams.append(Stream(index=0, codec_type="audio", codec_name="pcm_s16le"))
    
    valid_audio = []
    for m in caps.get_muxers_by_category("audio"):
        if planner.plan_convert(audio, m.name, f"dummy.{m.name}").is_valid:
            valid_audio.append(m.name)
    print(f"Valid targets (Audio): {len(valid_audio)} found.")
    print(f"Examples: {', '.join(valid_audio[:10])}...")

    print("\n[3] INPUT: PNG Image with Transparency (RGBA)")
    image = Media(path="transparent.png", container="png", duration=0, size=100)
    vs = Stream(index=0, codec_type="video", codec_name="png")
    vs.pix_fmt = "rgba"
    image.streams.append(vs)
    
    valid_img = []
    for m in caps.get_muxers_by_category("image"):
        if planner.plan_convert(image, m.name, f"dummy.{m.name}").is_valid:
            valid_img.append(m.name)
    print(f"Valid targets (Image): {len(valid_img)} found.")
    
    plan_jpg = planner.plan_convert(image, "jpeg", "dummy.jpeg")
    print(f"Is it possible to convert RGBA to JPEG directly? {'YES' if plan_jpg.is_valid else 'NO'}")
    if not plan_jpg.is_valid:
        print(f"Reason: {plan_jpg.error_reason}")

    print("\n[4] NEGATIVE DEMONSTRATION: Internal Inputs Exclusion (Pipes)")
    all_formats = caps.formats.keys()
    pipes = [f for f in all_formats if "pipe" in f]
    print(f"'pipe' formats found in the public list: {len(pipes)}")
    if len(pipes) == 0:
        print("SUCCESS: Inputs like 'webp_pipe' are correctly filtered out.")

    print("\n" + "="*60)

if __name__ == "__main__":
    demo_intelligence()
