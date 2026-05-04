import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error
from io import BytesIO
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="Church Attendance Monitoring System",
    page_icon="⛪",
    layout="wide"
)

# =========================
# HELPER FUNCTIONS
# =========================
def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
    return df


def smart_prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts flexible CSV column names and tries to standardize them
    into the structure needed by the dashboard.
    """

    df = normalize_columns(df)

    column_aliases = {
        "date": ["date", "attendance_date", "day", "record_date"],
        "time_of_day": ["time_of_day", "time", "mass_time", "service_time"],
        "attendance": ["attendance", "attendees", "attendance_count", "headcount"],
        "foot_traffic_count": ["foot_traffic_count", "foot_traffic", "foottraffic", "traffic_count", "foot_traffic_sensor"],
        "capacity": ["capacity", "max_capacity", "church_capacity"],
        "event_type": ["event_type", "event", "service_type", "mass_type"],
    }

    found = {}

    for standard_col, aliases in column_aliases.items():
        for alias in aliases:
            if alias in df.columns:
                found[standard_col] = alias
                break

    renamed = {}
    for std, original in found.items():
        renamed[original] = std

    df = df.rename(columns=renamed)

    if "date" not in df.columns:
        raise ValueError("CSV must contain a date column.")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])

    if "attendance" not in df.columns:
        raise ValueError("CSV must contain an attendance column.")

    df["attendance"] = pd.to_numeric(df["attendance"], errors="coerce").fillna(0)

    if "foot_traffic_count" not in df.columns:
        df["foot_traffic_count"] = df["attendance"]

    df["foot_traffic_count"] = pd.to_numeric(df["foot_traffic_count"], errors="coerce").fillna(0)

    if "capacity" not in df.columns:
        max_att = max(int(df["attendance"].max()), 1)
        df["capacity"] = max_att

    df["capacity"] = pd.to_numeric(df["capacity"], errors="coerce").fillna(df["attendance"].max())

    if "event_type" not in df.columns:
        df["event_type"] = "Regular Mass"

    if "time_of_day" not in df.columns:
        df["time_of_day"] = "08:00"

    df["occupancy_rate"] = np.where(
        df["capacity"] > 0,
        (df["attendance"] / df["capacity"]) * 100,
        0
    )

    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["day_name"] = df["date"].dt.day_name()
    df["year"] = df["date"].dt.year
    df["weekday_num"] = df["date"].dt.weekday
    df["day"] = df["date"].dt.day
    df["month_num"] = df["date"].dt.month

    return df.sort_values("date").reset_index(drop=True)


def combine_uploaded_csvs(uploaded_files):
    all_dfs = []
    file_names = []

    for file in uploaded_files:
        try:
            df = pd.read_csv(file)
            df = smart_prepare_dataframe(df)
            df["source_file"] = file.name
            all_dfs.append(df)
            file_names.append(file.name)
        except Exception as e:
            st.warning(f"Could not read {file.name}: {e}")

    if not all_dfs:
        return None, []

    combined = pd.concat(all_dfs, ignore_index=True)
    combined = combined.sort_values("date").reset_index(drop=True)
    return combined, file_names


def apply_filters(df, event_types, times, date_range):
    filtered = df.copy()

    if event_types:
        filtered = filtered[filtered["event_type"].isin(event_types)]

    if times:
        filtered = filtered[filtered["time_of_day"].isin(times)]

    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        filtered = filtered[(filtered["date"] >= start_date) & (filtered["date"] <= end_date)]

    return filtered


def create_excel_download(df_dict):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in df_dict.items():
            safe_sheet_name = str(sheet_name)[:31]
            df.to_excel(writer, index=False, sheet_name=safe_sheet_name)
    output.seek(0)
    return output


def train_linear_regression(df):
    working = df.dropna(subset=["foot_traffic_count", "attendance"]).copy()

    if len(working) < 2:
        return None

    X = working[["foot_traffic_count"]]
    y = working["attendance"]

    model = LinearRegression()
    model.fit(X, y)
    preds = model.predict(X)

    working["predicted_attendance"] = preds

    metrics = {
        "r2": r2_score(y, preds) if len(working) > 1 else 0,
        "mae": mean_absolute_error(y, preds),
        "slope": float(model.coef_[0]),
        "intercept": float(model.intercept_)
    }

    return model, working, metrics


def forecast_next_days(df, periods=30):
    """
    Simple thesis-friendly forecasting:
    Linear regression on date index after daily aggregation.
    """
    daily = df.groupby("date", as_index=False)["attendance"].sum().sort_values("date")

    if len(daily) < 2:
        return None, None

    daily["day_index"] = np.arange(len(daily))

    X = daily[["day_index"]]
    y = daily["attendance"]

    model = LinearRegression()
    model.fit(X, y)

    future_index = np.arange(len(daily), len(daily) + periods)
    future_dates = pd.date_range(
        start=daily["date"].max() + pd.Timedelta(days=1),
        periods=periods,
        freq="D"
    )

    forecast_values = model.predict(future_index.reshape(-1, 1))
    forecast_values = np.maximum(forecast_values, 0)

    forecast_df = pd.DataFrame({
        "date": future_dates,
        "forecast_attendance": forecast_values.round(0).astype(int)
    })

    return daily, forecast_df


def metric_card(title, value, help_text=""):
    st.metric(label=title, value=value, help=help_text)


# =========================
# SESSION STATE
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "users" not in st.session_state:
    # Single-file only, so accounts are temporary during runtime
    st.session_state.users = {
        "admin": "admin123"
    }

if "current_user" not in st.session_state:
    st.session_state.current_user = None


# =========================
# LOGIN / CREATE ACCOUNT
# =========================
def show_auth_screen():
    st.title("⛪ Church Attendance Monitoring System")
    st.markdown("Upload CSV files to monitor attendance, analyze patterns, and generate predictive insights.")

    info_col1, info_col2 = st.columns([2, 1])

    with info_col1:
        st.info(
            "This version uses **CSV upload only**. "
            "No sensor and no extra Python files are needed."
        )

    with info_col2:
        st.caption("Default test login")
        st.code("Username: admin\nPassword: admin123")

    tab1, tab2 = st.tabs(["Log In", "Create Account"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Log In", use_container_width=True)

            if login_btn:
                if username in st.session_state.users and st.session_state.users[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.success("Login successful.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")

    with tab2:
        with st.form("create_account_form"):
            new_username = st.text_input("New Username")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            create_btn = st.form_submit_button("Create Account", use_container_width=True)

            if create_btn:
                if not new_username or not new_password:
                    st.error("Please complete all fields.")
                elif new_username in st.session_state.users:
                    st.error("Username already exists.")
                elif new_password != confirm_password:
                    st.error("Passwords do not match.")
                else:
                    st.session_state.users[new_username] = new_password
                    st.success("Account created successfully. You may now log in.")


if not st.session_state.logged_in:
    show_auth_screen()
    st.stop()


# =========================
# MAIN APP
# =========================
st.sidebar.title("Navigation")
selected_page = st.sidebar.radio(
    "Go to",
    ["HOME", "Attendance Records", "Predicted Insights", "Reports and Exports"]
)

st.sidebar.markdown("---")
st.sidebar.write(f"Logged in as: **{st.session_state.current_user}**")

if st.sidebar.button("Log Out", use_container_width=True):
    st.session_state.logged_in = False
    st.session_state.current_user = None
    st.rerun()

st.title("⛪ Church Attendance Monitoring Dashboard")

st.markdown(
    """
