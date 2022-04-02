from __future__ import annotations

from typing import List, Dict

import pandas as pd

from app.services.statistics.statistics_calculation import StatisticsCalculation


class DynamicStatisticsCalculation(StatisticsCalculation):
    """A class for providing text related statistics dynamically (i.e., in the request time) from Elastic database."""

    def calculate_term_tf_idfs(self: DynamicStatisticsCalculation, article_content: str) -> pd.DataFrame:
        term_tfs = self.calculate_term_tfs(article_content)
        term_dfs = self.calculate_term_dfs(list(term_tfs.keys()))

        term_statistics = pd.DataFrame(
            index=term_tfs.keys(),
            data={
                "tf": term_tfs.values(),
                "df": term_dfs.values(),
            },
        )

        total_article_count = self.article_repository.get_total_article_count()
        term_statistics["tf-idf"] = round(
            term_statistics["tf"] * self.calculate_term_idfs(total_article_count, term_statistics["df"]),
            self.TF_IDF_DECIMAL_PLACE_COUNT,
        )

        return term_statistics[["tf-idf"]]

    def calculate_term_tfs(self: DynamicStatisticsCalculation, content: str) -> Dict[str, int]:
        """Calculate TF (term frequency) for each term in the given text content.

        Args:
            content (str): The text content whose terms should be analyzed.

        Returns:
            Dict[str, int]: A collection of terms as keys and TFs as values.
        """
        term_statistics = self.article_repository.get_article_content_term_statistics(content, False)
        return {term: term_statistic["term_freq"] for term, term_statistic in term_statistics.items()}

    def calculate_term_dfs(self: DynamicStatisticsCalculation, terms: List[str]) -> Dict[str, int]:
        """Calculate DF (document frequency) for the given terms.

        Args:
            terms (List[str]): The text content whose terms should be analyzed.

        Returns:
            Dict[str, int]: A collection of terms as keys and DFs as values.
        """
        term_search_results = self.article_repository.search_articles_by_terms(terms, ["content"], 0)

        return {terms[i]: term_search_results[i]["hits"]["total"] for i in range(len(terms))}
