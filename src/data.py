"""Data loading, cleaning, feature engineering."""
import numpy as np
import pandas as pd
from .config import DATA_PATH, FACTORIES, PRODUCT_FACTORY, STATE_COORDS

CAT = ["Product Name", "Factory", "Region", "Ship Mode"]
NUM = ["distance_km", "Units", "order_year"]
TARGET = "lead_time"


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = p2 - p1, np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * r * np.arcsin(np.sqrt(a))


def distance_to(df: pd.DataFrame, factory) -> np.ndarray:
    """Distance (km) from a factory (str or Series) to each order's state centroid."""
    st = df["State/Province"].map(STATE_COORDS)
    lat = st.map(lambda x: x[0]).to_numpy(); lon = st.map(lambda x: x[1]).to_numpy()
    if isinstance(factory, str):
        flat, flon = FACTORIES[factory]
    else:
        flat = factory.map(lambda f: FACTORIES[f][0]).to_numpy()
        flon = factory.map(lambda f: FACTORIES[f][1]).to_numpy()
    return haversine(flat, flon, lat, lon)


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%d-%m-%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%d-%m-%Y")
    df[TARGET] = (df["Ship Date"] - df["Order Date"]).dt.days
    df["order_year"] = df["Order Date"].dt.year
    df["Factory"] = df["Product Name"].map(PRODUCT_FACTORY)
    df["distance_km"] = distance_to(df, df["Factory"])
    df["margin"] = df["Gross Profit"] / df["Sales"]
    return df


def clean(df: pd.DataFrame, k: float = 3.0) -> pd.DataFrame:
    """Drop extreme lead-time outliers (k*IQR, computed within each order year)."""
    keep = pd.Series(True, index=df.index)
    for _, g in df.groupby("order_year"):
        q1, q3 = g[TARGET].quantile([.25, .75]); iqr = q3 - q1
        keep[g.index] = g[TARGET].between(q1 - k * iqr, q3 + k * iqr)
    return df[keep & (df[TARGET] > 0)].copy()
