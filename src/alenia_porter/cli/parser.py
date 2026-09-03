"""
CLI Parser for Alenia-Porter.
"""
import argparse

def get_parser():
    parser = argparse.ArgumentParser(description="Alenia-Porter Multimedia CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    cmds = [
        "help", "version", "info", "metadata", "convert", "optimize", "compress",
        "resize", "crop", "rotate", "trim", "cut", "merge", "concat",
        "extract-audio", "mute", "audio-extract", "volume", "normalize", "fade",
        "speed", "fps", "frame", "thumbnail", "gif", "subtitle", "watermark",
        "remux", "formats", "codecs", "filters", "hardware", "config", "lang",
        "clear", "exit"
    ]
    
    for c in cmds:
        p = subparsers.add_parser(c, help=f"{c} command")
        if c in ("info", "metadata", "optimize", "compress", "mute", "normalize"):
            p.add_argument("file", help="Input file")
            if c == "metadata":
                p.add_argument("--json", action="store_true")
        elif c in ("convert", "remux", "extract-audio", "audio-extract"):
            p.add_argument("input", help="Input file")
            p.add_argument("output", help="Output file")
            p.add_argument("--overwrite", action="store_true")
        
    return parser
