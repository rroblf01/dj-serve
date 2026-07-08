import pytest
from dj_spa import DjSpaConfigError, dj_spa


def test_validate_config_dist_dir_not_exists(tmp_path):
    """Test that DjSpaConfigError is raised when dist_dir doesn't exist."""
    with pytest.raises(DjSpaConfigError, match="dist_dir does not exist"):
        dj_spa("/", str(tmp_path / "nonexistent"))


def test_validate_config_dist_dir_not_directory(tmp_path):
    """Test that DjSpaConfigError is raised when dist_dir is not a directory."""
    file_path = tmp_path / "file.txt"
    file_path.write_text("content")

    with pytest.raises(DjSpaConfigError, match="dist_dir is not a directory"):
        dj_spa("/", str(file_path))


def test_validate_config_entry_point_not_exists(tmp_path):
    """Test that DjSpaConfigError is raised when entry_point doesn't exist."""
    dist = tmp_path / "dist"
    dist.mkdir()

    with pytest.raises(DjSpaConfigError, match="entry_point.*not found"):
        dj_spa("/", str(dist), entry_point="nonexistent.html")


def test_validate_config_error_400_not_exists(tmp_path, caplog):
    """Test that warning is logged when error_400_path doesn't exist."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    with caplog.at_level("WARNING"):
        dj_spa("/", str(dist), error_400=str(tmp_path / "400.html"))

    assert "error_400_path does not exist" in caplog.text


def test_validate_config_error_500_not_exists(tmp_path, caplog):
    """Test that warning is logged when error_500_path doesn't exist."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")

    with caplog.at_level("WARNING"):
        dj_spa("/", str(dist), error_500=str(tmp_path / "500.html"))

    assert "error_500_path does not exist" in caplog.text


def test_validate_config_success(tmp_path):
    """Test that valid configuration doesn't raise any errors."""
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>index</html>")
    (dist / "400.html").write_text("<html>400</html>")
    (dist / "500.html").write_text("<html>500</html>")

    # Should not raise any exceptions
    dj_spa(
        "/",
        str(dist),
        entry_point="index.html",
        error_400=str(dist / "400.html"),
        error_500=str(dist / "500.html"),
    )
