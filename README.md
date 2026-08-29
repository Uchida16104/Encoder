# Encoder

Encoder is a Python 3 character-encoding inspection, preview, conversion, and export application for CSV, SQL, and general text files.

The project has two interfaces:

- **Web application:** Django on Vercel.
- **Desktop application:** Tkinter.

The web UI integrates HTMX, Tailwind CSS, hyperscript, Alpine.js, Motion, sql.js, and PyScript as requested.

## What Encoder does

1. Upload a CSV, SQL, TXT, dump, or other text-oriented file.
2. Detect an input encoding using BOM detection, strict decoding probes, and `charset-normalizer`.
3. Preview the decoded content.
4. For CSV files, show a tabular preview and try to detect the delimiter.
5. Choose any encoding registered with Python's `codecs` registry, including aliases.
6. Choose an error policy: `strict`, `replace`, `ignore`, or `backslashreplace`.
7. Export the converted bytes.
8. Optionally run SQL preview text through sql.js in the browser.

## Important limitation about “all encodings”

No software can guarantee every historical, proprietary, undocumented, or corrupted byte encoding. Encoder therefore uses Python's codec registry for conversion (which is much broader than a fixed dropdown) and `charset-normalizer` for detection. Detection is heuristic; when confidence is low, select the source encoding manually.

Also, no single target encoding can represent every Unicode character. For example, legacy Japanese codecs such as CP932 cannot represent arbitrary emoji. Use `errors=strict` to detect this safely, or `replace`/`ignore` when intentional data loss is acceptable.

## Project structure

```text
Encoder/
├── manage.py
├── requirements.txt
├── pyproject.toml
├── vercel.json
├── README.md
├── encoder_project/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── converter/
│   ├── __init__.py
│   ├── apps.py
│   ├── codec_utils.py
│   └── views.py
├── templates/
│   └── index.html
├── static/
├── desktop/
│   └── encoder_tk.py
└── tests/
    └── test_codec_utils.py
```

## Local web development

```bash
cd Encoder
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## Desktop application

With the virtual environment activated:

```bash
python desktop/encoder_tk.py
```

The desktop core works without third-party packages, but installing `requirements.txt` enables better automatic encoding detection through `charset-normalizer`.

## Test

```bash
python -m pytest -q
```

## Vercel deployment

The current Vercel Django template supports Django with the Python Runtime and documents automatic detection of `manage.py`, the WSGI entrypoint, and static-file handling. Encoder follows that project layout. See the official Vercel Django template for the current deployment behavior.

### Option A: Vercel CLI

```bash
npm i -g vercel
cd Encoder
vercel login
vercel
```

Set a production secret before or during deployment:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Use the generated value for the `DJANGO_SECRET_KEY` environment variable in Vercel.

### Option B: GitHub import

1. Push this project to GitHub.
2. Import the repository into Vercel.
3. Set `DJANGO_SECRET_KEY` as an Environment Variable.
4. Deploy.

## API

### `GET /`
Returns the web UI.

### `POST /api/inspect/`
Multipart form field:

- `file`: uploaded text-oriented file.

Returns JSON containing detected encoding, confidence, file type, text preview, and CSV rows when applicable.

### `POST /api/convert/`
Multipart/form fields:

- `file`
- `source_encoding` (`auto` or a Python codec name)
- `target_encoding`
- `errors` (`strict`, `replace`, `ignore`, `backslashreplace`)

Returns the converted bytes as a download response.

### `GET /health/`
Returns a small JSON health response.

## Security and operational notes

- Uploaded files are processed in memory and are not intentionally persisted by the application.
- The server limits individual uploads to 10 MiB.
- SQL input is previewed as text. The web application's optional sql.js feature executes SQL in the user's browser, not against the server database.
- Do not upload confidential data to an Internet-facing deployment unless the deployment's privacy, authentication, logging, and retention requirements have been reviewed.
- For large files, use chunked or asynchronous processing instead of the simple synchronous endpoint in this starter.

## Third-party frontend libraries

The HTML currently references CDN-hosted versions of:

- HTMX
- Tailwind CSS
- hyperscript
- Alpine.js
- Motion
- sql.js
- PyScript

For production environments with strict supply-chain policies, pin and self-host these assets and add Subresource Integrity where appropriate.
