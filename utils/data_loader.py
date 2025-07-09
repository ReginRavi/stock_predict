import yfinance as yf
import pandas as pd
import streamlit as st

@st.cache_data
def load_stock_data(ticker, period="1y"):
    '''
    Load stock data with caching
    '''
    try:
        data = yf.download(ticker, period=period)
        return data
    except Exception as e:
        st.error(f"Error loading data for {ticker}: {str(e)}")
        return pd.DataFrame()

def get_stock_info(ticker):
    '''
    Get stock information
    '''
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return info
    except Exception as e:
        st.error(f"Error getting stock info: {str(e)}")
        return {}
