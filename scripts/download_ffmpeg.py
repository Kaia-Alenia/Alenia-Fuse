"""Download the platform FFmpeg build (CLI wrapper).

This script used to be a standalone draft that wrote binaries to
relative `bin/<platform>/` folders and left macOS half done. It is now
just a thin wrapper around the real implementation in
`fuse.ffmpeg.downloader`, which downloads into the user cache and
verifies both binaries before accepting them.

Usage:
    python scripts/download_ffmpeg.py [--cache-dir DIR]
"""
import argparse
import sys
from pathlib import Path

# Allow running from a source checkout without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fuse.ffmpeg.downloader import download_ffmpeg  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Download the platform FFmpeg build.")
    parser.add_argument("--cache-dir", default=None,
                        help="Cache folder (default: ~/.cache/alenia-fuse/ffmpeg)")
    args = parser.parse_args()
    try:
        ffmpeg, ffprobe = download_ffmpeg(args.cache_dir)
    except Exception as exc:
        print(f"FFmpeg download failed: {exc}", file=sys.stderr)
        return 1
    print(f"ffmpeg:  {ffmpeg}")
    print(f"ffprobe: {ffprobe}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
