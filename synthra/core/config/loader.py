"""Discrete source file byte-stream reader."""

from pathlib import Path
from synthra.core.config.exceptions import ConfigurationFileMissing


class ConfigurationLoader:
    """Pure disk reader tracking byte stream location streams."""

    @staticmethod
    def load_bytes(file_path: Path) -> bytes:
        """Reads a physical location path asset and returns raw file contents.

        Args:
            file_path: Absolute or relative Path to the file.

        Returns:
            The raw bytes read from the file.

        Raises:
            ConfigurationFileMissing: If the file does not exist, is unreachable,
                                      or is a directory.
        """
        if not file_path.exists() or file_path.is_dir():
            raise ConfigurationFileMissing(
                f"Configuration file missing or unreachable: {file_path}"
            )
        try:
            return file_path.read_bytes()
        except OSError as err:
            raise ConfigurationFileMissing(
                f"Failed to read file from disk due to OS error: {err}"
            ) from err
