from unittest.mock import MagicMock, patch

from dj_serve import dj_serve
from dj_serve.views import spa_view


def _content(response):
    return b"".join(response.streaming_content)


def test_serve_existing_file(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("hello world")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/test.txt")
    response = spa_view(
        request, path="test.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"hello world" in _content(response)


def test_serve_root_serves_entry(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/")
    response = spa_view(request, path="", dist_dir=str(dist), entry_point="index.html")
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


def test_spa_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/spa/route")
    response = spa_view(
        request, path="some/spa/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


def test_missing_file_returns_404(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/nonexistent")
    response = spa_view(
        request, path="nonexistent", dist_dir=str(dist), entry_point="nonexistent.html"
    )
    assert response.status_code == 404


def test_path_traversal_rejected(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    (tmp_path / "secrets.txt").write_text("secret")

    request = rf.get("/../secrets.txt")
    response = spa_view(
        request, path="../secrets.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 404


def test_custom_400_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = spa_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="nonexistent.html",
        error_400_path=str(error_400),
    )
    assert response.status_code == 400
    assert b"bad request" in _content(response)


def test_custom_500_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_500 = tmp_path / "500.html"
    error_500.write_text("<html>server error</html>")

    exists_mock = MagicMock()
    exists_mock.side_effect = [Exception("boom"), True]
    with patch("pathlib.Path.exists", exists_mock):
        request = rf.get("/")
        response = spa_view(
            request,
            path="",
            dist_dir=str(dist),
            entry_point="index.html",
            error_500_path=str(error_500),
        )
    assert response.status_code == 500
    assert b"server error" in _content(response)


def test_correct_mimetype(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = spa_view(
        request, path="style.css", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "text/css"


def test_nosniff_header_on_file(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "app.js").write_text("console.log('hi')")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/app.js")
    response = spa_view(
        request, path="app.js", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


def test_nosniff_header_on_spa_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/route")
    response = spa_view(
        request, path="some/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


def test_nosniff_header_on_error_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = spa_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="nonexistent.html",
        error_400_path=str(error_400),
    )
    assert response.status_code == 400
    assert response["X-Content-Type-Options"] == "nosniff"


def test_cache_control_none(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = spa_view(
        request, path="style.css", dist_dir=str(dist), entry_point="index.html"
    )
    assert "Cache-Control" not in response


def test_cache_control_string(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = spa_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="public, max-age=3600",
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = spa_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="public, max-age=3600",
    )
    assert response["Cache-Control"] == "public, max-age=3600"


def test_cache_control_dict(rf, tmp_path):
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
    response = spa_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=31536000, immutable"

    request = rf.get("/script.js")
    response = spa_view(
        request,
        path="script.js",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = spa_view(
        request, path="", dist_dir=str(dist), entry_point="index.html", cache_control=cc
    )
    assert response["Cache-Control"] == "no-cache"


def test_cache_control_on_error_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = spa_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="nonexistent.html",
        error_400_path=str(error_400),
        cache_control={"*.html": "no-cache"},
    )
    assert response.status_code == 400
    assert response["Cache-Control"] == "no-cache"


def test_cache_control_in_dj_serve(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/", str(dist), cache_control="public, max-age=86400")
    assert pattern.default_args["cache_control"] == "public, max-age=86400"


def test_url_pattern_resolves(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/", str(dist))
    match = pattern.resolve("/")
    assert match is not None
    assert match.kwargs["path"] == ""

    match = pattern.resolve("/some/route")
    assert match is not None
    assert match.kwargs["path"] == "some/route"

    match = pattern.resolve("/style.css")
    assert match is not None
    assert match.kwargs["path"] == "style.css"

    match = pattern.resolve("/app/about")
    assert match is not None
    assert match.kwargs["path"] == "app/about"


def test_url_pattern_with_prefix(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/app", str(dist))
    # Should not match root
    match = pattern.resolve("/")
    assert match is None

    match = pattern.resolve("/app/")
    assert match is not None
    assert match.kwargs["path"] == ""

    match = pattern.resolve("/app/some/route")
    assert match is not None
    assert match.kwargs["path"] == "some/route"

    match = pattern.resolve("/app/style.css")
    assert match is not None
    assert match.kwargs["path"] == "style.css"
