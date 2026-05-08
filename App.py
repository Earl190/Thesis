import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from datetime import datetime
from user_management import show_user_management_page
from auth import initialize_auth_state, show_auth_screen, show_first_time_setup 
from predictive_insights import show_predictive_insights
from sensor_page import show_sensor_page
from reports_page import show_reports_page
from scheduling_page import show_scheduling_page
from settings_page import show_settings_page 
from db_connection import load_attendance_data  
from staff_page import show_staff_dashboard 

st.set_page_config(page_title="Church Attendance Monitoring System (CAMS)", layout="wide")

if "live_count" not in st.session_state:
    st.session_state.live_count = 0
if "max_capacity" not in st.session_state:
    st.session_state.max_capacity = 500
if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False
if "sensor_log" not in st.session_state:
    st.session_state.sensor_log = []
if "sensor_increments" not in st.session_state:
    st.session_state.sensor_increments = []
if "sim_time_minutes" not in st.session_state:
    st.session_state.sim_time_minutes = -60
if "selected_event_type" not in st.session_state:
    st.session_state.selected_event_type = "Regular Mass"
if "selected_mass_time" not in st.session_state:
    st.session_state.selected_mass_time = "08:00"

initialize_auth_state()

@st.cache_data(ttl=300) 
def load_data():
    df = load_attendance_data()
    return df

def get_live_sensor_data():
    if not st.session_state.sensor_log:
        return pd.DataFrame(
            columns=[
                "date", "sim_time", "mass_time", "attendance", "foot_traffic_count",
                "capacity", "event_type", "year", "holiday_flag", "weather_condition",
            ]
        )
    df = pd.DataFrame(st.session_state.sensor_log)
    df["date"] = pd.to_datetime(df["date"])
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["day_of_week"] = df["date"].dt.day_name()
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)

    if "holiday_flag" not in df.columns:
        df["holiday_flag"] = 0
    if "weather_condition" not in df.columns:
        df["weather_condition"] = "Unknown"
    return df

def get_combined_data():
    historical_data = load_data()
    live_data = get_live_sensor_data()
    combined = pd.concat([historical_data, live_data], ignore_index=True)

    if not combined.empty:
        combined["date"] = pd.to_datetime(combined["date"])
        combined["year"] = combined["date"].dt.year
        combined["month"] = combined["date"].dt.month
        combined["day_of_week"] = combined["date"].dt.day_name()
        combined["is_weekend"] = combined["date"].dt.dayofweek.isin([5, 6]).astype(int)
        combined = combined.sort_values("date")
    return combined

def prepare_aggregated_data(df):
    df = df.copy()
    if df.empty:
        empty_daily = pd.DataFrame(columns=["date", "attendance", "foot_traffic_count", "capacity"])
        empty_monthly = pd.DataFrame(columns=["date", "attendance", "foot_traffic_count", "capacity"])
        return empty_daily, empty_monthly

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    daily_data = (
        df.groupby(df["date"].dt.date)
        .agg({"attendance": "mean", "foot_traffic_count": "mean", "capacity": "mean"})
        .round(0) 
        .reset_index()
    )
    daily_data["date"] = pd.to_datetime(daily_data["date"])

    monthly_data = (
        df.groupby(df["date"].dt.to_period("M"))
        .agg({"attendance": "mean", "foot_traffic_count": "mean", "capacity": "mean"})
        .round(0) 
        .reset_index()
    )
    monthly_data["date"] = monthly_data["date"].astype(str)

    return daily_data, monthly_data

if not st.session_state.logged_in:
    if st.session_state.get("needs_setup", False):
        show_first_time_setup()
    else:
        show_auth_screen()
    st.stop()

if st.session_state.get("role") == "Staff":
    st.sidebar.title("Staff Navigation")
    st.sidebar.success(f"Logged in as: {st.session_state.current_user_name}")
    st.sidebar.info("Role: Church Staff")
    
    if st.sidebar.button("Log Out", width='stretch'):
        st.session_state.logged_in = False
        st.session_state.needs_setup = False
        st.session_state.current_user = None
        st.session_state.current_user_name = None
        st.session_state.role = None
        st.rerun()
        
    data = get_combined_data() 
    show_staff_dashboard(data)
    st.stop() 

st.sidebar.title("Navigation Bar")

current_name = st.session_state.current_user_name or "User"
st.sidebar.success(f"Logged in as: {current_name}")
st.sidebar.warning("Role: Administrator") 

if st.sidebar.button("Log Out", width='stretch'):
    st.session_state.logged_in = False
    st.session_state.needs_setup = False
    st.session_state.current_user = None
    st.session_state.current_user_name = None
    st.session_state.role = None
    st.rerun()

page = st.sidebar.radio(
    "Go to:",
    [
        "HOME",
        "Attendance Records",
        "Sensor",
        "Predicted Insights",
        "Service & Event Scheduling",
        "Reports and Exports",
        "User Management",
        "Settings"
    ],
)

data = get_combined_data()

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")

services = ["All Services"]
if not data.empty and "mass_time" in data.columns:
    services += sorted(data["mass_time"].dropna().unique().tolist())
