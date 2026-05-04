import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="Church Attendance Monitoring System", layout="wide")

if "live_count" not in st.session_state:
    st.session_state.live_count = 0

if "max_capacity" not in st.session_state:
    st.session_state.max_capacity = 500

if "simulation_running" not in st.session_state:
    st.session_state.simulation_running = False

if "sensor_log" not in st.session_state:
    st.session_state.sensor_log = []

if "selected_event_type" not in st.session_state:
    st.session_state.selected_event_type = "Regular Mass"

if "selected_mass_time" not in st.session_state:
    st.session_state.selected_mass_time = "08:00"

@st.cache_data
def load_data():
    files = [
        "church_attendance_2020.csv",
        "church_attendance_2021.csv",
        "church_attendance_2022.csv",
        "church_attendance_2023.csv",
        "church_attendance_2024.csv",
        "church_attendance_2025.csv"
    ]

    df_list = [pd.read_csv(file) for file in files]
    df = pd.concat(df_list, ignore_index=True)

    df.columns = df.columns.str.strip().str.lower()

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])

    df["year"] = df["date"].dt.year

    return df

def get_live_sensor_data():
    if not st.session_state.sensor_log:
        return pd.DataFrame(columns=[
            "date",
            "mass_time",
            "attendance",
            "foot_traffic_count",
            "capacity",
            "event_type",
            "year"
        ])
    df = pd.DataFrame(st.session_state.sensor_log)
    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])
    df["year"] = df["date"].dt.year
    return df


