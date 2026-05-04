import streamlit as st
import pandas as pd
import plotly.express as px

def show_staff_dashboard(data):
    st.title("Church Staff Portal")
    
    current_name = st.session_state.get("current_user_name", "Staff Member")
    st.markdown(f"Welcome, **{current_name}**. Here is the recent attendance overview.")
    
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

    st.divider()

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

    st.divider()

    if filtered_data.empty:
        st.info("No attendance data available for the selected filters.")
        return

    left_col, right_col = st.columns(2)

    with left_col:
        st.caption("Recent Attendance Trends")
        daily_trend = filtered_data.groupby(filtered_data["date"].dt.date)["attendance"].mean().reset_index()
        daily_trend["date"] = pd.to_datetime(daily_trend["date"]) 
        
        fig_line = px.line(
            daily_trend, 
            x="date", 
            y="attendance", 
            markers=True,
            title="Daily Attendance Overview"
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with right_col:
        st.caption("Attendance by Event Type")
        if "event_type" in filtered_data.columns:
            event_summary = filtered_data.groupby("event_type", as_index=False)["attendance"].mean()
            fig_bar = px.bar(
                event_summary, 
                x="event_type", 
                y="attendance",
                title="Average Turnout per Event"
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Event type data not available.")

    st.divider()

    
    st.subheader("Recent Automated Sensor Logs")
    st.caption("Data is logged automatically. Contact the System Administrator for any discrepancies.")
    
    available_cols = filtered_data.columns.tolist()
    display_cols = [c for c in ["date", "mass_time", "event_type", "attendance", "foot_traffic_count", "capacity"] if c in available_cols]
    
    staff_df = filtered_data[display_cols].sort_values("date", ascending=False).head(50) 
    
    st.dataframe(staff_df, use_container_width=True, hide_index=True)