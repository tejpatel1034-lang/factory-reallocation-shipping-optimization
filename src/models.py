"""Model training, evaluation and selection."""
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .config import MODEL_PATH, RANDOM_STATE
from .data import CAT, NUM, TARGET


def _pipe(model):
    pre = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), CAT),
        ("num", StandardScaler(), NUM)])
    return Pipeline([("pre", pre), ("model", model)])


def candidates():
    return {
        "Linear Regression (baseline)": _pipe(LinearRegression()),
        "Random Forest": _pipe(RandomForestRegressor(n_estimators=150, max_depth=12, min_samples_leaf=5,
                                                     n_jobs=-1, random_state=RANDOM_STATE)),
        "Gradient Boosting": _pipe(GradientBoostingRegressor(n_estimators=200, max_depth=3,
                                                             learning_rate=0.08, random_state=RANDOM_STATE)),
    }


def train_and_select(df: pd.DataFrame):
    X, y = df[CAT + NUM], df[TARGET]
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=RANDOM_STATE)
    rows = []
    for name, pipe in candidates().items():
        pipe.fit(Xtr, ytr); p = pipe.predict(Xte)
        # within-year R2: removes the (large) year offset so it reflects route/mode signal only
        yr = Xte["order_year"].to_numpy()
        res_true = yte.to_numpy() - pd.Series(yte.to_numpy()).groupby(yr).transform("mean").to_numpy()
        res_pred = p - pd.Series(p).groupby(yr).transform("mean").to_numpy()
        rows.append({"Model": name,
                     "RMSE": np.sqrt(mean_squared_error(yte, p)),
                     "MAE": mean_absolute_error(yte, p),
                     "R2": r2_score(yte, p),
                     "R2_within_year": r2_score(res_true, res_pred)})
    m = pd.DataFrame(rows).sort_values("RMSE").reset_index(drop=True)
    # Selection: lowest RMSE, but prefer the simpler model if within 2% of the best.
    best = m.loc[0, "Model"]
    for name in ["Linear Regression (baseline)", "Random Forest", "Gradient Boosting"]:
        if m.loc[m.Model == name, "RMSE"].iloc[0] <= m.loc[0, "RMSE"] * 1.02:
            best = name; break
    final = candidates()[best].fit(X, y)   # refit on all data
    joblib.dump({"model": final, "name": best, "metrics": m}, MODEL_PATH)
    return m, best, final
