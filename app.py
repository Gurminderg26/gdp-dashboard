import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(layout="wide")

# Load data
df = pd.read_csv("refined_gdp_per_capita_long.csv")
df = df.dropna()
df["Year"] = df["Year"].astype(int)

# Sort & growth
df = df.sort_values(["Country", "Year"])
df["YoY_Growth_%"] = df.groupby("Country")["GDP_per_capita_USD"].pct_change() * 100

# Sidebar filters
st.sidebar.title("🔧 Dashboard Controls")

countries = st.sidebar.multiselect(
    "Select Countries",
    options=sorted(df["Country"].unique()),
    default=list(df["Country"].unique()[:8])
)

year_min, year_max = int(df.Year.min()), int(df.Year.max())
year_range = st.sidebar.slider(
    "Select Year Range",
    year_min,
    year_max,
    (2000, year_max)
)

top_n = st.sidebar.slider("Top N Countries (Ranking)", 5, 30, 10)

# Filter
filtered = df[
    (df["Country"].isin(countries)) &
    (df["Year"].between(year_range[0], year_range[1]))
]

# CAGR
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

# Title
st.title("🌍 Global GDP per Capita – Interactive Dashboard")

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Countries Selected", len(countries))
col2.metric("Year Range", f"{year_range[0]} – {year_range[1]}")
col3.metric("Avg CAGR", f"{(cagr_df.CAGR.mean() * 100):.2f}%")

# Map
latest_year = filtered["Year"].max()
map_df = filtered[filtered["Year"] == latest_year]

fig_map = px.choropleth(
    map_df,
    locations="Country",
    locationmode="country names",
    color="GDP_per_capita_USD",
    hover_name="Country",
    title=f"GDP per Capita by Country ({latest_year})"
)
st.plotly_chart(fig_map, use_container_width=True)

# Trend
fig_trend = px.line(
    filtered,
    x="Year",
    y="GDP_per_capita_USD",
    color="Country",
    title="GDP per Capita Trends"
)
st.plotly_chart(fig_trend, use_container_width=True)

# CAGR bar
top_cagr = cagr_df.sort_values("CAGR", ascending=False).head(top_n)
fig_cagr = px.bar(
    top_cagr,
    x="Country",
    y="CAGR",
    title="Top Countries by CAGR"
)
st.plotly_chart(fig_cagr, use_container_width=True)

# Table + export
st.subheader("📋 Data")
st.dataframe(filtered)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    csv,
    "gdp_dashboard_export.csv",
    "text/csv"
)
