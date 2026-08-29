"""Encoder browser-side PyScript helper.

This module intentionally performs no DOM access. It only imports Python's
standard library so that PyScript can be verified without JavaScript globals.
"""
import platform

PY_VERSION = platform.python_version()
print(f"Encoder PyScript OK | Python {PY_VERSION} | build 2026-08-29-v2")
