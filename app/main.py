from typing import List, Dict, Any

from dotenv import load_dotenv
from fastapi import FastAPI

from app.utility.data_extraction import extract_content_from_page

from app.services.statistics.dynamic_statistics_calculation import DynamicStatisticsCalculation
from app.services.statistics.static_statistics_calculation import StaticStatisticsCalculation

load_dotenv(".env")
app = FastAPI()


@app.get("/tfidf", name="important_terms")
def get_terms_with_highest_tf_idf(url: str, limit: int, dynamic: bool = False) -> Dict[str, List[Dict[str, Any]]]:
    """Find terms in the content of the given page URL with highest TF-IDF.

    Args:
        url (str): URL of the page whose content are to be analyzed.
        limit (int): Maximum number of terms to be returned.
        dynamic (bool): Whether to use dynamic calculation (True) or static calculation (True). Defaults to True.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A collection of terms and their TF-IDFs sorted by descending order of TF-IDFs.
    """
    article_content = extract_content_from_page(url)
    calculation_service = DynamicStatisticsCalculation() if dynamic else StaticStatisticsCalculation()

    return {"terms": calculation_service.get_terms_with_highest_tf_idf(article_content, limit)}


@app.get("/page_content", name="page_content")
def get_page_content(url: str) -> Dict[str, str]:
    """Extract content of the page with the given URL.

    Args:
        url (str): URL of the page whose content are to be extracted.

    Returns:
        Dict[str, str]:
    """
    return {"page_content": extract_content_from_page(url)}


# @app.on_event("shutdown")
# def app_shutdown() -> None:
#     """Close Elastic connection when API shuts down."""
#     ElasticDatabase.get_client().close()
