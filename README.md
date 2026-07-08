[![PyPI version](https://img.shields.io/pypi/v/dj-spa.svg)](https://pypi.org/project/dj-spa/)
[![Python versions](https://img.shields.io/pypi/pyversions/dj-spa.svg)](https://pypi.org/project/dj-spa/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Typing: Typed](https://img.shields.io/badge/typing-PEP%20561-brightgreen.svg)](https://peps.python.org/pep-0561/)
[![CI](https://github.com/rroblf01/dj-spa/actions/workflows/ci.yml/badge.svg)](https://github.com/rroblf01/dj-spa/actions/workflows/ci.yml)

# dj-spa

Serve SPAs (Vue, React, Angular, Svelte, or vanilla HTML) directly from Django — no separate static server needed.

```python
from dj_spa import dj_spa

urlpatterns = [
    dj_spa("/", "dist/", "index.html", "dist/400.html", "dist/500.html"),
]
```

## Why?

Traditional Django + SPA setups require either:

- **A separate static file server** (nginx, Apache, CDN) — adds deployment complexity.
- **`django.contrib.staticfiles`** — not designed for SPAs; no client-side routing fallback, no custom error pages per frontend.

`dj-spa` solves both:

| Feature | `staticfiles` | `dj-spa` |
|---------|---------------|----------|
| SPA fallback (client-side routing) | ❌ | ✅ |
| Custom 400/500 pages per SPA | ❌ | ✅ |
| Isolated error handling (no global handlers) | ❌ | ✅ |
| Path traversal protection | ❌ | ✅ |
| Correct MIME types | ✅ | ✅ |
| Works with any prefix | ✅ | ✅ |

## Installation

```bash
pip install dj-spa
```

Requires **Django ≥ 4.0** and **Python ≥ 3.10**.

## Usage

### Basic SPA

```python
from django.urls import include, path
from dj_spa import dj_spa

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("myapi.urls")),
    dj_spa("/", "dist/"),
]
```

`dj_spa("/", "dist/")` will:

1. Serve files from `dist/` (e.g., `dist/style.css` at `/style.css`).
2. For any other route under `/`, serve `dist/index.html` — this enables client-side routing (Vue Router, React Router, etc.).
3. Return 404 if neither the file nor `index.html` exists.

### With custom error pages

```python
dj_spa("/", "dist/", error_400="dist/400.html", error_500="dist/500.html")
```

Error pages are served **only for routes under this prefix** — your API and admin endpoints keep their default error handling.

### With a prefix

```python
dj_spa("/app", "dist/", "index.html")
```

Serves the SPA at `/app/`, `/app/about`, `/app/dashboard`, etc.

### Vanilla HTML site

```python
dj_spa("/", "site/", entry_point="index.html")
```

Works the same way — SPA fallback just means unknown routes serve `index.html`.

### Cache-Control headers

```python
dj_spa("/", "dist/", cache_control="public, max-age=3600")
```

Apply the same value to all responses, or use a dict with glob patterns:

```python
dj_spa("/", "dist/", cache_control={
    "*.html": "no-cache",
    "*.css":  "public, max-age=31536000, immutable",
    "*.js":   "public, max-age=31536000, immutable",
    "*":      "public, max-age=3600",
})
```

| `cache_control` | Behaviour |
|-----------------|-----------|
| `None` (default) | No `Cache-Control` header |
| `str` | Same value for every response |
| `dict[str, str]` | Glob patterns matched against the filename; first match wins |

## API

```python
def dj_spa(
    prefix: str,
    dist_dir: str,
    entry_point: str = "index.html",
    error_400: str | None = None,
    error_500: str | None = None,
    cache_control: str | dict[str, str] | None = None,
) -> URLPattern:
```

| Argument | Default | Description |
|----------|---------|-------------|
| `prefix` | — | URL prefix (e.g., `/`, `/app`) |
| `dist_dir` | — | Path to the directory with static files |
| `entry_point` | `"index.html"` | HTML file to serve for SPA fallback (client-side routing) |
| `error_400` | `None` | Path to a custom 400 error page |
| `error_500` | `None` | Path to a custom 500 error page |
| `cache_control` | `None` | `Cache-Control` header value. `str` for all files, `dict` for per-pattern (glob) |

## How it works

1. Django resolves the URL through the `re_path` pattern.
2. The view looks for the requested file in `dist_dir`.
3. If found → served with the correct MIME type.
4. If not found → serves `entry_point` (SPA fallback).
5. If the entry point is missing → serves the custom `error_400` page, or 404.
6. If an exception occurs → serves the custom `error_500` page, or 500.

All error handling is **contained within the view** — no global `handler400`/`handler500` configuration needed.

## Testing locally

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