def get_combined_data():
    historical_data = load_data()
    live_data = get_live_sensor_data()
    combined = pd.concat([historical_data, live_data], ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"], format="mixed", errors="coerce")
    combined = combined.dropna(subset=["date"])
    combined["year"] = combined["date"].dt.year
    combined = combined.sort_values("date")
    return combined


def update_sensor_simulation():
    if st.session_state.simulation_running:
        increment = np.random.randint(5, 25)
        st.session_state.live_count += increment

        if st.session_state.live_count > st.session_state.max_capacity:
            st.session_state.live_count = st.session_state.max_capacity

        now = datetime.now()

        st.session_state.sensor_log.append({
            "date": now,
            "mass_time": st.session_state.selected_mass_time,
            "attendance": st.session_state.live_count,
            "foot_traffic_count": st.session_state.live_count,
            "capacity": st.session_state.max_capacity,
            "event_type": st.session_state.selected_event_type
        })


def prepare_aggregated_data(df):
    df = df.copy()

    if df.empty:
        daily_data = pd.DataFrame(columns=["date", "attendance", "foot_traffic_count", "capacity"])
        monthly_data = pd.DataFrame(columns=["date", "attendance", "foot_traffic_count", "capacity"])
        return daily_data, monthly_data

    df["date"] = pd.to_datetime(df["date"], format="mixed", errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    daily_data = (
        df.groupby("date", as_index=False)
        .agg({
            "attendance": "mean",
            "foot_traffic_count": "mean",
            "capacity": "mean"
        })
    )

    monthly_data = (
        df.groupby(df["date"].dt.to_period("M"))
        .agg({
            "attendance": "mean",
            "foot_traffic_count": "mean",
            "capacity": "mean"
        })
        .reset_index()
    )

    monthly_data["date"] = monthly_data["date"].astype(str)

    return daily_data, monthly_data

if st.session_state.simulation_running:
    st_autorefresh(interval=2000, key="sensor_refresh")
    update_sensor_simulation()

data = get_combined_data()
st.sidebar.title("Navigation Bar")
page = st.sidebar.radio("Go to:", [
    "HOME",
    "Attendance Records",
    "Sensor",
    "Predicted Insights",
    "Reports and Exports",
    "Settings"
])

st.sidebar.divider()
st.sidebar.header("Dashboard Filters")

selected_service = st.sidebar.selectbox(
    "Select Service Time",
    ["All Services"] + sorted(data["mass_time"].dropna().unique().tolist())
)

years = sorted(data["year"].dropna().unique().tolist())
selected_year = st.sidebar.multiselect(
    "Select Year",
    options=years,
    default=years
)

selected_event = st.sidebar.multiselect(
    "Event Type",
    options=sorted(data["event_type"].dropna().unique().tolist()),
    default=sorted(data["event_type"].dropna().unique().tolist())
)

filtered_data = data.copy()

if selected_service != "All Services":
    filtered_data = filtered_data[filtered_data["mass_time"] == selected_service]

filtered_data = filtered_data[
    (filtered_data["year"].isin(selected_year)) &
    (filtered_data["event_type"].isin(selected_event))
]

filtered_data = filtered_data.sort_values("date")
daily_data, monthly_data = prepare_aggregated_data(filtered_data)

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
            monthly_data,
            x="date",
            y="attendance",
            markers=True,
            title="Monthly Average Attendance Overview"
        )
        fig_home.update_layout(
            xaxis_title="Month",
            yaxis_title="Average Attendance",
            hovermode="x unified"
        )
        st.plotly_chart(fig_home, use_container_width=True)
    else:
        st.info("No data available for the selected filters.")

elif page == "Attendance Records":
    st.title("Attendance Records")
    st.markdown("Interactive analytics of church attendance.")

    chart_view = st.selectbox(
        "Select chart view",
        ["Monthly Average Attendance", "Daily Average Attendance", "Monthly Total Attendance"]
    )

    col1, col2 = st.columns(2)

    with col1:
        if chart_view == "Monthly Average Attendance":
            if not monthly_data.empty:
                fig_line = px.line(
                    monthly_data,
                    x="date",
                    y="attendance",
                    markers=True,
                    title="Monthly Average Attendance"
                )
                fig_line.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Average Attendance",
                    hovermode="x unified"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No monthly data available.")

        elif chart_view == "Daily Average Attendance":
            if not daily_data.empty:
                fig_line = px.line(
                    daily_data,
                    x="date",
                    y="attendance",
                    markers=True,
                    title="Daily Average Attendance"
                )
                fig_line.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Average Attendance",
                    hovermode="x unified"
                )
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.info("No daily data available.")

        elif chart_view == "Monthly Total Attendance":
            if not filtered_data.empty:
                monthly_total = (
                    filtered_data.groupby(filtered_data["date"].dt.to_period("M"))["attendance"]
                    .sum()
                    .reset_index()
                )
                monthly_total["date"] = monthly_total["date"].astype(str)

                fig_bar = px.bar(
                    monthly_total,
                    x="date",
                    y="attendance",
                    title="Monthly Total Attendance"
                )
                fig_bar.update_layout(
                    xaxis_title="Month",
                    yaxis_title="Total Attendance"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No attendance data available.")

    with col2:
        if not filtered_data.empty:
            fig_scatter = px.scatter(
                filtered_data,
                x="foot_traffic_count",
                y="attendance",
                color="event_type",
                title="Foot Traffic vs Attendance",
                trendline="ols"
            )
            fig_scatter.update_layout(
                xaxis_title="Foot Traffic Count",
                yaxis_title="Attendance"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.info("No data available for regression graph.")

    st.divider()

    col3, col4 = st.columns(2)

    with col3:
        if not filtered_data.empty:
            fig_hist = px.histogram(
                filtered_data,
                x="attendance",
                nbins=20,
                title="Attendance Distribution"
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        else:
            st.info("No data available for attendance distribution.")

    with col4:
        if not filtered_data.empty:
            fig_box = px.box(
                filtered_data,
                x="event_type",
                y="attendance",
                title="Attendance by Event Type"
            )
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            st.info("No data available for event type comparison.")

    with st.expander("View Raw Data"):
        st.dataframe(filtered_data, use_container_width=True)

elif page == "Sensor":
    st.title("Live Sensor Feed & Alert System")
    st.markdown("Simulating real-time data from entrance threshold sensors.")

    sensor_col, alert_col = st.columns([1, 2])

    with sensor_col:
        st.subheader("Sensor Controls")

        st.session_state.selected_mass_time = st.selectbox(
            "Mass Time for Simulation",
            ["06:00", "08:00", "10:00", "12:00", "15:00", "17:00", "19:00"],
            index=1
        )

        st.session_state.selected_event_type = st.selectbox(
            "Event Type for Simulation",
            ["Regular Mass", "Sunday Mass", "Wedding", "Funeral", "Holiday Mass", "Special Event"],
            index=0
        )

        btn1, btn2, btn3 = st.columns(3)

        with btn1:
            if st.button("Start"):
                st.session_state.simulation_running = True

        with btn2:
            if st.button("Pause"):
                st.session_state.simulation_running = False

        with btn3:
            if st.button("Reset"):
                st.session_state.simulation_running = False
                st.session_state.live_count = 0
                st.session_state.sensor_log = []

        st.metric(
            "Live Occupancy Count",
            f"{st.session_state.live_count} / {st.session_state.max_capacity}"
        )

    with alert_col:
        st.subheader("System Status")

        occupancy_rate = (
            st.session_state.live_count / st.session_state.max_capacity
            if st.session_state.max_capacity > 0 else 0
        )

        if occupancy_rate >= 1.0:
            st.error("CRITICAL ALERT: Maximum capacity reached or exceeded.")
        elif occupancy_rate >= 0.85:
            st.warning(f"WARNING: Capacity is nearing the limit ({int(occupancy_rate * 100)}% full).")
        elif occupancy_rate >= 0.50:
            st.info(f"Notice: The church is filling up steadily ({int(occupancy_rate * 100)}% full).")
        else:
            st.success("Status Normal: Capacity is currently at safe, comfortable levels.")

        live_df = get_live_sensor_data()

        if not live_df.empty:
            fig_live = px.line(
                live_df,
                x="date",
                y="foot_traffic_count",
                markers=True,
                title="Live Sensor Foot Traffic"
            )
            fig_live.update_layout(
                xaxis_title="Time",
                yaxis_title="Foot Traffic Count",
                hovermode="x unified"
            )
            st.plotly_chart(fig_live, use_container_width=True)
        else:
            st.info("No live sensor data yet. Start the simulation.")

elif page == "Predicted Insights":
    st.title("Predicted Insights")
    st.markdown("Simple Linear Regression based on foot traffic count.")

    model_data = filtered_data.dropna(subset=["foot_traffic_count", "attendance"]).copy()

    if len(model_data) >= 2:
        X = model_data[["foot_traffic_count"]]
        y = model_data["attendance"]

        model = LinearRegression()
        model.fit(X, y)

        y_pred = model.predict(X)
        r2 = r2_score(y, y_pred)

        col1, col2, col3 = st.columns(3)
        col1.metric("Slope", f"{model.coef_[0]:.2f}")
        col2.metric("Intercept", f"{model.intercept_:.2f}")
        col3.metric("R² Score", f"{r2:.3f}")

        st.subheader("Regression Graph")

        fig_reg = px.scatter(
            model_data,
            x="foot_traffic_count",
            y="attendance",
            color="event_type",
            title="Simple Linear Regression: Foot Traffic vs Attendance",
            trendline="ols"
        )
        st.plotly_chart(fig_reg, use_container_width=True)

        st.subheader("Prediction Tool")

        input_traffic = st.slider(
            "Select Foot Traffic Count",
            min_value=int(model_data["foot_traffic_count"].min()),
            max_value=int(model_data["foot_traffic_count"].max()),
            value=int(model_data["foot_traffic_count"].mean())
        )

        predicted_attendance = model.predict(pd.DataFrame({"foot_traffic_count": [input_traffic]}))[0]

        st.success(
            f"Predicted attendance for foot traffic count of {input_traffic}: {predicted_attendance:.0f}"
        )
    else:
        st.warning("Not enough data to train the regression model yet.")

elif page == "Reports and Exports":
    st.title("Reports and Exports")
    st.markdown("Generate and export attendance reports.")

    st.info("Export functionality is ready.")
    csv = filtered_data.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download Attendance Data as CSV",
        data=csv,
        file_name="church_attendance_data.csv",
        mime="text/csv",
    )

elif page == "Settings":
    st.title("Settings")
    st.markdown("Configure your dashboard parameters.")

    st.subheader("Church Capacity Configuration")
    st.session_state.max_capacity = st.number_input(
        "Set Maximum Church Capacity",
        min_value=100,
        max_value=5000,
        value=st.session_state.max_capacity,
        step=50
    )

    st.success(f"Maximum capacity is currently set to: {st.session_state.max_capacity}")