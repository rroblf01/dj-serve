import pytest
from unittest.mock import patch

from dj_spa import dj_spa
from dj_spa.views import async_spa_view


def _content(response):
    return b"".join(response.streaming_content)


@pytest.mark.asyncio
async def test_async_serve_existing_file(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("hello world")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/test.txt")
    response = await async_spa_view(
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
    response = await async_spa_view(
        request, path="", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


@pytest.mark.asyncio
async def test_async_spa_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/spa/route")
    response = await async_spa_view(
        request, path="some/spa/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


@pytest.mark.asyncio
async def test_async_missing_file_returns_404(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/nonexistent")
    response = await async_spa_view(
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
    response = await async_spa_view(
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
    response = await async_spa_view(
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
        response = await async_spa_view(
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
    response = await async_spa_view(
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
    response = await async_spa_view(
        request, path="app.js", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


@pytest.mark.asyncio
async def test_async_nosniff_header_on_spa_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/route")
    response = await async_spa_view(
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
    response = await async_spa_view(
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
    response = await async_spa_view(
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
    response = await async_spa_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="public, max-age=3600",
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = await async_spa_view(
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
    response = await async_spa_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=31536000, immutable"

    request = rf.get("/script.js")
    response = await async_spa_view(
        request,
        path="script.js",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = await async_spa_view(
        request, path="", dist_dir=str(dist), entry_point="index.html", cache_control=cc
    )
    assert response["Cache-Control"] == "no-cache"


def test_async_mode_in_dj_spa(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_spa("/", str(dist), async_mode=True)
    assert getattr(pattern.callback, "__name__", None) == "async_spa_view"


def test_sync_mode_in_dj_spa(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_spa("/", str(dist), async_mode=False)
    assert getattr(pattern.callback, "__name__", None) == "spa_view"


def test_default_mode_is_sync(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_spa("/", str(dist))
    assert getattr(pattern.callback, "__name__", None) == "spa_view"
