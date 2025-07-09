from darts.models import NBEATSModel
from darts import TimeSeries
from darts.dataprocessing.transformers import Scaler
import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import numpy as np

def run_darts(ticker, forecast_days=14):
    try:
        # Download data
        df = yf.download(ticker, period="1y")
        
        # Don't reset index - work with the DatetimeIndex directly
        # Create TimeSeries directly from the dataframe with DatetimeIndex
        # Use fill_missing_dates=True to handle missing dates (weekends, holidays)
        try:
            series = TimeSeries.from_dataframe(
                df, 
                time_col=None, 
                value_cols="Close",
                fill_missing_dates=True,
                freq='B'  # Business day frequency (excludes weekends)
            )
        except:
            # Fallback: let Darts try to infer the frequency
            series = TimeSeries.from_dataframe(
                df, 
                time_col=None, 
                value_cols="Close",
                fill_missing_dates=True,
                freq=None  # Let Darts infer the frequency
            )
        
        # Scale data
        scaler = Scaler()
        series_scaled = scaler.fit_transform(series)
        
        # Split data
        train_size = int(len(series_scaled) * 0.8)
        train_series = series_scaled[:train_size]
        
        # Create and train model
        model = NBEATSModel(
            input_chunk_length=30,
            output_chunk_length=min(7, forecast_days),
            n_epochs=20,
            random_state=42,
            pl_trainer_kwargs={
                "accelerator": "cpu",
                "enable_progress_bar": False
            }
        )
        
        with st.spinner("Training Darts model..."):
            model.fit(train_series)
        
        # Make prediction
        prediction_scaled = model.predict(forecast_days)
        prediction = scaler.inverse_transform(prediction_scaled)
        
        # Create plot
        fig = go.Figure()
        
        # Historical data (last 60 days)
        historical = series.tail(60)
        fig.add_trace(go.Scatter(
            x=historical.time_index,
            y=historical.values().flatten(),
            name="Historical",
            line=dict(color="#1f77b4")
        ))
        
        # Prediction
        fig.add_trace(go.Scatter(
            x=prediction.time_index,
            y=prediction.values().flatten(),
            name="Darts Forecast",
            line=dict(color="#2ca02c", dash="dash")
        ))
        
        fig.update_layout(
            title="🔮 Darts (N-BEATS) Forecast",
            xaxis_title="Date",
            yaxis_title="Price ($)",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        return prediction
        
    except Exception as e:
        st.error(f"Darts model error: {str(e)}")
        return None