__all__ = ["dj_spa", "DjSpaConfigError"]

import logging
from typing import Callable

from django.urls import re_path
from django.urls.resolvers import URLPattern

from .config import DjSpaConfigError, validate_config
from .views import CacheControl, async_spa_view, spa_view

logger = logging.getLogger(__name__)


def dj_spa(
    prefix: str,
    dist_dir: str,
    entry_point: str = "index.html",
    error_400: str | None = None,
    error_500: str | None = None,
    cache_control: CacheControl = None,
    async_mode: bool = False,
) -> URLPattern:
    """Configure SPA serving for Django.

    Args:
        prefix: URL prefix for the SPA (e.g., "/" or "/app").
        dist_dir: Path to the directory containing static files.
        entry_point: Name of the entry point HTML file (default: "index.html").
        error_400: Optional path to custom 400 error page.
        error_500: Optional path to custom 500 error page.
        cache_control: Optional cache control configuration.
        async_mode: If True, use async view for ASGI servers (default: False).

    Returns:
        URLPattern for Django URL configuration.

    Raises:
        DjSpaConfigError: If configuration is invalid.
    """
    logger.debug(f"Configuring dj-spa: prefix={prefix}, dist_dir={dist_dir}")
    validate_config(dist_dir, entry_point, error_400, error_500)

    prefix = prefix.rstrip("/")
    regex = rf"^{prefix}/(?P<path>.*)$"
    view: Callable = async_spa_view if async_mode else spa_view
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
