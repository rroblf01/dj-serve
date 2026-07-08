"""Production static file middleware integration for dj-spa.

This module provides dj_spa_middleware() which wraps a Django application
with WhiteNoise (WSGI) or WhiteSnout (ASGI) for production-grade static
file serving.
"""

import logging
from typing import Any, Callable

logger = logging.getLogger(__name__)


def dj_spa_middleware(
    app: Callable,
    dist_dir: str,
    async_mode: bool = False,
    **kwargs: Any,
) -> Callable:
    """Wrap Django app with production static file middleware.

    This function automatically selects the appropriate backend based on
    async_mode:
    - async_mode=False → WhiteNoise (WSGI)
    - async_mode=True → WhiteSnout (ASGI)

    Args:
        app: Django WSGI or ASGI application to wrap
        dist_dir: Path to the directory containing static files
        async_mode: If True, use WhiteSnout (ASGI); if False, use WhiteNoise (WSGI)
        **kwargs: Additional arguments passed to the backend constructor
                  (e.g., cache_max_age, security_headers, etc.)

    Returns:
        Wrapped application with static file middleware

    Raises:
        ImportError: If the required backend is not installed

    Examples:
        WSGI (gunicorn, waitress, etc.):

            from django.core.wsgi import get_wsgi_application
            from dj_spa import dj_spa_middleware

            application = get_wsgi_application()
            application = dj_spa_middleware(application, "dist/")

        ASGI (uvicorn, daphne, etc.):

            from django.core.asgi import get_asgi_application
            from dj_spa import dj_spa_middleware

            application = get_asgi_application()
            application = dj_spa_middleware(application, "dist/", async_mode=True)

    """
    if async_mode:
        return _setup_whitesnout(app, dist_dir, **kwargs)
    else:
        return _setup_whitenoise(app, dist_dir, **kwargs)


def _setup_whitenoise(app: Callable, dist_dir: str, **kwargs: Any) -> Callable:
    """Setup WhiteNoise middleware for WSGI applications."""
    try:
        from whitenoise import WhiteNoise
    except ImportError as exc:
        raise ImportError(
            "WhiteNoise is required for WSGI static file serving. "
            "Install it with: pip install dj-spa[wsgi]"
        ) from exc

    logger.info(f"Configuring WhiteNoise for WSGI with dist_dir={dist_dir}")

    # WhiteNoise configuration
    # root: directory to serve files from
    # Additional kwargs are passed through (e.g., max_age, autorefresh)
    whitenoise_kwargs = {"root": dist_dir}
    whitenoise_kwargs.update(kwargs)

    return WhiteNoise(app, **whitenoise_kwargs)  # type: ignore


def _setup_whitesnout(app: Callable, dist_dir: str, **kwargs: Any) -> Callable:
    """Setup WhiteSnout middleware for ASGI applications."""
    try:
        from whitesnout import WhiteSnout
    except ImportError as exc:
        raise ImportError(
            "WhiteSnout is required for ASGI static file serving. "
            "Install it with: pip install dj-spa[asgi]"
        ) from exc

    logger.info(f"Configuring WhiteSnout for ASGI with dist_dir={dist_dir}")

    # WhiteSnout configuration
    # directory: directory to serve files from
    # Additional kwargs are passed through (e.g., cache_max_age, security_headers)
    whitesnout_kwargs = {"directory": dist_dir}
    whitesnout_kwargs.update(kwargs)

    return WhiteSnout(app, **whitesnout_kwargs)  # type: ignore
