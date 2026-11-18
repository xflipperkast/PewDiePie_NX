#!/usr/bin/env python3
"""Keep selected Android resource locales and compact their shared string pool.

Resource IDs, default/density/version variants and retained values are preserved.
"""
import argparse
from pathlib import Path
import struct

U32_MAX = 0xffffffff
def u16(b, o): return struct.unpack_from('<H', b, o)[0]
def u32(b, o): return struct.unpack_from('<I', b, o)[0]
def put32(b, o, value): struct.pack_into('<I', b, o, value)


def chunks(data, start):
    while start < len(data):
        kind, header, size = struct.unpack_from('<HHI', data, start)
        if not 8 <= header <= size or start + size > len(data): raise ValueError('Malformed resource chunk')
        yield kind, bytearray(data[start:start + size])
        start += size


def entries(chunk):
    header, flags, count, base = u16(chunk, 2), chunk[9], u32(chunk, 12), u32(chunk, 16)
    seen = set()
    for index in range(count):
        if flags & 1:
            offset = u16(chunk, header + index * 4 + 2) * 4
        elif flags & 2:
            offset = u16(chunk, header + index * 2)
            if offset == 0xffff: continue
            offset *= 4
        else:
            offset = u32(chunk, header + index * 4)
            if offset == U32_MAX: continue
        start = base + offset
        size = u16(chunk, start)
        if chunk[start + 2] & 1:
            for pos in range(start + size, start + size + u32(chunk, start + 12) * 12, 12):
                if pos + 4 not in seen:
                    seen.add(pos + 4); yield pos + 4
        elif start + size not in seen:
            seen.add(start + size); yield start + size


class Pool:
    def __init__(self, data):
        self.data = data
        self.header, self.count, self.styles, self.flags = u16(data, 2), u32(data, 8), u32(data, 12), u32(data, 16)
        self.start, self.style_start = u32(data, 20), u32(data, 24)

    def raw(self, index):
        start = self.start + u32(self.data, self.header + index * 4)
        pos = start
        if self.flags & 256:
            for _ in range(2):
                n = self.data[pos]; pos += 1
                if n & 128: n = ((n & 127) << 8) | self.data[pos]; pos += 1
            end = pos + n + 1
        else:
            n = u16(self.data, pos); pos += 2
            if n & 0x8000: n = ((n & 0x7fff) << 16) | u16(self.data, pos); pos += 2
            end = pos + n * 2 + 2
        return bytes(self.data[start:end])

    def spans(self, index):
        if index >= self.styles: return []
        offset = u32(self.data, self.header + self.count * 4 + index * 4)
        if offset == U32_MAX: return []
        out, pos = [], self.style_start + offset
        while u32(self.data, pos) != U32_MAX:
            out.append(struct.unpack_from('<III', self.data, pos)); pos += 12
        return out


def compact(data, languages):
    root_header = bytearray(data[:u16(data, 2)])
    parts = list(chunks(data, len(root_header)))
    pool = Pool(next(chunk for kind, chunk in parts if kind == 1))
    packages, used = [], set()
    kept_configs = dropped_configs = 0
    for kind, package in parts:
        if kind != 0x200: continue
        header = bytearray(package[:u16(package, 2)])
        selected = []
        old_offset = len(header)
        for item_kind, item in chunks(package, len(header)):
            item_start = old_offset
            old_offset += len(item)
            if item_kind == 0x201:
                language = bytes(item[28:30])
                if language != b'\0\0' and language not in languages:
                    dropped_configs += 1; continue
                kept_configs += 1
                for pos in entries(item):
                    if item[pos + 3] == 3: used.add(u32(item, pos + 4))
            elif item_kind not in {1, 0x202, 0x203}:
                raise ValueError(f'Unsupported metadata chunk {item_kind:#x}; refusing unsafe compaction')
            if item_kind == 1:
                for field in (268, 276):
                    if u32(package, field) == item_start:
                        put32(header, field, len(header) + sum(len(x) for _, x in selected))
            selected.append((item_kind, item))
        packages.append((header, selected))
    pending = list(used)
    while pending:
        for index, _, _ in pool.spans(pending.pop()):
            if index not in used: used.add(index); pending.append(index)
    order = sorted(used)
    mapping = {old: new for new, old in enumerate(order)}
    offsets, strings = [], bytearray()
    for old in order:
        offsets.append(len(strings)); strings.extend(pool.raw(old))
    strings.extend(b'\0' * (-len(strings) % 4))
    styled = any(pool.spans(old) for old in order)
    style_offsets, styles = [], bytearray()
    if styled:
        for old in order:
            spans = pool.spans(old)
            style_offsets.append(len(styles) if spans else U32_MAX)
            for name, first, last in spans: styles.extend(struct.pack('<III', mapping[name], first, last))
            if spans: styles.extend(struct.pack('<III', U32_MAX, U32_MAX, U32_MAX))
    string_start = 28 + len(order) * 4 + len(style_offsets) * 4
    style_start = string_start + len(strings) if styled else 0
    new_pool = struct.pack('<HH6I', 1, 28, string_start + len(strings) + len(styles), len(order),
                           len(style_offsets), pool.flags & ~1, string_start, style_start)
    new_pool += struct.pack(f'<{len(offsets)}I', *offsets)
    new_pool += struct.pack(f'<{len(style_offsets)}I', *style_offsets) + strings + styles
    output = root_header + new_pool
    values_checked = 0
    for header, selected in packages:
        for kind, item in selected:
            if kind == 0x201:
                for pos in entries(item):
                    if item[pos + 3] == 3:
                        old = u32(item, pos + 4)
                        put32(item, pos + 4, mapping[old]); values_checked += 1
        body = b''.join(item for _, item in selected)
        put32(header, 4, len(header) + len(body)); output += header + body
    put32(output, 4, len(output))
    # Check every retained string's bytes and style spans independently of IDs.
    check = Pool(new_pool)
    for old, new in mapping.items():
        assert pool.raw(old) == check.raw(new)
        assert [(mapping[n], a, b) for n, a, b in pool.spans(old)] == check.spans(new)
    return bytes(output), dict(original_bytes=len(data), compact_bytes=len(output), kept_configs=kept_configs,
                               removed_locale_configs=dropped_configs, strings_before=pool.count,
                               strings_after=len(order), checked_string_values=values_checked)


if __name__ == '__main__':
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path); parser.add_argument('output', type=Path)
    parser.add_argument('--locales', nargs='+', default=['en', 'ru'])
    args = parser.parse_args()
    result, report = compact(args.source.read_bytes(), {s.encode('ascii') for s in args.locales})
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_bytes(result)
    print(json.dumps(report, indent=2))
