import fnmatch
import mimetypes
from pathlib import Path

from django.http import (
    FileResponse,
    HttpRequest,
    HttpResponseBase,
    HttpResponseNotFound,
)

CacheControl = str | dict[str, str] | None


def spa_view(
    request: HttpRequest,
    path: str,
    dist_dir: str,
    entry_point: str,
    error_400_path: str | None = None,
    error_500_path: str | None = None,
    cache_control: CacheControl = None,
) -> HttpResponseBase:
    try:
        if ".." in path:
            return HttpResponseNotFound("Not Found")

        dist = Path(dist_dir).resolve()

        if not path or path.strip("/") == "":
            target = dist / entry_point
            if not target.exists():
                resp = _error_response(error_400_path, 400, cache_control)
                if resp is not None:
                    return resp
                return HttpResponseNotFound("Not Found")
            return _file_response(target, "text/html", cache_control)

        target = (dist / path).resolve()
        if not str(target).startswith(str(dist)):
            return HttpResponseNotFound("Not Found")

        if target.exists() and target.is_file():
            return _file_response(target, cache_control=cache_control)

        entry = dist / entry_point
        if entry.exists():
            return _file_response(entry, "text/html", cache_control)

        resp = _error_response(error_400_path, 400, cache_control)
        if resp is not None:
            return resp
        return HttpResponseNotFound("Not Found")
    except Exception:
        resp = _error_response(error_500_path, 500, cache_control)
        if resp is not None:
            return resp
        return HttpResponseNotFound("Server Error", status=500)


def _file_response(
    path: Path, forced_type: str | None = None, cache_control: CacheControl = None
) -> FileResponse:
    content_type = (
        forced_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    )
    response = FileResponse(open(path, "rb"), content_type=content_type)
    response["X-Content-Type-Options"] = "nosniff"
    _apply_cache_control(response, cache_control, path.name)
    return response


def _error_response(
    error_path: str | None, status: int, cache_control: CacheControl = None
) -> FileResponse | None:
    if error_path and Path(error_path).exists():
        response = FileResponse(
            open(error_path, "rb"), content_type="text/html", status=status
        )
        response["X-Content-Type-Options"] = "nosniff"
        _apply_cache_control(response, cache_control, Path(error_path).name)
        return response
    return None


def _apply_cache_control(
    response: FileResponse, cache_control: CacheControl, filename: str
) -> None:
    if cache_control is None:
        return
    if isinstance(cache_control, str):
        response["Cache-Control"] = cache_control
        return
    for pattern, value in cache_control.items():
        if fnmatch.fnmatch(filename, pattern):
            response["Cache-Control"] = value
            return
