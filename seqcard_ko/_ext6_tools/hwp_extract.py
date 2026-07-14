#!/usr/bin/env python3
"""HWP v5 BodyText extractor (olefile + zlib, no external deps beyond olefile).
Standard technique: BodyText/SectionN streams are raw-deflate compressed (if
FileHeader compression bit set). Each record = 4-byte header (tag:10,level:10,size:12,
size==0xFFF -> next 4 bytes = extended size) + payload. HWPTAG_PARA_TEXT=0x43 payload
is UTF-16LE text with inline control chars (chars <0x20 except tab/newline, and the
extended-control-char blocks) that must be stripped/interpreted.
"""
import olefile, zlib, struct, sys, re

HWPTAG_PARA_TEXT = 0x43
CTRL_EXTENDED = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21}

def get_bodytext_sections(path):
    ole = olefile.OleFileIO(path)
    # detect compression from FileHeader
    compressed = True
    if ole.exists('FileHeader'):
        hdr = ole.openstream('FileHeader').read()
        if len(hdr) >= 40:
            flags = struct.unpack('<I', hdr[36:40])[0]
            compressed = bool(flags & 1)
    sections = []
    names = ole.listdir(streams=True, storages=False)
    sec_streams = sorted(
        [n for n in names if len(n) == 2 and n[0] == 'BodyText'],
        key=lambda n: int(re.sub(r'\D', '', n[1]) or 0)
    )
    for n in sec_streams:
        raw = ole.openstream(n).read()
        if compressed:
            try:
                data = zlib.decompressobj(-15).decompress(raw)
            except zlib.error:
                data = zlib.decompress(raw)
        else:
            data = raw
        sections.append(data)
    ole.close()
    return sections

def parse_records_text(data):
    out = []
    pos = 0
    n = len(data)
    while pos + 4 <= n:
        header = struct.unpack('<I', data[pos:pos+4])[0]
        tag_id = header & 0x3FF
        level = (header >> 10) & 0x3FF
        size = (header >> 20) & 0xFFF
        pos += 4
        if size == 0xFFF:
            if pos + 4 > n:
                break
            size = struct.unpack('<I', data[pos:pos+4])[0]
            pos += 4
        payload = data[pos:pos+size]
        pos += size
        if tag_id == HWPTAG_PARA_TEXT:
            text = decode_para_text(payload)
            if text.strip():
                out.append(text)
    return out

def decode_para_text(payload):
    chars = []
    i = 0
    n = len(payload)
    while i + 2 <= n:
        code = struct.unpack('<H', payload[i:i+2])[0]
        i += 2
        if code == 0x0D:  # paragraph break marker sometimes embedded
            chars.append('\n')
        elif code in (0x09,):
            chars.append('\t')
        elif code < 0x20:
            # extended control char: skip its inline fixed-size extra data (varies);
            # most inline controls (0x00-0x1F except tab/CR) are followed by 7 more
            # WCHARs of control data per HWP spec (total 8 WCHARs including this one).
            i += 14  # skip 7 more WCHAR (2 bytes each)
        elif 0xD800 <= code <= 0xDFFF:
            # surrogate pair (rare in Korean text) - skip low surrogate too if present
            continue
        else:
            chars.append(chr(code))
    return ''.join(chars)

def extract_text(path):
    sections = get_bodytext_sections(path)
    all_paras = []
    for sec in sections:
        all_paras.extend(parse_records_text(sec))
    return '\n'.join(all_paras)

if __name__ == '__main__':
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    text = extract_text(src)
    if dst:
        with open(dst, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"wrote {len(text)} chars to {dst}")
    else:
        print(text[:2000])
