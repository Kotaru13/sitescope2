"""Сравнение линейного, бинарного поиска и dict при поиске записи по числовому id."""
import csv, json, random, statistics, time, platform, sys
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
SIZES = [1_000, 10_000, 100_000]
REPEATS = 7
SEED = 42

def linear_search(records, key):
    for r in records:
        if r[0] == key:
            return r
    return None

def binary_search(sorted_records, ids, key):
    lo, hi = 0, len(ids) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if ids[mid] == key:
            return sorted_records[mid]
        if ids[mid] < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return None

def median_us_per_lookup(fn, keys, repeats=REPEATS):
    """Медиана по повторам среднего времени одного поиска, в микросекундах."""
    runs = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        for k in keys:
            fn(k)
        runs.append((time.perf_counter_ns() - t0) / len(keys) / 1000)
    return statistics.median(runs)

def make_dataset(n, rnd):
    ids = rnd.sample(range(1, n * 10), n)          # уникальные id, неупорядоченные
    records = [(i, f"title-{i}") for i in ids]
    return records

def run():
    rnd = random.Random(SEED)
    rows, prep_rows = [], []
    for n in SIZES:
        records = make_dataset(n, rnd)
        t0 = time.perf_counter_ns(); srt = sorted(records); t_sort = (time.perf_counter_ns() - t0) / 1e3
        ids = [r[0] for r in srt]
        t0 = time.perf_counter_ns(); dct = {r[0]: r for r in records}; t_dict = (time.perf_counter_ns() - t0) / 1e3
        prep_rows.append({"N": n, "sort_us": round(t_sort, 1), "dict_build_us": round(t_dict, 1)})
        existing = rnd.sample([r[0] for r in records], 100)
        present = set(ids)
        missing = []
        while len(missing) < 100:
            k = rnd.randint(1, n * 10)
            if k not in present:
                missing.append(k)
        lin = lambda k: linear_search(records, k)
        bin_ = lambda k: binary_search(srt, ids, k)
        dic = lambda k: dct.get(k)
        for k in existing + missing:                # одинаковость результатов
            assert lin(k) == bin_(k) == dic(k)
        for label, keys in (("найден", existing), ("не найден", missing)):
            rows.append({"N": n, "condition": label,
                         "linear_us": median_us_per_lookup(lin, keys),
                         "binary_us": median_us_per_lookup(bin_, keys),
                         "dict_us": median_us_per_lookup(dic, keys)})
    return rows, prep_rows

def plot(rows):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, cond in zip(axes, ("найден", "не найден")):
        sel = [r for r in rows if r["condition"] == cond]
        for key, name in (("linear_us", "Линейный O(n)"), ("binary_us", "Бинарный O(log n)"), ("dict_us", "dict O(1) средн.")):
            ax.plot([r["N"] for r in sel], [r[key] for r in sel], marker="o", label=name)
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(f"Ключ {cond}")
        ax.set_xlabel("N, записей"); ax.grid(True, which="both", alpha=.3)
    axes[0].set_ylabel("Время одного поиска, мкс (медиана)"); axes[0].legend()
    fig.suptitle("Поиск записи по числовому id (локальные структуры, без Elasticsearch)")
    fig.tight_layout(); fig.savefig(RES / "benchmark.png", dpi=150)

if __name__ == "__main__":
    RES.mkdir(exist_ok=True)
    rows, prep = run()
    env = {"python": sys.version.split()[0], "platform": platform.platform(), "repeats": REPEATS, "seed": SEED}
    with (RES / "benchmark.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    (RES / "benchmark_prep.json").write_text(json.dumps({"env": env, "prep": prep}, ensure_ascii=False, indent=2), encoding="utf-8")
    plot(rows)
    for r in rows: print({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    print(prep, env)
