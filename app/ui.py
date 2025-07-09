import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

from app.predictor import forecast_stock
from utils.data_loader import load_stock_data
from utils.llm_wrapper import get_gemini_insights, display_formatted_insights

def display_dashboard():
    st.title("📊 Stock Price Prediction with GenAI Insights")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Configuration")
        ticker = st.text_input("Enter Stock Ticker", "AAPL").upper()
        period = st.selectbox("Historical Period", ["1y", "6mo", "3mo", "1mo"])
        forecast_days = st.slider("Forecast Days", 7, 30, 14)
        
        # Check API key
        import os
        if not os.getenv("GOOGLE_API_KEY"):
            st.error("Please add your Gemini API key to .env file")
            st.stop()
    
    if ticker:
        try:
            # Load and display stock data
            with st.spinner("Loading stock data..."):
                df = load_stock_data(ticker, period)
                
            if df.empty:
                st.error(f"No data found for ticker {ticker}")
                return
            
            # Display current price info
            current_price = float(df["Close"].iloc[-1])
            price_change = float(df["Close"].iloc[-1] - df["Close"].iloc[-2])
            price_change_pct = (price_change / float(df["Close"].iloc[-2])) * 100
            volume = int(df['Volume'].iloc[-1])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Price", f"${current_price:.2f}", f"{price_change:.2f} ({price_change_pct:.1f}%)")
            with col2:
                st.metric("Volume", f"{volume:,}")
            with col3:
                # Calculate market cap if possible
                try:
                    import yfinance as yf
                    stock_info = yf.Ticker(ticker).info
                    market_cap = stock_info.get('marketCap', 'N/A')
                    if market_cap != 'N/A':
                        market_cap = f"${market_cap:,.0f}"
                    st.metric("Market Cap", market_cap)
                except:
                    st.metric("Market Cap", "N/A")
            
            # Plot historical data
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df.index, 
                y=df["Close"], 
                name="Close Price",
                line=dict(color="#1f77b4")
            ))
            fig.update_layout(
                title=f"{ticker} Historical Price",
                xaxis_title="Date",
                yaxis_title="Price ($)",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Generate predictions
            st.subheader("🔮 Forecasting Results")
            prophet_forecast, darts_forecast = forecast_stock(ticker, forecast_days)
            
            # Get AI insights with better formatting
            st.subheader("🤖 AI Insights")
            with st.spinner("Generating AI insights..."):
                insights = get_gemini_insights(ticker, df, prophet_forecast, darts_forecast)
                
                # Use the new formatted display function
                if insights.startswith("❌"):
                    st.error(insights)
                else:
                    display_formatted_insights(insights)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please check your ticker symbol and try again.")