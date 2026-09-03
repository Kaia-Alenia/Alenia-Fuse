import urllib.request
import zipfile
import os
import shutil

def download_macos():
    try:
        # User-Agent needed for evermeet
        req = urllib.request.Request(
            'https://evermeet.cx/ffmpeg/getrelease/zip', 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response, open('mac_ffmpeg.zip', 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        with zipfile.ZipFile('mac_ffmpeg.zip', 'r') as zip_ref:
            zip_ref.extract('ffmpeg', 'bin/macos-arm64/')
        os.remove('mac_ffmpeg.zip')
        
        req = urllib.request.Request(
            'https://evermeet.cx/ffmpeg/getrelease/ffprobe/zip', 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        with urllib.request.urlopen(req) as response, open('mac_ffprobe.zip', 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
            
        with zipfile.ZipFile('mac_ffprobe.zip', 'r') as zip_ref:
            zip_ref.extract('ffprobe', 'bin/macos-arm64/')
        os.remove('mac_ffprobe.zip')
        print("macOS binaries downloaded")
    except Exception as e:
        print(f"Failed macOS download: {e}")

if __name__ == "__main__":
    download_macos()
