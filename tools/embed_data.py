#!/usr/bin/env python3
"""Generate aligned runtime byte arrays from their preferred binary/text inputs."""
import argparse
from pathlib import Path
import zlib

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
parser.add_argument('--symbol', required=True); parser.add_argument('--raw', action='store_true')
args = parser.parse_args()
data = args.source.read_bytes(); packed = data if args.raw else zlib.compress(data, 9)
visibility = '' if args.raw else 'static '
name = args.symbol if args.raw else args.symbol + '_zlib'
text = f'/* Generated from {args.source.name} by tools/embed_data.py. */\n#include <stddef.h>\n#include <stdint.h>\n'
text += f'{visibility}const size_t {args.symbol}_size = {len(data)};\n'
text += f'{visibility}const uint8_t {name}[] __attribute__((aligned(8))) = {{\n'
text += '\n'.join('    ' + ','.join(f'0x{x:02x}' for x in packed[i:i+24]) + ',' for i in range(0, len(packed), 24))
text += '\n};\n'; args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(text)
