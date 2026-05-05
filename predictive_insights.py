import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from sklearn.model_selection import train_test_split
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

def prepare_time_series(df):
    if df.empty:
        return pd.DataFrame(columns=["date", "attendance"])

    ts = df.copy()
    ts["date"] = pd.to_datetime(ts["date"])
    
    ts["attendance"] = pd.to_numeric(ts["attendance"], errors="coerce").fillna(0)

    ts = (
        ts.groupby(ts["date"].dt.to_period("M"))["attendance"]
        .mean()
        .reset_index()
    )
    ts["date"] = ts["date"].dt.to_timestamp()
    ts = ts.sort_values("date")
    return ts

def holt_winters_forecast(ts_df, periods=6):
    if len(ts_df) < 24:
        return pd.DataFrame(columns=["date", "forecast_attendance"]), None, None, None

    ts = ts_df.copy().sort_values("date").reset_index(drop=True)
    
    ts["attendance"] = ts["attendance"].astype(float)
    
    model = ExponentialSmoothing(
        ts["attendance"], 
        trend="add", 
        seasonal="add", 
        seasonal_periods=12,
        initialization_method="estimated"
    )
    fitted_model = model.fit()
    
    forecast_values = fitted_model.forecast(periods)
    forecast_values = np.maximum(forecast_values, 0)  
    
    future_dates = pd.date_range(
        ts["date"].max() + pd.offsets.MonthBegin(1),
        periods=periods,
        freq="MS"
    )
    
    result = pd.DataFrame({
        "date": future_dates,
        "forecast_attendance": forecast_values.values.round(0)
    })
    
    mae = mean_absolute_error(ts["attendance"], fitted_model.fittedvalues)
    rmse = np.sqrt(mean_squared_error(ts["attendance"], fitted_model.fittedvalues))
    mape = mean_absolute_percentage_error(ts["attendance"], fitted_model.fittedvalues)
    
    return result, mae, rmse, mape