selected_service = st.sidebar.selectbox("Select Service Time", services)

years = []
if not data.empty and "year" in data.columns:
    years = sorted(data["year"].dropna().unique().tolist())
selected_year = st.sidebar.multiselect("Select Year", options=years, default=years)

events = []
if not data.empty and "event_type" in data.columns:
    events = sorted(data["event_type"].dropna().unique().tolist())
selected_event = st.sidebar.multiselect("Event Type", options=events, default=events)

filtered_data = data.copy()

if not filtered_data.empty:
    if selected_service != "All Services":
        filtered_data = filtered_data[filtered_data["mass_time"] == selected_service]
    if years:
        if len(selected_year) > 0:
            filtered_data = filtered_data[filtered_data["year"].isin(selected_year)]
        else:
            filtered_data = filtered_data.iloc[0:0]
    if events:
        if len(selected_event) > 0:
            filtered_data = filtered_data[filtered_data["event_type"].isin(selected_event)]
        else:
            filtered_data = filtered_data.iloc[0:0]

    filtered_data = filtered_data.sort_values("date")

daily_data, monthly_data = prepare_aggregated_data(filtered_data)

# --- PAGE RENDERING ---
if page == "HOME":
    st.title("Predictive Insights on Church Attendance")
    st.markdown("Welcome to the church attendance monitoring system.")

    col1, col2, col3 = st.columns(3)

    avg_attendance = int(filtered_data["attendance"].mean()) if not filtered_data.empty else 0
    max_attendance = int(filtered_data["attendance"].max()) if not filtered_data.empty else 0
    live_attendance = st.session_state.live_count

    col1.metric("Average Attendance", avg_attendance)
    col2.metric("Highest Recorded Attendance", max_attendance)
    col3.metric("Current Live Count", live_attendance)

    st.divider()

    if not monthly_data.empty:
        fig_home = px.line(
            monthly_data, x="date", y="attendance", markers=True,
            title="Monthly Average Attendance Overview",
        )
        
        # Plotly range slider handles zooming, thickness set to hide mini-graph
        fig_home.update_xaxes(rangeslider=dict(visible=True, thickness=0.02))
        st.plotly_chart(fig_home, width='stretch')
    else:
        st.info("No data available for the selected filters.")

    if not filtered_data.empty:
        low_threshold = max(filtered_data["attendance"].median() * 0.70, 1)
        latest_attendance = filtered_data.sort_values("date").iloc[-1]["attendance"]

        if latest_attendance < low_threshold:
            st.warning("Low attendance trend detected. Consider outreach, scheduling review, or event promotion.")
        else:
            st.success("Attendance trend is currently within the normal operating range.")

elif page == "Attendance Records":
    st.title("Attendance Records")

    if filtered_data.empty:
        st.info("Historical charts render here once data is loaded from the database.")
    else:
        top1, top2 = st.columns(2)

        with top1:
            fig_daily = px.line(daily_data, x="date", y="attendance", markers=True, title="Daily Attendance Trend")
            
            # Plotly range slider handles zooming, thickness set to hide mini-graph
            fig_daily.update_xaxes(rangeslider=dict(visible=True, thickness=0.02))
            st.plotly_chart(fig_daily, width='stretch')

        with top2:
            event_summary = filtered_data.groupby("event_type", as_index=False)["attendance"].mean().sort_values("attendance", ascending=False)
            fig_event = px.bar(event_summary, x="event_type", y="attendance", title="Average Attendance by Event Type")
            
            # Plotly range slider handles zooming, thickness set to hide mini-graph
            fig_event.update_xaxes(rangeslider=dict(visible=True, thickness=0.02))
            st.plotly_chart(fig_event, width='stretch')

        bottom1, bottom2 = st.columns(2)

        with bottom1:
            dow_summary = filtered_data.groupby("day_of_week", as_index=False)["attendance"].mean()
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dow_summary["day_of_week"] = pd.Categorical(dow_summary["day_of_week"], categories=order, ordered=True)
            dow_summary = dow_summary.sort_values("day_of_week")
            fig_dow = px.bar(dow_summary, x="day_of_week", y="attendance", title="Average Attendance by Day")
            
            # Plotly range slider handles zooming, thickness set to hide mini-graph
            fig_dow.update_xaxes(rangeslider=dict(visible=True, thickness=0.02))
            st.plotly_chart(fig_dow, width='stretch')

        with bottom2:
            display_cols = [c for c in ["date", "mass_time", "event_type", "attendance", "foot_traffic_count", "capacity", "weather_condition", "holiday_flag"] if c in filtered_data.columns]
            st.dataframe(filtered_data[display_cols].sort_values("date", ascending=False), width='stretch', hide_index=True)

elif page == "Sensor":
    show_sensor_page()

elif page == "Predicted Insights":
    show_predictive_insights(filtered_data)

elif page == "Service & Event Scheduling":
    show_scheduling_page(filtered_data)

elif page == "Reports and Exports":
    show_reports_page(filtered_data, monthly_data)

elif page == "User Management":            
    show_user_management_page()

elif page == "Settings":
    show_settings_page()