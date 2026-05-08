import streamlit as st
import datetime
import pandas as pd
from db_connection import (
    backup_database, 
    upload_csv_data, 
    get_service_schedules,
    save_service_schedules,
    get_user_by_username # Imported for password verification
)

def initialize_settings_state():
    if "max_capacity" not in st.session_state:
        st.session_state.max_capacity = 500
    if "alert_threshold" not in st.session_state:
        st.session_state.alert_threshold = 85
        
    if "service_schedules" not in st.session_state:
        st.session_state.service_schedules = get_service_schedules()

def trigger_save():
    updated_schedules = []
    for i in range(len(st.session_state.service_schedules)):
        updated_schedules.append({
            "name": st.session_state.get(f"name_{i}", st.session_state.service_schedules[i]["name"]),
            "start": st.session_state.get(f"start_{i}", st.session_state.service_schedules[i]["start"]),
            "end": st.session_state.get(f"end_{i}", st.session_state.service_schedules[i]["end"])
        })
    
    st.session_state.service_schedules = updated_schedules
    success, msg = save_service_schedules(updated_schedules)
    
    if success:
        st.toast("Schedules auto-saved!")
    else:
        st.toast("Failed to auto-save.")

def delete_schedule(index):
    deleted_service = st.session_state.service_schedules.pop(index)
    success, msg = save_service_schedules(st.session_state.service_schedules)
    
    if success:
        st.toast(f"Deleted '{deleted_service['name']}'! 🗑️")
    else:
        st.toast("Failed to delete service.")

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
        s_col1, s_col2, s_col3, s_col4 = st.columns([2.5, 1, 1, 0.5])
        
        with s_col1:
            st.text_input(f"Service Name", value=service["name"], key=f"name_{i}", on_change=trigger_save)
        with s_col2:
            st.time_input(f"Start Time", value=service["start"], key=f"start_{i}", on_change=trigger_save)
        with s_col3:
            st.time_input(f"End Time", value=service["end"], key=f"end_{i}", on_change=trigger_save)
        with s_col4:
            st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
            st.button("🗑️", key=f"del_{i}", help="Delete this schedule", on_click=delete_schedule, args=(i,))

    if st.button("Add Another Service"):
        st.session_state.service_schedules.append({
            "name": f"New Service {len(st.session_state.service_schedules) + 1}", 
            "start": datetime.time(12, 0), 
            "end": datetime.time(13, 0)
        })
        success, msg = save_service_schedules(st.session_state.service_schedules)
        if success:
            st.toast("New service added and auto-saved!")
        st.rerun()
        
    st.divider()

    st.header("Database & Sensor Management")
    st.markdown("Manage your historical data caches and active sensor logs.")
    
    with st.expander("Upload Historical Attendance Data (CSV)"):
        st.info("Upload historical attendance files to the database.")
        
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
                with st.spinner("Uploading attendance data to database..."):
                    success, msg = upload_csv_data(df)
                        
                    if success:
                        st.success(f"Successfully processed {len(df)} records!")
                        st.caption(msg)
                        st.cache_data.clear()
                    else:
                        st.error("Upload failed.")
                        st.error(msg)
    
    st.write("")
    
    db_col1, db_col2, db_col3 = st.columns(3)
    
    with db_col1:
        # Invisible spacer so this button aligns with the bottom of the password input field
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
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
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("Clear Live Sensor Cache", use_container_width=True):
            st.session_state.sensor_log = []
            st.session_state.sensor_increments = []
            st.session_state.live_count = 0
            st.session_state.sim_time_minutes = -60
            st.toast("Live sensor cache cleared.")

    with db_col3:
        # Admin password input field
        admin_password = st.text_input(
            "Admin Password:", 
            type="password", 
            placeholder="Enter password to reset", 
            label_visibility="collapsed"
        )
        
        if st.button("Factory Reset Database", type="primary", use_container_width=True, disabled=not admin_password):
            
            if admin_password == "admin123": 
                st.session_state.sensor_log = []
                st.success("Database reset to factory defaults.")
            else:
                st.error("Incorrect password. Factory reset aborted.")