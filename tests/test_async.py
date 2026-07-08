import builtins
import pytest
from unittest.mock import MagicMock, patch

from dj_serve import dj_serve
from dj_serve.views import async_serve_view


def _content(response):
    return b"".join(response.streaming_content)


@pytest.mark.asyncio
async def test_async_serve_existing_file(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("hello world")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/test.txt")
    response = await async_serve_view(
        request, path="test.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"hello world" in _content(response)


@pytest.mark.asyncio
async def test_async_serve_root_serves_entry(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/")
    response = await async_serve_view(
        request, path="", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


@pytest.mark.asyncio
async def test_async_serve_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/serve/route")
    response = await async_serve_view(
        request, path="some/serve/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


@pytest.mark.asyncio
async def test_async_missing_file_returns_404(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/nonexistent")
    response = await async_serve_view(
        request, path="nonexistent", dist_dir=str(dist), entry_point="nonexistent.html"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_async_path_traversal_rejected(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    (tmp_path / "secrets.txt").write_text("secret")

    request = rf.get("/../secrets.txt")
    response = await async_serve_view(
        request, path="../secrets.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_async_custom_400_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = await async_serve_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="nonexistent.html",
        error_400_path=str(error_400),
    )
    assert response.status_code == 400
    assert b"bad request" in _content(response)


@pytest.mark.asyncio
async def test_async_custom_500_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_500 = tmp_path / "500.html"
    error_500.write_text("<html>server error</html>")

    call_count = [0]

    async def mock_exists(path):
        call_count[0] += 1
        if call_count[0] == 1:
            raise Exception("boom")
        return True

    with patch("aiofiles.os.path.exists", mock_exists):
        request = rf.get("/")
        response = await async_serve_view(
            request,
            path="",
            dist_dir=str(dist),
            entry_point="index.html",
            error_500_path=str(error_500),
        )
    assert response.status_code == 500
    assert b"server error" in _content(response)


@pytest.mark.asyncio
async def test_async_correct_mimetype(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = await async_serve_view(
        request, path="style.css", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "text/css"


@pytest.mark.asyncio
async def test_async_nosniff_header_on_file(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "app.js").write_text("console.log('hi')")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/app.js")
    response = await async_serve_view(
        request, path="app.js", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_async_nosniff_header_on_serve_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/route")
    response = await async_serve_view(
        request, path="some/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_async_nosniff_header_on_error_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = await async_serve_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="nonexistent.html",
        error_400_path=str(error_400),
    )
    assert response.status_code == 400
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_async_cache_control_none(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = await async_serve_view(
        request, path="style.css", dist_dir=str(dist), entry_point="index.html"
    )
    assert "Cache-Control" not in response


@pytest.mark.asyncio
async def test_async_cache_control_string(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = await async_serve_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="public, max-age=3600",
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = await async_serve_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="public, max-age=3600",
    )
    assert response["Cache-Control"] == "public, max-age=3600"


@pytest.mark.asyncio
async def test_async_cache_control_dict(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "script.js").write_text("console.log('hi')")
    (dist / "app.html").write_text("<html>app</html>")
    (dist / "index.html").write_text("<html>index</html>")

    cc = {
        "*.html": "no-cache",
        "*.css": "public, max-age=31536000, immutable",
        "*": "public, max-age=3600",
    }

    request = rf.get("/style.css")
    response = await async_serve_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=31536000, immutable"

    request = rf.get("/script.js")
    response = await async_serve_view(
        request,
        path="script.js",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = await async_serve_view(
        request, path="", dist_dir=str(dist), entry_point="index.html", cache_control=cc
    )
    assert response["Cache-Control"] == "no-cache"


def test_async_mode_in_dj_serve(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/", str(dist), async_mode=True)
    assert getattr(pattern.callback, "__name__", None) == "async_serve_view"


def test_sync_mode_in_dj_serve(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/", str(dist), async_mode=False)
    assert getattr(pattern.callback, "__name__", None) == "serve_view"


def test_default_mode_is_sync(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/", str(dist))
    assert getattr(pattern.callback, "__name__", None) == "serve_view"


@pytest.mark.asyncio
async def test_async_500_without_custom_page(rf, tmp_path):
    """Exception in async view without error_500_path returns 500."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    exists_mock = MagicMock()
    exists_mock.side_effect = Exception("boom")
    with patch("aiofiles.os.path.exists", exists_mock):
        request = rf.get("/")
        response = await async_serve_view(
            request, path="", dist_dir=str(dist), entry_point="index.html"
        )
    assert response.status_code == 500
    assert b"Server Error" in response.content


@pytest.mark.asyncio
async def test_async_unknown_mime_type_fallback(rf, tmp_path):
    """Async: unknown extension gets application/octet-stream."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "data.zzz").write_text("binary content")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/data.zzz")
    response = await async_serve_view(
        request, path="data.zzz", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_async_missing_aiofiles(rf, tmp_path):
    """async_serve_view raises ImportError when aiofiles is missing."""
    original_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "aiofiles":
            raise ImportError(f"No module named {name}")
        return original_import(name, *args, **kwargs)

    with patch("builtins.__import__", mock_import):
        with pytest.raises(ImportError, match="aiofiles"):
            await async_serve_view(
                rf.get("/"), path="", dist_dir="/tmp", entry_point="index.html"
            )


@pytest.mark.asyncio
async def test_async_empty_string_error_400_path(rf, tmp_path):
    """Async: empty string error_400_path is ignored."""
    dist = tmp_path / "dist"
    dist.mkdir()

    request = rf.get("/")
    response = await async_serve_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="index.html",
        error_400_path="",
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_async_cache_control_on_error_page(rf, tmp_path):
    """Async: Cache-Control applied to error response."""
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = await async_serve_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="nonexistent.html",
        error_400_path=str(error_400),
        cache_control={"*.html": "no-cache"},
    )
    assert response.status_code == 400
    assert response["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_async_cache_control_on_fallback(rf, tmp_path):
    """Async: Cache-Control applied to SPA fallback."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/route")
    response = await async_serve_view(
        request,
        path="some/route",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="no-cache",
    )
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-cache"


@pytest.mark.asyncio
async def test_async_cache_control_dict_no_match(rf, tmp_path):
    """Async: Cache-Control dict with no matching pattern omits header."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "app.js").write_text("console.log('hi')")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/app.js")
    response = await async_serve_view(
        request,
        path="app.js",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control={"*.css": "max-age=3600"},
    )
    assert response.status_code == 200
    assert "Cache-Control" not in response


@pytest.mark.asyncio
async def test_async_empty_file(rf, tmp_path):
    """Async: Zero-byte file is served successfully."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "empty.txt").write_text("")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/empty.txt")
    response = await async_serve_view(
        request, path="empty.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"


@pytest.mark.asyncio
async def test_async_path_traversal_via_symlink(rf, tmp_path):
    """Async: symlink pointing outside dist_dir is rejected."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    outside = tmp_path / "secrets.txt"
    outside.write_text("secret data")
    link = dist / "evil_link.txt"
    link.symlink_to(outside)

    request = rf.get("/evil_link.txt")
    response = await async_serve_view(
        request, path="evil_link.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_async_non_root_entry_missing_with_error_400(rf, tmp_path):
    """Async: non-root path with no entry_point and custom 400 returns 400."""
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>custom 400</html>")

    request = rf.get("/nonexistent")
    response = await async_serve_view(
        request,
        path="nonexistent",
        dist_dir=str(dist),
        entry_point="index.html",
        error_400_path=str(error_400),
    )
    assert response.status_code == 400
    body = b"".join(response.streaming_content)
    assert b"custom 400" in body


@pytest.mark.asyncio
async def test_async_extensionless_file_mime(rf, tmp_path):
    """Async: files without extension get application/octet-stream."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "Makefile").write_text("all:\n\techo hello")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/Makefile")
    response = await async_serve_view(
        request, path="Makefile", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "application/octet-stream"
