"""Создаёт индекс sitescope-pages с явным mapping и загружает catalog.jsonl через bulk."""
import json
from pathlib import Path


INDEX = "sitescope-pages"
DATA = Path(__file__).resolve().parent.parent / "data" / "catalog.jsonl"
MAPPING = {"mappings": {"properties": {
    "id": {"type": "keyword"},
    "title": {"type": "text", "analyzer": "russian"},
    "description": {"type": "text", "analyzer": "russian"},
    "category": {"type": "keyword"},
    "tags": {"type": "keyword"},
    "published_at": {"type": "date"}}},
    "settings": {"number_of_shards": 1, "number_of_replicas": 0}}

def main(url="http://127.0.0.1:9200"):
    from elasticsearch import Elasticsearch, helpers
    es = Elasticsearch(url)
    print("Elasticsearch version:", es.info()["version"]["number"])
    if es.indices.exists(index=INDEX):
        es.indices.delete(index=INDEX)
    es.indices.create(index=INDEX, **MAPPING)
    with DATA.open(encoding="utf-8") as f:
        actions = ({"_index": INDEX, "_id": d["id"], "_source": d} for d in map(json.loads, f))
        ok, _ = helpers.bulk(es, actions)
    es.indices.refresh(index=INDEX)
    print("Проиндексировано:", ok, "| count в индексе:", es.count(index=INDEX)["count"])
    # text разбирается на токены, keyword хранится целиком
    print(es.indices.analyze(index=INDEX, field="title", text="Списки и словари в Python")["tokens"])

if __name__ == "__main__":
    main()
