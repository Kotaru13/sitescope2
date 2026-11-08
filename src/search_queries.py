"""Шесть сценариев Query DSL + Precision@5 для пяти пользовательских запросов."""
import json
from pathlib import Path

INDEX = "sitescope-pages"
QDIR = Path(__file__).resolve().parent.parent / "queries"
RES = Path(__file__).resolve().parent.parent / "results"

# Эталон: какие из 20 ручных документов релевантны каждому запросу
RELEVANCE = {
    "python списки и словари": {"manual-01", "manual-02", "manual-03"},
    "elasticsearch индекс mapping": {"manual-04", "manual-05", "manual-06"},
    "доступность бюджет простоя": {"manual-07", "manual-08", "manual-09"},
    "кривая ванны надёжность": {"manual-10", "manual-11", "manual-12"},
    "бинарный поиск алгоритм": {"manual-13", "manual-14", "manual-15"},
}

def precision_at_k(returned_ids, relevant, k=5):
    top = returned_ids[:k]
    return sum(1 for i in top if i in relevant) / k if k else 0.0

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main(url="http://127.0.0.1:9200"):
    from elasticsearch import Elasticsearch
    es = Elasticsearch(url)
    RES.mkdir(exist_ok=True)
    report = {"es_version": es.info()["version"]["number"], "count": es.count(index=INDEX)["count"],
              "scenarios": {}, "precision": {}}
    for q in sorted(QDIR.glob("scenario_*.json")):
        r = es.search(index=INDEX, **load(q))
        report["scenarios"][q.stem] = {"total": r["hits"]["total"]["value"],
            "top5": [(h["_source"]["id"], h["_source"]["title"], h["_score"]) for h in r["hits"]["hits"][:5]]}
    scores = []
    for text, rel in RELEVANCE.items():
        body = {"size": 5, "query": {"multi_match": {"query": text, "fields": ["title^2", "description"]}}}
        ids = [h["_source"]["id"] for h in es.search(index=INDEX, **body)["hits"]["hits"]]
        p = precision_at_k(ids, rel)
        scores.append(p)
        report["precision"][text] = {"returned": ids, "P@5": p}
    report["precision"]["mean"] = sum(scores) / len(scores)
    (RES / "es_results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
