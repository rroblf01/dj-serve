import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DjServeConfigError(Exception):
    """Raised when dj-spa configuration is invalid."""


def validate_config(
    dist_dir: str,
    entry_point: str,
    error_400_path: str | None = None,
    error_500_path: str | None = None,
) -> None:
    """Validate dj-spa configuration at startup.

    Args:
        dist_dir: Path to the directory containing static files.
        entry_point: Name of the entry point HTML file (e.g., "index.html").
        error_400_path: Optional path to custom 400 error page.
        error_500_path: Optional path to custom 500 error page.

    Raises:
        DjServeConfigError: If configuration is invalid.
    """
    dist_path = Path(dist_dir)

    if not dist_path.exists():
        raise DjServeConfigError(f"dist_dir does not exist: {dist_dir}")

    if not dist_path.is_dir():
        raise DjServeConfigError(f"dist_dir is not a directory: {dist_dir}")

    entry_path = dist_path / entry_point
    if not entry_path.exists():
        raise DjServeConfigError(
            f"entry_point '{entry_point}' not found in dist_dir: {entry_path}"
        )

    if error_400_path and not Path(error_400_path).exists():
        logger.warning(f"error_400_path does not exist: {error_400_path}")

    if error_500_path and not Path(error_500_path).exists():
        logger.warning(f"error_500_path does not exist: {error_500_path}")
