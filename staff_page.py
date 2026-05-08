import streamlit as st
import pandas as pd
import plotly.express as px
from db_connection import get_service_schedules, save_service_schedules 

def handle_acknowledgment(sched_name, user_name):
    db_schedules = get_service_schedules()
    
    for sched in db_schedules:
        if sched.get("name") == sched_name:
            if "acknowledged_by" not in sched:
                sched["acknowledged_by"] = []
                
            if user_name not in sched["acknowledged_by"]:
                sched["acknowledged_by"].append(user_name)
    
    save_service_schedules(db_schedules)
    st.cache_data.clear()

def show_staff_dashboard(data):
    st.title("Church Staff Portal")
    
    current_name = st.session_state.get("current_user_name", "Staff Member")
    st.markdown(f"Welcome, **{current_name}**. Here is the recent attendance overview.")
    
    db_schedules = get_service_schedules()
    
    unacknowledged_schedules = []
    acknowledged_schedules = []
    
    for sched in db_schedules:
        if "acknowledged_by" not in sched:
            sched["acknowledged_by"] = []
            
        if current_name not in sched["acknowledged_by"]:
            unacknowledged_schedules.append(sched)
        else:
            acknowledged_schedules.append(sched)

    st.sidebar.divider()
    st.sidebar.subheader("Pending Acknowledgments")
    
    if unacknowledged_schedules:
        st.sidebar.warning(f"You have {len(unacknowledged_schedules)} pending tasks.")
        
        # --- FIX APPLIED HERE: Added enumerate to ensure unique keys ---
        for i, sched in enumerate(unacknowledged_schedules):
            with st.sidebar.expander(f"⚠️ {sched['name']}", expanded=True):
                st.write(f"**Time:** {sched['start']} - {sched['end']}")
                st.write("Ensure monitoring systems are prepared.")
                
                st.button(
                    "Acknowledge", 
                    key=f"ack_{sched['name']}_{i}", # <--- Unique key generated here
                    on_click=handle_acknowledgment,
                    args=(sched['name'], current_name),
                    width='stretch'
                )
    else:
        st.sidebar.success("You are caught up! No new schedules.")
        
    # --- SIDEBAR: FILTERS ---
    st.sidebar.divider()
    st.sidebar.header("Dashboard Filters")

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

    # --- MAIN VIEW: METRICS ---
    with st.container(border=True):
        st.subheader("Attendance Overview")
        col1, col2, col3 = st.columns(3)
        
        avg_attendance = int(filtered_data["attendance"].mean()) if not filtered_data.empty else 0
        max_attendance = int(filtered_data["attendance"].max()) if not filtered_data.empty else 0
        
        if not filtered_data.empty and "event_type" in filtered_data.columns:
            latest_event = filtered_data.sort_values("date").iloc[-1]["event_type"]
        else:
            latest_event = "N/A"

        col1.metric("Average Attendance", avg_attendance)
        col2.metric("Highest Recorded", max_attendance)
        col3.metric("Latest Event Logged", latest_event)

    with st.container(border=True):
        st.subheader("Acknowledgment History")
        if acknowledged_schedules:
            history_records = []
            for sched in acknowledged_schedules:
                history_records.append({
                    "Event Name": sched.get("name", "Unknown"),
                    "Start Time": sched.get("start", "N/A"),
                    "End Time": sched.get("end", "N/A"),
                    "Acknowledged By": ", ".join(sched.get("acknowledged_by", []))
                })
            
            df_history = pd.DataFrame(history_records)
            st.dataframe(df_history, width='stretch', hide_index=True)
        else:
            st.info("You haven't acknowledged any schedules yet.")

    if filtered_data.empty:
        st.info("No attendance data available for the selected filters.")
        return

    with st.container(border=True):
        st.subheader("Attendance Trends")
        left_col, right_col = st.columns(2)

        with left_col:
            st.caption("Recent Attendance Trends")
            daily_trend = filtered_data.groupby(filtered_data["date"].dt.date)["attendance"].mean().reset_index()
            daily_trend["date"] = pd.to_datetime(daily_trend["date"]) 
            
            fig_line = px.line(
                daily_trend, 
                x="date", 
                y="attendance", 
                markers=True
            )
            
            fig_line.update_xaxes(rangeslider_visible=True)
            
            fig_line.update_layout(height=400)
            st.plotly_chart(fig_line, width='stretch')

        with right_col:
            st.caption("Attendance by Event Type")
            if "event_type" in filtered_data.columns:
                event_summary = filtered_data.groupby("event_type", as_index=False)["attendance"].mean()
                fig_bar = px.bar(
                    event_summary, 
                    x="event_type", 
                    y="attendance"
                )
                
                fig_bar.update_xaxes(rangeslider_visible=True)
                
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, width='stretch')
            else:
                st.info("Event type data not available.")

    with st.container(border=True):
        st.subheader("Recent Automated Sensor Logs")
        st.caption("Data is logged automatically. Contact the System Administrator for any discrepancies.")
        
        available_cols = filtered_data.columns.tolist()
        display_cols = [c for c in ["date", "mass_time", "event_type", "attendance", "foot_traffic_count", "capacity"] if c in available_cols]
        
        staff_df = filtered_data[display_cols].sort_values("date", ascending=False).head(50) 
        
        st.dataframe(staff_df, width='stretch', hide_index=True)