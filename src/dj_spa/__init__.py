__all__ = ["dj_spa"]

from django.urls import re_path
from django.urls.resolvers import URLPattern

from .views import CacheControl, spa_view


def dj_spa(
    prefix: str,
    dist_dir: str,
    entry_point: str = "index.html",
    error_400: str | None = None,
    error_500: str | None = None,
    cache_control: CacheControl = None,
) -> URLPattern:
    prefix = prefix.rstrip("/")
    regex = rf"^{prefix}/(?P<path>.*)$"
    return re_path(
        regex,
        spa_view,
        kwargs={
            "dist_dir": dist_dir,
            "entry_point": entry_point,
            "error_400_path": error_400,
            "error_500_path": error_500,
            "cache_control": cache_control,
        },
    )
