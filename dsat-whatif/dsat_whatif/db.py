from __future__ import annotations
from typing import Any, Dict
from pymongo import MongoClient

class MongoClientFactory:
    _cache: Dict[str, MongoClient] = {}

    @classmethod
    def get(cls, uri: str) -> MongoClient:
        if uri not in cls._cache:
            cls._cache[uri] = MongoClient(uri)
        return cls._cache[uri]
