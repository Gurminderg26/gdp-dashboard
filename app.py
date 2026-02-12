import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(
    page_title="Global GDP Dashboard",
    page_icon="🌍",
    layout="wide"
)

# -------------------------
# LOAD DATA (Optimized)
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("refined_gdp_per_capita_long.csv")
    df = df.dropna()
    df["Year"] = df["Year"].astype(int)
    df = df.sort_values(["Country", "Year"])
    df["YoY_Growth_%"] = df.groupby("Country")["GDP_per_capita_USD"].pct_change() * 100
    return df

df = load_data()

# -------------------------
# SIDEBAR
# -------------------------
st.sidebar.title("🔧 Controls")

countries = st.sidebar.multiselect(
    "Select Countries",
    sorted(df["Country"].unique()),
    default=sorted(df["Country"].unique())[:8]
)

year_range = st.sidebar.slider(
    "Select Year Range",
    int(df.Year.min()),
    int(df.Year.max()),
    (2000, int(df.Year.max()))
)

top_n = st.sidebar.slider("Top N (CAGR Ranking)", 5, 25, 10)

# Filter data
filtered = df[
    (df["Country"].isin(countries)) &
    (df["Year"].between(year_range[0], year_range[1]))
]

# -------------------------
# CAGR
# -------------------------
def calculate_cagr(group):
    start = group.iloc[0]["GDP_per_capita_USD"]
    end = group.iloc[-1]["GDP_per_capita_USD"]
    years = group.iloc[-1]["Year"] - group.iloc[0]["Year"]
    if years > 0 and start > 0:
        return (end / start) ** (1 / years) - 1
    return np.nan

cagr_df = (
    filtered.groupby("Country")
    .apply(calculate_cagr)
    .reset_index(name="CAGR")
    .dropna()
)

# -------------------------
# HEADER
# -------------------------
st.title("🌍 Global GDP per Capita Intelligence Dashboard")
st.markdown("Interactive economic comparison, growth trends, and performance analytics.")

# -------------------------
# KPI SECTION
# -------------------------
col1, col2, col3, col4 = st.columns(4)

col1.metric("Countries Selected", len(countries))
col2.metric("Year Range", f"{year_range[0]} – {year_range[1]}")
col3.metric("Average CAGR", f"{(cagr_df.CAGR.mean()*100):.2f}%")
col4.metric("Latest Year", filtered["Year"].max())

st.divider()

# -------------------------
# MAP
# -------------------------
latest_year = filtered["Year"].max()
map_df = filtered[filtered["Year"] == latest_year]

fig_map = px.choropleth(
    map_df,
    locations="Country",
    locationmode="country names",
    color="GDP_per_capita_USD",
    hover_name="Country",
    color_continuous_scale="viridis",
    title=f"GDP per Capita by Country ({latest_year})"
)

st.plotly_chart(fig_map, use_container_width=True)

st.divider()

# -------------------------
# TREND + CAGR SIDE BY SIDE
# -------------------------
colA, colB = st.columns(2)

with colA:
    fig_trend = px.line(
        filtered,
        x="Year",
        y="GDP_per_capita_USD",
        color="Country",
        title="GDP per Capita Trends"
    )
    st.plotly_chart(fig_trend, use_container_width=True)

with colB:
    top_cagr = cagr_df.sort_values("CAGR", ascending=False).head(top_n)
    fig_cagr = px.bar(
        top_cagr,
        x="Country",
        y="CAGR",
        title="Top Countries by CAGR"
    )
    st.plotly_chart(fig_cagr, use_container_width=True)

st.divider()

# -------------------------
# PIE CHART - GDP DISTRIBUTION
# -------------------------
if len(map_df) > 1:
    fig_pie = px.pie(
        map_df,
        names="Country",
        values="GDP_per_capita_USD",
        title=f"GDP per Capita Distribution by Country ({latest_year})"
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# -------------------------
# DATA EXPORT
# -------------------------
st.subheader("📥 Export Data")
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download Filtered Data (CSV)",
    csv,
    "gdp_dashboard_export.csv",
    "text/csv"
)