This dashboard allows church staff to upload historical attendance CSV files,
review attendance records, analyze trends, and generate predictive insights
using simple linear regression and time-series forecasting.
"""
)

uploaded_files = st.sidebar.file_uploader(
    "Upload CSV file(s)",
    type=["csv"],
    accept_multiple_files=True
)

template_expander = st.sidebar.expander("Expected CSV columns")
with template_expander:
    st.write("Recommended columns:")
    st.code(
        "date, time_of_day, attendance, foot_traffic_count, capacity, event_type",
        language="text"
    )
    st.write("Example:")
    sample_df = pd.DataFrame({
        "date": ["2025-01-05", "2025-01-12"],
        "time_of_day": ["08:00", "10:00"],
        "attendance": [120, 185],
        "foot_traffic_count": [140, 210],
        "capacity": [300, 300],
        "event_type": ["Regular Mass", "Special Event"]
    })
    st.dataframe(sample_df, use_container_width=True)

if not uploaded_files:
    st.warning("Please upload at least one CSV file from the sidebar to continue.")
    st.stop()

data, source_files = combine_uploaded_csvs(uploaded_files)

if data is None or data.empty:
    st.error("No valid data could be loaded from the uploaded files.")
    st.stop()

# =========================
# SIDEBAR FILTERS
# =========================
all_event_types = sorted(data["event_type"].dropna().unique().tolist())
all_times = sorted(data["time_of_day"].dropna().astype(str).unique().tolist())

min_date = data["date"].min().date()
max_date = data["date"].max().date()

st.sidebar.markdown("---")
st.sidebar.subheader("Filters")

selected_events = st.sidebar.multiselect(
    "Event Type",
    options=all_event_types,
    default=all_event_types
)

selected_times = st.sidebar.multiselect(
    "Time of Day",
    options=all_times,
    default=all_times
)

selected_date_range = st.sidebar.date_input(
    "Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

filtered_data = apply_filters(data, selected_events, selected_times, selected_date_range)

if filtered_data.empty:
    st.warning("No data matched the selected filters.")
    st.stop()

# =========================
# HOME PAGE
# =========================
if selected_page == "HOME":
    col1, col2, col3, col4 = st.columns(4)

    total_records = len(filtered_data)
    total_attendance = int(filtered_data["attendance"].sum())
    avg_attendance = round(filtered_data["attendance"].mean(), 2)
    avg_occupancy = round(filtered_data["occupancy_rate"].mean(), 2)

    with col1:
        metric_card("Total Records", f"{total_records:,}", "Number of uploaded attendance entries after filtering.")
    with col2:
        metric_card("Total Attendance", f"{total_attendance:,}", "Combined attendance from filtered records.")
    with col3:
        metric_card("Average Attendance", f"{avg_attendance:,.2f}", "Average attendance per record.")
    with col4:
        metric_card("Average Occupancy", f"{avg_occupancy:.2f}%", "Attendance compared with church capacity.")

    st.markdown("---")

    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        daily_attendance = filtered_data.groupby("date", as_index=False)["attendance"].sum()

        fig_daily = px.line(
            daily_attendance,
            x="date",
            y="attendance",
            markers=True,
            title="Daily Attendance Trend",
            labels={"date": "Date", "attendance": "Attendance"}
        )

        fig_daily.update_traces(
            hovertemplate="<b>Date:</b> %{x}<br><b>Attendance:</b> %{y}<extra></extra>"
        )

        fig_daily.update_layout(
            xaxis_title="Date",
            yaxis_title="Attendance"
        )

        st.plotly_chart(fig_daily, use_container_width=True)
        st.caption("This graph shows how total church attendance changes over time based on the uploaded CSV records.")

    with chart_col2:
        event_summary = filtered_data.groupby("event_type", as_index=False)["attendance"].sum()

        fig_event = px.bar(
            event_summary,
            x="event_type",
            y="attendance",
            title="Attendance by Event Type",
            labels={"event_type": "Event Type", "attendance": "Total Attendance"},
            text_auto=True
        )

        fig_event.update_traces(
            hovertemplate="<b>Event Type:</b> %{x}<br><b>Total Attendance:</b> %{y}<extra></extra>"
        )

        st.plotly_chart(fig_event, use_container_width=True)
        st.caption("This graph compares which church event types have the highest total attendance.")

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        monthly_attendance = filtered_data.groupby("month", as_index=False)["attendance"].sum()

        fig_month = px.area(
            monthly_attendance,
            x="month",
            y="attendance",
            title="Monthly Attendance Summary",
            labels={"month": "Month", "attendance": "Total Attendance"}
        )

        fig_month.update_traces(
            hovertemplate="<b>Month:</b> %{x}<br><b>Total Attendance:</b> %{y}<extra></extra>"
        )

        st.plotly_chart(fig_month, use_container_width=True)
        st.caption("This graph summarizes attendance totals per month for easier seasonal analysis.")

    with chart_col4:
        day_summary = filtered_data.groupby("day_name", as_index=False)["attendance"].mean()
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        day_summary["day_name"] = pd.Categorical(day_summary["day_name"], categories=day_order, ordered=True)
        day_summary = day_summary.sort_values("day_name")

        fig_day = px.bar(
            day_summary,
            x="day_name",
            y="attendance",
            title="Average Attendance by Day of Week",
            labels={"day_name": "Day", "attendance": "Average Attendance"},
            text_auto=".2f"
        )

        fig_day.update_traces(
            hovertemplate="<b>Day:</b> %{x}<br><b>Average Attendance:</b> %{y:.2f}<extra></extra>"
        )

        st.plotly_chart(fig_day, use_container_width=True)
        st.caption("This graph helps identify which days usually have higher or lower attendance.")

    st.markdown("---")

    st.subheader("Uploaded Source Files")
    st.write(source_files)

# =========================
# ATTENDANCE RECORDS PAGE
# =========================
elif selected_page == "Attendance Records":
    st.subheader("Attendance Records")

    display_df = filtered_data.copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

    preferred_columns = [
        "date", "time_of_day", "event_type", "attendance",
        "foot_traffic_count", "capacity", "occupancy_rate", "source_file"
    ]
    available_columns = [c for c in preferred_columns if c in display_df.columns]
    display_df = display_df[available_columns]

    st.dataframe(display_df, use_container_width=True, height=500)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Attendance Distribution")
        fig_hist = px.histogram(
            filtered_data,
            x="attendance",
            nbins=20,
            title="Distribution of Attendance",
            labels={"attendance": "Attendance"}
        )

        fig_hist.update_traces(
            hovertemplate="<b>Attendance Range:</b> %{x}<br><b>Count:</b> %{y}<extra></extra>"
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        st.caption("This chart shows how often different attendance values occur in the records.")

    with col2:
        st.subheader("Capacity vs Attendance")
        fig_scatter = px.scatter(
            filtered_data,
            x="capacity",
            y="attendance",
            color="event_type",
            hover_data=["date", "time_of_day", "foot_traffic_count"],
            title="Attendance Compared with Capacity"
        )

        fig_scatter.update_traces(
            hovertemplate=(
                "<b>Capacity:</b> %{x}<br>"
                "<b>Attendance:</b> %{y}<br>"
                "<extra></extra>"
            )
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("This chart helps show whether actual attendance stays far below, near, or above capacity.")

elif selected_page == "Predicted Insights":
    st.subheader("Predictive Insights")

    tab1, tab2 = st.tabs(["Simple Linear Regression", "Time-Series Forecasting"])

    with tab1:
        st.markdown(
            """
