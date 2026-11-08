"""CLI: python src/search.py --query "..." [--category X] [--limit 5]"""
import argparse

def build_query(query, category=None, limit=5):
    bool_q = {"must": [{"multi_match": {"query": query, "fields": ["title^2", "description"]}}]}
    if category:
        bool_q["filter"] = [{"term": {"category": category}}]
    return {"size": limit, "query": {"bool": bool_q}}

if __name__ == "__main__":
    from elasticsearch import Elasticsearch
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True)
    ap.add_argument("--category")
    ap.add_argument("--limit", type=int, default=5)
    a = ap.parse_args()
    es = Elasticsearch("http://127.0.0.1:9200")
    for h in es.search(index="sitescope-pages", **build_query(a.query, a.category, a.limit))["hits"]["hits"]:
        print(f'{h["_score"]:.3f}  {h["_source"]["id"]}  {h["_source"]["title"]}')
