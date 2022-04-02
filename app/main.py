from dotenv import load_dotenv
from fastapi import FastAPI

from app.data_storage.elastic_database import ElasticDatabase
from app.utility.data_extraction import extract_content_from_page

from app.services.statistics.dynamic_statistics_calculation import DynamicStatisticsCalculation
from app.services.statistics.static_statistics_calculation import StaticStatisticsCalculation

load_dotenv(".env")
app = FastAPI()


@app.get("/tfidf", name="Important Terms")
async def get_term_with_highest_tf_idfs(url: str, limit: int, dynamic: bool = True) -> dict:
    document = extract_content_from_page(url)
    calculation_service = DynamicStatisticsCalculation() if dynamic else StaticStatisticsCalculation()

    return {"terms": calculation_service.get_terms_with_highest_tf_idf(document, limit)}


@app.on_event("shutdown")
async def app_shutdown() -> None:
    """Close Elastic connection when API shuts down."""
    ElasticDatabase.get_client().close()
