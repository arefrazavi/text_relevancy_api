from __future__ import annotations

import os
from typing import Dict, Any

import pandas as pd
from pathlib import Path
from tqdm import tqdm

from app.repositories.article_repository import ArticleRepository
from app.services.statistics.static_statistics_calculation import StaticStatisticsCalculation
from app.utility.data_extraction import download_dataset
from app.utility.file_management import remove_directory_content, get_directory_file_paths


class ArticleETL:
    """Performing ETL process on article data."""

    def __init__(self: ArticleETL, reset_data: bool = False, reset_statistics: bool = False) -> None:
        """
        Args:
            reset_data (bool): Whether to reset data in our data storage platforms (e.g. Elastic database and local data lake)
            reset_statistics (bool): Whether to redo article related statistics.
        """
        self._article_repository = ArticleRepository()

        self.config = {
            "reset_data": reset_data,
            "reset_statistics": reset_statistics,
            "source_dataset_id": os.getenv("SOURCE_DATASET_ID"),
        }

    @property
    def article_repository(self: ArticleETL) -> ArticleRepository:
        """The repository to access article data."""
        return self._article_repository

    @property
    def config(self: ArticleETL) -> Dict[str, Any]:
        """Required configuration for ETL process."""
        return self._config

    @config.setter
    def config(self: ArticleETL, config: Dict[str, Any]) -> None:
        self._validate_config(config)
        self._config = config

    def run(self: ArticleETL) -> None:
        print("\nExtracting articles...")
        self._extract_articles(self.config["source_dataset_id"])

        print("\nPreparing statistics...")
        self._prepare_statistics()

        print("\nLoading articles to Elastic database...")
        self._load_articles_to_database()

        print("\nELT process is complete.")

    def _validate_config(self: ArticleETL, config: Dict[str, Any]) -> None:
        """Validate if the config contains all the required parameters."""
        if not config.get("source_dataset_id"):
            raise ArticleETLError("Source dataset ID is not given.")

    def _extract_articles(self: ArticleETL, source_dataset_id: str) -> None:
        """Extract the initial corpus of articles and store it in our data lake.

        Args:
            source_dataset_id (str): The source (Kaggle) ID for the dataset.
        """
        destination_path = Path(f"{self.article_repository.data_lake_path}/{self.article_repository.corpus_bucket}")

        if self.config["reset_data"]:
            remove_directory_content(destination_path)

        # Skip downloading dataset if it already exits in data lake.
        if not get_directory_file_paths(destination_path):
            download_dataset(source_dataset_id, destination_path)

    def _prepare_statistics(self: ArticleETL) -> None:
        """Calculate article related statistics and store it in our data lake as static calculation."""
        term_statistics_path = Path(
            f"{self.article_repository.data_lake_path}/{self.article_repository.term_statistics_key}"
        )

        if not self.config["reset_statistics"] and term_statistics_path.exists():
            return

        print("Calculating static term statistics...")
        statistics_calculation = StaticStatisticsCalculation()
        term_dfs = statistics_calculation.calculate_all_term_dfs()

        print("Loading static term statistics to data lake...")
        pd.DataFrame(
            {
                "term": term_dfs.keys(),
                "df": term_dfs.values(),
            }
        ).to_parquet(term_statistics_path)

    def _load_articles_to_database(self: ArticleETL) -> None:
        """Create an Elastic index and insert all the corpus articles into it."""
        if not self.config["reset_data"] and self.article_repository.article_index_exists():
            return

        articles = self.article_repository.get_static_articles().fillna("")
        article_count = self.article_repository.get_static_article_count()

        self.article_repository.create_index(True)

        progress_bar = tqdm(total=article_count)
        progress_bar.set_description(f"    Inserting {article_count} articles into Elastic database:")
        for articles_batch in articles.partitions:
            self.article_repository.insert_articles(articles_batch.compute())


class ArticleETLError(Exception):
    """Raise when an error in processing article data occurs."""

    def __init__(self: ArticleETLError, error_message: str) -> None:
        super(ArticleETLError, self).__init__(error_message)
