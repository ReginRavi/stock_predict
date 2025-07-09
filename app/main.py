import streamlit as st
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
