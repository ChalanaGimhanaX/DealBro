import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

import pytest
from bson import ObjectId


def _match_query(document: Dict[str, Any], query: Dict[str, Any]) -> bool:
    if not query:
        return True

    # Support a minimal subset of Mongo queries used by the codebase/tests.
    if "$or" in query:
        return any(_match_query(document, sub) for sub in query["$or"])

    for key, expected in query.items():
        if key == "$or":
            continue

        if isinstance(expected, dict) and "$regex" in expected:
            value = str(document.get(key, ""))
            pattern = expected["$regex"]
            flags = re.IGNORECASE if expected.get("$options", "") == "i" else 0
            if re.search(pattern, value, flags) is None:
                return False
            continue

        if document.get(key) != expected:
            return False

    return True


@dataclass
class _InsertOneResult:
    inserted_id: ObjectId


class InMemoryMongoCollection:
    def __init__(self):
        self._docs: Dict[ObjectId, Dict[str, Any]] = {}

    def create_index(self, *args, **kwargs):
        return None

    def insert_one(self, document: Dict[str, Any]) -> _InsertOneResult:
        doc = dict(document)
        _id = doc.get("_id") or ObjectId()
        doc["_id"] = _id
        self._docs[_id] = doc
        return _InsertOneResult(inserted_id=_id)

    def find_one(self, query: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        query = query or {}
        for doc in self._docs.values():
            if _match_query(doc, query):
                return dict(doc)
        return None

    def update_one(self, query: Dict[str, Any], update: Dict[str, Any]):
        for _id, doc in self._docs.items():
            if _match_query(doc, query):
                if "$set" in update and isinstance(update["$set"], dict):
                    doc.update(update["$set"])
                return None
        return None

    def count_documents(self, query: Optional[Dict[str, Any]] = None) -> int:
        query = query or {}
        return sum(1 for doc in self._docs.values() if _match_query(doc, query))


class InMemoryMongoDatabase:
    def __init__(self):
        self.sources = InMemoryMongoCollection()
        self.deal_posts = InMemoryMongoCollection()
        self.deal_items = InMemoryMongoCollection()
        self.deal_fingerprints = InMemoryMongoCollection()


@pytest.fixture()
def mongo_db() -> InMemoryMongoDatabase:
    return InMemoryMongoDatabase()


@pytest.fixture()
def sample_source(mongo_db: InMemoryMongoDatabase) -> dict:
    source = {
        "name": "testforum",
        "base_url": "https://testforum.com",
        "enabled": True,
    }
    result = mongo_db.sources.insert_one(source)
    source["_id"] = result.inserted_id
    return source

