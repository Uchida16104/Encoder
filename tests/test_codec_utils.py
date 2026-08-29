import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from converter.codec_utils import decode_bytes, encode_text, detect_encoding


def test_utf8_roundtrip():
    text = 'Encoder 日本語 café 🚀'
    assert decode_bytes(encode_text(text, 'utf-8'), 'utf-8') == text


def test_cp932_roundtrip():
    text = '日本語 ABC'
    assert decode_bytes(encode_text(text, 'cp932'), 'cp932') == text


def test_utf8_detection():
    assert detect_encoding('日本語'.encode('utf-8')) in {'utf-8', 'ascii'}
