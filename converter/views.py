from __future__ import annotations

import json
import os

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .codec_utils import (
    COMMON_ENCODINGS, csv_preview, decode_bytes, detect_encoding,
    detect_file_type, encode_text, preview_text, validate_codec,
)

MAX_BYTES = 10 * 1024 * 1024


def _file_bytes(uploaded) -> bytes:
    if uploaded.size > MAX_BYTES:
        raise ValueError(f'ファイルサイズが上限 {MAX_BYTES // (1024 * 1024)} MiB を超えています。')
    return uploaded.read()


@require_GET
def index(request):
    return render(request, 'index.html', {
        'common_encodings': COMMON_ENCODINGS,
    })


@require_GET
def health(request):
    return JsonResponse({'status': 'ok', 'service': 'Encoder'})


@require_POST
def inspect_file(request):
    uploaded = request.FILES.get('file')
    if not uploaded:
        return JsonResponse({'ok': False, 'error': 'ファイルがありません。'}, status=400)
    try:
        data = _file_bytes(uploaded)
        detected, confidence, candidates = detect_encoding(data)
        text = decode_bytes(data, detected, errors='replace')
        file_type = detect_file_type(uploaded.name)
        payload = {
            'ok': True,
            'filename': os.path.basename(uploaded.name),
            'size': len(data),
            'file_type': file_type,
            'detected_encoding': detected,
            'confidence': round(confidence, 4),
            'candidates': candidates,
            'preview': preview_text(text),
        }
        if file_type == 'csv':
            payload['csv'] = csv_preview(text)
        return JsonResponse(payload, json_dumps_params={'ensure_ascii': False})
    except UnicodeError as exc:
        return JsonResponse({'ok': False, 'error': f'文字コードの解析に失敗しました: {exc}'}, status=422)
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)


@require_POST
def convert_file(request):
    uploaded = request.FILES.get('file')
    source = request.POST.get('source_encoding', 'auto').strip()
    target = request.POST.get('target_encoding', 'utf-8').strip()
    errors = request.POST.get('errors', 'strict').strip()
    if errors not in {'strict', 'replace', 'ignore', 'backslashreplace'}:
        errors = 'strict'

    if not uploaded:
        return JsonResponse({'ok': False, 'error': 'ファイルがありません。'}, status=400)

    try:
        data = _file_bytes(uploaded)
        detected, confidence, _ = detect_encoding(data)
        source_used = detected if source in ('', 'auto') else validate_codec(source)
        target_used = validate_codec(target)
        text = decode_bytes(data, source_used, errors=errors)
        out = encode_text(text, target_used, errors=errors)
        file_type = detect_file_type(uploaded.name)

        response = HttpResponse(out, content_type='application/octet-stream')
        stem, dot, ext = os.path.basename(uploaded.name).rpartition('.')
        suffix = f'.{ext}' if dot else ''
        response['Content-Disposition'] = f'attachment; filename="{stem or uploaded.name}.converted{suffix}"'
        response['X-Encoder-Source'] = source_used
        response['X-Encoder-Target'] = target_used
        response['X-Encoder-Detected-Confidence'] = str(round(confidence, 4))
        response['X-Encoder-File-Type'] = file_type
        return response
    except UnicodeEncodeError as exc:
        return JsonResponse({
            'ok': False,
            'error': f'変換先 {target!r} に表現できない文字があります。errors=replace または ignore を選択してください。',
            'detail': str(exc),
        }, status=422)
    except UnicodeDecodeError as exc:
        return JsonResponse({
            'ok': False,
            'error': f'入力文字コード {source!r} では読み込めません。自動判定または別の文字コードを選択してください。',
            'detail': str(exc),
        }, status=422)
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=400)