def show_predictive_insights(filtered_data):
    st.title("Predicted Insights")
    model_tab, forecast_tab = st.tabs(["Simple Linear Regression", "Time-Series Forecasting"])

    with model_tab:
        st.markdown(
            "This section uses Simple Linear Regression to predict church attendance "
            "based on foot traffic count."
        )

        model_data = filtered_data.dropna(subset=["foot_traffic_count", "attendance"]).copy()

        if len(model_data) >= 5:
            X = model_data[["foot_traffic_count"]]
            y = model_data["attendance"]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = LinearRegression()
            model.fit(X_train, y_train)

            y_pred_test = model.predict(X_test)
            r2 = r2_score(y_test, y_pred_test)
            mae = mean_absolute_error(y_test, y_pred_test)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric(
                "Slope",
                f"{model.coef_[0]:.2f}",
                help="This shows how much attendance is expected to increase when foot traffic increases by 1."
            )
            col2.metric(
                "Intercept",
                f"{model.intercept_:.2f}",
                help="This is the predicted attendance when foot traffic is zero."
            )
            col3.metric(
                "R² Score",
                f"{r2:.3f}",
                help="This shows how well the model explains the test data. A value closer to 1 means better performance."
            )
            col4.metric(
                "MAE",
                f"{mae:.2f}",
                help="Mean Absolute Error on the test data. Lower values mean better prediction accuracy."
            )

            st.caption(
                f"Training rows: {len(X_train)} | Testing rows: {len(X_test)} | "
                "The model is trained on 80% of the filtered data and tested on the remaining 20%."
            )

            st.subheader("Regression Graph")
            st.info(
                "This graph shows the relationship between foot traffic and attendance. "
                "Blue markers represent recorded church services or events, while the red line "
                "shows the regression model's predicted trend."
            )

            line_x = np.linspace(
                model_data["foot_traffic_count"].min(),
                model_data["foot_traffic_count"].max(),
                100
            )
            line_y = model.predict(pd.DataFrame({"foot_traffic_count": line_x}))

            scatter_fig = px.scatter(
                model_data,
                x="foot_traffic_count",
                y="attendance",
                color="event_type" if "event_type" in model_data.columns else None,
                title="Simple Linear Regression: Foot Traffic vs Attendance",
                custom_data=["event_type"] if "event_type" in model_data.columns else None
            )

            if "event_type" in model_data.columns:
                scatter_fig.update_traces(
                    hovertemplate=
                    "<b>Foot Traffic Count:</b> %{x}<br>"
                    "<b>Attendance:</b> %{y}<br>"
                    "<b>Event Type:</b> %{customdata[0]}<br>"
                    "<extra></extra>"
                )
            else:
                scatter_fig.update_traces(
                    hovertemplate=
                    "<b>Foot Traffic Count:</b> %{x}<br>"
                    "<b>Attendance:</b> %{y}<br>"
                    "<extra></extra>"
                )

            scatter_fig.add_scatter(
                x=line_x,
                y=line_y,
                mode="lines",
                name="Regression Line",
                hovertemplate=
                "<b>Foot Traffic Count:</b> %{x:.0f}<br>"
                "<b>Predicted Attendance:</b> %{y:.0f}<br>"
                "<extra></extra>"
            )

            scatter_fig.update_layout(
                xaxis_title="Foot Traffic Count",
                yaxis_title="Attendance"
            )

            st.plotly_chart(scatter_fig, use_container_width=True)

            st.subheader("Actual vs Predicted Test Results")
            test_results = pd.DataFrame({
                "foot_traffic_count": X_test["foot_traffic_count"].values,
                "actual_attendance": y_test.values,
                "predicted_attendance": np.round(y_pred_test, 0)
            }).sort_values("foot_traffic_count")

            st.caption(
                "This table compares actual attendance and predicted attendance using only the testing dataset."
            )
            st.dataframe(test_results, use_container_width=True)

            st.subheader("Prediction Tool")
            st.caption(
                "Use the slider below to estimate attendance based on a selected foot traffic count."
            )

            input_traffic = st.slider(
                "Select Foot Traffic Count",
                min_value=int(model_data["foot_traffic_count"].min()),
                max_value=int(model_data["foot_traffic_count"].max()),
                value=int(model_data["foot_traffic_count"].mean()),
            )

            predicted_attendance = model.predict(
                pd.DataFrame({"foot_traffic_count": [input_traffic]})
            )[0]

            st.success(
                f"Predicted attendance for foot traffic count of {input_traffic}: "
                f"{predicted_attendance:.0f}"
            )

            st.info(
                "Interpretation: if the number of people detected around the church reaches the selected "
                "foot traffic count, the model estimates that the attendance may be around the value shown above."
            )

        else:
            st.warning(
                "Not enough data to train and test the regression model properly yet. "
                "At least 5 records are recommended."
            )

    with forecast_tab:
        st.markdown("Monthly attendance forecasting based on historical attendance trends using Holt-Winters Exponential Smoothing.")
        ts_data = prepare_time_series(filtered_data)
        forecast_months = st.slider("Forecast Months Ahead", min_value=3, max_value=12, value=6)
        
        # Call the new Holt-Winters function and unpack 4 metrics
        forecast_df, forecast_mae, forecast_rmse, forecast_mape = holt_winters_forecast(ts_data, periods=forecast_months)

        if len(ts_data) >= 24 and not forecast_df.empty:
            hist_plot = ts_data.rename(columns={"attendance": "value"}).copy()
            hist_plot["series"] = "Historical"

            fut_plot = forecast_df.rename(columns={"forecast_attendance": "value"}).copy()
            fut_plot["series"] = "Forecast"

            combined_plot = pd.concat(
                [
                    hist_plot[["date", "value", "series"]],
                    fut_plot[["date", "value", "series"]],
                ],
                ignore_index=True
            )

            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric(
                "Forecast Horizon",
                f"{forecast_months} months",
                help="This shows how many future months are included in the forecast."
            )
            c2.metric(
                "Last Historical Average",
                f"{ts_data['attendance'].iloc[-1]:.0f}",
                help="This shows the latest monthly average attendance from the historical data."
            )
            c3.metric(
                "MAE",
                f"{forecast_mae:.2f}",
                help="This shows the average forecast error. Lower values mean the forecast is more accurate."
            )
            c4.metric(
                "RMSE",
                f"{forecast_rmse:.2f}",
                help="Root Mean Squared Error. Penalizes larger errors more than MAE."
            )
            c5.metric(
                "MAPE",
                f"{forecast_mape:.2%}",
                help="Mean Absolute Percentage Error. Shows the average error as a percentage of actual values."
            )

            st.info(
                "This graph shows the historical attendance trend and the forecasted attendance for the next selected months. "
                "Move your mouse over the line to view the exact values."
            )

            fig_forecast = px.line(
                combined_plot,
                x="date",
                y="value",
                color="series",
                markers=True,
                title="Attendance Time-Series Forecast (Holt-Winters)",
            )

            fig_forecast.update_traces(
                hovertemplate=
                "<b>Date:</b> %{x}<br>"
                "<b>Attendance:</b> %{y:.0f}<br>"
                "<extra></extra>"
            )

            fig_forecast.update_layout(
                xaxis_title="Date",
                yaxis_title="Attendance"
            )

            st.plotly_chart(fig_forecast, use_container_width=True)

            upcoming_low = forecast_df[
                forecast_df["forecast_attendance"] < max(ts_data["attendance"].median() * 0.75, 1)
            ]

            if not upcoming_low.empty:
                first_low = upcoming_low.iloc[0]
                st.warning(
                    f"Low attendance alert: forecast suggests lower turnout around "
                    f"{first_low['date'].strftime('%B %Y')} with an estimated attendance of "
                    f"{int(first_low['forecast_attendance'])}."
                )
            else:
                st.success("Forecast does not currently indicate a low-attendance month.")

            st.caption("Forecast table showing the estimated attendance for the upcoming months.")
            st.dataframe(forecast_df, use_container_width=True)
        else:
            st.warning("At least 24 months of attendance history are needed for Holt-Winters time-series forecasting.")