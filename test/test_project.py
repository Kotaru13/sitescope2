import json, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import availability as av, benchmark as bm, generate_data as gd, search_queries as sq, search, bathtub

class TestAvailability(unittest.TestCase):
    def test_budget_30_days(self):
        self.assertAlmostEqual(av.downtime_budget(30 * 86400, 99.99) / 60, 4.32, places=2)
    def test_budget_365_days(self):
        self.assertAlmostEqual(av.downtime_budget(365 * 86400, 99.99) / 60, 52.56, places=2)
    def test_incidents_scenario(self):
        r = av.incident_report(30 * 86400, [75, 100, 40], 99.99)
        self.assertEqual(r["downtime_s"], 215)
        self.assertAlmostEqual(r["reserve_s"], 44.2, places=3)
        self.assertFalse(r["fits_extra_60s"])
        self.assertAlmostEqual(r["A_pct"], r["MTBF/(MTBF+MTTR)_pct"], places=9)
    def test_edge_zero_downtime(self):
        self.assertEqual(av.availability(1000, 0), 100.0)
    def test_edge_invalid(self):
        with self.assertRaises(ValueError): av.availability(100, 200)
        with self.assertRaises(ValueError): av.downtime_budget(100, 101)

class TestData(unittest.TestCase):
    def test_format_and_size(self):
        docs = [json.loads(l) for l in (ROOT / "data" / "catalog.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertGreaterEqual(len(docs), 1000)
        self.assertEqual({"id", "title", "description", "category", "tags", "published_at"}, set(docs[0]))
        self.assertEqual(len({d["id"] for d in docs}), len(docs))
        self.assertGreaterEqual(sum(d["id"].startswith("manual-") for d in docs), 20)
    def test_reproducible(self):
        self.assertEqual(gd.generate(), gd.generate())

class TestSearchLogic(unittest.TestCase):
    def test_precision(self):
        self.assertEqual(sq.precision_at_k(["a", "b", "c", "d", "e"], {"a", "c"}), 0.4)
        self.assertEqual(sq.precision_at_k([], {"a"}), 0.0)
    def test_query_files_valid(self):
        files = list((ROOT / "queries").glob("scenario_*.json"))
        self.assertEqual(len(files), 6)
        for f in files: self.assertIn("query", json.loads(f.read_text(encoding="utf-8")))
    def test_build_query_category_filter(self):
        self.assertIn("filter", search.build_query("x", "math")["query"]["bool"])
        self.assertNotIn("filter", search.build_query("x")["query"]["bool"])

class TestBenchmark(unittest.TestCase):
    def test_three_algorithms_agree(self):
        import random
        recs = bm.make_dataset(500, random.Random(1)); srt = sorted(recs); ids = [r[0] for r in srt]
        d = {r[0]: r for r in recs}
        for k in [r[0] for r in recs[:50]] + [-1, 10**9]:
            self.assertEqual(bm.linear_search(recs, k), bm.binary_search(srt, ids, k))
            self.assertEqual(bm.binary_search(srt, ids, k), d.get(k))
    def test_median_positive(self):
        self.assertGreater(bm.median_us_per_lookup(lambda k: k, [1, 2, 3], repeats=5), 0)

class TestBathtub(unittest.TestCase):
    def test_phases(self):
        self.assertGreater(bathtub.hazard(0), bathtub.hazard(3))
        self.assertAlmostEqual(bathtub.hazard(15), 1.0, delta=0.01)
        self.assertGreater(bathtub.hazard(36), bathtub.hazard(30))

if __name__ == "__main__":
    unittest.main()
