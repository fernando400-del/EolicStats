# -*- coding: utf-8 -*-
"""
Created on Fri Nov 20 11:06:45 2025
@author: foceguera
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

st.set_page_config(
    page_title="EolicStats",
    page_icon=":chart_with_upwards_trend:",
    layout="wide",
)

"""
# :material/query_stats: EolicStats

Estadísticas eólicas: Recurso (test)
"""

""  
cols = st.columns([1, 3])

SENSORS = ["Ane", "Vta", "Temp", "Hum"]

DEFAULT_SENSORS = ["Ane", "Vta"]


def stats_to_str(sensors):
    return ",".join(sensors)

if "sensors_input" not in st.session_state:
    st.session_state.sensors_input = st.query_params.get(
        "sensors", stats_to_str(DEFAULT_SENSORS)).split(",")


# Callback to update query param when input changes
def update_query_param():
    if st.session_state.sensors_input:
        st.query_params["sensors"] = stats_to_str(st.session_state.sensors_input)
    else:
        st.query_params.pop("sensors", None)


# top_left_cell = cols[0].container(
#     border=True, height="stretch", vertical_alignment="center")

top_left_cell = cols[0].container(
    border=True, height="stretch", vertical_alignment="center")



with top_left_cell:
    # Selectbox for stock sensors
    sensors = st.multiselect(
        "Sensores",
        options=sorted(set(SENSORS) | set(st.session_state.sensors_input)),
        default=st.session_state.sensors_input,
        placeholder="Selecciona al menos un sensor. Ejemplo: Ane",
        accept_new_options=True)

# Time horizon selector
horizon_map = {
    "1 Months": "1mo",
    "3 Months": "3mo",
    "6 Months": "6mo",
    "1 Year": "1y",
    "5 Years": "5y",
    "10 Years": "10y",
    "20 Years": "20y"}

with top_left_cell:
    # Buttons for picking time horizon
    horizon = st.pills(
        "Time horizon",
        options=list(horizon_map.keys()),
        default="6 Months")

sensors = [t.upper() for t in sensors]

# Update query param when text input changes
if sensors:
    st.query_params["stats"] = stats_to_str(sensors)
else:
    # Clear the param if input is empty
    st.query_params.pop("stats", None)

if not sensors:
    top_left_cell.info("Selecciona al menos un sensor", icon=":material/info:")
    st.stop()


right_cell = cols[1].container(
    border=True, height="stretch", vertical_alignment="center"
)


@st.cache_resource(show_spinner=False, ttl="6h")
def load_data(sensors, period):
    sensors_obj = yf.Sensors(sensors)
    data = sensors_obj.history(period=period)
    if data is None:
        raise RuntimeError("YFinance returned no data.")
    return data["Close"]


# Load the data
try:
    data = load_data(sensors, horizon_map[horizon])
except yf.exceptions.YFRateLimitError as e:
    st.warning("YFinance is rate-limiting us :(\nTry again later.")
    load_data.clear()  # Remove the bad cache entry.
    st.stop()

empty_columns = data.columns[data.isna().all()].tolist()

if empty_columns:
    st.error(f"Error loading data for sensors: {', '.join(empty_columns)}.")
    st.stop()

# Normalize prices (start at 1)
normalized = data.div(data.iloc[0])

latest_norm_values = {normalized[sensor].iat[-1]: sensor for sensor in sensors}
max_norm_value = max(latest_norm_values.items())
min_norm_value = min(latest_norm_values.items())

bottom_left_cell = cols[0].container(
    border=True, height="stretch", vertical_alignment="center")

with bottom_left_cell:
    cols = st.columns(2)
    cols[0].metric(
        "Best sensor",
        max_norm_value[1],
        delta=f"{round(max_norm_value[0] * 100)}%",
        width="content")
    cols[1].metric(
        "Worst sensor",
        min_norm_value[1],
        delta=f"{round(min_norm_value[0] * 100)}%",
        width="content")


# Plot normalized stats
with right_cell:
    st.altair_chart(
        alt.Chart(
            normalized.reset_index().melt(
                id_vars=["Date"], var_name="Stats", value_name="Normalized value"))
        .mark_line()
        .encode(
            alt.X("Date:T"),
            alt.Y("Normalized value:Q").scale(zero=False),
            alt.Color("Stock:N")).properties(height=400))

""
""

# Plot individual sensor vs peer average
"""
## Individual stocks vs peer average

For the analysis below, the "peer average" when analyzing stock X always
excludes X itself.
"""

if len(sensors) <= 1:
    st.warning("Pick 2 or more tickers to compare them")
    st.stop()

NUM_COLS = 4
cols = st.columns(NUM_COLS)

for i, sensor in enumerate(sensors):
    # Calculate peer average (excluding current stat)
    peers = normalized.drop(columns=[sensor])
    peer_avg = peers.mean(axis=1)

    # Create DataFrame with peer average.
    plot_data = pd.DataFrame(
        {
            "Date": normalized.index,
            sensor: normalized[sensor],
            "Peer average": peer_avg,
        }
    ).melt(id_vars=["Date"], var_name="Series", value_name="Price")

    chart = (
        alt.Chart(plot_data)
        .mark_line()
        .encode(
            alt.X("Date:T"),
            alt.Y("Price:Q").scale(zero=False),
            alt.Color(
                "Series:N",
                scale=alt.Scale(domain=[sensor, "Peer average"], range=["red", "gray"]),
                legend=alt.Legend(orient="bottom"),
            ),
            alt.Tooltip(["Date", "Series", "Price"]),
        )
        .properties(title=f"{sensor} vs peer average", height=300)
    )

    cell = cols[(i * 2) % NUM_COLS].container(border=True)
    cell.write("")
    cell.altair_chart(chart, use_container_width=True)

    # Create Delta chart
    plot_data = pd.DataFrame(
        {
            "Date": normalized.index,
            "Delta": normalized[sensor] - peer_avg,
        }
    )

    chart = (
        alt.Chart(plot_data)
        .mark_area()
        .encode(
            alt.X("Date:T"),
            alt.Y("Delta:Q").scale(zero=False),
        )
        .properties(title=f"{sensor} minus peer average", height=300)
    )

    cell = cols[(i * 2 + 1) % NUM_COLS].container(border=True)
    cell.write("")
    cell.altair_chart(chart, use_container_width=True)

""
""

"""
## Raw data
"""

data 
