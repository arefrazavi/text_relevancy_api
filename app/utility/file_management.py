import os
import shutil
from pathlib import Path


def remove_directory_content(directory_path: Path) -> None:
    for content_names in os.listdir(directory_path):
        content_path = directory_path / content_names
        try:
            shutil.rmtree(content_path)
        except OSError:
            os.remove(content_path)


def get_directory_file_paths(directory_path: Path, pattern: str = "**/*.*") -> list:
    return list(directory_path.glob(pattern))
