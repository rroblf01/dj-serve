# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-07-08

### Added

- 121 tests (was 58) with 100% code coverage
- Django 6.0 URL resolver compatibility (leading `/` stripped by root resolver)
- `_build_regex()` helper extracted for testable regex generation
- Server integration tests: real WSGI (waitress) and ASGI (uvicorn) servers in pytest
- Test coverage for: symlink traversal, path traversal variants, HEAD requests, Range headers, directory index, unicode filenames, multiple prefixes, empty prefix, extensionless files, empty files, empty dict cache control, empty string error paths, middleware kwargs override, production warning variants
- Full async parity tests matching all sync edge cases
- ImportError tests for missing whitenoise/whitesnout dependencies

### Changed

- `pyproject.toml`: version 1.1.0, added waitress and uvicorn to dev dependencies
- `.gitignore`: expanded patterns for coverage, caches, and IDE files

### Fixed

- `async_serve_view`: `target.is_file()` changed to `await aiofiles.os.path.isfile()` (was calling sync method on async path)

## [1.0.0] - 2026-07-08

### Added

- Core `dj_serve()` function returning a URLPattern for serving SPAs and static sites
- `serve_view()` and `async_serve_view()` for synchronous and asynchronous serving
- SPA fallback for client-side routing (Vue Router, React Router, etc.)
- Custom 400/500 error pages scoped per frontend prefix
- Isolated error handling — no global `handler400`/`handler500` configuration needed
- Path traversal protection
- Automatic MIME type detection
- Configurable `Cache-Control` headers via string or dict with glob patterns
- `X-Content-Type-Options: nosniff` security header on all file responses
- `async_mode` parameter for non-blocking I/O with `aiofiles` (ASGI support)
- `dj_serve_middleware()` for production static file serving
- WhiteNoise integration for WSGI deployments (`pip install dj-serve[wsgi]`)
- WhiteSnout integration for ASGI deployments (`pip install dj-serve[asgi]`)
- Configuration validation at startup with `DjServeConfigError`
- Error logging in views via Python `logging`
- Production warning when using the builtin server without middleware
- PEP 561 type annotations (`py.typed`)
- Full test suite: 58 tests with pytest, pytest-django, and pytest-asyncio
- CI/CD with GitHub Actions — tests on Python 3.10–3.14, publish to PyPI on release
- Optional dependency groups: `[async]`, `[wsgi]`, `[asgi]`

### Changed

- Package renamed from `dj-spa` to `dj-serve` for uniqueness on PyPI
- All internal references renamed from `spa` to `serve` for consistency
- Return type set to `HttpResponseBase` for Django 6.0 compatibility (where `FileResponse` no longer inherits from `HttpResponse`)

[1.0.0]: https://github.com/rroblf01/dj-serve/releases/tag/v1.0.0
