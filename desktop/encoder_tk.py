#!/usr/bin/env python3
"""Encoder desktop application.

Tkinter desktop counterpart to the Django/Vercel web application.
No third-party package is required for the core desktop converter.
charset-normalizer is optional and improves automatic detection.
"""
from __future__ import annotations

import codecs
import csv
import io
import os
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

try:
    from charset_normalizer import from_bytes
except ImportError:
    from_bytes = None

MAX_BYTES = 10 * 1024 * 1024
COMMON_ENCODINGS = [
    'utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le', 'utf-32-be',
    'ascii', 'cp932', 'shift_jis', 'shift_jisx0213', 'euc_jp', 'iso2022_jp',
    'euc_jis_2004', 'iso2022_jp_2004', 'latin-1', 'iso-8859-1', 'iso-8859-2', 'iso-8859-5',
    'iso-8859-15', 'cp1250', 'cp1251', 'cp1252', 'cp1256', 'cp1258', 'koi8-r', 'koi8-u', 'mac_roman',
    'gb2312', 'gbk', 'gb18030', 'hz', 'big5', 'big5hkscs', 'euc_kr', 'cp949'
]


def valid_codec(name: str) -> str:
    return codecs.lookup(name.strip()).name


def detect(data: bytes) -> str:
    boms = [(b'\xef\xbb\xbf', 'utf-8-sig'), (b'\xff\xfe\x00\x00', 'utf-32-le'),
            (b'\x00\x00\xfe\xff', 'utf-32-be'), (b'\xff\xfe', 'utf-16-le'), (b'\xfe\xff', 'utf-16-be')]
    for bom, enc in boms:
        if data.startswith(bom):
            return enc
    if data and all(b < 128 for b in data):
        return 'ascii'
    best = None
    if from_bytes:
        try:
            match = from_bytes(data).best()
            if match and match.encoding:
                best = match.encoding
        except Exception:
            pass
    if best:
        return best
    for enc in ('utf-8', 'cp932', 'euc_jp', 'iso2022_jp'):
        try:
            data.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return 'latin-1'


def csv_rows(text: str, max_rows: int = 100):
    try:
        dialect = csv.Sniffer().sniff(text[:200000], delimiters=',\t;|')
    except csv.Error:
        dialect = csv.excel
    rows = []
    for i, row in enumerate(csv.reader(io.StringIO(text), dialect)):
        rows.append(row)
        if i + 1 >= max_rows:
            break
    return rows


class EncoderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Encoder — Character Encoding Converter')
        self.geometry('1180x760')
        self.minsize(920, 620)
        self.file_path: Path | None = None
        self.raw = b''
        self.text = ''
        self.source = tk.StringVar(value='auto')
        self.target = tk.StringVar(value='utf-8')
        self.errors = tk.StringVar(value='strict')
        self.detected = tk.StringVar(value='-')
        self.build_ui()

    def build_ui(self):
        root = ttk.Frame(self, padding=14); root.pack(fill='both', expand=True)
        top = ttk.Frame(root); top.pack(fill='x')
        ttk.Label(top, text='Encoder', font=('TkDefaultFont', 20, 'bold')).pack(side='left')
        ttk.Label(top, text='  CSV / SQL / TXT • Inspect • Preview • Convert').pack(side='left', padx=8)
        ttk.Button(top, text='Open', command=self.open_file).pack(side='right')

        controls = ttk.LabelFrame(root, text='Conversion')
        controls.pack(fill='x', pady=12)
        for col, (label, var) in enumerate((('Input', self.source), ('Output', self.target), ('Errors', self.errors))):
            ttk.Label(controls, text=label).grid(row=0, column=col*2, sticky='w', padx=(8, 4), pady=8)
            if label == 'Errors':
                widget = ttk.Combobox(controls, textvariable=var, values=['strict','replace','ignore','backslashreplace'], state='readonly', width=22)
            else:
                widget = ttk.Combobox(controls, textvariable=var, values=['auto'] + COMMON_ENCODINGS, width=28)
            widget.grid(row=0, column=col*2+1, sticky='ew', padx=(0, 8), pady=8)
        ttk.Button(controls, text='Inspect', command=self.inspect).grid(row=1, column=0, columnspan=2, sticky='ew', padx=8, pady=8)
        ttk.Button(controls, text='Export converted file', command=self.export).grid(row=1, column=2, columnspan=2, sticky='ew', padx=8, pady=8)
        ttk.Label(controls, text='Detected:').grid(row=2, column=0, sticky='e', padx=8, pady=(0,8))
        ttk.Label(controls, textvariable=self.detected, font=('TkDefaultFont', 10, 'bold')).grid(row=2, column=1, sticky='w', pady=(0,8))
        for c in range(4): controls.columnconfigure(c, weight=1)

        preview_frame = ttk.LabelFrame(root, text='Preview (max 40,000 characters)')
        preview_frame.pack(fill='both', expand=True)
        self.text_widget = tk.Text(preview_frame, wrap='none', undo=False)
        self.text_widget.pack(side='left', fill='both', expand=True)
        y = ttk.Scrollbar(preview_frame, orient='vertical', command=self.text_widget.yview); y.pack(side='right', fill='y')
        self.text_widget.configure(yscrollcommand=y.set)
        x = ttk.Scrollbar(root, orient='horizontal', command=self.text_widget.xview); x.pack(fill='x')
        self.text_widget.configure(xscrollcommand=x.set)

        status = ttk.Label(root, text='Open a file to begin.', relief='sunken', anchor='w')
        status.pack(fill='x', pady=(8,0))
        self.status_label = status

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[('Text/CSV/SQL', '*.txt *.csv *.sql *.dump *.sqlite'), ('All files', '*.*')])
        if not path: return
        try:
            data = Path(path).read_bytes()
            if len(data) > MAX_BYTES: raise ValueError('File exceeds 10 MiB.')
            self.file_path, self.raw = Path(path), data
            self.inspect()
        except Exception as exc:
            messagebox.showerror('Encoder', str(exc))

    def inspect(self):
        if not self.raw:
            return messagebox.showwarning('Encoder', 'ファイルを先に選択してください。')
        try:
            enc = detect(self.raw)
            self.detected.set(enc)
            self.source.set(enc)
            self.text = self.raw.decode(valid_codec(enc), errors='replace')
            self.text_widget.delete('1.0', 'end')
            self.text_widget.insert('1.0', self.text[:40000])
            self.status_label.config(text=f'{self.file_path.name if self.file_path else ""} | {len(self.raw):,} bytes | detected={enc}')
        except Exception as exc:
            messagebox.showerror('Encoder', str(exc))

    def export(self):
        if not self.raw or not self.file_path:
            return messagebox.showwarning('Encoder', 'ファイルを先に選択してください。')
        try:
            source = self.source.get().strip() or detect(self.raw)
            if source == 'auto': source = detect(self.raw)
            target = valid_codec(self.target.get())
            errors = self.errors.get()
            text = self.raw.decode(valid_codec(source), errors=errors)
            output = text.encode(target, errors=errors)
            default = self.file_path.with_name(self.file_path.stem + '.converted' + self.file_path.suffix)
            path = filedialog.asksaveasfilename(initialfile=default.name, defaultextension=default.suffix)
            if not path: return
            Path(path).write_bytes(output)
            messagebox.showinfo('Encoder', f'Exported:\n{path}\n\n{source} → {target}\n{len(output):,} bytes')
        except UnicodeEncodeError:
            messagebox.showerror('Encoder', '変換先に表現できない文字があります。errors=replace/ignoreを試してください。')
        except Exception as exc:
            messagebox.showerror('Encoder', str(exc))


if __name__ == '__main__':
    EncoderApp().mainloop()
