import os

FOLDERS = [
    ".github/workflows",
    "app",
    "data/cache",
    "models",
    "utils",
    ".streamlit"
]

FILES = {
    "README.md": """# 📈 Stock Price Prediction with GenAI Insights

A comprehensive stock prediction application using Prophet, Darts, and Google's Gemini 1.5 for AI-powered insights.

## Setup
1. Install requirements: `pip install -r requirements.txt`
2. Add your Gemini API key to `.env` file
3. Run: `streamlit run app/main.py`

## Features
- Prophet forecasting
- Darts deep learning predictions
- Gemini 1.5 AI insights
- Interactive dashboard
""",
    
    ".gitignore": """.env
__pycache__/
*.pyc
data/cache/
*.log
.DS_Store
venv/
env/
""",
    
    "requirements.txt": """streamlit==1.28.0
pandas==2.1.0
yfinance==0.2.20
prophet==1.1.4
darts==0.25.0
plotly==5.15.0
torch==2.0.1
pytorch-lightning==2.0.7
google-generativeai==0.3.0
python-dotenv==1.0.0
transformers==4.33.0
scikit-learn==1.3.0
numpy==1.24.3
""",
    
    ".streamlit/config.toml": """[server]
headless = true
port = 8501

[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
""",
    
    ".env": """# Add your Google Gemini API key here
GOOGLE_API_KEY=your_gemini_api_key_here
""",
    
    ".github/workflows/deploy.yml": """name: Deploy to Streamlit Cloud
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    - name: Deploy to Streamlit
      run: echo "Streamlit deploy happens on Streamlit Cloud platform."
""",
    
    "app/main.py": """import streamlit as st
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ui import display_dashboard
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(
    page_title="Stock Prediction GenAI", 
    layout="wide",
    initial_sidebar_state="expanded"
)

if __name__ == "__main__":
    display_dashboard()
""",
    
    "app/ui.py": """import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime, timedelta

from app.predictor import forecast_stock
from utils.data_loader import load_stock_data
from utils.llm_wrapper import get_gemini_insights

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
            
            # Get AI insights
            st.subheader("🤖 AI Insights")
            with st.spinner("Generating AI insights..."):
                insights = get_gemini_insights(ticker, df, prophet_forecast, darts_forecast)
                st.write(insights)
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Please check your ticker symbol and try again.")
""",
    
    "app/predictor.py": """from models.prophet_model import run_prophet
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
""",
    
    "models/prophet_model.py": """from prophet import Prophet
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
""",
    
    "models/darts_model.py": """from darts.models import NBEATSModel
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
        
        # Reset index to make Date a column
        df = df.reset_index()
        
        # Create TimeSeries
        series = TimeSeries.from_dataframe(df, "Date", "Close")
        
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
""",
    
    "utils/data_loader.py": """import yfinance as yf
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
""",
    
    "utils/llm_wrapper.py": """import google.generativeai as genai
import os
import streamlit as st
import pandas as pd
from datetime import datetime

def get_gemini_insights(ticker, historical_data, prophet_forecast, darts_forecast):
    '''
    Get insights from Gemini 1.5 model
    '''
    try:
        # Configure Gemini
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "❌ Gemini API key not configured. Please add it to your .env file."
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prepare data summary
        current_price = float(historical_data["Close"].iloc[-1])
        price_change = float(historical_data["Close"].iloc[-1] - historical_data["Close"].iloc[-2])
        price_change_pct = (price_change / float(historical_data["Close"].iloc[-2])) * 100
        
        # Get recent performance
        recent_high = float(historical_data["High"].tail(30).max())
        recent_low = float(historical_data["Low"].tail(30).min())
        avg_volume = int(historical_data["Volume"].tail(30).mean())
        
        # Forecast summaries
        prophet_summary = ""
        darts_summary = ""
        
        if prophet_forecast is not None:
            prophet_avg = float(prophet_forecast["yhat"].mean())
            prophet_summary = f"Prophet predicts average price of ${prophet_avg:.2f}"
        
        if darts_forecast is not None:
            darts_avg = float(darts_forecast.values().mean())
            darts_summary = f"Darts predicts average price of ${darts_avg:.2f}"
        
        # Create prompt
        prompt = f'''
        Please provide a comprehensive analysis of {ticker} stock based on the following data:
        
        Current Market Data:
        - Current Price: ${current_price:.2f}
        - Price Change: {price_change:.2f} ({price_change_pct:.1f}%)
        - 30-day High: ${recent_high:.2f}
        - 30-day Low: ${recent_low:.2f}
        - Average Volume: {avg_volume:,.0f}
        
        Forecast Results:
        - {prophet_summary}
        - {darts_summary}
        
        Please provide:
        1. Market sentiment analysis
        2. Technical analysis insights
        3. Risk assessment
        4. Investment recommendation (buy/hold/sell)
        5. Key factors to monitor
        
        Keep the analysis professional but accessible, around 200-300 words.
        '''
        
        # Generate response
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"❌ Error generating insights: {str(e)}"

def get_market_summary():
    '''
    Get general market summary from Gemini
    '''
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return "API key not configured"
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = "Provide a brief summary of current market conditions and trends. Keep it under 100 words."
        
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Error: {str(e)}"
"""
}

def create_structure():
    """
    Create the project structure and files
    """
    try:
        # Create folders
        for folder in FOLDERS:
            os.makedirs(folder, exist_ok=True)
            print(f"📁 Created folder: {folder}")
        
        # Create files
        for file_path, content in FILES.items():
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"📄 Created file: {file_path}")
        
        print("\n✅ Project structure and boilerplate created successfully!")
        print("\n🔧 Next steps:")
        print("1. Add your Gemini API key to the .env file")
        print("2. Install requirements: pip install -r requirements.txt")
        print("3. Run the app: streamlit run app/main.py")
        
    except Exception as e:
        print(f"❌ Error creating structure: {str(e)}")

if __name__ == "__main__":
    create_structure()