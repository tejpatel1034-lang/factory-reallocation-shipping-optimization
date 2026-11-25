"""Run the full pipeline: clean -> train -> evaluate -> simulate -> save reports & figures."""
import json
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.config import REPORTS
from src.data import clean, load_raw
from src.models import train_and_select
from src.simulate import kpis, recommend_all

raw = load_raw(); df = clean(raw)
print(f"rows: raw={len(raw):,} clean={len(df):,}")
metrics, best, model = train_and_select(df)
print(metrics.round(3).to_string()); print("Selected:", best)
metrics.round(4).to_csv(REPORTS / "model_metrics.csv", index=False)

rec = recommend_all(model, df, 0.5, top_n=1)
rec.round(3).to_csv(REPORTS / "recommendations.csv", index=False)
k = kpis(rec, df["Product Name"].nunique() * df["Region"].nunique())
json.dump({"selected_model": best, "kpis": {a: round(float(b), 3) for a, b in k.items()},
           "corr_distance_leadtime": round(float(df["distance_km"].corr(df["lead_time"])), 4)},
          open(REPORTS / "summary.json", "w"), indent=2)
print(json.dumps({a: round(float(b), 3) for a, b in k.items()}, indent=2))

F = REPORTS / "figures"; plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False})
def save(name):
    plt.tight_layout(); plt.savefig(F / name, dpi=150); plt.close()
fig, ax = plt.subplots(figsize=(7, 4)); (df.groupby("Factory")["Units"].sum() / 1e3).sort_values().plot.barh(ax=ax, color="#e8590c")
ax.set_xlabel("Units shipped (thousands)"); ax.set_title("Volume by factory"); save("volume_by_factory.png")
fig, ax = plt.subplots(figsize=(7, 4)); df.groupby("Product Name")["Gross Profit"].sum().sort_values().plot.barh(ax=ax, color="#2f9e44")
ax.set_title("Gross profit by product ($)"); save("profit_by_product.png")
fig, ax = plt.subplots(figsize=(7, 4)); ax.scatter(df["distance_km"], df["lead_time"], s=4, alpha=.3, color="#1c7ed6")
ax.set_xlabel("Factory-to-customer distance (km)"); ax.set_ylabel("Lead time (days)"); ax.set_title("Distance vs lead time"); save("distance_vs_leadtime.png")
fig, ax = plt.subplots(figsize=(7, 4)); ax.bar(metrics["Model"].str.replace(" (baseline)", "", regex=False), metrics["RMSE"], color="#7048e8")
ax.set_ylabel("RMSE (days)"); ax.set_title("Model comparison"); plt.xticks(rotation=15); save("model_comparison.png")
fig, ax = plt.subplots(figsize=(7, 4)); rec.groupby("Recommended factory").size().plot.bar(ax=ax, color="#f08c00")
ax.set_title("Recommended factory (product x region count)"); plt.xticks(rotation=20); save("recommended_factories.png")
print("done")
