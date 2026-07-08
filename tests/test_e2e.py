"""End-to-end tests for dj-serve with production middleware."""

import pytest


@pytest.fixture
def static_dir(tmp_path):
    """Create a static directory with test files."""
    dist = tmp_path / "dist"
    dist.mkdir()

    # Create index.html
    (dist / "index.html").write_text("<html><body>serve</body></html>")

    # Create some static files
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "app.js").write_text("console.log('hello');")
    (dist / "data.json").write_text('{"key": "value"}')

    # Create error pages
    (dist / "400.html").write_text("<html><body>Bad Request</body></html>")
    (dist / "500.html").write_text("<html><body>Server Error</body></html>")

    return dist


def test_whitenoise_serves_static_files_wsgi(static_dir):
    """Test that WhiteNoise serves static files correctly via WSGI."""
    from whitenoise import WhiteNoise
    from io import BytesIO

    # Create a simple WSGI app
    def simple_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"Hello from Django"]

    # Wrap with WhiteNoise
    app = WhiteNoise(simple_app, root=str(static_dir))

    # Simulate a WSGI request for a static file
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/style.css",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "wsgi.input": BytesIO(),
        "wsgi.errors": BytesIO(),
    }

    response_started = []

    def start_response(status, headers):
        response_started.append((status, headers))

    # Call the WSGI app
    result = app(environ, start_response)

    # Check response
    assert response_started, "Response should have started"
    status, headers = response_started[0]
    assert status == "200 OK"

    # Check content
    body = b"".join(result)
    assert b"body { color: red; }" in body

    # Check headers
    header_dict = dict(headers)
    assert "Content-Type" in header_dict
    assert "text/css" in header_dict["Content-Type"]


def test_whitenoise_cache_headers_wsgi(static_dir):
    """Test that WhiteNoise sets cache headers correctly."""
    from whitenoise import WhiteNoise
    from io import BytesIO

    # Create a simple WSGI app
    def simple_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"Hello from Django"]

    # Wrap with WhiteNoise with cache settings
    app = WhiteNoise(simple_app, root=str(static_dir), max_age=3600)

    # Simulate a WSGI request
    environ = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/style.css",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "wsgi.input": BytesIO(),
        "wsgi.errors": BytesIO(),
    }

    response_started = []

    def start_response(status, headers):
        response_started.append((status, headers))

    # Call the WSGI app
    result = app(environ, start_response)
    b"".join(result)  # Consume the response

    # Check headers
    assert response_started
    status, headers = response_started[0]
    header_dict = dict(headers)

    # WhiteNoise should set Cache-Control
    assert "Cache-Control" in header_dict
    assert "max-age" in header_dict["Cache-Control"]


def test_whitesnout_serves_static_files_asgi(static_dir):
    """Test that WhiteSnout serves static files correctly via ASGI."""
    import asyncio
    from whitesnout import WhiteSnout

    # Create a simple ASGI app
    async def simple_app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Hello from Django",
            }
        )

    # Wrap with WhiteSnout
    app = WhiteSnout(simple_app, directory=str(static_dir))

    # Create ASGI scope for a static file request
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/style.css",
        "query_string": b"",
        "headers": [],
    }

    # Collect response
    response_started = False
    response_body = []
    response_headers = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        nonlocal response_started
        if message["type"] == "http.response.start":
            response_started = True
            response_headers.extend(message.get("headers", []))
        elif message["type"] == "http.response.body":
            response_body.append(message.get("body", b""))

    # Run the ASGI app
    asyncio.run(app(scope, receive, send))

    # Check response
    assert response_started
    body = b"".join(response_body)
    assert b"body { color: red; }" in body

    # Check headers
    header_dict = {k.decode(): v.decode() for k, v in response_headers}
    assert "content-type" in header_dict
    assert "text/css" in header_dict["content-type"]


def test_whitesnout_cache_headers_asgi(static_dir):
    """Test that WhiteSnout sets cache headers correctly."""
    import asyncio
    from whitesnout import WhiteSnout

    # Create a simple ASGI app
    async def simple_app(scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")],
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": b"Hello from Django",
            }
        )

    # Wrap with WhiteSnout with cache settings
    app = WhiteSnout(
        simple_app,
        directory=str(static_dir),
        cache_max_age=3600,
    )

    # Create ASGI scope
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/style.css",
        "query_string": b"",
        "headers": [],
    }

    response_headers = []

    async def receive():
        return {"type": "http.request", "body": b""}

    async def send(message):
        if message["type"] == "http.response.start":
            response_headers.extend(message.get("headers", []))

    # Run the ASGI app
    asyncio.run(app(scope, receive, send))

    # Check headers
    header_dict = {k.decode(): v.decode() for k, v in response_headers}
    assert "cache-control" in header_dict
    assert "max-age" in header_dict["cache-control"]


