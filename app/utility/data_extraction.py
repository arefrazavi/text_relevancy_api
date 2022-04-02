from pathlib import Path

import kaggle
import requests

from bs4 import BeautifulSoup


def scrape_page(page_url: str) -> str:
    """Get the HTML text content of a page by its URL.

    Args:
        page_url (str): The page URL.

    Returns:
        str: The HTML text content
    """
    response = requests.get(page_url)

    return response.text


def extract_content_from_page(page_url: str) -> str:
    """Get the text content of an HTML page (inside the body tag).

    Args:
        page_url (str): The page URL.

    Returns:
        str:
    """
    soup = BeautifulSoup(scrape_page(page_url), "html.parser")

    # Remove tags whose content is not important for us.
    for tag in soup(["style", "script", "math"]):
        tag.decompose()

    # Strip extra whitespaces from the text.
    return " ".join(soup.stripped_strings)


def download_dataset(dataset_id: str, destination_path: Path) -> None:
    """Download a Kaggle dataset into the destination path.

    Args:
        dataset_id (str): The Kaggle dataset ID.
        destination_path (Path): Path to where the dataset should be stored.
    """
    kaggle.api.dataset_download_files(dataset=dataset_id, path=destination_path, unzip=True)
