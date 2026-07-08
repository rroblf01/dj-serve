import mimetypes
from pathlib import Path

from django.http import FileResponse, HttpRequest, HttpResponse, HttpResponseNotFound


def spa_view(
    request: HttpRequest,
    path: str,
    dist_dir: str,
    entry_point: str,
    error_400_path: str | None = None,
    error_500_path: str | None = None,
) -> HttpResponse:
    try:
        if ".." in path:
            return HttpResponseNotFound("Not Found")

        dist = Path(dist_dir).resolve()

        if not path or path.strip("/") == "":
            target = dist / entry_point
            if not target.exists():
                return _error_response(error_400_path, 400) or HttpResponseNotFound("Not Found")
            return _file_response(target, "text/html")

        target = (dist / path).resolve()
        if not str(target).startswith(str(dist)):
            return HttpResponseNotFound("Not Found")

        if target.exists() and target.is_file():
            return _file_response(target)

        entry = dist / entry_point
        if entry.exists():
            return _file_response(entry, "text/html")

        return _error_response(error_400_path, 400) or HttpResponseNotFound("Not Found")
    except Exception:
        return _error_response(error_500_path, 500) or HttpResponseNotFound("Server Error", status=500)


def _file_response(path: Path, forced_type: str | None = None) -> FileResponse:
    content_type = forced_type or mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return FileResponse(open(path, "rb"), content_type=content_type)


def _error_response(error_path: str | None, status: int) -> FileResponse | None:
    if error_path and Path(error_path).exists():
        return FileResponse(open(error_path, "rb"), content_type="text/html", status=status)
    return None
