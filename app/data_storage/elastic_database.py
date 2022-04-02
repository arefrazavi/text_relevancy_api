from __future__ import annotations

import os
from collections import deque
from typing import List, Optional, Any, Dict

from elastic_transport import ObjectApiResponse
from elasticsearch import Elasticsearch, helpers


class ElasticDatabase:
    client = None

    @classmethod
    def get_client(cls: Any[Elasticsearch]) -> Elasticsearch:
        if not cls.client:
            cls.client = Elasticsearch(
                f"{os.getenv('ES_HOST')}:{os.getenv('ES_PORT')}",
                basic_auth=(str(os.getenv("ELASTIC_USERNAME")), str(os.getenv("ELASTIC_PASSWORD"))),
            )

        return cls.client

    @classmethod
    def create_index(cls: Any[Elasticsearch], index: str, body: dict, force: bool = False) -> ObjectApiResponse[Any]:
        if force:
            cls.delete_index(index=index)

        return cls.get_client().indices.create(index=index, body=body, ignore=400)

    @classmethod
    def delete_index(cls: Any[Elasticsearch], index: str) -> ObjectApiResponse[Any]:
        return cls.get_client().indices.delete(index=index, ignore=[400, 404])

    @classmethod
    def index_exists(cls: Any[Elasticsearch], index: str) -> bool:
        return cls.get_client().indices.exists(index=index)

    @classmethod
    def insert_bulk(cls: Any[Elasticsearch], index: str, documents: List[dict]) -> deque:
        return deque(helpers.parallel_bulk(client=cls.get_client(), actions=documents, index=index))

    @classmethod
    def insert_one(cls: Any[Elasticsearch], index: str, document: dict) -> ObjectApiResponse[Any]:
        return cls.get_client().index(client=cls.get_client(), index=index, document=document)

    @classmethod
    def search(cls: Any[Elasticsearch], index: str, body: dict) -> ObjectApiResponse[Any]:
        return cls.get_client().search(index=index, body=body)

    @classmethod
    def multi_search(cls: Any[Elasticsearch], index: str, queries: List[Dict[Any, Any]]) -> ObjectApiResponse[Any]:
        return cls.get_client().msearch(
            searches=queries, index=index, search_type="dfs_query_then_fetch", rest_total_hits_as_int=True
        )

    @classmethod
    def get_term_vectors(
        cls: Any[Elasticsearch],
        index: str,
        doc: dict,
        fields: List[str],
        term_statistics: bool = False,
        field_statistics: bool = False,
        positions: bool = False,
    ) -> ObjectApiResponse[Any]:
        return cls.get_client().termvectors(
            index=index,
            doc=doc,
            fields=fields,
            term_statistics=term_statistics,
            field_statistics=field_statistics,
            positions=positions,
            payloads=False,
            offsets=False,
        )

    @classmethod
    def analyze(
        cls: Any[Elasticsearch], text: str, index: Optional[str] = None, analyzer: Optional[str] = None
    ) -> ObjectApiResponse[Any]:
        return cls.get_client().indices.analyze(text=text, index=index, analyzer=analyzer)

    @classmethod
    def count(cls: Any[Elasticsearch], index: str, query: Optional[dict] = None) -> ObjectApiResponse[Any]:
        return cls.get_client().count(index=index, query=query)
