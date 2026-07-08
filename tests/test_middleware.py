"""Unit tests for dj_serve_middleware()."""

import pytest
from unittest.mock import MagicMock, patch

from dj_serve import dj_serve_middleware


def test_middleware_wsgi_mode():
    """Test that async_mode=False uses WhiteNoise."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_serve.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        result = dj_serve_middleware(app, dist_dir, async_mode=False)

        mock_setup.assert_called_once_with(app, dist_dir)
        assert result == mock_setup.return_value


def test_middleware_asgi_mode():
    """Test that async_mode=True uses WhiteSnout."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_serve.middleware._setup_whitesnout") as mock_setup:
        mock_setup.return_value = MagicMock()
        result = dj_serve_middleware(app, dist_dir, async_mode=True)

        mock_setup.assert_called_once_with(app, dist_dir)
        assert result == mock_setup.return_value


def test_middleware_default_is_wsgi():
    """Test that default (no async_mode) uses WhiteNoise."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_serve.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        result = dj_serve_middleware(app, dist_dir)

        mock_setup.assert_called_once_with(app, dist_dir)
        assert result == mock_setup.return_value


def test_middleware_passes_kwargs():
    """Test that kwargs are passed to the backend."""
    app = MagicMock()
    dist_dir = "/tmp/dist"
    kwargs = {"cache_max_age": 3600, "security_headers": True}

    with patch("dj_serve.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        dj_serve_middleware(app, dist_dir, async_mode=False, **kwargs)

        mock_setup.assert_called_once_with(app, dist_dir, **kwargs)


def test_middleware_wsgi_missing_whitenoise():
    """Test that ImportError is raised when WhiteNoise is not installed."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_serve.middleware._setup_whitenoise") as mock_setup:
        mock_setup.side_effect = ImportError("WhiteNoise not installed")

        with pytest.raises(ImportError, match="WhiteNoise not installed"):
            dj_serve_middleware(app, dist_dir, async_mode=False)


def test_middleware_asgi_missing_whitesnout():
    """Test that ImportError is raised when WhiteSnout is not installed."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_serve.middleware._setup_whitesnout") as mock_setup:
        mock_setup.side_effect = ImportError("WhiteSnout not installed")

        with pytest.raises(ImportError, match="WhiteSnout not installed"):
            dj_serve_middleware(app, dist_dir, async_mode=True)


def test_setup_whitenoise_with_real_library(tmp_path):
    """Test that _setup_whitenoise works with real WhiteNoise library."""
    from dj_serve.middleware import _setup_whitenoise
    from whitenoise import WhiteNoise

    # Create a simple WSGI app
    def simple_app(environ, start_response):
        start_response("200 OK", [("Content-Type", "text/plain")])
        return [b"Hello World"]

    # Create dist directory
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("test content")

    # Setup WhiteNoise
    wrapped_app = _setup_whitenoise(simple_app, str(dist))

    # Verify it's a WhiteNoise instance
    assert isinstance(wrapped_app, WhiteNoise)


def test_middleware_passes_kwargs_whitesnout():
    """Test that kwargs are passed to the WhiteSnout backend."""
    app = MagicMock()
    dist_dir = "/tmp/dist"
    kwargs = {"cache_max_age": 3600}

    with patch("dj_serve.middleware._setup_whitesnout") as mock_setup:
        mock_setup.return_value = MagicMock()
        dj_serve_middleware(app, dist_dir, async_mode=True, **kwargs)

        mock_setup.assert_called_once_with(app, dist_dir, **kwargs)


def test_middleware_truthy_async_mode():
    """Truthy/falsy non-boolean values for async_mode are accepted."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_serve.middleware._setup_whitenoise") as mock_wn:
        with patch("dj_serve.middleware._setup_whitesnout") as mock_ws:
            # None -> WSGI (falsy)
            dj_serve_middleware(app, dist_dir, async_mode=None)
            mock_wn.assert_called_once()
            mock_wn.reset_mock()

            # 1 -> ASGI (truthy)
            dj_serve_middleware(app, dist_dir, async_mode=1)
            mock_ws.assert_called_once()


def test_setup_whitesnout_with_real_library(tmp_path):
    """Test that _setup_whitesnout works with real WhiteSnout library."""
    from dj_serve.middleware import _setup_whitesnout
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
                "body": b"Hello World",
            }
        )

    # Create dist directory
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("test content")

    # Setup WhiteSnout
    wrapped_app = _setup_whitesnout(simple_app, str(dist))

    # Verify it's a WhiteSnout instance
    assert isinstance(wrapped_app, WhiteSnout)


def test_middleware_kwargs_override_root_whitenoise():
    """kwargs can override the default 'root' key for WhiteNoise."""
    app = MagicMock()
    dist_dir = "/tmp/dist"
    custom_root = "/custom/path"

    with patch("dj_serve.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        dj_serve_middleware(app, dist_dir, async_mode=False, root=custom_root)
        mock_setup.assert_called_once_with(app, dist_dir, root=custom_root)


def test_middleware_kwargs_override_directory_whitesnout():
    """kwargs can override the default 'directory' key for WhiteSnout."""
    app = MagicMock()
    dist_dir = "/tmp/dist"
    custom_dir = "/custom/path"

    with patch("dj_serve.middleware._setup_whitesnout") as mock_setup:
        mock_setup.return_value = MagicMock()
        dj_serve_middleware(app, dist_dir, async_mode=True, directory=custom_dir)
        mock_setup.assert_called_once_with(app, dist_dir, directory=custom_dir)


def test_setup_whitenoise_import_error():
    """_setup_whitenoise raises ImportError when whitenoise is unavailable."""
    from dj_serve.middleware import _setup_whitenoise

    with patch.dict("sys.modules", {"whitenoise": None}):
        with pytest.raises(ImportError, match="WhiteNoise is required"):
            _setup_whitenoise(lambda: None, "/tmp/dist")


def test_setup_whitesnout_import_error():
    """_setup_whitesnout raises ImportError when whitesnout is unavailable."""
    from dj_serve.middleware import _setup_whitesnout

    with patch.dict("sys.modules", {"whitesnout": None}):
        with pytest.raises(ImportError, match="WhiteSnout is required"):
            _setup_whitesnout(lambda: None, "/tmp/dist")
