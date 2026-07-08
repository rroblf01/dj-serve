__all__ = ["dj_serve", "dj_serve_middleware", "DjServeConfigError"]

import logging
from typing import Callable

from django.conf import settings
from django.urls import re_path
from django.urls.resolvers import URLPattern

from .config import DjServeConfigError, validate_config
from .middleware import dj_serve_middleware
from .views import CacheControl, async_serve_view, serve_view

logger = logging.getLogger(__name__)


def dj_serve(
    prefix: str,
    dist_dir: str,
    entry_point: str = "index.html",
    error_400: str | None = None,
    error_500: str | None = None,
    cache_control: CacheControl = None,
    async_mode: bool = False,
) -> URLPattern:
    """Configure serve serving for Django.

    Args:
        prefix: URL prefix for the serve (e.g., "/" or "/app").
        dist_dir: Path to the directory containing static files.
        entry_point: Name of the entry point HTML file (default: "index.html").
        error_400: Optional path to custom 400 error page.
        error_500: Optional path to custom 500 error page.
        cache_control: Optional cache control configuration.
        async_mode: If True, use async view for ASGI servers (default: False).

    Returns:
        URLPattern for Django URL configuration.

    Raises:
        DjServeConfigError: If configuration is invalid.
    """
    logger.debug(f"Configuring dj-serve: prefix={prefix}, dist_dir={dist_dir}")
    validate_config(dist_dir, entry_point, error_400, error_500)

    # Warn if using builtin in production without static middleware
    if not settings.DEBUG and not _has_static_middleware():
        server_type = "asgi.py" if async_mode else "wsgi.py"
        logger.warning(
            f"dj-serve is using the builtin static file server in production. "
            f"For better performance, configure dj_serve_middleware() in your "
            f"{server_type} with the appropriate backend."
        )

    prefix = prefix.rstrip("/")
    regex = rf"^{prefix}/(?P<path>.*)$"
    view: Callable = async_serve_view if async_mode else serve_view
    return re_path(
        regex,
        view,
        kwargs={
            "dist_dir": dist_dir,
            "entry_point": entry_point,
            "error_400_path": error_400,
            "error_500_path": error_500,
            "cache_control": cache_control,
        },
    )


def _has_static_middleware() -> bool:
    """Check if WhiteNoise or WhiteSnout is configured in Django middleware."""
    middleware = getattr(settings, "MIDDLEWARE", [])
    for mw in middleware:
        if "whitenoise" in mw.lower() or "whitesnout" in mw.lower():
            return True
    return False
