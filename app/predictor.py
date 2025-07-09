from models.prophet_model import run_prophet
from models.darts_model import run_darts
import streamlit as st

def forecast_stock(ticker, forecast_days=14):
    '''
    Run both Prophet and Darts forecasting models
    '''
    try:
        col1, col2 = st.columns(2)
        
        with col1:
            prophet_forecast = run_prophet(ticker, forecast_days)
            
        with col2:
            darts_forecast = run_darts(ticker, forecast_days)
            
        return prophet_forecast, darts_forecast
        
    except Exception as e:
        st.error(f"Forecasting error: {str(e)}")
        return None, None
