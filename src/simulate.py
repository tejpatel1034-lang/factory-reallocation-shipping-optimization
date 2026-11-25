"""Scenario simulation engine + recommendation logic."""
import numpy as np
import pandas as pd
from .config import (FACTORIES, FREIGHT_RATE_PER_UNIT_KM, HIGH_LOAD_INCREASE,
                     MED_LOAD_INCREASE, PRODUCT_FACTORY)
from .data import CAT, NUM, distance_to


def _scenario_frame(orders: pd.DataFrame, factory: str) -> pd.DataFrame:
    s = orders.copy()
    s["Factory"] = factory
    s["distance_km"] = distance_to(s, factory)
    return s


def simulate_product(model, df, product, region=None, ship_mode=None, year=None):
    """Predict lead time, distance and freight for `product` if made at each factory."""
    o = df[df["Product Name"] == product]
    if region and region != "All":
        o = o[o["Region"] == region]
    if ship_mode and ship_mode != "All":
        o = o[o["Ship Mode"] == ship_mode]
    if o.empty:
        return pd.DataFrame()
    if year is None:
        year = int(df["order_year"].max())
    cur = PRODUCT_FACTORY[product]
    fac_units = df.groupby("Factory")["Units"].sum()
    prod_units = df.loc[df["Product Name"] == product, "Units"].sum()
    train_rng = (df.loc[df["Product Name"] == product, "distance_km"].min(),
                 df.loc[df["Product Name"] == product, "distance_km"].max())
    rows = []
    for f in FACTORIES:
        s = _scenario_frame(o, f); s["order_year"] = year
        lt = float(model.predict(s[CAT + NUM]).mean())
        dist = float((s["distance_km"] * s["Units"]).sum() / s["Units"].sum())
        freight = float((s["distance_km"] * s["Units"]).sum() * FREIGHT_RATE_PER_UNIT_KM)
        in_rng = float(s["distance_km"].between(*train_rng).mean())
        load_inc = 0.0 if f == cur else prod_units / max(fac_units.get(f, 1), 1)
        risk = "High" if load_inc > HIGH_LOAD_INCREASE else "Medium" if load_inc > MED_LOAD_INCREASE else "Low"
        rows.append({"Factory": f, "Current": f == cur, "Pred. lead time (days)": lt,
                     "Avg distance (km)": dist, "Freight proxy ($)": freight,
                     "Confidence (%)": 100 * in_rng, "Capacity load increase (%)": 100 * load_inc,
                     "Risk": risk, "Orders simulated": len(s),
                     "Baseline GP ($)": float(o["Gross Profit"].sum())})
    r = pd.DataFrame(rows)
    b = r[r.Current].iloc[0]
    r["Lead time reduction (days)"] = b["Pred. lead time (days)"] - r["Pred. lead time (days)"]
    r["Lead time reduction (%)"] = 100 * r["Lead time reduction (days)"] / b["Pred. lead time (days)"]
    r["Distance reduction (%)"] = 100 * (b["Avg distance (km)"] - r["Avg distance (km)"]) / b["Avg distance (km)"]
    r["Profit impact ($)"] = b["Freight proxy ($)"] - r["Freight proxy ($)"]
    r["Profit impact (%)"] = 100 * r["Profit impact ($)"] / r["Baseline GP ($)"]
    return r


def rank(r: pd.DataFrame, speed_weight: float = 0.5) -> pd.DataFrame:
    """Score = w*operational gain + (1-w)*profit gain - risk penalty (current factory excluded)."""
    if r.empty:
        return r
    r = r.copy()
    speed = 0.5 * r["Distance reduction (%)"] + 0.5 * r["Lead time reduction (%)"] * 100

    def mm(x):
        return (x - x.min()) / (x.max() - x.min()) if x.max() > x.min() else x * 0
    penalty = r["Risk"].map({"Low": 0, "Medium": 0.1, "High": 0.25})
    r["Score"] = (speed_weight * mm(speed) + (1 - speed_weight) * mm(r["Profit impact ($)"]) - penalty).round(3)
    r.loc[r.Current, "Score"] = np.nan
    return r.sort_values("Score", ascending=False, na_position="last").reset_index(drop=True)


REC_COLS = ["Lead time reduction (days)", "Lead time reduction (%)", "Distance reduction (%)",
            "Profit impact ($)", "Profit impact (%)", "Risk", "Confidence (%)", "Score"]


def recommend_all(model, df, speed_weight=0.5, top_n=1):
    """Best alternative factory for every product x region."""
    out = []
    for p in sorted(df["Product Name"].unique()):
        for reg in sorted(df["Region"].unique()):
            r = rank(simulate_product(model, df, p, reg), speed_weight)
            if r.empty:
                continue
            for _, a in r[~r.Current].head(top_n).iterrows():
                out.append({"Product": p, "Region": reg, "Current factory": PRODUCT_FACTORY[p],
                            "Recommended factory": a["Factory"], **{k: a[k] for k in REC_COLS}})
    return pd.DataFrame(out)


def kpis(rec: pd.DataFrame, total_pairs: int):
    good = rec[(rec["Distance reduction (%)"] > 0) & (rec["Profit impact ($)"] > 0)]
    return {
        "Lead Time Reduction (%)": rec["Lead time reduction (%)"].mean(),
        "Distance Reduction (%)": rec["Distance reduction (%)"].mean(),
        "Profit Impact Stability (% recs with profit gain)": 100 * (rec["Profit impact ($)"] >= 0).mean(),
        "Scenario Confidence Score (%)": rec["Confidence (%)"].mean(),
        "Recommendation Coverage (%)": 100 * len(good) / max(total_pairs, 1),
    }