**Model Purpose:**  
This model estimates church attendance based on **foot traffic count**.

**Independent Variable:** Foot Traffic Count  
**Dependent Variable:** Attendance
"""
        )

        lr_result = train_linear_regression(filtered_data)

        if lr_result is None:
            st.warning("Not enough data to train the linear regression model.")
        else:
            model, regression_df, metrics = lr_result

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("R² Score", f"{metrics['r2']:.4f}")
            m2.metric("MAE", f"{metrics['mae']:.2f}")
            m3.metric("Slope", f"{metrics['slope']:.4f}")
            m4.metric("Intercept", f"{metrics['intercept']:.2f}")

            fig_reg = px.scatter(
                regression_df,
                x="foot_traffic_count",
                y="attendance",
                title="Linear Regression: Foot Traffic Count vs Attendance",
                labels={
                    "foot_traffic_count": "Foot Traffic Count",
                    "attendance": "Attendance"
                },
                hover_data=["date", "event_type", "time_of_day"]
            )

            regression_df = regression_df.sort_values("foot_traffic_count")

            fig_reg.add_trace(
                go.Scatter(
                    x=regression_df["foot_traffic_count"],
                    y=regression_df["predicted_attendance"],
                    mode="lines",
                    name="Regression Line"
                )
            )

            fig_reg.update_traces(
                hovertemplate="<b>Foot Traffic:</b> %{x}<br><b>Attendance:</b> %{y}<extra></extra>"
            )

            st.plotly_chart(fig_reg, use_container_width=True)

            st.caption(
                "The regression line shows the estimated relationship between foot traffic and attendance. "
                "A higher R² score means the model explains the data better."
            )

            st.markdown("#### Predict Attendance Manually")
            input_col1, input_col2 = st.columns([1, 2])

            with input_col1:
                manual_foot_traffic = st.number_input(
                    "Enter Foot Traffic Count",
                    min_value=0,
                    value=100,
                    step=1
                )

            predicted_attendance = model.predict(pd.DataFrame({"foot_traffic_count": [manual_foot_traffic]}))[0]
            predicted_attendance = max(predicted_attendance, 0)

            with input_col2:
                st.success(f"Predicted Attendance: {predicted_attendance:.2f}")

    with tab2:
        st.markdown(
            """
