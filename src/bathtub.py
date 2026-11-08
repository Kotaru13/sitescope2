"""Иллюстративная кривая ванны: СИНТЕТИЧЕСКАЯ модель, не прогноз для конкретного продукта."""
import math
from pathlib import Path

RES = Path(__file__).resolve().parent.parent / "results"
T_EARLY, T_WEAR, T_END = 6, 28, 36   # границы фаз, условные месяцы

def hazard(t):
    """λ(t), отказов на 1000 устройств в условный месяц (условные единицы)."""
    base = 1.0
    early = 8.0 * math.exp(-t / 1.5)
    wear = 0.0 if t < T_WEAR else 0.35 * (t - T_WEAR) ** 2
    return base + early + wear

def main():
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ts = [i / 10 for i in range(0, T_END * 10 + 1)]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12, 4.5), gridspec_kw={"width_ratios": [1.6, 1]})
    ax.plot(ts, [hazard(t) for t in ts], "k", lw=2)
    ax.axvspan(0, T_EARLY, color="#f4c7c3", alpha=.6, label="Ранние отказы (λ убывает)")
    ax.axvspan(T_EARLY, T_WEAR, color="#c8e6c9", alpha=.6, label="Нормальная работа (λ ≈ const)")
    ax.axvspan(T_WEAR, T_END, color="#ffe0b2", alpha=.6, label="Износ (λ растёт)")
    ax.set_xlim(0, T_END); ax.set_xlabel("Возраст системы t, условные месяцы"); ax.set_ylabel("λ(t), усл. ед.")
    ax.set_title("Кривая ванны\nсинтетическая модель, не прогноз для конкретного продукта", fontsize=10)
    ax.legend(fontsize=8, loc="upper center")
    ax2.axis("off"); ax2.set_title("Инженерные действия по фазам", fontsize=10)
    acts = [("Ранние отказы", "Приёмочное тестирование,\nприработка, burn-in", "#f4c7c3"),
            ("Нормальная работа", "Наблюдение и диагностика:\nмониторинг, алерты, разбор инцидентов", "#c8e6c9"),
            ("Износ", "Профилактика и замена\nизнашивающихся узлов", "#ffe0b2")]
    for i, (h, txt, c) in enumerate(acts):
        y = .8 - i * .32
        ax2.text(.02, y, f"{h}\n{txt}", va="center", fontsize=9, transform=ax2.transAxes,
                 bbox=dict(boxstyle="round", fc=c, ec="k"))
    fig.tight_layout(); fig.savefig(RES / "bathtub.png", dpi=150)

if __name__ == "__main__":
    RES.mkdir(exist_ok=True); main(); print("results/bathtub.png")
