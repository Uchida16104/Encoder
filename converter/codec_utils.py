from __future__ import annotations

import codecs
import csv
import io
import re
from typing import Any

try:
    from charset_normalizer import from_bytes
except ImportError:  # pragma: no cover
    from_bytes = None

MAX_PREVIEW_CHARS = 40_000
BOM_ENCODINGS = {
    b'\xef\xbb\xbf': 'utf-8-sig',
    b'\xff\xfe\x00\x00': 'utf-32-le',
    b'\x00\x00\xfe\xff': 'utf-32-be',
    b'\xff\xfe': 'utf-16-le',
    b'\xfe\xff': 'utf-16-be',
}

COMMON_ENCODINGS = [
    'utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be',
    'utf-32', 'utf-32-le', 'utf-32-be', 'ascii',
    'cp932', 'shift_jis', 'shift_jisx0213', 'euc_jp', 'iso2022_jp',
    'iso2022_jp_1', 'iso2022_jp_2', 'iso2022_jp_3', 'iso2022_jp_ext',
    'euc_jis_2004', 'iso2022_jp_2004',
    'latin-1', 'iso-8859-1', 'iso-8859-2', 'iso-8859-5',
    'iso-8859-15', 'cp1250', 'cp1251', 'cp1252', 'cp1256', 'cp1258',
    'koi8-r', 'koi8-u', 'mac_roman',
    'gb2312', 'gbk', 'gb18030', 'hz', 'big5', 'big5hkscs',
    'euc_kr', 'cp949',
]


def validate_codec(name: str) -> str:
    name = (name or '').strip()
    if not name:
        raise LookupError('文字コードを指定してください。')
    try:
        return codecs.lookup(name).name
    except LookupError as exc:
        raise LookupError(f'未知の文字コードです: {name}') from exc


def detect_encoding(data: bytes) -> tuple[str, float, list[dict[str, Any]]]:
    for bom, enc in BOM_ENCODINGS.items():
        if data.startswith(bom):
            return enc, 1.0, [{'encoding': enc, 'confidence': 1.0, 'source': 'BOM'}]

    candidates: list[dict[str, Any]] = []

    # charset-normalizer is the primary heuristic detector. UTF-16/32 are intentionally
    # not treated as strong strict-decode candidates because many arbitrary byte strings
    # are technically decodable by those codecs. BOM detection above is authoritative.
    if from_bytes is not None:
        try:
            matches = from_bytes(data).best(n=8)
            for match in matches:
                encoding = match.encoding or 'unknown'
                confidence = max(0.0, min(1.0, 1.0 - float(match.chaos)))
                candidates.append({'encoding': encoding, 'confidence': confidence, 'source': 'charset-normalizer'})
        except Exception:
            pass

    # Strict-decode probes are useful as a fallback/tie-breaker for common Japanese
    # encodings, but they are deliberately lower confidence than an explicit BOM.
    for enc in ('utf-8', 'cp932', 'shift_jis', 'euc_jp', 'iso2022_jp'):
        try:
            data.decode(enc)
            candidates.append({'encoding': enc, 'confidence': 0.70 if enc != 'utf-8' else 0.80, 'source': 'strict-decode'})
        except UnicodeDecodeError:
            pass

    # ASCII is valid UTF-8, so only use it when there are no non-ASCII bytes.
    if data and all(b < 128 for b in data):
        return 'ascii', 1.0, [{'encoding': 'ascii', 'confidence': 1.0, 'source': 'ASCII'}]

    if candidates:
        candidates.sort(key=lambda x: x['confidence'], reverse=True)
        best = candidates[0]
        unique = []
        seen = set()
        for item in candidates:
            key = item['encoding'].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return best['encoding'], float(best['confidence']), unique[:8]

    # latin-1 is byte-preserving for 0x00-0xFF; useful as a lossless fallback
    return 'latin-1', 0.10, [{'encoding': 'latin-1', 'confidence': 0.10, 'source': 'lossless-fallback'}]


def decode_bytes(data: bytes, encoding: str, errors: str = 'strict') -> str:
    return data.decode(validate_codec(encoding), errors=errors)


def encode_text(text: str, encoding: str, errors: str = 'strict') -> bytes:
    return text.encode(validate_codec(encoding), errors=errors)


def preview_text(text: str, limit: int = MAX_PREVIEW_CHARS) -> dict[str, Any]:
    truncated = len(text) > limit
    return {
        'text': text[:limit],
        'truncated': truncated,
        'characters': len(text),
        'lines': text.count('\n') + (1 if text else 0),
    }


def csv_preview(text: str, limit_rows: int = 100, max_cell: int = 500) -> dict[str, Any]:
    sample = text[:200_000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',\t;|')
    except csv.Error:
        dialect = csv.excel
    try:
        has_header = csv.Sniffer().has_header(sample)
    except csv.Error:
        has_header = False

    reader = csv.reader(io.StringIO(text), dialect)
    rows = []
    for idx, row in enumerate(reader):
        rows.append([cell[:max_cell] for cell in row])
        if idx + 1 >= limit_rows:
            break
    return {'rows': rows, 'has_header': has_header, 'delimiter': dialect.delimiter}


def detect_file_type(filename: str) -> str:
    name = filename.lower()
    if name.endswith('.csv'):
        return 'csv'
    if re.search(r'\.(sql|sqlite|dump)$', name):
        return 'sql'
    return 'text'