**Forecasting Purpose:**  
This time-series forecasting section estimates future church attendance trends
based on historical attendance patterns from the uploaded CSV files.

**Forecasting Method Used:**  
A simple linear regression model applied to a daily attendance time index.
"""
        )

        forecast_days = st.slider("Forecast Days", min_value=7, max_value=90, value=30, step=1)

        historical_daily, forecast_df = forecast_next_days(filtered_data, periods=forecast_days)

        if historical_daily is None or forecast_df is None:
            st.warning("Not enough data to create a forecast.")
        else:
            fig_forecast = go.Figure()

            fig_forecast.add_trace(
                go.Scatter(
                    x=historical_daily["date"],
                    y=historical_daily["attendance"],
                    mode="lines+markers",
                    name="Historical Attendance"
                )
            )

            fig_forecast.add_trace(
                go.Scatter(
                    x=forecast_df["date"],
                    y=forecast_df["forecast_attendance"],
                    mode="lines+markers",
                    name="Forecast Attendance"
                )
            )

            fig_forecast.update_layout(
                title="Time-Series Attendance Forecast",
                xaxis_title="Date",
                yaxis_title="Attendance"
            )

            st.plotly_chart(fig_forecast, use_container_width=True)

            st.caption(
                "The forecast extends the historical attendance trend into future dates. "
                "This can help church staff estimate expected attendance for planning purposes."
            )

            st.dataframe(forecast_df, use_container_width=True)

# =========================
# REPORTS AND EXPORTS PAGE
# =========================
elif selected_page == "Reports and Exports":
    st.subheader("Reports and Exports")

    summary_df = filtered_data.groupby(["event_type", "month"], as_index=False).agg(
        total_attendance=("attendance", "sum"),
        average_attendance=("attendance", "mean"),
        average_foot_traffic=("foot_traffic_count", "mean"),
        average_capacity=("capacity", "mean")
    )

    summary_df["average_attendance"] = summary_df["average_attendance"].round(2)
    summary_df["average_foot_traffic"] = summary_df["average_foot_traffic"].round(2)
    summary_df["average_capacity"] = summary_df["average_capacity"].round(2)

    st.markdown("### Summary Report")
    st.dataframe(summary_df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        csv_data = filtered_data.copy()
        csv_data["date"] = csv_data["date"].dt.strftime("%Y-%m-%d")
        csv_bytes = csv_data.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download Filtered Data as CSV",
            data=csv_bytes,
            file_name="filtered_attendance_data.csv",
            mime="text/csv",
            use_container_width=True
        )

    with col2:
        export_excel = create_excel_download({
            "Filtered Data": filtered_data.assign(date=filtered_data["date"].dt.strftime("%Y-%m-%d")),
            "Summary Report": summary_df
        })

        st.download_button(
            label="Download Reports as Excel",
            data=export_excel,
            file_name="church_attendance_reports.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("### Quick Report Insights")

    highest_event = filtered_data.groupby("event_type")["attendance"].sum().sort_values(ascending=False)
    top_event = highest_event.index[0] if not highest_event.empty else "N/A"

    peak_day_df = filtered_data.groupby("date", as_index=False)["attendance"].sum().sort_values("attendance", ascending=False)
    peak_day = peak_day_df.iloc[0]["date"].strftime("%Y-%m-%d") if not peak_day_df.empty else "N/A"
    peak_attendance = int(peak_day_df.iloc[0]["attendance"]) if not peak_day_df.empty else 0

    insight_col1, insight_col2, insight_col3 = st.columns(3)
    insight_col1.info(f"Highest-attendance event type: **{top_event}**")
    insight_col2.info(f"Peak attendance day: **{peak_day}**")
    insight_col3.info(f"Attendance on peak day: **{peak_attendance:,}**")

    st.markdown(
        """
This section helps the church generate printable and downloadable summaries
from uploaded CSV files. These outputs can support meetings, planning,
reporting, and thesis presentation.
"""
    )