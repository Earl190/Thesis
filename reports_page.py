import streamlit as st
import pandas as pd
from predictive_insights import prepare_time_series, holt_winters_forecast
def show_reports_page(filtered_data, monthly_data):
    
    st.title("Reports and Exports")
    st.markdown("Generate and export attendance reports.")

    if filtered_data.empty:
        st.info("No filtered data is available yet for export.")
    else:
        report_choice = st.selectbox(
            "Choose Report Type",
            ["Filtered Attendance Data", "Monthly Summary", "Forecast Summary"],
        )

        if report_choice == "Filtered Attendance Data":
            export_df = filtered_data.copy()

        elif report_choice == "Monthly Summary":
            export_df = monthly_data.copy()
            
        else:
            forecast_df, _ = holt_winters_forecast(
                prepare_time_series(filtered_data),
                periods=6
            )
            export_df = (
                forecast_df.copy()
                if not forecast_df.empty
                else pd.DataFrame(columns=["date", "forecast_attendance"])
            )

        st.dataframe(export_df, use_container_width=True)

        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Download Attendance Data as CSV",
            data=csv,
            file_name="church_attendance_data.csv",
            mime="text/csv",
        )