import os
import shutil
import zipfile
from pathlib import Path
from typing import Optional


def remove_directory_content(directory_path: Path) -> None:
    for content_names in os.listdir(directory_path):
        content_path = directory_path / content_names
        try:
            shutil.rmtree(content_path)
        except OSError:
            os.remove(content_path)


def get_directory_file_paths(directory_path: Path, pattern: str = "**/*.*") -> list:
    return list(directory_path.glob(pattern))


def decompress(
    source_path: Path,
    destination_path: Optional[Path] = None,
    password: Optional[str] = None,
) -> None:
    """Extract the contents of the given zip file into a destination directory.

    Args:
        source_path (Path): Path to the zip file to be extracted.
        destination_path (Optional[Path]): Path to the destination directory in which file contents are to be extracted.
        password (Optional[str]): Password of the given zip file.
    """

    # The zip file will be extracted in destination path, if given, otherwise in its own directory.
    destination_path = destination_path if destination_path else source_path.parent
    encoded_password = password.encode() if password else None
    try:
        with zipfile.ZipFile(source_path, "r") as archive:
            archive.extractall(path=destination_path, pwd=encoded_password)
    except RuntimeError:
        os.system(f"unzip {source_path} -d {destination_path}")
