#!/usr/bin/env python3
"""Remove all audio after the caller has confirmed that there is no speech."""
import argparse
import json
from pathlib import Path
import subprocess


def probe(path):
    return json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-show_streams', '-show_format',
        '-of', 'json', str(path)
    ]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--speech-status', required=True, choices=['no-speech'])
    args = parser.parse_args()
    source = args.input.resolve(strict=True)
    before = probe(source)
    if not any(s['codec_type'] == 'video' for s in before['streams']):
        parser.error('Input has no video stream')
    if not any(s['codec_type'] == 'audio' for s in before['streams']):
        print(json.dumps({'status': 'already-no-audio', 'path': str(source)}, ensure_ascii=False))
        return
    output = source.with_name(source.stem + '_无BGM.mp4')
    if output.exists():
        parser.error(f'Output already exists: {output}')
    subprocess.run([
        'ffmpeg', '-nostdin', '-v', 'error', '-n', '-i', str(source),
        '-map', '0:v:0', '-c:v', 'copy', '-an', '-movflags', '+faststart', str(output)
    ], check=True)
    after = probe(output)
    if not output.stat().st_size or any(s['codec_type'] == 'audio' for s in after['streams']):
        raise RuntimeError('Output validation failed')
    delta = abs(float(before['format']['duration']) - float(after['format']['duration']))
    if delta > 0.5:
        raise RuntimeError(f'Output duration mismatch: {delta}s')
    print(json.dumps({'status': 'audio-removed', 'path': str(output),
                      'bytes': output.stat().st_size, 'duration': after['format']['duration'],
                      'note': 'All audio, including ambience and effects, was removed.'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
