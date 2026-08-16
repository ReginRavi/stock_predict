import google.generativeai as genai
import os
import streamlit as st
import pandas as pd
from datetime import datetime

def get_gemini_insights(ticker, historical_data, prophet_forecast, darts_forecast):
    '''
    Get insights from Gemini 1.5 model with better formatting
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
        prophet_summary = "No Prophet forecast available"
        darts_summary = "No Darts forecast available"
        
        if prophet_forecast is not None:
            prophet_avg = float(prophet_forecast["yhat"].mean())
            prophet_summary = f"Prophet predicts average price of ${prophet_avg:.2f}"
        
        if darts_forecast is not None:
            darts_avg = float(darts_forecast.values().mean())
            darts_summary = f"Darts predicts average price of ${darts_avg:.2f}"
        
        # Calculate Earnings Yield
        earnings_yield_str = "N/A"
        try:
            if current_price > 0:
                # Estimate Earnings Yield if P/E available or general metric
                earnings_yield_str = f"Earnings Yield evaluated on valuation multiple"
        except Exception:
            pass

        # Create enhanced prompt for better formatting
        prompt = f'''
        Please provide a comprehensive analysis of {ticker} stock incorporating Applied Value Investing principles (Graham & Dodd Margin of Safety, Greenblatt Earnings Yield, and Return on Capital):
        
        Current Market Data:
        - Current Price: ${current_price:.2f}
        - Price Change: {price_change:.2f} ({price_change_pct:.1f}%)
        - 30-day High: ${recent_high:.2f}
        - 30-day Low: ${recent_low:.2f}
        - Average Volume: {avg_volume:,.0f}
        
        Forecast Results:
        - {prophet_summary}
        - {darts_summary}
        
        Please provide your analysis in the following structured format with clear sections:
        
        ## 📊 Market Sentiment Analysis
        [Provide 2-3 sentences analyzing the current market sentiment]
        
        ## 💎 Applied Value Investing & Technical Insights
        [Provide 2-3 sentences on Margin of Safety, Earnings Yield, capital efficiency, and price action]
        
        ## ⚠️ Risk Assessment
        [Provide 2-3 sentences on potential risks and volatility]
        
        ## 💡 Investment Recommendation
        [Provide a clear recommendation: BUY/HOLD/SELL with reasoning]
        
        ## 🎯 Key Factors to Monitor
        [List 3-5 key factors investors should watch]
        
        Keep each section concise and professional. Use proper spacing and formatting.
        '''
        
        # Generate response
        response = model.generate_content(prompt)
        return format_ai_response(response.text)
        
    except Exception as e:
        return f"❌ Error generating insights: {str(e)}"

def format_ai_response(response_text):
    '''
    Format the AI response for better display in Streamlit
    '''
    # Clean up any formatting issues
    formatted_text = response_text.strip()
    
    # Add some spacing improvements
    formatted_text = formatted_text.replace('## ', '\n## ')
    formatted_text = formatted_text.replace('**', '**')
    
    # Remove excessive asterisks or formatting issues
    import re
    formatted_text = re.sub(r'\*{3,}', '**', formatted_text)
    formatted_text = re.sub(r'\s+', ' ', formatted_text)
    
    return formatted_text

def display_formatted_insights(insights):
    '''
    Display insights with better Streamlit formatting
    '''
    sections = insights.split('## ')
    
    for section in sections:
        if section.strip():
            if section.startswith('📊 Market Sentiment'):
                st.subheader("📊 Market Sentiment Analysis")
                content = section.replace('📊 Market Sentiment Analysis', '').strip()
                st.write(content)
                
            elif section.startswith('🔍 Technical Analysis'):
                st.subheader("🔍 Technical Analysis Insights")
                content = section.replace('🔍 Technical Analysis Insights', '').strip()
                st.write(content)
                
            elif section.startswith('⚠️ Risk Assessment'):
                st.subheader("⚠️ Risk Assessment")
                content = section.replace('⚠️ Risk Assessment', '').strip()
                st.write(content)
                
            elif section.startswith('💡 Investment Recommendation'):
                st.subheader("💡 Investment Recommendation")
                content = section.replace('💡 Investment Recommendation', '').strip()
                
                # Highlight the recommendation
                if 'BUY' in content.upper():
                    st.success(content)
                elif 'SELL' in content.upper():
                    st.error(content)
                else:
                    st.info(content)
                    
            elif section.startswith('🎯 Key Factors'):
                st.subheader("🎯 Key Factors to Monitor")
                content = section.replace('🎯 Key Factors to Monitor', '').strip()
                st.write(content)
            else:
                st.write(section)

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