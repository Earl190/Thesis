import streamlit as st
import pandas as pd
import numpy as np 
import time

from datetime import datetime
from db_connection import upload_csv_data

def get_live_sensor_data():
    if not st.session_state.get("sensor_log"):
        return pd.DataFrame(
            columns=[
                "date", "sim_time", "mass_time", "attendance",
                "foot_traffic_count", "capacity", "event_type",
                "year", "holiday_flag", "weather_condition",
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

def show_sensor_page():
    st.title("Live Sensor Feed & Alert System")
    st.markdown("Simulating real-time D3.js/IoT threshold sensor data using a predictive Normal Distribution curve.")

    sensor_col, alert_col = st.columns([1, 2])

    st.divider()
    st.subheader("Database Synchronization")
    st.caption("Push the finalized simulation data to SQL Server. This makes it available to your sidebar filters and historical dashboards.")

    if st.button("Sync Final Data to Database", type="primary"):
        final_live_df = get_live_sensor_data()
        
        if not final_live_df.empty:
            final_record_df = final_live_df.tail(1).copy()
            final_record_df["mass_time"] = st.session_state.get("selected_mass_time", "08:00")
            final_record_df["event_type"] = st.session_state.get("selected_event_type", "Regular Mass")
           
            foot_traffic = final_record_df["foot_traffic_count"].iloc[0]
            noise_factor = np.random.normal(loc=0.95, scale=0.04)
            noise_factor = min(1.0, max(0.80, noise_factor))
            
            final_record_df["attendance"] = int(foot_traffic * noise_factor)
            
            success, msg = upload_csv_data(final_record_df)
            
            if success:
                st.success(f"Data synced directly to database! {msg}")
                st.info("The main dashboard sidebar filters will now detect this event upon refresh.")
                
                st.cache_data.clear()
            else:
                st.error(f"Database sync failed: {msg}")
        else:
            st.warning("No data generated yet. Run the simulation first.")

    with sensor_col:
        st.subheader("Sensor Controls")
        st.session_state.selected_mass_time = st.selectbox(
            "Mass Time for Simulation",
            ["06:00", "08:00", "10:00", "12:00", "3:00", "5:00", "7:00"],
            index=1,
        )
        st.session_state.selected_event_type = st.selectbox(
            "Event Type",
            ["Regular Mass", "Sunday Mass", "Wedding", "Funeral", "Holiday Mass"],
            index=0,
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
                st.session_state.sensor_increments = []
                st.session_state.sim_time_minutes = -60

        live_count_placeholder = st.empty()
        timeline_placeholder = st.empty()

    with alert_col:
        st.subheader("Live Dashboard Analytics")
        alert_placeholder = st.empty()
        bar_chart_placeholder = st.empty()
        line_chart_placeholder = st.empty()

    def update_ui_placeholders():
        max_cap = st.session_state.get('max_capacity', 500)
        current_count = st.session_state.get('live_count', 0)
        current_time = st.session_state.get('sim_time_minutes', -60)
        
        live_count_placeholder.metric(
            "Live Occupancy Count",
            f"{current_count} / {max_cap}",
            help="This shows how many people are currently counted inside the church during the simulation."
        )
        
        sim_time_str = f"T {current_time} mins" if current_time <= 0 else f"T +{current_time} mins"
        timeline_placeholder.metric("Simulation Timeline", sim_time_str)

        occupancy_rate = (current_count / max_cap) if max_cap > 0 else 0
        with alert_placeholder.container():
            if occupancy_rate >= 1.0:
                st.error("CRITICAL ALERT: Maximum capacity reached or exceeded.")
            elif occupancy_rate >= 0.85:
                st.warning(f"WARNING: Capacity is nearing the limit ({int(occupancy_rate * 100)}% full).")
            elif occupancy_rate >= 0.50:
                st.info(f"Notice: The church is filling up steadily ({int(occupancy_rate * 100)}% full).")
            else:
                st.success("Status Normal: Capacity is currently at safe, comfortable levels.")

        live_df = get_live_sensor_data()
        increments_df = pd.DataFrame(st.session_state.get('sensor_increments', []))

        if not increments_df.empty:
            with bar_chart_placeholder.container():
                st.markdown("**Sensor Detections per Minute (Arrival Rate)**")
                st.caption("This graph shows how many people entered the church during each minute of the simulation.")
                st.bar_chart(increments_df, x="sim_time", y="arrivals", height=300)

        if not live_df.empty:
            with line_chart_placeholder.container():
                st.markdown("**Cumulative Attendance Over Time**")
                st.caption("This graph shows the total number of people inside the church as the simulation continues.")
                
                chart_data = live_df[["sim_time", "foot_traffic_count"]].copy()
                chart_data["Max Capacity"] = max_cap
                
                st.line_chart(
                    chart_data, 
                    x="sim_time", 
                    y=["foot_traffic_count", "Max Capacity"],
                    height=300,
                    color=["#8ab4f8", "#ff6d6d"] 
                )
        elif not st.session_state.get("simulation_running", False):
            with line_chart_placeholder.container():
                st.info("No live sensor data yet. Click 'Start' to begin the fast-forward simulation.")

    update_ui_placeholders()

    if st.session_state.get("simulation_running", False):
        while st.session_state.simulation_running:
            
            t = st.session_state.get('sim_time_minutes', -60)
            max_cap = st.session_state.get('max_capacity', 500)
            
            if t <= 30:
                mean = -5
                std_dev = 15
                expected_total = max_cap * 0.85
                prob = (1 / (std_dev * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((t - mean) / std_dev) ** 2)
                noise_factor = np.random.uniform(0.7, 1.3)
                
                increment = int(expected_total * prob * noise_factor)
                increment = max(0, increment)
                
                st.session_state.live_count = st.session_state.get('live_count', 0) + increment
                if st.session_state.live_count > max_cap:
                    st.session_state.live_count = max_cap

                now = datetime.now()
                st.session_state.sensor_increments.append({"sim_time": t, "arrivals": increment})
                st.session_state.sensor_log.append({
                    "date": now, 
                    "sim_time": t, 
                    "mass_time": st.session_state.get("selected_mass_time", "08:00"),
                    "attendance": st.session_state.live_count, 
                    "foot_traffic_count": st.session_state.live_count,
                    "capacity": max_cap, 
                    "event_type": st.session_state.get("selected_event_type", "Regular Mass"),
                    "holiday_flag": 0, 
                    "weather_condition": "Clear",
                })
                
                st.session_state.sim_time_minutes += 1
            else:
                st.session_state.simulation_running = False

            update_ui_placeholders()
            
            time.sleep(0.5)