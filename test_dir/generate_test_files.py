import os
import random
import subprocess

from PIL import Image, ImageDraw

test_dir = os.path.dirname(os.path.abspath(__file__))

audio_formats = ["mp3", "ogg", "wav", "m4a", "flac"]
video_formats = ["mp4", "mkv", "webm", "avi", "mov"]
image_formats = ["jpg", "png", "webp", "bmp", "tiff"]

print(f"Generating 15 test files in: {test_dir}")

# Generate Audio Files
for fmt in audio_formats:
    target_file = os.path.join(test_dir, f"sample_audio.{fmt}")
    codec = "libmp3lame" if fmt == "mp3" else "libvorbis" if fmt == "ogg" else "aac" if fmt == "m4a" else "flac" if fmt == "flac" else "pcm_s16le"
    ffmpeg_path = r"C:\Users\BearS\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe"
    subprocess.run([
        ffmpeg_path, "-y",
        "-f", "lavfi", "-i", "sine=f=261.63:d=3",
        "-f", "lavfi", "-i", "sine=f=329.63:d=3",
        "-f", "lavfi", "-i", "sine=f=392.00:d=3",
        "-filter_complex", "[0:a][1:a][2:a]amix=inputs=3:duration=first,volume=1.6",
        "-c:a", codec,
        target_file
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Generate Video Files
for fmt in video_formats:
    target_file = os.path.join(test_dir, f"sample_video.{fmt}")
    vcodec = "libx264"
    if fmt == "webm":
        vcodec = "libvpx-vp9"
    elif fmt == "avi":
        vcodec = "mpeg4"
    
    acodec = "aac"
    if fmt == "webm":
        acodec = "libvorbis"
    elif fmt == "wav":
        acodec = "pcm_s16le"
    elif fmt == "flac":
        acodec = "flac"
        
    subprocess.run([
        ffmpeg_path, "-y",
        "-f", "lavfi", "-i", "testsrc2=size=320x240:d=3",
        "-f", "lavfi", "-i", "sine=f=261.63:d=3",
        "-c:v", vcodec,
        "-c:a", acodec,
        "-shortest",
        target_file
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# Generate Image Files
def create_pixel_art_landscape():
    img = Image.new("RGB", (320, 240), "#0f172a")
    draw = ImageDraw.Draw(img)
    for y in range(120):
        r = int(15 + (120 - y) * 0.8)
        g = int(23 + (120 - y) * 0.5)
        b = int(42 + (120 - y) * 0.2)
        draw.line([(0, y), (320, y)], fill=(r, g, b))
    random.seed(42)
    for _ in range(30):
        sx = random.randint(0, 320)
        sy = random.randint(0, 100)
        draw.point((sx, sy), fill="#ffffff")
    draw.ellipse([240, 30, 270, 60], fill="#fef08a")
    draw.polygon([(0, 240), (80, 120), (180, 240)], fill="#1e293b")
    draw.polygon([(100, 240), (220, 90), (320, 240)], fill="#0f172a")
    draw.polygon([(200, 240), (280, 150), (320, 240)], fill="#1e293b")
    draw.rectangle([0, 200, 320, 240], fill="#064e3b")
    return img

img_base = create_pixel_art_landscape()
for fmt in image_formats:
    target_file = os.path.join(test_dir, f"sample_image.{fmt}")
    pillow_fmt = "JPEG" if fmt == "jpg" else "MPO" if fmt == "mpo" else fmt.upper()
    img_base.save(target_file, format=pillow_fmt)

print("Generated 15 test files successfully!")
