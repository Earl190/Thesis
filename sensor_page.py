import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np 

from db_connection import upload_csv_data

def get_live_sensor_data():
    if not st.session_state.sensor_log:
        return pd.DataFrame(
            columns=[
                "date",
                "sim_time",
                "mass_time",
                "attendance",
                "foot_traffic_count",
                "capacity",
                "event_type",
                "year",
                "holiday_flag",
                "weather_condition",
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
            
            final_record_df["mass_time"] = st.session_state.selected_mass_time
            final_record_df["event_type"] = st.session_state.selected_event_type
            
           
            foot_traffic = final_record_df["foot_traffic_count"].iloc[0]
            
            noise_factor = np.random.normal(loc=0.95, scale=0.04)
            
            noise_factor = min(1.0, max(0.80, noise_factor))
            
            final_record_df["attendance"] = int(foot_traffic * noise_factor)
            
            success, msg = upload_csv_data(final_record_df)
            
            if success:
                st.success(f"Data synced directly to database! {msg}")
                st.info("The main dashboard sidebar filters will now detect this event upon refresh.")
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

        st.metric(
            "Live Occupancy Count",
            f"{st.session_state.live_count} / {st.session_state.max_capacity}",
            help="This shows how many people are currently counted inside the church during the simulation."
        )
        st.metric(
            "Simulation Timeline",
            f"T {st.session_state.sim_time_minutes} mins"
            if st.session_state.sim_time_minutes <= 0
            else f"T +{st.session_state.sim_time_minutes} mins",
            help="This shows the simulated time before or after the start of the service."
        )

    with alert_col:
        st.subheader("Live Dashboard Analytics")
        occupancy_rate = (
            st.session_state.live_count / st.session_state.max_capacity
            if st.session_state.max_capacity > 0
            else 0
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
        increments_df = pd.DataFrame(st.session_state.sensor_increments)

        if not increments_df.empty:
            st.caption("This graph shows how many people entered the church during each minute of the simulation.")

            fig_bar = px.bar(
                increments_df,
                x="sim_time",
                y="arrivals",
                title="Sensor Detections per Minute (Arrival Rate)",
                labels={
                    "sim_time": "Minutes relative to Service Start (0)",
                    "arrivals": "People Entering"
                },
            )

            fig_bar.update_traces(
                hovertemplate=
                "<b>Minute:</b> %{x}<br>"
                "<b>People Entering:</b> %{y}<br>"
                "<extra></extra>"
            )

            fig_bar.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_bar, use_container_width=True)

        if not live_df.empty:
            st.caption("This graph shows the total number of people inside the church as the simulation continues.")

            fig_line = px.line(
                live_df,
                x="sim_time",
                y="foot_traffic_count",
                title="Cumulative Attendance Over Time",
                labels={
                    "sim_time": "Minutes relative to Service Start (0)",
                    "foot_traffic_count": "Total Inside"
                },
            )

            fig_line.update_traces(
                hovertemplate=
                "<b>Minute:</b> %{x}<br>"
                "<b>Total Inside:</b> %{y}<br>"
                "<extra></extra>"
            )

            fig_line.add_hline(
                y=st.session_state.max_capacity,
                line_dash="dot",
                annotation_text="Max Capacity",
                annotation_position="bottom right",
            )

            fig_line.update_layout(height=300, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("No live sensor data yet. Click 'Start' to begin the fast-forward simulation.")