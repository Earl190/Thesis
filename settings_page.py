import streamlit as st
import datetime
import pandas as pd
from db_connection import backup_database, upload_csv_data, upload_demographic_data

def initialize_settings_state():
    if "max_capacity" not in st.session_state:
        st.session_state.max_capacity = 500
    if "alert_threshold" not in st.session_state:
        st.session_state.alert_threshold = 85
    if "export_format" not in st.session_state:
        st.session_state.export_format = "CSV"
    if "service_schedules" not in st.session_state:
        st.session_state.service_schedules = [
            {"name": "Morning Mass", "start": datetime.time(8, 0), "end": datetime.time(9, 0)},
            {"name": "Evening Mass", "start": datetime.time(18, 0), "end": datetime.time(19, 0)}
        ]

def show_settings_page():
    initialize_settings_state()
    
    st.title("System Settings")
    st.markdown("Configure your dashboard parameters, service schedules, and data preferences.")

    st.header("Church Capacity Thresholds")
    st.markdown("Set limits/ visual alerts when the automated sensors detect high foot traffic.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.max_capacity = st.number_input(
            "Maximum Church Capacity",
            min_value=100,
            max_value=5000,
            value=st.session_state.max_capacity,
            step=50,
            help="Set the maximum number of people allowed inside."
        )
    with col2:
        st.session_state.alert_threshold = st.slider(
            "Capacity Warning Threshold (%)",
            min_value=50,
            max_value=100,
            value=st.session_state.alert_threshold,
            step=5,
            help="Trigger a dashboard alert when attendance reaches this percentage of max capacity."
        )
    st.info(f"Alerts will trigger when live attendance reaches **{int(st.session_state.max_capacity * (st.session_state.alert_threshold / 100))}** attendees.")
    st.divider()

    st.header("Service Schedules")
    st.markdown("Define service times to accurately segment the attendance data collected by the sensors.")
    
    for i, service in enumerate(st.session_state.service_schedules):
        s_col1, s_col2, s_col3 = st.columns([2, 1, 1])
        with s_col1:
            service["name"] = st.text_input(f"Service Name", value=service["name"], key=f"name_{i}")
        with s_col2:
            service["start"] = st.time_input(f"Start Time", value=service["start"], key=f"start_{i}")
        with s_col3:
            service["end"] = st.time_input(f"End Time", value=service["end"], key=f"end_{i}")

    if st.button("Add Another Service"):
        st.session_state.service_schedules.append({
            "name": f"New Service {len(st.session_state.service_schedules) + 1}", 
            "start": datetime.time(12, 0), 
            "end": datetime.time(13, 0)
        })
        st.rerun()
    st.divider()

    st.header("Data Export Preferences")
    st.markdown("Select the default file format for downloading attendance reports and predictive insights.")
    
    st.session_state.export_format = st.radio(
        "Default Export Format",
        options=["CSV", "Excel (.xlsx)"],
        index=0 if st.session_state.export_format == "CSV" else 1,
        horizontal=True
    )
    st.divider()

    st.header("Database & Sensor Management")
    st.markdown("Manage your historical data caches and active sensor logs.")
    
    with st.expander("Upload Historical & Demographic Data (CSV)"):
        st.info("Upload historical attendance or demographic files to the database.")
        
        upload_type = st.radio(
            "Select Data Type to Upload:",
            ["Church Attendance Data", "Demographic Data"],
            horizontal=True
        )
        
        uploaded_file = st.file_uploader("Select a CSV file", type="csv")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                uploaded_file.seek(0) 
                df = pd.read_csv(uploaded_file, encoding='latin-1')
            
            st.write("Data Preview:")
            st.dataframe(df) 
            
            if st.button("Commit Records to Database", type="secondary"):
                with st.spinner(f"Uploading {upload_type.lower()} to database..."):
                    
                    if upload_type == "Church Attendance Data":
                        success, msg = upload_csv_data(df)
                    else:
                        success, msg = upload_demographic_data(df)
                        
                    if success:
                        st.success(f"Successfully processed {len(df)} records!")
                        st.caption(msg)
                    else:
                        st.error("Upload failed.")
                        st.error(msg)
    
    st.write("")
    
    db_col1, db_col2, db_col3 = st.columns(3)
    
    with db_col1:
        if st.button("Trigger Manual Backup", use_container_width=True):
            with st.spinner("Executing SQL Server Backup..."):
                success, message = backup_database()
                if success:
                    st.success("Backup successful!")
                    st.caption(f"Saved to: `{message}`")
                else:
                    st.error("Backup failed.")
                    st.error(f"Details: {message}")
            
    with db_col2:
        if st.button("Clear Live Sensor Cache", use_container_width=True):
            st.session_state.sensor_log = []
            st.session_state.sensor_increments = []
            st.session_state.live_count = 0
            st.session_state.sim_time_minutes = -60
            st.toast("Live sensor cache cleared.")

    with db_col3:
        if st.button("Factory Reset Database", type="primary", use_container_width=True):
            st.session_state.sensor_log = []
            st.toast("Database reset to factory defaults. All unsaved data lost.")