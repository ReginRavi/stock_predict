from prophet import Prophet
import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta

def run_prophet(ticker, forecast_days=14):
    try:
        # Download data
        df = yf.download(ticker, period="1y")
        df = df.reset_index()[["Date", "Close"]]
        df.columns = ["ds", "y"]
        
        # Create and fit model
        model = Prophet(
            daily_seasonality=True,
            weekly_seasonality=True,
            yearly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(df)
        
        # Make future dataframe
        future = model.make_future_dataframe(periods=forecast_days)
        forecast = model.predict(future)
        
        # Plot results
        fig = go.Figure()
        
        # Historical data
        fig.add_trace(go.Scatter(
            x=df["ds"], 
            y=df["y"], 
            name="Historical",
            line=dict(color="#1f77b4")
        ))
        
        # Forecast
        forecast_data = forecast.tail(forecast_days)
        fig.add_trace(go.Scatter(
            x=forecast_data["ds"], 
            y=forecast_data["yhat"], 
            name="Prophet Forecast",
            line=dict(color="#ff7f0e", dash="dash")
        ))
        
        # Confidence intervals
        fig.add_trace(go.Scatter(
            x=forecast_data["ds"],
            y=forecast_data["yhat_upper"],
            fill=None,
            mode='lines',
            line_color='rgba(0,0,0,0)',
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=forecast_data["ds"],
            y=forecast_data["yhat_lower"],
            fill='tonexty',
            mode='lines',
            line_color='rgba(0,0,0,0)',
            name='Confidence Interval',
            fillcolor='rgba(255,127,14,0.2)'
        ))
        
        fig.update_layout(
            title="📈 Prophet Forecast",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        return forecast_data
        
    except Exception as e:
        st.error(f"Prophet model error: {str(e)}")
        return None
