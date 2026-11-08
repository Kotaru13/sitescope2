"""Калькулятор доступности, бюджета простоя, MTTR/MTBF. Все времена — в секундах."""
import csv, json
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
TARGETS = [99.0, 99.9, 99.95, 99.99, 99.999]
PERIODS = {"24 часа": 24 * 3600, "7 суток": 7 * 86400, "30 суток": 30 * 86400, "365 суток": 365 * 86400}

def availability(total_s, downtime_s):
    if total_s <= 0 or downtime_s < 0 or downtime_s > total_s:
        raise ValueError("нужно 0 <= D <= T и T > 0")
    return (total_s - downtime_s) / total_s * 100

def downtime_budget(total_s, target_pct):
    if not 0 <= target_pct <= 100:
        raise ValueError("цель должна быть в диапазоне 0..100 %")
    return round(total_s * (100 - target_pct) / 100, 6)

def incident_report(total_s, incidents_s, target_pct):
    d = sum(incidents_s)
    budget = downtime_budget(total_s, target_pct)
    n = len(incidents_s)
    mttr = d / n
    mtbf = (total_s - d) / n          # допущение: ремонтируемая система, непрерывное наблюдение
    return {"downtime_s": d, "A_pct": availability(total_s, d), "budget_s": budget,
            "budget_used_pct": d / budget * 100, "reserve_s": budget - d,
            "fits_extra_60s": budget - d >= 60, "MTTR_s": mttr, "MTBF_s": mtbf,
            "MTBF/(MTBF+MTTR)_pct": mtbf / (mtbf + mttr) * 100}

def plot_budget(rep):
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(8, 2.8))
    inc = [75, 100, 40]; left = 0
    for i, s in enumerate(inc, 1):
        ax.barh(0, s, left=left, label=f"Инцидент {i}: {s} с"); left += s
    ax.barh(0, rep["reserve_s"], left=left, color="#cfe8cf", edgecolor="k", label=f"Резерв: {rep['reserve_s']:.1f} с")
    ax.axvline(rep["budget_s"], color="r", ls="--", label=f"Бюджет 99,99%: {rep['budget_s']:.1f} с")
    ax.set_yticks([]); ax.set_xlabel("секунды (окно 30 суток)")
    ax.set_title(f"Бюджет простоя: израсходовано {rep['budget_used_pct']:.1f}%")
    ax.legend(loc="upper center", bbox_to_anchor=(.5, -.35), ncol=2, fontsize=8)
    fig.tight_layout(); fig.savefig(RES / "downtime_budget.png", dpi=150)

if __name__ == "__main__":
    RES.mkdir(exist_ok=True)
    with (RES / "downtime_budgets.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["period", "target_%", "budget_s", "budget_min"])
        for pn, ps in PERIODS.items():
            for t in TARGETS:
                b = downtime_budget(ps, t); w.writerow([pn, t, round(b, 3), round(b / 60, 4)])
                if t == 99.99: print(f"{pn} / 99,99%: {b:.2f} с = {b/60:.2f} мин")
    rep = incident_report(30 * 86400, [75, 100, 40], 99.99)
    (RES / "incidents.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2), encoding="utf-8")
    plot_budget(rep); print(json.dumps(rep, ensure_ascii=False, indent=2))
