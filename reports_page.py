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
            export_months = st.slider("Months to Forecast for Export", min_value=3, max_value=12, value=6)
            
            forecast_results = holt_winters_forecast(
                prepare_time_series(filtered_data),
                periods=export_months
            )
            
            if isinstance(forecast_results, tuple):
                forecast_df = forecast_results[0]
            else:
                forecast_df = forecast_results

            export_df = (
                forecast_df.copy()
                if not forecast_df.empty
                else pd.DataFrame(columns=["date", "forecast_attendance"])
            )

        st.dataframe(export_df, width='stretch', hide_index=True)

        if report_choice == "Forecast Summary":
            file_name_export = "simulated_2026_forecast.csv"
        else:
            file_name_export = "church_attendance_data.csv"

        csv = export_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=f"Download {report_choice} Data as CSV",
            data=csv,
            file_name=file_name_export,
            mime="text/csv",
        )