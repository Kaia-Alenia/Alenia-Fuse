import sys
sys.path.insert(0, 'src')
from alenia_porter.cli.human_parser import parse_human_syntax

tests = [
    ['convert', 'movie.mp4', 'to', 'webm'],
    ['trim', 'movie.mp4', 'from', '00:01:00', 'to', '00:02:00'],
    ['resize', 'movie.mp4', '1280x720'],
    ['speed', 'movie.mp4', '2x'],
    ['extract', 'audio', 'from', 'movie.mp4'],
    ['volume', 'song.mp3', '+20%'],
    ['normalize', 'song.mp3'],
    ['thumbnail', 'movie.mp4', 'at', '00:00:10'],
    ['gif', 'movie.mp4'],
    ['fade', 'song.mp3', 'in', '3s'],
]

print('Human parser tests:')
for t in tests:
    result = parse_human_syntax(t)
    status = 'OK' if result else 'FAIL'
    cmd = result.command if result else 'None'
    joined = ' '.join(t)
    print(f'  {status}: {joined!r:<50} command={cmd}')
