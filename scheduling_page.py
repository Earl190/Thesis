import streamlit as st
import pandas as pd
import plotly.express as px


def show_scheduling_page(filtered_data):
    st.title("Service & Event Scheduling")
    st.markdown("Plan church services and events based on attendance patterns and predicted demand.")

    if filtered_data.empty:
        st.info("No data available for scheduling recommendations. Please upload attendance CSV files first.")
        return

    scheduler_data = filtered_data.copy()
    scheduler_data["date"] = pd.to_datetime(scheduler_data["date"], errors="coerce")
    scheduler_data = scheduler_data.dropna(subset=["date"])

    if scheduler_data.empty:
        st.info("No valid dated records found for scheduling.")
        return

    st.subheader("Recommended Scheduling Insights")

    col1, col2 = st.columns(2)

    day_summary = (
        scheduler_data.groupby("day_of_week", as_index=False)["attendance"]
        .mean()
        .sort_values("attendance", ascending=False)
    )

    if not day_summary.empty:
        best_day = day_summary.iloc[0]["day_of_week"]
    else:
        best_day = "N/A"

    # Best time recommendation
    if "mass_time" in scheduler_data.columns:
        time_summary = (
            scheduler_data.groupby("mass_time", as_index=False)["attendance"]
            .mean()
            .sort_values("attendance", ascending=False)
        )
        if not time_summary.empty:
            best_time = time_summary.iloc[0]["mass_time"]
        else:
            best_time = "N/A"
    else:
        time_summary = pd.DataFrame(columns=["mass_time", "attendance"])
        best_time = "N/A"

    with col1:
        st.metric(
            "Best Day to Schedule",
            best_day,
            help="This is the day with the highest average attendance based on the selected records."
        )

    with col2:
        st.metric(
            "Best Service Time",
            best_time,
            help="This is the service time with the highest average attendance based on the selected records."
        )

    st.divider()

    left, right = st.columns(2)

    with left:
        st.caption("This chart shows the average attendance per day of the week to help choose the best day for services or events.")

        if not day_summary.empty:
            order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            day_summary["day_of_week"] = pd.Categorical(
                day_summary["day_of_week"],
                categories=order,
                ordered=True
            )
            day_summary = day_summary.sort_values("day_of_week")

            fig_day = px.bar(
                day_summary,
                x="day_of_week",
                y="attendance",
                title="Recommended Days for Services/Events"
            )
            fig_day.update_traces(
                hovertemplate=
                "<b>Day:</b> %{x}<br>"
                "<b>Average Attendance:</b> %{y:.0f}<br>"
                "<extra></extra>"
            )
            st.plotly_chart(fig_day, use_container_width=True)
        else:
            st.info("No day-based data available.")

    with right:
        st.caption("This chart shows which service time usually attracts the highest attendance.")

        if not time_summary.empty:
            fig_time = px.bar(
                time_summary,
                x="mass_time",
                y="attendance",
                title="Recommended Service Times"
            )
            fig_time.update_traces(
                hovertemplate=
                "<b>Service Time:</b> %{x}<br>"
                "<b>Average Attendance:</b> %{y:.0f}<br>"
                "<extra></extra>"
            )
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No service time data available.")

    st.divider()

    st.subheader("Event Type Recommendations")

    if "event_type" in scheduler_data.columns:
        event_summary = (
            scheduler_data.groupby("event_type", as_index=False)["attendance"]
            .mean()
            .sort_values("attendance", ascending=False)
        )

        if not event_summary.empty:
            best_event = event_summary.iloc[0]["event_type"]
            best_event_avg = int(event_summary.iloc[0]["attendance"])

            st.success(
                f"Recommended high-attendance event type: **{best_event}** "
                f"(average attendance: **{best_event_avg}**)."
            )

            fig_event = px.bar(
                event_summary,
                x="event_type",
                y="attendance",
                title="Average Attendance by Event Type"
            )
            fig_event.update_traces(
                hovertemplate=
                "<b>Event Type:</b> %{x}<br>"
                "<b>Average Attendance:</b> %{y:.0f}<br>"
                "<extra></extra>"
            )
            st.plotly_chart(fig_event, use_container_width=True)
        else:
            st.info("No event type data available.")
    else:
        st.info("No event type column found in the data.")

    st.divider()

    st.subheader("Suggested Schedule Planner")

    recommended_day = best_day if best_day != "N/A" else "Sunday"
    recommended_time = best_time if best_time != "N/A" else "08:00"

    plan_col1, plan_col2, plan_col3 = st.columns(3)

    day_options = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    default_day_index = day_options.index(recommended_day) if recommended_day in day_options else 6

    with plan_col1:
        selected_schedule_day = st.selectbox(
            "Choose Day",
            day_options,
            index=default_day_index
        )

    available_times = ["06:00", "08:00", "10:00", "15:00", "17:00", "18:00"]
    default_time_index = available_times.index(recommended_time) if recommended_time in available_times else 1

    with plan_col2:
        selected_schedule_time = st.selectbox(
            "Choose Time",
            available_times,
            index=default_time_index
        )

    if "event_type" in scheduler_data.columns:
        available_events = sorted(scheduler_data["event_type"].dropna().unique().tolist())
        if not available_events:
            available_events = ["Regular Mass"]
    else:
        available_events = ["Regular Mass"]

    with plan_col3:
        selected_schedule_event = st.selectbox(
            "Choose Event Type",
            available_events,
            index=0
        )

    schedule_match = scheduler_data[scheduler_data["day_of_week"] == selected_schedule_day].copy()

    if "mass_time" in schedule_match.columns:
        schedule_match = schedule_match[schedule_match["mass_time"] == selected_schedule_time]

    if "event_type" in schedule_match.columns:
        schedule_match = schedule_match[schedule_match["event_type"] == selected_schedule_event]

    if not schedule_match.empty:
        predicted_attendance = int(schedule_match["attendance"].mean())
    else:
        predicted_attendance = int(scheduler_data["attendance"].mean())

    st.info(
        f"Estimated attendance for **{selected_schedule_event}** on **{selected_schedule_day}** at **{selected_schedule_time}** "
        f"is around **{predicted_attendance} attendees**."
    )

    max_capacity = st.session_state.get("max_capacity", 500)

    if predicted_attendance >= max_capacity * 0.90:
        st.warning("This schedule may approach full capacity. Consider crowd control planning or an additional service.")
    elif predicted_attendance < max_capacity * 0.50:
        st.info("This schedule may have lower attendance. Consider promotions or rescheduling if needed.")
    else:
        st.success("This schedule appears balanced based on the available attendance data.")

    planner_df = pd.DataFrame({
        "Recommended Day": [selected_schedule_day],
        "Recommended Time": [selected_schedule_time],
        "Event Type": [selected_schedule_event],
        "Estimated Attendance": [predicted_attendance],
        "Capacity": [max_capacity]
    })

    st.dataframe(planner_df, use_container_width=True)