import requests
from bs4 import BeautifulSoup
import json
import sys
import argparse
import hashlib
import time
import logging
from typing import Dict, Any, Optional
from functools import wraps
import os
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from circuitbreaker import circuit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
CACHE_TTL = 3600  # 1 hour in seconds
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
MAX_RETRIES = 3
CIRCUIT_BREAKER_FAILURE_THRESHOLD = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT = 60

# Ensure cache directory exists
os.makedirs(CACHE_DIR, exist_ok=True)

class CacheManager:
    """Simple file-based cache manager for stock analysis data"""
    
    @staticmethod
    def get_cache_key(symbol: str, source: str) -> str:
        """Generate cache key for symbol and source"""
        return hashlib.md5(f"{symbol}_{source}".encode()).hexdigest()
    
    @staticmethod
    def get_cache_path(cache_key: str) -> str:
        """Get full path for cache file"""
        return os.path.join(CACHE_DIR, f"{cache_key}.json")
    
    @staticmethod
    def is_cache_valid(cache_path: str) -> bool:
        """Check if cache file exists and is still valid"""
        if not os.path.exists(cache_path):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_path)
        return file_age < CACHE_TTL
    
    @staticmethod
    def get(cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache"""
        cache_path = CacheManager.get_cache_path(cache_key)
        
        if not CacheManager.is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_path}: {e}")
            return None
    
    @staticmethod
    def set(cache_key: str, data: Dict[str, Any]) -> None:
        """Store data in cache"""
        cache_path = CacheManager.get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Cached data for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_path}: {e}")

def build_session() -> requests.Session:
    """Build HTTP session with proper headers and timeout"""
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
    return session

def retry_on_request_error(retry_state):
    """Custom retry condition for request errors"""
    if retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        return isinstance(exception, (requests.RequestException, requests.Timeout, requests.ConnectionError))
    return False

@circuit(failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD, 
          recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT)
@retry(stop=stop_after_attempt(MAX_RETRIES),
       wait=wait_exponential(multiplier=1, min=4, max=10),
       retry=retry_if_exception_type((requests.RequestException, requests.Timeout, requests.ConnectionError)))
def fetch_screener_data(symbol: str) -> Dict[str, Any]:
    """Fetch fundamental data from Screener.in with caching and resilience"""
    cache_key = CacheManager.get_cache_key(symbol, "screener")
    cached_data = CacheManager.get(cache_key)
    
    if cached_data:
        logger.info(f"Returning cached Screener data for {symbol}")
        return cached_data
    
    url = f"https://www.screener.in/company/{symbol.upper()}/"
    session = build_session()
    
    try:
        response = session.get(url, timeout=30)
        if response.status_code == 404:
            error_data = {"error": f"Symbol {symbol} not found on Screener.in"}
            CacheManager.set(cache_key, error_data)
            return error_data
        response.raise_for_status()
    except requests.RequestException as e:
        error_data = {"error": f"Error fetching Screener data: {e}"}
        logger.error(f"Request failed for {symbol}: {e}")
        raise
    
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

    data = {
        "company": company_name,
        "fundamental_ratios": ratios,
        "pros": pros,
        "cons": cons,
        "timestamp": time.time(),
        "source": "screener.in"
    }
    
    CacheManager.set(cache_key, data)
    return data

@circuit(failure_threshold=CIRCUIT_BREAKER_FAILURE_THRESHOLD, 
          recovery_timeout=CIRCUIT_BREAKER_RECOVERY_TIMEOUT)
@retry(stop=stop_after_attempt(MAX_RETRIES),
       wait=wait_exponential(multiplier=1, min=4, max=10),
       retry=retry_if_exception_type((requests.RequestException, requests.Timeout, requests.ConnectionError)))
def fetch_trendlyne_info(symbol: str) -> Dict[str, Any]:
    """Fetch analyst recommendations from Trendlyne with caching and resilience"""
    cache_key = CacheManager.get_cache_key(symbol, "trendlyne")
    cached_data = CacheManager.get(cache_key)
    
    if cached_data:
        logger.info(f"Returning cached Trendlyne data for {symbol}")
        return cached_data
    
    url = f"https://trendlyne.com/stock-quotes/NSE/{symbol.upper()}/"
    session = build_session()
    
    try:
        response = session.get(url, timeout=30, allow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        body_text = soup.get_text()
    except requests.RequestException as e:
        logger.warning(f"Request failed for {symbol} on Trendlyne: {e}")
        body_text = ""
    
    import re
    
    recommendation = "N/A"
    target_price = "N/A"
    analyst_count = "N/A"

    # Extract consensus rating
    ratings = ["Strong Buy", "Buy", "Hold", "Sell", "Strong Sell"]
    for rating in ratings:
        if re.search(rf"\b{rating}\b", body_text, re.IGNORECASE):
            recommendation = rating
            break

    # Extract target price
    target_match = re.search(r"share price target of Rs ([\d,.]+)", body_text)
    if target_match:
        target_price = target_match.group(1)

    # Extract analyst count
    analyst_match = re.search(r"from (\d+) analysts", body_text)
    if analyst_match:
        analyst_count = analyst_match.group(1)

    data = {
        "recommendation": recommendation,
        "target_price": target_price,
        "analyst_coverage": analyst_count,
        "timestamp": time.time(),
        "source": "trendlyne.com"
    }
    
    CacheManager.set(cache_key, data)
    return data

def standardize_output(symbol: str, screener_data: Dict[str, Any], trendlyne_data: Dict[str, Any]) -> Dict[str, Any]:
    """Standardize JSON output format"""
    if "error" in screener_data:
        return screener_data
    
    return {
        "metadata": {
            "symbol": symbol.upper(),
            "company": screener_data.get("company", symbol),
            "analysis_timestamp": time.time(),
            "cache_ttl_seconds": CACHE_TTL,
            "version": "2.0"
        },
        "fundamentals": {
            "ratios": screener_data.get("fundamental_ratios", {}),
            "pros": screener_data.get("pros", []),
            "cons": screener_data.get("cons", []),
            "source": screener_data.get("source", "screener.in"),
            "last_updated": screener_data.get("timestamp")
        },
        "analyst_recommendations": {
            "consensus_rating": trendlyne_data.get("recommendation", "N/A"),
            "target_price": trendlyne_data.get("target_price", "N/A"),
            "analyst_count": trendlyne_data.get("analyst_coverage", "N/A"),
            "source": trendlyne_data.get("source", "trendlyne.com"),
            "last_updated": trendlyne_data.get("timestamp")
        },
        "sources": {
            "fundamentals": f"https://www.screener.in/company/{symbol.upper()}/",
            "recommendations": f"https://trendlyne.com/stock-quotes/NSE/{symbol.upper()}/"
        },
        "performance": {
            "cache_hits": 2 if (CacheManager.get(CacheManager.get_cache_key(symbol, "screener")) and 
                              CacheManager.get(CacheManager.get_cache_key(symbol, "trendlyne"))) else 0,
            "request_time_ms": None  # Could be implemented if needed
        }
    }

def fetch_analysis(symbol: str) -> Dict[str, Any]:
    """Main analysis function with enhanced error handling and logging"""
    logger.info(f"Starting analysis for symbol: {symbol}")
    
    try:
        screener_data = fetch_screener_data(symbol)
        if "error" in screener_data:
            logger.error(f"Screener data fetch failed: {screener_data['error']}")
            return screener_data

        trendlyne_data = fetch_trendlyne_info(symbol)
        
        # Handle Trendlyne errors gracefully
        if "error" in trendlyne_data:
            logger.warning(f"Trendlyne data fetch failed: {trendlyne_data['error']}")
            trendlyne_data = {
                "recommendation": "N/A",
                "target_price": "N/A", 
                "analyst_coverage": "N/A",
                "error": trendlyne_data["error"]
            }
        
        return standardize_output(symbol, screener_data, trendlyne_data)
        
    except Exception as e:
        logger.error(f"Analysis failed for {symbol}: {e}")
        return {"error": f"Analysis failed: {str(e)}", "symbol": symbol.upper()}

def clear_cache(symbol: Optional[str] = None) -> None:
    """Clear cache for specific symbol or all cache"""
    if symbol:
        # Clear cache for specific symbol
        for source in ["screener", "trendlyne"]:
            cache_key = CacheManager.get_cache_key(symbol, source)
            cache_path = CacheManager.get_cache_path(cache_key)
            if os.path.exists(cache_path):
                os.remove(cache_path)
                logger.info(f"Cleared cache for {symbol} from {source}")
    else:
        # Clear all cache
        for filename in os.listdir(CACHE_DIR):
            if filename.endswith('.json'):
                os.remove(os.path.join(CACHE_DIR, filename))
        logger.info("Cleared all cache")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a stock using Screener.in and Trendlyne with caching and resilience")
    parser.add_argument("symbol", help="Stock symbol (e.g., HDFCBANK, RELIANCE)")
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache before analysis")
    parser.add_argument("--cache-only", action="store_true", help="Return cached data only if available")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if args.clear_cache:
        clear_cache(args.symbol)
    
    analysis = fetch_analysis(args.symbol)
    print(json.dumps(analysis, indent=2))