from __future__ import annotations

import os
from functools import lru_cache
from typing import Dict, List

import dask.dataframe as dd
import pandas as pd

from app.data_storage.elastic_database import ElasticDatabase


class ArticleRepository:
    @property
    def index(self: ArticleRepository) -> str:
        return "articles"

    @property
    def index_settings(self: ArticleRepository) -> dict:
        return {
            "settings": {
                "index": {"number_of_shards": 2, "number_of_replicas": 2},
                "analysis": {
                    "analyzer": {
                        "content_analyzer": {
                            "tokenizer": "standard",
                            "filter": ["lowercase", "asciifolding", "kstem", "english_stop", "english_add_stop"],
                            "char_filter": ["html_strip", "token_char_filter"],
                        }
                    },
                    "filter": {
                        "english_stop": {"type": "stop", "stopwords": "_english_"},
                        "english_add_stop": {"type": "stop", "stopwords": ["has", "have"]},
                    },
                    "char_filter": {
                        "token_char_filter": {
                            "type": "pattern_replace",
                            "pattern": "[\\p{Punct}\\p{Digit}]",
                            "replacement": "",
                        }
                    },
                },
            },
            "mappings": {
                "properties": {
                    "title": {
                        "type": "text",
                        "fields": {"prefix": {"type": "search_as_you_type"}},
                        "analyzer": "content_analyzer",
                    },
                    "url": {"type": "keyword", "null_value": ""},
                    "content": {"type": "text", "term_vector": "yes", "store": "true", "analyzer": "content_analyzer"},
                }
            },
        }

    @property
    def data_lake_path(self: ArticleRepository) -> str:
        return os.getenv("DATA_LAKE_PATH", "data_lake")

    @property
    def corpus_bucket(self: ArticleRepository) -> str:
        return os.getenv("CORPUS_BUCKET", "corpus")

    @property
    def statistics_bucket(self: ArticleRepository) -> str:
        return os.getenv("STATISTICS_BUCKET", "stats")

    @property
    def term_statistics_key(self: ArticleRepository) -> str:
        return os.getenv("TERM_STATISTICS_KEY", "term_statistics.parquet")

    def create_index(self: ArticleRepository, force: bool = False) -> None:
        """Create an Elastic index for articles.

        Args:
            force: Whether to recreate the index.
        """
        ElasticDatabase.create_index(self.index, self.index_settings, force)

    def article_index_exists(self: ArticleRepository) -> bool:
        """Check whether the article index already exists."""
        return ElasticDatabase.index_exists(self.index)

    def insert_articles(self: ArticleRepository, articles: pd.DataFrame) -> None:
        """Insert a batch of articles into the database.

        Args:
            articles (pd.DataFrame): A batch of articles.
        """
        articles_dict = articles[["url", "content"]].to_dict(orient="records")
        ElasticDatabase.insert_bulk(self.index, articles_dict)

    def search_articles_by_terms(
        self: ArticleRepository, terms: List[str], fields: List[str], limit: int, offset: int = 0
    ) -> List[dict]:
        """Find articles which contain a term for each term in the given list.

        Args:
            terms (List[str]): A collection of search terms.
            fields (List[str]): The article fields to search for the terms
            limit (int): Number of articles to return.
            offset (int): Starting offset for returned articles.

        Returns:
            List[dict]: A collection of search results including the requested number of articles and other information
                        (e.g., total number of found articles) for each term.
        """
        searches: List[dict] = []
        for term in terms:
            searches.extend(
                [{}, {"query": {"multi_match": {"query": term, "fields": fields}}, "from": offset, "size": limit}]
            )

        return ElasticDatabase.multi_search(self.index, searches)["responses"]

    def get_article_content_term_statistics(
        self: ArticleRepository, content: str, additional_statistics: bool
    ) -> Dict[str, dict]:
        """Get term statistics (e.g., term frequency)

        Args:
            content (str): The content whose terms are being analyzed.
            additional_statistics (bool): Whether to return additional term statistics (e.g., shard document frequency)

        Returns:
            Dict[str, Any] A collection of term statistics for each term.
        """
        return ElasticDatabase.get_term_vectors(
            self.index, {"content": content}, fields=["content"], term_statistics=additional_statistics
        ).body["term_vectors"]["content"]["terms"]

    def get_total_article_count(self: ArticleRepository) -> int:
        """Get count of total articles in the database in all shards.

        Returns:
            int:
        """
        return ElasticDatabase.count(self.index)["count"]

    @lru_cache
    def get_static_articles(self: ArticleRepository, file_pattern: str = "*.csv") -> dd.DataFrame:
        """Get the articles from the corpus in the data lake.

        Args:
            file_pattern (str):

        Returns:
            dd.DataFrame: A partitioned collection of articles.
        """
        return dd.read_csv(f"{self.data_lake_path}/{self.corpus_bucket}/{file_pattern}", dtype=object).dropna(
            subset=["content"]
        )

    @lru_cache
    def get_static_article_count(self: ArticleRepository) -> int:
        """Get count of total articles in the corpus.

        Returns:
            int:
        """
        return self.get_static_articles().shape[0].compute()

    @lru_cache
    def get_static_term_statistics(self: ArticleRepository) -> pd.DataFrame:
        """Get the processed term statistics (e.g. term DFs) from the data lake.

        Returns:
            pd.DataFrame
        """
        return pd.read_parquet(f"{self.data_lake_path}/{self.term_statistics_key}").set_index("term")