def test_middleware_integration_wsgi(static_dir, settings):
    """Test full integration with dj_serve_middleware for WSGI."""
    from dj_serve import dj_serve_middleware
    from django.core.handlers.wsgi import WSGIHandler

    # Create Django app
    django_app = WSGIHandler()

    # Wrap with dj_serve_middleware
    app = dj_serve_middleware(django_app, str(static_dir), async_mode=False)

    # Verify it's wrapped
    assert app is not None


def test_middleware_integration_asgi(static_dir, settings):
    """Test full integration with dj_serve_middleware for ASGI."""
    from dj_serve import dj_serve_middleware
    from django.core.handlers.asgi import ASGIHandler

    # Create Django app
    django_app = ASGIHandler()

    # Wrap with dj_serve_middleware
    app = dj_serve_middleware(django_app, str(static_dir), async_mode=True)

    # Verify it's wrapped
    assert app is not None


def test_production_warning_in_production_mode(static_dir, settings, caplog):
    """Test that a warning is logged when using builtin in production."""
    import logging
    from dj_serve import dj_serve

    # Set DEBUG to False (production mode)
    settings.DEBUG = False
    settings.MIDDLEWARE = []  # No static middleware

    # Capture warnings
    with caplog.at_level(logging.WARNING):
        dj_serve("/", str(static_dir))

    # Check if warning was logged
    assert any(
        "builtin static file server in production" in record.message
        for record in caplog.records
    )


def test_no_warning_in_debug_mode(static_dir, settings, caplog):
    """Test that no warning is logged when DEBUG is True."""
    import logging
    from dj_serve import dj_serve

    # Set DEBUG to True (development mode)
    settings.DEBUG = True
    settings.MIDDLEWARE = []

    with caplog.at_level(logging.WARNING):
        dj_serve("/", str(static_dir))

    # Check that no warning was logged
    assert not any(
        "builtin static file server in production" in record.message
        for record in caplog.records
    )


def test_no_warning_with_static_middleware(static_dir, settings, caplog):
    """Test that no warning is logged when static middleware is configured."""
    import logging
    from dj_serve import dj_serve

    # Set DEBUG to False but configure middleware
    settings.DEBUG = False
    settings.MIDDLEWARE = ["whitenoise.middleware.WhiteNoiseMiddleware"]

    with caplog.at_level(logging.WARNING):
        dj_serve("/", str(static_dir))

    # Check that no warning was logged
    assert not any(
        "builtin static file server in production" in record.message
        for record in caplog.records
    )


def test_production_warning_asgi(static_dir, settings, caplog):
    """Test warning mentions asgi.py when async_mode=True."""
    import logging
    from dj_serve import dj_serve

    settings.DEBUG = False
    settings.MIDDLEWARE = []

    with caplog.at_level(logging.WARNING):
        dj_serve("/", str(static_dir), async_mode=True)

    assert any("asgi.py" in record.message for record in caplog.records), (
        "Warning should mention asgi.py"
    )


def test_middleware_as_tuple(static_dir, settings, caplog):
    """MIDDLEWARE as a tuple is handled correctly."""
    import logging
    from dj_serve import dj_serve

    settings.DEBUG = False
    settings.MIDDLEWARE = ("whitenoise.middleware.WhiteNoiseMiddleware",)

    with caplog.at_level(logging.WARNING):
        dj_serve("/", str(static_dir))

    assert not any(
        "builtin static file server in production" in record.message
        for record in caplog.records
    )


def test_middleware_various_casing(static_dir, settings, caplog):
    """Middleware detection works with various casing."""
    import logging
    from dj_serve import dj_serve

    settings.DEBUG = False
    cases = [
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "WhiteNoise",
        "whitesnout.middleware.WhiteSnoutMiddleware",
        "WhiteSnout",
        "WHITENOISE",
    ]
    for middleware_value in cases:
        settings.MIDDLEWARE = [middleware_value]
        with caplog.at_level(logging.WARNING):
            dj_serve("/", str(static_dir))

        assert not any(
            "builtin static file server in production" in record.message
            for record in caplog.records
        ), f"Warning should not appear with middleware={middleware_value}"
        caplog.clear()


def test_production_warning_wsgi(static_dir, settings, caplog):
    """Test warning mentions wsgi.py when async_mode=False (default)."""
    import logging
    from dj_serve import dj_serve

    settings.DEBUG = False
    settings.MIDDLEWARE = []

    with caplog.at_level(logging.WARNING):
        dj_serve("/", str(static_dir), async_mode=False)

    assert any("wsgi.py" in record.message for record in caplog.records), (
        "Warning should mention wsgi.py"
    )
