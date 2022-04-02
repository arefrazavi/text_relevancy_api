from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Final, Dict, Any, List

import numpy as np
import pandas as pd

from app.repositories.article_repository import ArticleRepository


class StatisticsCalculation(ABC):
    """An abstract base class for providing text related statistics."""

    TF_IDF_DECIMAL_PLACE_COUNT: Final[int] = 1
    IDF_DECIMAL_PLACE_COUNT: Final[int] = 5

    def __init__(self: StatisticsCalculation) -> None:
        self._article_repository = ArticleRepository()

    @property
    def article_repository(self: StatisticsCalculation) -> ArticleRepository:
        return self._article_repository

    def get_terms_with_highest_tf_idf(self: StatisticsCalculation, content: str, limit: int) -> List[Dict[str, Any]]:
        """Find terms in the given content with highest TF-IDF.

        Args:
            content (str): The content in which terms are to be analyzed.
            limit (int): Maximum number of terms to be returned.

        Returns:
            List[Dict[str, Any]]: A collection of terms and their TF-IDFs sorted by descending order of TF-IDFs.
        """
        term_tf_idfs = self.calculate_term_tf_idfs(content)

        return (
            term_tf_idfs.sort_values(by="tf-idf", ascending=False)
            .head(limit)
            .reset_index()
            .rename(columns={"index": "term"})
            .to_dict(orient="records")
        )

    def calculate_term_idfs(self: StatisticsCalculation, article_count: int, term_df: pd.Series) -> pd.Series:
        """Calculate IDF (inverse document frequency) of the given terms.

        Args:
            article_count (int): Number of articles (documents) in the dataset, i.e., `n` in IDF formula
            term_df: a collection of DFs (document frequencies) for the given terms.

        Returns:
            pd.Series: A collection of IDFs for the given terms.
        """
        return round(np.log((article_count + 1) / (term_df + 1)) + 1, self.IDF_DECIMAL_PLACE_COUNT)

    @abstractmethod
    def calculate_term_tf_idfs(self: StatisticsCalculation, content: str) -> pd.DataFrame:
        """Calculate TF-IDF measure for each term in the given text content.

        Args:
            content (str): The text content whose terms should be analyzed.

        Returns:
            pd.DataFrame:
        """
