"""Nassau Candy - Factory Reallocation & Shipping Optimization (Streamlit)."""
import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.config import FACTORIES, MODEL_PATH, PRODUCT_FACTORY
from src.data import clean, load_raw
from src.simulate import kpis, rank, recommend_all, simulate_product

st.set_page_config(page_title="Nassau Candy Optimizer", page_icon="🍬", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.5rem}
div[data-testid="stMetric"]{background:#fff7ed;border:1px solid #fed7aa;padding:12px;border-radius:12px}
</style>""", unsafe_allow_html=True)


@st.cache_data
def get_data():
    return clean(load_raw())


@st.cache_resource
def get_model():
    if not MODEL_PATH.exists():
        from src.models import train_and_select
        return train_and_select(get_data())[2]
    return joblib.load(MODEL_PATH)["model"]


df, model = get_data(), get_model()

st.title("🍬 Factory Reallocation & Shipping Optimization")
st.caption("Predict lead times, simulate factory reassignments, and balance speed with profitability.")

with st.sidebar:
    st.header("Controls")
    product = st.selectbox("Product", sorted(df["Product Name"].unique()))
    region = st.selectbox("Region", ["All"] + sorted(df["Region"].unique()))
    mode = st.selectbox("Ship mode", ["All"] + sorted(df["Ship Mode"].unique()))
    w = st.slider("Optimization priority (profit ⟷ speed)", 0.0, 1.0, 0.5, 0.05)
    top_n = st.number_input("Top-N recommendations", 1, 4, 3)
    st.info(f"Current factory: **{PRODUCT_FACTORY[product]}**")

sim = rank(simulate_product(model, df, product, region, mode), w)
t1, t2, t3, t4, t5 = st.tabs(["🏭 Simulator", "🔀 What-If", "⭐ Recommendations", "⚠️ Risk & Impact", "📊 Overview"])

with t1:
    if sim.empty:
        st.warning("No orders match this filter.")
    else:
        c = st.columns(3)
        cur = sim[sim.Current].iloc[0]
        c[0].metric("Orders simulated", f"{int(cur['Orders simulated']):,}")
        c[1].metric("Current avg distance", f"{cur['Avg distance (km)']:.0f} km")
        c[2].metric("Current predicted lead time", f"{cur['Pred. lead time (days)']:.1f} d")
        fig = px.bar(sim.sort_values("Avg distance (km)"), x="Factory", y="Avg distance (km)",
                     color="Current", color_discrete_map={True: "#e8590c", False: "#94a3b8"},
                     title="Average shipping distance by candidate factory")
        st.plotly_chart(fig, width="stretch")
        st.dataframe(sim[["Factory", "Current", "Pred. lead time (days)", "Avg distance (km)",
                          "Freight proxy ($)", "Risk", "Score"]].round(2), hide_index=True, width="stretch")

with t2:
    if not sim.empty:
        alts = sim[~sim.Current]
        pick = st.selectbox("Compare current vs.", alts["Factory"])
        a = alts[alts.Factory == pick].iloc[0]
        c = st.columns(3)
        c[0].metric("Distance change", f"{-a['Distance reduction (%)']:.1f}%")
        c[1].metric("Lead time change", f"{-a['Lead time reduction (days)']:.2f} d")
        c[2].metric("Freight saving (proxy)", f"${a['Profit impact ($)']:.2f}")
        m = go.Figure()
        for n, (la, lo) in FACTORIES.items():
            m.add_trace(go.Scattergeo(lat=[la], lon=[lo], text=n, mode="markers+text", textposition="top center",
                                      marker=dict(size=12, color="#e8590c" if n == PRODUCT_FACTORY[product]
                                                  else "#2563eb" if n == pick else "#94a3b8"), showlegend=False))
        m.update_geos(scope="north america", showland=True, landcolor="#f1f5f9")
        m.update_layout(margin=dict(l=0, r=0, t=30, b=0), title="Factories (orange = current, blue = candidate)")
        st.plotly_chart(m, width="stretch")

with t3:
    rec = recommend_all(model, df, w, top_n=int(top_n))
    k = kpis(rec[rec.Product == product] if product else rec, df["Region"].nunique())
    cols = st.columns(5)
    for col, (n, v) in zip(cols, k.items()):
        col.metric(n.split(" (")[0], f"{v:.1f}%")
    st.subheader("Ranked reassignment suggestions")
    st.dataframe(rec[rec.Product == product].round(2), hide_index=True, width="stretch")
    with st.expander("All products"):
        st.dataframe(rec.round(2), hide_index=True, width="stretch")
    st.download_button("⬇️ Download all recommendations (CSV)", rec.to_csv(index=False), "recommendations.csv")

with t4:
    if not sim.empty:
        for _, r in sim[~sim.Current].iterrows():
            icon = {"High": "🔴", "Medium": "🟠", "Low": "🟢"}[r["Risk"]]
            msg = (f"{icon} **{r['Factory']}** · risk **{r['Risk']}** · capacity load +{r['Capacity load increase (%)']:.0f}% · "
                   f"profit impact ${r['Profit impact ($)']:.2f} ({r['Profit impact (%)']:.2f}% of GP) · confidence {r['Confidence (%)']:.0f}%")
            (st.error if r["Risk"] == "High" else st.warning if r["Profit impact ($)"] < 0 else st.success)(msg)

with t5:
    c = st.columns(4)
    c[0].metric("Orders", f"{len(df):,}"); c[1].metric("Sales", f"${df['Sales'].sum():,.0f}")
    c[2].metric("Gross profit", f"${df['Gross Profit'].sum():,.0f}"); c[3].metric("Units", f"{df['Units'].sum():,}")
    st.plotly_chart(px.bar(df.groupby("Factory")["Gross Profit"].sum().reset_index(), x="Factory", y="Gross Profit",
                           color="Factory", title="Gross profit by factory"), width="stretch")
    st.plotly_chart(px.box(df, x="Region", y="distance_km", color="Region", title="Shipping distance by region"),
                    width="stretch")
    st.caption("⚠️ Ship dates in the source file are 2026–2030, so absolute lead times (~900–1,640 days) are a data artifact. "
               "See README → Data caveats.")
