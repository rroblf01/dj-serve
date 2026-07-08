"""Unit tests for dj_spa_middleware()."""

import pytest
from unittest.mock import MagicMock, patch

from dj_spa import dj_spa_middleware


def test_middleware_wsgi_mode():
    """Test that async_mode=False uses WhiteNoise."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_spa.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        result = dj_spa_middleware(app, dist_dir, async_mode=False)

        mock_setup.assert_called_once_with(app, dist_dir)
        assert result == mock_setup.return_value


def test_middleware_asgi_mode():
    """Test that async_mode=True uses WhiteSnout."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_spa.middleware._setup_whitesnout") as mock_setup:
        mock_setup.return_value = MagicMock()
        result = dj_spa_middleware(app, dist_dir, async_mode=True)

        mock_setup.assert_called_once_with(app, dist_dir)
        assert result == mock_setup.return_value


def test_middleware_default_is_wsgi():
    """Test that default (no async_mode) uses WhiteNoise."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_spa.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        result = dj_spa_middleware(app, dist_dir)

        mock_setup.assert_called_once_with(app, dist_dir)
        assert result == mock_setup.return_value


def test_middleware_passes_kwargs():
    """Test that kwargs are passed to the backend."""
    app = MagicMock()
    dist_dir = "/tmp/dist"
    kwargs = {"cache_max_age": 3600, "security_headers": True}

    with patch("dj_spa.middleware._setup_whitenoise") as mock_setup:
        mock_setup.return_value = MagicMock()
        dj_spa_middleware(app, dist_dir, async_mode=False, **kwargs)

        mock_setup.assert_called_once_with(app, dist_dir, **kwargs)


def test_middleware_wsgi_missing_whitenoise():
    """Test that ImportError is raised when WhiteNoise is not installed."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_spa.middleware._setup_whitenoise") as mock_setup:
        mock_setup.side_effect = ImportError("WhiteNoise not installed")

        with pytest.raises(ImportError, match="WhiteNoise not installed"):
            dj_spa_middleware(app, dist_dir, async_mode=False)


def test_middleware_asgi_missing_whitesnout():
    """Test that ImportError is raised when WhiteSnout is not installed."""
    app = MagicMock()
    dist_dir = "/tmp/dist"

    with patch("dj_spa.middleware._setup_whitesnout") as mock_setup:
        mock_setup.side_effect = ImportError("WhiteSnout not installed")

        with pytest.raises(ImportError, match="WhiteSnout not installed"):
            dj_spa_middleware(app, dist_dir, async_mode=True)


def test_setup_whitenoise_with_real_library(tmp_path):
    """Test that _setup_whitenoise works with real WhiteNoise library."""
    from dj_spa.middleware import _setup_whitenoise
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


def test_setup_whitesnout_with_real_library(tmp_path):
    """Test that _setup_whitesnout works with real WhiteSnout library."""
    from dj_spa.middleware import _setup_whitesnout
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
