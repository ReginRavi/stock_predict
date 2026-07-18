import requests
from bs4 import BeautifulSoup
import json
import sys
import argparse

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    return session

def fetch_screener_data(symbol: str):
    url = f"https://www.screener.in/company/{symbol.upper()}/"
    session = build_session()
    
    try:
        response = session.get(url)
        if response.status_code == 404:
            return {"error": f"Symbol {symbol} not found on Screener.in"}
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Error fetching Screener data: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")
    
    ratios = {}
    ratio_items = soup.select("#top-ratios li")
    for item in ratio_items:
        name_el = item.select_one(".name")
        val_el = item.select_one(".number")
        if name_el and val_el:
            ratios[name_el.get_text(strip=True)] = val_el.get_text(strip=True)

    pros = [li.get_text(strip=True) for li in soup.select(".pros ul li")]
    cons = [li.get_text(strip=True) for li in soup.select(".cons ul li")]
    company_name = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else symbol

    return {
        "company": company_name,
        "fundamental_ratios": ratios,
        "pros": pros,
        "cons": cons
    }

def fetch_trendlyne_info(symbol: str):
    url = f"https://trendlyne.com/stock-quotes/NSE/{symbol.upper()}/"
    session = build_session()
    
    try:
        response = session.get(url, allow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        return {"error": f"Error fetching Trendlyne data: {e}"}

    soup = BeautifulSoup(response.text, "html.parser")
    body_text = soup.get_text()
    
    import re
    
    recommendation = "N/A"
    target_price = "N/A"
    analyst_count = "N/A"

    # 1. Consensus Rating
    # Search for specific common consensus terms in the text
    ratings = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
    for rating in ratings:
        if re.search(rf"\b{rating}\b", body_text, re.IGNORECASE):
            recommendation = rating
            break

    # 2. Target Price & Analyst Count
    # Using regex based on research findings
    # Pattern 1: "share price target of Rs 1,157"
    target_match = re.search(r"share price target of Rs ([\d,.]+)", body_text)
    if target_match:
        target_price = target_match.group(1)

    # Pattern 2: "from 39 analysts"
    analyst_match = re.search(r"from (\d+) analysts", body_text)
    if analyst_match:
        analyst_count = analyst_match.group(1)

    return {
        "recommendation": recommendation,
        "target_price": target_price,
        "analyst_coverage": analyst_count
    }

def fetch_analysis(symbol: str):
    screener_data = fetch_screener_data(symbol)
    if "error" in screener_data:
        return screener_data

    trendlyne_data = fetch_trendlyne_info(symbol)
    
    return {
        "company": screener_data["company"],
        "symbol": symbol.upper(),
        "recommendation": trendlyne_data.get("recommendation", "N/A"),
        "target_price": trendlyne_data.get("target_price", "N/A"),
        "analyst_coverage": trendlyne_data.get("analyst_coverage", "N/A"),
        "fundamental_ratios": screener_data["fundamental_ratios"],
        "pros": screener_data["pros"],
        "cons": screener_data["cons"],
        "sources": {
            "fundamentals": f"https://www.screener.in/company/{symbol.upper()}/",
            "recommendations": f"https://trendlyne.com/stock-quotes/NSE/{symbol.upper()}/"
        }
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a stock using Screener.in and Trendlyne")
    parser.add_argument("symbol", help="Stock symbol (e.g., HDFCBANK, RELIANCE)")
    args = parser.parse_args()

    analysis = fetch_analysis(args.symbol)
    print(json.dumps(analysis, indent=2))
