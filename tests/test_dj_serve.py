from unittest.mock import MagicMock, patch

from dj_serve import dj_serve
from dj_serve.views import serve_view


def _content(response):
    return b"".join(response.streaming_content)


def test_serve_existing_file(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("hello world")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/test.txt")
    response = serve_view(
        request, path="test.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"hello world" in _content(response)


def test_serve_root_serves_entry(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/")
    response = serve_view(
        request, path="", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


def test_serve_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/serve/route")
    response = serve_view(
        request, path="some/serve/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"<html>index</html>" in _content(response)


def test_missing_file_returns_404(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/nonexistent")
    response = serve_view(
        request, path="nonexistent", dist_dir=str(dist), entry_point="nonexistent.html"
    )
    assert response.status_code == 404


def test_path_traversal_rejected(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    (tmp_path / "secrets.txt").write_text("secret")

    request = rf.get("/../secrets.txt")
    response = serve_view(
        request, path="../secrets.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 404


def test_custom_400_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = serve_view(
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
        response = serve_view(
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
    response = serve_view(
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
    response = serve_view(
        request, path="app.js", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


def test_nosniff_header_on_serve_fallback(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/route")
    response = serve_view(
        request, path="some/route", dist_dir=str(dist), entry_point="index.html"
    )
    assert response["X-Content-Type-Options"] == "nosniff"


def test_nosniff_header_on_error_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = serve_view(
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
    response = serve_view(
        request, path="style.css", dist_dir=str(dist), entry_point="index.html"
    )
    assert "Cache-Control" not in response


def test_cache_control_string(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = serve_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="public, max-age=3600",
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = serve_view(
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
    response = serve_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=31536000, immutable"

    request = rf.get("/script.js")
    response = serve_view(
        request,
        path="script.js",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response["Cache-Control"] == "public, max-age=3600"

    request = rf.get("/")
    response = serve_view(
        request, path="", dist_dir=str(dist), entry_point="index.html", cache_control=cc
    )
    assert response["Cache-Control"] == "no-cache"


def test_cache_control_on_error_page(rf, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>bad request</html>")

    request = rf.get("/")
    response = serve_view(
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
    assert match.kwargs["path"] == "/"

    match = pattern.resolve("/some/route")
    assert match is not None
    assert match.kwargs["path"] == "/some/route"

    match = pattern.resolve("/style.css")
    assert match is not None
    assert match.kwargs["path"] == "/style.css"

    match = pattern.resolve("/app/about")
    assert match is not None
    assert match.kwargs["path"] == "/app/about"


def test_url_pattern_with_prefix(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("/app", str(dist))
    # Should not match root
    match = pattern.resolve("/")
    assert match is None

    match = pattern.resolve("app/")
    assert match is not None
    assert match.kwargs["path"] == ""

    match = pattern.resolve("app/some/route")
    assert match is not None
    assert match.kwargs["path"] == "some/route"

    match = pattern.resolve("app/style.css")
    assert match is not None
    assert match.kwargs["path"] == "style.css"


def test_path_traversal_via_symlink(rf, tmp_path):
    """Symlink pointing outside dist_dir is rejected."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    outside = tmp_path / "secrets.txt"
    outside.write_text("secret data")
    link = dist / "evil_link.txt"
    link.symlink_to(outside)

    request = rf.get("/evil_link.txt")
    response = serve_view(
        request, path="evil_link.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 404


def test_path_traversal_variants(rf, tmp_path):
    """Multiple path traversal variants are all rejected."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    (tmp_path / "secrets.txt").write_text("secret")

    variants = [
        "....//....//secrets.txt",
        "../secrets.txt",
        "../../../etc/passwd",
        "foo/../../secrets.txt",
    ]
    for path in variants:
        request = rf.get(f"/{path}")
        response = serve_view(
            request, path=path, dist_dir=str(dist), entry_point="index.html"
        )
        assert response.status_code == 404, f"Traversal not blocked: {path}"


def test_500_without_custom_page(rf, tmp_path):
    """Exception inside serve_view returns 500 Server Error."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    exists_mock = MagicMock()
    exists_mock.side_effect = Exception("boom")
    with patch("pathlib.Path.exists", exists_mock):
        request = rf.get("/")
        response = serve_view(
            request, path="", dist_dir=str(dist), entry_point="index.html"
        )
    assert response.status_code == 500
    assert b"Server Error" in response.content


def test_unknown_mime_type_fallback(rf, tmp_path):
    """Files with unknown extension get application/octet-stream."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "data.zzz").write_text("binary content")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/data.zzz")
    response = serve_view(
        request, path="data.zzz", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "application/octet-stream"


def test_cache_control_dict_no_match(rf, tmp_path):
    """Cache-Control dict with no matching pattern omits the header."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "app.js").write_text("console.log('hi')")
    (dist / "index.html").write_text("<html>index</html>")

    cc = {"*.css": "max-age=3600"}
    request = rf.get("/app.js")
    response = serve_view(
        request,
        path="app.js",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control=cc,
    )
    assert response.status_code == 200
    assert "Cache-Control" not in response


def test_head_request(rf, tmp_path):
    """HEAD requests return 200."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "test.txt").write_text("hello world")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.head("/test.txt")
    response = serve_view(
        request, path="test.txt", dist_dir=str(dist), entry_point="index.html"
    )
    # FileResponse returns 200 for HEAD; body stripping happens at WSGI level
    assert response.status_code == 200


def test_range_request_headers(rf, tmp_path):
    """Range request headers are passed through correctly."""
    dist = tmp_path / "dist"
    dist.mkdir()
    content = "x" * 100
    (dist / "data.txt").write_text(content)
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/data.txt", HTTP_RANGE="bytes=0-9")
    response = serve_view(
        request, path="data.txt", dist_dir=str(dist), entry_point="index.html"
    )
    # FileResponse handles Range at WSGI iteration level, so status is 200 here
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"


def test_directory_index(rf, tmp_path):
    """Requesting a directory path falls back to entry_point."""
    dist = tmp_path / "dist"
    dist.mkdir()
    subdir = dist / "subdir"
    subdir.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/subdir")
    response = serve_view(
        request, path="subdir", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert b"index" in _content(response)


def test_unicode_filename(rf, tmp_path):
    """Files with unicode and special characters are served correctly."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "café.json").write_text('{"name": "café"}')
    (dist / "file with spaces.js").write_text("console.log('hi')")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/café.json")
    response = serve_view(
        request, path="café.json", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert "café".encode("utf-8") in _content(response)
    assert response["Content-Type"] == "application/json"

    request = rf.get("/file with spaces.js")
    response = serve_view(
        request,
        path="file with spaces.js",
        dist_dir=str(dist),
        entry_point="index.html",
    )
    assert response.status_code == 200
    assert b"console.log" in _content(response)


def test_multiple_dj_serve_calls(tmp_path):
    """Multiple dj_serve() calls with different prefixes work."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    p1 = dj_serve("/", str(dist))
    p2 = dj_serve("/app", str(dist))
    p3 = dj_serve("/admin", str(dist))

    assert p1.resolve("/") is not None
    assert p2.resolve("app/") is not None
    assert p3.resolve("admin/") is not None
    # No cross-contamination
    assert p2.resolve("/") is None
    assert p3.resolve("/") is None


def test_cache_control_on_fallback_path(rf, tmp_path):
    """Cache-Control string applied on SPA fallback response."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/some/route")
    response = serve_view(
        request,
        path="some/route",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control="no-cache",
    )
    assert response.status_code == 200
    assert response["Cache-Control"] == "no-cache"


def test_empty_prefix(tmp_path):
    """Empty prefix matches everything."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("", str(dist))
    assert pattern.resolve("/") is not None
    assert pattern.resolve("/any/path") is not None


def test_empty_prefix_resolves(tmp_path):
    """Empty prefix regex works with Django 6.0+ URL resolution."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    pattern = dj_serve("", str(dist))
    match = pattern.resolve("/")
    assert match is not None
    # With Django 6.0, root resolver strips /, so path will be /
    assert match.kwargs["path"] == "/"


def test_prefix_trailing_slash(tmp_path):
    """Prefix with trailing slash behaves same as without."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    p1 = dj_serve("/app", str(dist))
    p2 = dj_serve("/app/", str(dist))
    # Both should produce the same regex
    assert p1.pattern.regex.pattern == p2.pattern.regex.pattern


def test_extensionless_file_mime(rf, tmp_path):
    """Files without extension get application/octet-stream."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "Makefile").write_text("all:\n\techo hello")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/Makefile")
    response = serve_view(
        request, path="Makefile", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "application/octet-stream"


def test_empty_file(rf, tmp_path):
    """Zero-byte file is served successfully."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "empty.txt").write_text("")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/empty.txt")
    response = serve_view(
        request, path="empty.txt", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain"
    body = b"".join(response.streaming_content)
    assert len(body) == 0


def test_cache_control_empty_dict(rf, tmp_path):
    """Empty dict cache_control adds no header."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "style.css").write_text("body { color: red; }")
    (dist / "index.html").write_text("<html>index</html>")

    request = rf.get("/style.css")
    response = serve_view(
        request,
        path="style.css",
        dist_dir=str(dist),
        entry_point="index.html",
        cache_control={},
    )
    assert response.status_code == 200
    assert "Cache-Control" not in response


def test_root_no_entry_no_error_page(rf, tmp_path):
    """Root path with missing entry_point and no error page returns 404."""
    dist = tmp_path / "dist"
    dist.mkdir()

    request = rf.get("/")
    response = serve_view(
        request, path="", dist_dir=str(dist), entry_point="index.html"
    )
    assert response.status_code == 404
    assert b"Not Found" in response.content


def test_empty_string_error_400_path(rf, tmp_path):
    """Empty string error_400_path is ignored, returns plain 404."""
    dist = tmp_path / "dist"
    dist.mkdir()

    request = rf.get("/")
    response = serve_view(
        request,
        path="",
        dist_dir=str(dist),
        entry_point="index.html",
        error_400_path="",
    )
    assert response.status_code == 404


def test_django_5_compatible_regex():
    """Django < 6.0 regex branch produces leading / in pattern."""
    from dj_serve.__init__ import _build_regex

    assert _build_regex("/", (5, 1, 0, "final", 0)) == r"^/(?P<path>.*)$"
    assert _build_regex("/app", (5, 1, 0, "final", 0)) == r"^/app/(?P<path>.*)$"


def test_django_6_regex_leading_slash_stripped():
    """Django >= 6.0 regex branch strips leading / from prefix."""
    from dj_serve.__init__ import _build_regex

    assert _build_regex("/", (6, 0, 0, "final", 0)) == r"^(?P<path>.*)$"
    assert _build_regex("/app", (6, 0, 0, "final", 0)) == r"^app/(?P<path>.*)$"


def test_build_regex_empty_prefix():
    """Empty prefix produces correct regex for both Django versions."""
    from dj_serve.__init__ import _build_regex

    assert _build_regex("", (5, 1, 0, "final", 0)) == r"^/(?P<path>.*)$"
    assert _build_regex("", (6, 0, 0, "final", 0)) == r"^(?P<path>.*)$"


def test_build_regex_trailing_slash_prefix():
    """Trailing slash on prefix is handled the same for both versions."""
    from dj_serve.__init__ import _build_regex

    assert _build_regex("/app/", (5, 1, 0, "final", 0)) == r"^/app/(?P<path>.*)$"
    assert _build_regex("/app/", (6, 0, 0, "final", 0)) == r"^app/(?P<path>.*)$"


def test_non_root_entry_missing_with_error_400(rf, tmp_path):
    """Non-root path with no entry_point and custom 400 page returns 400."""
    dist = tmp_path / "dist"
    dist.mkdir()
    error_400 = tmp_path / "400.html"
    error_400.write_text("<html>custom 400</html>")

    request = rf.get("/nonexistent")
    response = serve_view(
        request,
        path="nonexistent",
        dist_dir=str(dist),
        entry_point="index.html",
        error_400_path=str(error_400),
    )
    assert response.status_code == 400
    assert b"custom 400" in _content(response)
