import fnmatch
import logging
import mimetypes
from io import BytesIO
from pathlib import Path

from django.http import (
    FileResponse,
    HttpRequest,
    HttpResponseBase,
    HttpResponseNotFound,
)

logger = logging.getLogger(__name__)

CacheControl = str | dict[str, str] | None


def serve_view(
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
        logger.exception("Error serving serve file")
        resp = _error_response(error_500_path, 500, cache_control)
        if resp is not None:
            return resp
        return HttpResponseNotFound("Server Error", status=500)


async def async_serve_view(
    request: HttpRequest,
    path: str,
    dist_dir: str,
    entry_point: str,
    error_400_path: str | None = None,
    error_500_path: str | None = None,
    cache_control: CacheControl = None,
) -> HttpResponseBase:
    try:
        import aiofiles
        import aiofiles.os
    except ImportError as exc:
        raise ImportError(
            "Async mode requires aiofiles. Install it with: pip install dj-serve[async]"
        ) from exc

    try:
        if ".." in path:
            return HttpResponseNotFound("Not Found")

        dist = Path(dist_dir).resolve()

        if not path or path.strip("/") == "":
            target = dist / entry_point
            if not await aiofiles.os.path.exists(target):
                resp = await _async_error_response(error_400_path, 400, cache_control)
                if resp is not None:
                    return resp
                return HttpResponseNotFound("Not Found")
            return await _async_file_response(target, "text/html", cache_control)

        target = (dist / path).resolve()
        if not str(target).startswith(str(dist)):
            return HttpResponseNotFound("Not Found")

        if await aiofiles.os.path.exists(target) and await aiofiles.os.path.isfile(
            target
        ):
            return await _async_file_response(target, cache_control=cache_control)

        entry = dist / entry_point
        if await aiofiles.os.path.exists(entry):
            return await _async_file_response(entry, "text/html", cache_control)

        resp = await _async_error_response(error_400_path, 400, cache_control)
        if resp is not None:
            return resp
        return HttpResponseNotFound("Not Found")
    except Exception:
        logger.exception("Error serving serve file (async)")
        resp = await _async_error_response(error_500_path, 500, cache_control)
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


async def _async_file_response(
    path: Path, forced_type: str | None = None, cache_control: CacheControl = None
) -> FileResponse:
    import aiofiles

    content_type = (
        forced_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    )
    async with aiofiles.open(path, "rb") as f:
        content = await f.read()
    response = FileResponse(BytesIO(content), content_type=content_type)
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


async def _async_error_response(
    error_path: str | None, status: int, cache_control: CacheControl = None
) -> FileResponse | None:
    import aiofiles
    import aiofiles.os

    if error_path and await aiofiles.os.path.exists(error_path):
        async with aiofiles.open(error_path, "rb") as f:
            content = await f.read()
        response = FileResponse(
            BytesIO(content), content_type="text/html", status=status
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
