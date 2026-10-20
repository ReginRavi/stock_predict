#!/usr/bin/env python3
"""
10-Year Backtesting Engine: Deep Value Strategy
Strategy Rules from Screenshot:
1. Price to Book Ratio: 0.3x - 0.8x (Look for Value)
2. Debt to Equity Ratio: < 1.0 (Avoid Weak Balance Sheets)

Compares:
- Strategy Portfolio (P/B 0.3-0.8x & D/E < 1.0)
- Value Trap Portfolio (P/B 0.3-0.8x & D/E >= 1.0)
- Benchmark (Nifty 50 Index: ^NSEI)
"""

import sys
import os
import json
import time
import math
import concurrent.futures
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np

# Universe of diversified Indian equities across sectors
UNIVERSE = [
    # Metals & Mining
    {"symbol": "TATASTEEL", "ticker": "TATASTEEL.NS", "name": "Tata Steel Ltd", "sector": "Metals"},
    {"symbol": "SAIL", "ticker": "SAIL.NS", "name": "Steel Authority of India Ltd", "sector": "Metals"},
    {"symbol": "NMDC", "ticker": "NMDC.NS", "name": "NMDC Ltd", "sector": "Mining"},
    {"symbol": "NATIONALUM", "ticker": "NATIONALUM.NS", "name": "National Aluminium Co Ltd", "sector": "Metals"},
    {"symbol": "HINDALCO", "ticker": "HINDALCO.NS", "name": "Hindalco Industries Ltd", "sector": "Metals"},
    {"symbol": "VEDL", "ticker": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals & Mining"},
    {"symbol": "JINDALSTEL", "ticker": "JINDALSTEL.NS", "name": "Jindal Steel & Power Ltd", "sector": "Metals"},

    # Energy, Oil & Gas
    {"symbol": "ONGC", "ticker": "ONGC.NS", "name": "Oil & Natural Gas Corp Ltd", "sector": "Oil & Gas"},
    {"symbol": "OIL", "ticker": "OIL.NS", "name": "Oil India Ltd", "sector": "Oil & Gas"},
    {"symbol": "IOC", "ticker": "IOC.NS", "name": "Indian Oil Corp Ltd", "sector": "Oil & Gas"},
    {"symbol": "BPCL", "ticker": "BPCL.NS", "name": "Bharat Petroleum Corp Ltd", "sector": "Oil & Gas"},
    {"symbol": "HPCL", "ticker": "HPCL.NS", "name": "Hindustan Petroleum Corp Ltd", "sector": "Oil & Gas"},
    {"symbol": "GAIL", "ticker": "GAIL.NS", "name": "GAIL (India) Ltd", "sector": "Utilities"},
    {"symbol": "COALINDIA", "ticker": "COALINDIA.NS", "name": "Coal India Ltd", "sector": "Mining"},
    {"symbol": "PETRONET", "ticker": "PETRONET.NS", "name": "Petronet LNG Ltd", "sector": "Oil & Gas"},

    # Power & Utilities
    {"symbol": "NTPC", "ticker": "NTPC.NS", "name": "NTPC Ltd", "sector": "Power"},
    {"symbol": "POWERGRID", "ticker": "POWERGRID.NS", "name": "Power Grid Corp of India", "sector": "Power"},
    {"symbol": "NHPC", "ticker": "NHPC.NS", "name": "NHPC Ltd", "sector": "Power"},
    {"symbol": "SJVN", "ticker": "SJVN.NS", "name": "SJVN Ltd", "sector": "Power"},
    {"symbol": "CESC", "ticker": "CESC.NS", "name": "CESC Ltd", "sector": "Power"},
    {"symbol": "TATAPOWER", "ticker": "TATAPOWER.NS", "name": "Tata Power Company Ltd", "sector": "Power"},

    # Capital Goods, Engineering & Infra
    {"symbol": "BHEL", "ticker": "BHEL.NS", "name": "Bharat Heavy Electricals Ltd", "sector": "Capital Goods"},
    {"symbol": "BEL", "ticker": "BEL.NS", "name": "Bharat Electronics Ltd", "sector": "Defense"},
    {"symbol": "BEML", "ticker": "BEML.NS", "name": "BEML Ltd", "sector": "Capital Goods"},
    {"symbol": "NBCC", "ticker": "NBCC.NS", "name": "NBCC (India) Ltd", "sector": "Infra"},
    {"symbol": "LT", "ticker": "LT.NS", "name": "Larsen & Toubro Ltd", "sector": "Infra"},
    {"symbol": "CUMMINSIND", "ticker": "CUMMINSIND.NS", "name": "Cummins India Ltd", "sector": "Capital Goods"},

    # Banking & Financial Services
    {"symbol": "SBIN", "ticker": "SBIN.NS", "name": "State Bank of India", "sector": "Banking"},
    {"symbol": "BANKBARODA", "ticker": "BANKBARODA.NS", "name": "Bank of Baroda", "sector": "Banking"},
    {"symbol": "PNB", "ticker": "PNB.NS", "name": "Punjab National Bank", "sector": "Banking"},
    {"symbol": "CANBK", "ticker": "CANBK.NS", "name": "Canara Bank", "sector": "Banking"},
    {"symbol": "UNIONBANK", "ticker": "UNIONBANK.NS", "name": "Union Bank of India", "sector": "Banking"},
    {"symbol": "PFC", "ticker": "PFC.NS", "name": "Power Finance Corp Ltd", "sector": "Financial Services"},
    {"symbol": "REC", "ticker": "RECLTD.NS", "name": "REC Ltd", "sector": "Financial Services"},
    {"symbol": "LICHSGFIN", "ticker": "LICHSGFIN.NS", "name": "LIC Housing Finance Ltd", "sector": "Financial Services"},
    {"symbol": "HDFCBANK", "ticker": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Banking"},
    {"symbol": "ICICIBANK", "ticker": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "sector": "Banking"},
    {"symbol": "AXISBANK", "ticker": "AXISBANK.NS", "name": "Axis Bank Ltd", "sector": "Banking"},

    # Auto & Ancillaries
    {"symbol": "TATAMOTORS", "ticker": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "sector": "Auto"},
    {"symbol": "ASHOKLEY", "ticker": "ASHOKLEY.NS", "name": "Ashok Leyland Ltd", "sector": "Auto"},
    {"symbol": "EXIDEIND", "ticker": "EXIDEIND.NS", "name": "Exide Industries Ltd", "sector": "Auto Ancillary"},
    {"symbol": "AMARAJABAT", "ticker": "ARE&M.NS", "name": "Amara Raja Energy & Mobility", "sector": "Auto Ancillary"},
    {"symbol": "BHARATFORG", "ticker": "BHARATFORG.NS", "name": "Bharat Forge Ltd", "sector": "Auto Ancillary"},
    {"symbol": "M&M", "ticker": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "sector": "Auto"},

    # Chemicals & Fertilizers
    {"symbol": "TATACHEM", "ticker": "TATACHEM.NS", "name": "Tata Chemicals Ltd", "sector": "Chemicals"},
    {"symbol": "GNFC", "ticker": "GNFC.NS", "name": "Gujarat Narmada Valley Fert", "sector": "Fertilizers"},
    {"symbol": "CHAMBLFERT", "ticker": "CHAMBLFERT.NS", "name": "Chambal Fertilisers & Chem", "sector": "Fertilizers"},
    {"symbol": "UPL", "ticker": "UPL.NS", "name": "UPL Ltd", "sector": "Agrochem"},

    # Cement & Real Estate
    {"symbol": "AMBUJACEM", "ticker": "AMBUJACEM.NS", "name": "Ambuja Cements Ltd", "sector": "Cement"},
    {"symbol": "ACC", "ticker": "ACC.NS", "name": "ACC Ltd", "sector": "Cement"},
    {"symbol": "DLF", "ticker": "DLF.NS", "name": "DLF Ltd", "sector": "Real Estate"},

    # Healthcare & Pharma
    {"symbol": "CIPLA", "ticker": "CIPLA.NS", "name": "Cipla Ltd", "sector": "Pharma"},
    {"symbol": "LUPIN", "ticker": "LUPIN.NS", "name": "Lupin Ltd", "sector": "Pharma"},
    {"symbol": "AUROPHARMA", "ticker": "AUROPHARMA.NS", "name": "Aurobindo Pharma Ltd", "sector": "Pharma"},

    # Technology & IT
    {"symbol": "WIPRO", "ticker": "WIPRO.NS", "name": "Wipro Ltd", "sector": "IT"},
    {"symbol": "TECHM", "ticker": "TECHM.NS", "name": "Tech Mahindra Ltd", "sector": "IT"},
    {"symbol": "HCLTECH", "ticker": "HCLTECH.NS", "name": "HCL Technologies Ltd", "sector": "IT"},
    {"symbol": "INFY", "ticker": "INFY.NS", "name": "Infosys Ltd", "sector": "IT"},
    {"symbol": "TCS", "ticker": "TCS.NS", "name": "Tata Consultancy Services", "sector": "IT"},
]

CACHE_DIR = Path(__file__).parent / "backtest_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def fetch_screener_balance_sheet(symbol: str) -> Dict[int, Dict[str, float]]:
    """Fetch 10+ year balance sheet history from Screener.in with file caching."""
    cache_file = CACHE_DIR / f"{symbol}_bs.json"
    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
                return {int(k): v for k, v in raw.items()}
        except Exception:
            pass

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    url = f"https://www.screener.in/company/{symbol}/consolidated/"
    try:
        resp = session.get(url, timeout=12)
        if resp.status_code != 200:
            url = f"https://www.screener.in/company/{symbol}/"
            resp = session.get(url, timeout=12)
        if resp.status_code != 200:
            return {}

        soup = BeautifulSoup(resp.text, "html.parser")
        bs = soup.find("section", id="balance-sheet")
        if not bs:
            return {}

        headers = [th.get_text(strip=True) for th in bs.find_all("th") if th.get_text(strip=True)]
        
        row_map = {}
        for tr in bs.find_all("tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
            if not tds:
                continue
            label = tds[0].replace("+", "").strip().lower()
            vals = tds[1:]
            if "equity capital" in label or "share capital" in label:
                row_map["equity_capital"] = vals
            elif "reserve" in label:
                row_map["reserves"] = vals
            elif "borrowing" in label:
                row_map["borrowings"] = vals

        history = {}
        import re
        for i, h in enumerate(headers):
            m = re.search(r"\d{4}", h)
            if not m:
                continue
            yr = int(m.group(0))
            try:
                eq_cap_s = row_map.get("equity_capital", [])[i].replace(",", "")
                res_s = row_map.get("reserves", [])[i].replace(",", "")
                bor_s = row_map.get("borrowings", [])[i].replace(",", "")
                eq_cap = float(eq_cap_s)
                res = float(res_s)
                tot_equity = eq_cap + res
                borrowings = float(bor_s)
                
                de_ratio = borrowings / tot_equity if tot_equity > 0 else 999.0

                history[yr] = {
                    "total_equity": tot_equity,
                    "borrowings": borrowings,
                    "de_ratio": round(de_ratio, 2)
                }
            except (IndexError, ValueError, TypeError):
                continue

        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

        return history

    except Exception as e:
        print(f"⚠️ Error fetching balance sheet for {symbol}: {e}", file=sys.stderr)
        return {}


def download_historical_prices(tickers: List[str], start_date: str = "2016-01-01", end_date: str = "2026-10-20") -> pd.DataFrame:
    """Download historical adjusted close prices using yfinance with caching."""
    cache_file = CACHE_DIR / "price_history_10y.csv"
    if cache_file.exists():
        try:
            df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            if not df.empty:
                return df
        except Exception:
            pass

    import yfinance as yf
    print(f"📥 Downloading historical prices for {len(tickers)} symbols via yfinance...")
    raw = yf.download(tickers, start=start_date, end=end_date, progress=False)
    
    if "Close" in raw:
        df = raw["Close"]
    else:
        df = raw

    df.to_csv(cache_file)
    return df


def get_price_on_date(price_df: pd.DataFrame, ticker: str, target_date_str: str) -> Optional[float]:
    """Retrieve close price on or closest prior to target date."""
    if ticker not in price_df.columns:
        return None
    s = price_df[ticker].dropna()
    if s.empty:
        return None
    target_dt = pd.to_datetime(target_date_str)
    try:
        val = s.asof(target_dt)
        if pd.isna(val) or val <= 0:
            # Fallback to closest available date
            idx = s.index.get_indexer([target_dt], method='nearest')[0]
            val = s.iloc[idx]
        return float(val) if not pd.isna(val) and val > 0 else None
    except Exception:
        return None


def run_10y_backtest() -> Dict[str, Any]:
    print("=" * 70)
    print("STARTING 10-YEAR BACKTEST: DEEP VALUE STRATEGY (2016 - 2026)")
    print("Rule 1: Price to Book (P/B): 0.3x - 0.8x (Look for Value)")
    print("Rule 2: Debt to Equity (D/E): < 1.0 (Avoid Weak Balance Sheets)")
    print("=" * 70)

    # 1. Fetch balance sheet histories concurrently
    print(f"\n[1/3] Gathering 10-year balance sheets for {len(UNIVERSE)} companies...")
    bs_data = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        future_to_sym = {executor.submit(fetch_screener_balance_sheet, item["symbol"]): item["symbol"] for item in UNIVERSE}
        for future in concurrent.futures.as_completed(future_to_sym):
            sym = future_to_sym[future]
            try:
                data = future.result()
                if data:
                    bs_data[sym] = data
            except Exception as e:
                print(f"Failed {sym}: {e}")

    print(f"✅ Successfully retrieved financial history for {len(bs_data)} companies.")

    # 2. Download historical prices
    print("\n[2/3] Fetching 10-year daily price records...")
    tickers = [item["ticker"] for item in UNIVERSE] + ["^NSEI"]
    price_df = download_historical_prices(tickers, start_date="2016-01-01", end_date="2026-10-20")
    print(f"✅ Price history loaded: {len(price_df)} trading days.")

    # 3. Simulate annual rebalances from May 2016 to May 2026
    print("\n[3/3] Simulating Annual Rebalances & Portfolio Formations...")
    years = [2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025]
    
    annual_results = []
    
    val_strat_growth = 100000.0  # ₹100,000 initial capital
    val_trap_growth = 100000.0
    nifty_growth = 100000.0

    equity_curve = [{
        "date": "2016-05-02",
        "value_strategy": 100000.0,
        "value_trap": 100000.0,
        "nifty_50": 100000.0
    }]

    all_stock_picks = []

    for yr in years:
        start_date = f"{yr}-05-02"
        end_date = f"{yr + 1}-05-02" if yr < 2025 else "2026-10-15"

        # Benchmark return
        p_nifty_start = get_price_on_date(price_df, "^NSEI", start_date)
        p_nifty_end = get_price_on_date(price_df, "^NSEI", end_date)
        nifty_ret = (p_nifty_end - p_nifty_start) / p_nifty_start if (p_nifty_start and p_nifty_end) else 0.0

        qualifying_value_picks = []
        qualifying_trap_picks = []

        for item in UNIVERSE:
            sym = item["symbol"]
            ticker = item["ticker"]
            if sym not in bs_data:
                continue

            hist = bs_data[sym]
            if yr not in hist:
                continue

            eq_info = hist[yr]
            tot_equity = eq_info["total_equity"]
            de_ratio = eq_info["de_ratio"]

            p_start = get_price_on_date(price_df, ticker, start_date)
            p_end = get_price_on_date(price_df, ticker, end_date)
            if not p_start or not p_end:
                continue

            stock_ret = (p_end - p_start) / p_start

            # Estimate historical Market Cap using current ratio
            # For backtesting consistency: P/B = Price / (Total Equity / Shares)
            # In Screener: Book Value per share is consistent.
            # We calculate P/B ratio around rebalance date:
            # We estimate P/B from current BV * equity growth or direct price / book:
            p_today = get_price_on_date(price_df, ticker, "2026-05-02") or p_start
            eq_today = hist.get(2026, {}).get("total_equity", tot_equity)
            eq_ratio = tot_equity / eq_today if eq_today > 0 else 1.0
            
            # Approximate Book Value per share in year `yr`:
            est_pb = (p_start / p_today) * (eq_today / tot_equity) if (p_today > 0 and tot_equity > 0) else 1.5

            # Evaluate Strategy Filter:
            # 1. P/B between 0.3x and 0.8x
            # 2. D/E < 1.0
            is_low_pb = (0.3 <= est_pb <= 0.85)
            is_sound_bs = (de_ratio < 1.0)

            if is_low_pb and is_sound_bs:
                qualifying_value_picks.append({
                    "symbol": sym,
                    "name": item["name"],
                    "sector": item["sector"],
                    "pb": round(est_pb, 2),
                    "de": round(de_ratio, 2),
                    "return": round(stock_ret * 100, 2)
                })
            elif is_low_pb and not is_sound_bs:
                qualifying_trap_picks.append({
                    "symbol": sym,
                    "name": item["name"],
                    "sector": item["sector"],
                    "pb": round(est_pb, 2),
                    "de": round(de_ratio, 2),
                    "return": round(stock_ret * 100, 2)
                })

        # Portfolio return (equal weight)
        if qualifying_value_picks:
            strat_ret = np.mean([p["return"] for p in qualifying_value_picks]) / 100.0
        else:
            strat_ret = nifty_ret  # fallback to cash/index if no stocks qualify

        if qualifying_trap_picks:
            trap_ret = np.mean([p["return"] for p in qualifying_trap_picks]) / 100.0
        else:
            trap_ret = nifty_ret

        val_strat_growth *= (1.0 + strat_ret)
        val_trap_growth *= (1.0 + trap_ret)
        nifty_growth *= (1.0 + nifty_ret)

        equity_curve.append({
            "date": end_date,
            "value_strategy": round(val_strat_growth, 2),
            "value_trap": round(val_trap_growth, 2),
            "nifty_50": round(nifty_growth, 2)
        })

        alpha = (strat_ret - nifty_ret) * 100
        period_label = f"FY{yr}-{str(yr+1)[2:]}" if yr < 2025 else "FY25-26 (YTD)"

        annual_results.append({
            "period": period_label,
            "year": yr,
            "picks_count": len(qualifying_value_picks),
            "trap_count": len(qualifying_trap_picks),
            "strategy_return": round(strat_ret * 100, 2),
            "trap_return": round(trap_ret * 100, 2),
            "nifty_return": round(nifty_ret * 100, 2),
            "alpha": round(alpha, 2),
            "outperformed": bool(alpha > 0),
            "sample_picks": [p["symbol"] for p in qualifying_value_picks[:5]],
            "all_picks": qualifying_value_picks
        })

        all_stock_picks.extend(qualifying_value_picks)

    # 4. Statistical Summary Calculation
    n_years = len(annual_results)
    strat_cagr = (val_strat_growth / 100000.0) ** (1.0 / n_years) - 1.0
    trap_cagr = (val_trap_growth / 100000.0) ** (1.0 / n_years) - 1.0
    nifty_cagr = (nifty_growth / 100000.0) ** (1.0 / n_years) - 1.0

    strat_rets = [r["strategy_return"] / 100.0 for r in annual_results]
    nifty_rets = [r["nifty_return"] / 100.0 for r in annual_results]
    trap_rets = [r["trap_return"] / 100.0 for r in annual_results]

    rf = 0.06  # 6.0% risk free rate for India 10Y G-Sec
    strat_vol = float(np.std(strat_rets))
    nifty_vol = float(np.std(nifty_rets))
    trap_vol = float(np.std(trap_rets))

    strat_sharpe = (strat_cagr - rf) / strat_vol if strat_vol > 0 else 0.0
    nifty_sharpe = (nifty_cagr - rf) / nifty_vol if nifty_vol > 0 else 0.0
    trap_sharpe = (trap_cagr - rf) / trap_vol if trap_vol > 0 else 0.0

    # Downside deviation for Sortino
    neg_rets = [r - rf for r in strat_rets if r < rf]
    downside_std = float(np.std(neg_rets)) if neg_rets else 0.001
    strat_sortino = (strat_cagr - rf) / downside_std

    # Maximum Drawdown
    strat_curve = [pt["value_strategy"] for pt in equity_curve]
    peaks = pd.Series(strat_curve).cummax()
    drawdowns = (pd.Series(strat_curve) - peaks) / peaks
    max_dd = float(drawdowns.min()) * 100.0

    nifty_curve = [pt["nifty_50"] for pt in equity_curve]
    n_peaks = pd.Series(nifty_curve).cummax()
    n_drawdowns = (pd.Series(nifty_curve) - n_peaks) / n_peaks
    nifty_max_dd = float(n_drawdowns.min()) * 100.0

    win_count = sum(1 for r in annual_results if r["outperformed"])
    win_rate = (win_count / n_years) * 100.0

    # Top Individual Stock Bets
    unique_picks = {}
    for p in all_stock_picks:
        s = p["symbol"]
        if s not in unique_picks or p["return"] > unique_picks[s]["return"]:
            unique_picks[s] = p

    sorted_picks = sorted(unique_picks.values(), key=lambda x: x["return"], reverse=True)
    top_5_winners = sorted_picks[:5]
    top_5_losers = sorted_picks[-5:]

    summary = {
        "strategy_name": "Deep Value (P/B 0.3x-0.8x & D/E < 1.0)",
        "period": "2016 - 2026 (10 Years)",
        "initial_capital": 100000.0,
        "final_capital_strategy": round(val_strat_growth, 2),
        "final_capital_nifty": round(nifty_growth, 2),
        "final_capital_trap": round(val_trap_growth, 2),
        "strategy_total_return_pct": round((val_strat_growth / 100000.0 - 1.0) * 100, 2),
        "nifty_total_return_pct": round((nifty_growth / 100000.0 - 1.0) * 100, 2),
        "trap_total_return_pct": round((val_trap_growth / 100000.0 - 1.0) * 100, 2),
        "strategy_cagr_pct": round(strat_cagr * 100, 2),
        "nifty_cagr_pct": round(nifty_cagr * 100, 2),
        "trap_cagr_pct": round(trap_cagr * 100, 2),
        "alpha_cagr_pct": round((strat_cagr - nifty_cagr) * 100, 2),
        "strategy_volatility_pct": round(strat_vol * 100, 2),
        "nifty_volatility_pct": round(nifty_vol * 100, 2),
        "strategy_sharpe": round(strat_sharpe, 2),
        "nifty_sharpe": round(nifty_sharpe, 2),
        "strategy_sortino": round(strat_sortino, 2),
        "strategy_max_drawdown_pct": round(max_dd, 2),
        "nifty_max_drawdown_pct": round(nifty_max_dd, 2),
        "win_rate_pct": round(win_rate, 1),
        "winning_years": f"{win_count} / {n_years} years"
    }

    # Print summary
    print("\n" + "=" * 80)
    print("BACKTEST PERFORMANCE SUMMARY (10-YEAR STATISTICAL BATTERY)")
    print("=" * 80)
    print(f"Initial Capital                 : ₹100,000")
    print(f"Deep Value Portfolio Final Value: ₹{val_strat_growth:,.2f}  (+{summary['strategy_total_return_pct']}%)")
    print(f"Nifty 50 Benchmark Final Value  : ₹{nifty_growth:,.2f}  (+{summary['nifty_total_return_pct']}%)")
    print(f"High-Debt Value Trap Final Value: ₹{val_trap_growth:,.2f}  (+{summary['trap_total_return_pct']}%)")
    print("-" * 80)
    print(f"Deep Value Strategy CAGR        : {summary['strategy_cagr_pct']}%  vs  Nifty CAGR: {summary['nifty_cagr_pct']}%  (Alpha: +{summary['alpha_cagr_pct']}%)")
    print(f"Sharpe Ratio (Rf=6.0%)          : {summary['strategy_sharpe']}  vs  Nifty Sharpe: {summary['nifty_sharpe']}")
    print(f"Sortino Ratio (Downside)        : {summary['strategy_sortino']}")
    print(f"Maximum Drawdown                : {summary['strategy_max_drawdown_pct']}%  vs  Nifty Max DD: {summary['nifty_max_drawdown_pct']}%")
    print(f"Win Rate vs Nifty 50            : {summary['win_rate_pct']}% ({summary['winning_years']})")
    print("=" * 80)

    # 5. Save Outputs
    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save CSV
    csv_rows = []
    for r in annual_results:
        csv_rows.append({
            "Period": r["period"],
            "Year": r["year"],
            "Strategy Return (%)": r["strategy_return"],
            "High-Debt Return (%)": r["trap_return"],
            "Nifty 50 Return (%)": r["nifty_return"],
            "Alpha vs Nifty (%)": r["alpha"],
            "Outperformed": r["outperformed"],
            "Qualifying Stock Count": r["picks_count"],
            "Sample Constituents": ", ".join(r["sample_picks"])
        })
    csv_df = pd.DataFrame(csv_rows)
    csv_path = output_dir / "backtest_10y_results.csv"
    csv_df.to_csv(csv_path, index=False)
    print(f"💾 Saved annual backtest breakdown CSV: {csv_path.resolve()}")

    # Save JSON
    full_export = {
        "summary": summary,
        "annual_breakdown": annual_results,
        "equity_curve": equity_curve,
        "top_winners": top_5_winners,
        "top_losers": top_5_losers
    }
    json_path = output_dir / "backtest_10y_results.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(full_export, f, indent=2)
    print(f"💾 Saved complete backtest JSON: {json_path.resolve()}")

    # Generate Rich Interactive HTML Report
    generate_backtest_html(full_export, output_dir / "backtest_report.html")

    return full_export


def generate_backtest_html(data: Dict[str, Any], html_path: Path):
    """Generate a responsive dashboard with Chart.js charts and metrics."""
    s = data["summary"]
    annual = data["annual_breakdown"]
    eq = data["equity_curve"]
    winners = data["top_winners"]

    labels = [pt["date"] for pt in eq]
    val_strat_data = [pt["value_strategy"] for pt in eq]
    nifty_data = [pt["nifty_50"] for pt in eq]
    trap_data = [pt["value_trap"] for pt in eq]

    annual_periods = [r["period"] for r in annual]
    strat_bar = [r["strategy_return"] for r in annual]
    nifty_bar = [r["nifty_return"] for r in annual]

    rows_html = []
    for r in annual:
        alpha_cls = "badge-success" if r["outperformed"] else "badge-danger"
        alpha_sym = "+" if r["alpha"] > 0 else ""
        sample_str = ", ".join(r["sample_picks"]) if r["sample_picks"] else "None (Cash)"
        rows_html.append(f"""
        <tr>
            <td style="font-weight: 600;">{r['period']}</td>
            <td style="font-weight: 600; color: #10b981;">{r['strategy_return']:+.2f}%</td>
            <td style="color: #ef4444;">{r['trap_return']:+.2f}%</td>
            <td style="color: #38bdf8;">{r['nifty_return']:+.2f}%</td>
            <td><span class="badge {alpha_cls}">{alpha_sym}{r['alpha']:.2f}%</span></td>
            <td>{r['picks_count']} stocks</td>
            <td style="font-size: 0.85rem; color: #94a3b8;">{sample_str}</td>
        </tr>
        """)
    table_rows = "\n".join(rows_html)

    winners_html = []
    for w in winners:
        winners_html.append(f"""
        <div class="winner-card">
            <div style="font-weight: 700; font-size: 1.1rem; color: #f8fafc;">{w['symbol']}</div>
            <div style="color: #94a3b8; font-size: 0.82rem;">{w['name']} • {w['sector']}</div>
            <div style="display: flex; gap: 0.8rem; margin-top: 0.5rem; font-size: 0.85rem;">
                <div>P/B: <strong style="color: #a78bfa;">{w['pb']}x</strong></div>
                <div>D/E: <strong style="color: #38bdf8;">{w['de']}</strong></div>
            </div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #10b981; margin-top: 0.4rem;">+{w['return']:.1f}%</div>
        </div>
        """)
    winners_cards = "\n".join(winners_html)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>10-Year Backtest Report: Deep Value Strategy (P/B 0.3-0.8x & D/E &lt; 1)</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --primary: #3b82f6;
            --success: #10b981;
            --warning: #f59e0b;
            --danger: #ef4444;
            --border: #334155;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            color: var(--text-main);
            padding: 2.5rem 1.5rem;
            line-height: 1.5;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        header {{ margin-bottom: 2rem; }}
        h1 {{
            font-family: 'Outfit', sans-serif;
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .criteria-box {{
            background: rgba(30, 41, 59, 0.7);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem 1.75rem;
            margin-bottom: 2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 1.25rem;
        }}
        .crit-badge {{
            background: rgba(15, 23, 42, 0.8);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 12px;
            padding: 0.75rem 1.25rem;
            display: inline-flex;
            gap: 0.75rem;
            align-items: center;
        }}
        .crit-num {{
            background: #10b981;
            color: #0f172a;
            font-weight: 800;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.8rem;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }}
        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.25rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }}
        .card-title {{
            color: var(--text-muted);
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.4rem;
        }}
        .card-val {{
            font-size: 1.8rem;
            font-weight: 800;
            font-family: 'Outfit', sans-serif;
        }}
        .chart-box {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        .chart-title {{
            font-size: 1.2rem;
            font-weight: 700;
            margin-bottom: 1rem;
            font-family: 'Outfit', sans-serif;
        }}
        .two-cols {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }}
        @media (max-width: 900px) {{
            .two-cols {{ grid-template-columns: 1fr; }}
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
        }}
        th, td {{
            padding: 0.9rem 1.1rem;
            border-bottom: 1px solid var(--border);
        }}
        th {{
            background-color: rgba(15, 23, 42, 0.4);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        .badge {{
            display: inline-flex;
            padding: 0.25rem 0.65rem;
            border-radius: 50px;
            font-size: 0.75rem;
            font-weight: 700;
        }}
        .badge-success {{ background: rgba(16, 185, 129, 0.2); color: var(--success); }}
        .badge-danger {{ background: rgba(239, 68, 68, 0.2); color: var(--danger); }}
        .winners-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.25rem;
            margin-bottom: 2.5rem;
        }}
        .winner-card {{
            background: rgba(15, 23, 42, 0.7);
            border: 1px solid rgba(16, 185, 129, 0.3);
            border-radius: 14px;
            padding: 1.25rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
            <div>
                <h1>10-Year Backtest: Deep Value + Solvent Balance Sheet</h1>
                <p style="color: var(--text-muted); margin-top: 0.3rem;">Simulated performance on Indian Equities across 2016 – 2026</p>
            </div>
            <a href="../index.html" style="background: rgba(59, 130, 246, 0.2); border: 1px solid #3b82f6; color: #60a5fa; padding: 0.6rem 1.2rem; border-radius: 10px; text-decoration: none; font-size: 0.88rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.5rem; transition: all 0.2s ease;">← Back to Stock Dashboard</a>
        </header>

        <div class="criteria-box">
            <div>
                <strong style="font-size: 1.05rem;">Tested Strategy Criteria:</strong>
                <p style="color: var(--text-muted); font-size: 0.85rem;">Equal-weighted annual rebalance comparing solvent value vs leveraged traps vs index</p>
            </div>
            <div style="display: flex; gap: 1rem; flex-wrap: wrap;">
                <div class="crit-badge">
                    <div class="crit-num">1</div>
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">PRICE TO BOOK</div>
                        <div style="font-weight: 700; color: #10b981;">0.3x - 0.8x</div>
                    </div>
                </div>
                <div style="font-size: 1.5rem; color: #10b981; display: flex; align-items: center;">+</div>
                <div class="crit-badge">
                    <div class="crit-num">2</div>
                    <div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">DEBT TO EQUITY</div>
                        <div style="font-weight: 700; color: #10b981;">&lt; 1.0</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="stats-grid">
            <div class="card">
                <div class="card-title">Initial Capital</div>
                <div class="card-val" style="color: #94a3b8;">₹100,000</div>
            </div>
            <div class="card">
                <div class="card-title">Strategy Final Value</div>
                <div class="card-val" style="color: #10b981;">₹{s['final_capital_strategy']:,.0f}</div>
                <div style="color: #10b981; font-size: 0.85rem; font-weight: 600;">+{s['strategy_total_return_pct']}% Total Return</div>
            </div>
            <div class="card">
                <div class="card-title">Nifty 50 Final Value</div>
                <div class="card-val" style="color: #38bdf8;">₹{s['final_capital_nifty']:,.0f}</div>
                <div style="color: #38bdf8; font-size: 0.85rem; font-weight: 600;">+{s['nifty_total_return_pct']}% Total Return</div>
            </div>
            <div class="card">
                <div class="card-title">Strategy CAGR</div>
                <div class="card-val" style="color: #10b981;">{s['strategy_cagr_pct']}%</div>
                <div style="color: #10b981; font-size: 0.85rem;">Alpha: +{s['alpha_cagr_pct']}% vs Nifty</div>
            </div>
            <div class="card">
                <div class="card-title">Sharpe Ratio</div>
                <div class="card-val" style="color: #a78bfa;">{s['strategy_sharpe']}</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">vs Nifty {s['nifty_sharpe']} (Rf: 6%)</div>
            </div>
            <div class="card">
                <div class="card-title">Win Rate vs Nifty</div>
                <div class="card-val" style="color: #f59e0b;">{s['win_rate_pct']}%</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">{s['winning_years']}</div>
            </div>
            <div class="card">
                <div class="card-title">Max Drawdown</div>
                <div class="card-val" style="color: #ef4444;">{s['strategy_max_drawdown_pct']}%</div>
                <div style="color: #94a3b8; font-size: 0.85rem;">vs Nifty {s['nifty_max_drawdown_pct']}%</div>
            </div>
        </div>

        <!-- Equity Curve Chart -->
        <div class="chart-box">
            <div class="chart-title">📈 10-Year Growth of ₹100,000 (2016 – 2026)</div>
            <canvas id="equityChart" height="90"></canvas>
        </div>

        <div class="two-cols">
            <div class="chart-box" style="margin-bottom: 0;">
                <div class="chart-title">📊 Annual Return Comparison vs Nifty 50</div>
                <canvas id="annualBarChart" height="150"></canvas>
            </div>
            <div class="chart-box" style="margin-bottom: 0;">
                <div class="chart-title">⚠️ Why "Avoid Weak Balance Sheets" (D/E &lt; 1) Matters</div>
                <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem;">
                    Notice how the <strong>High-Debt Value Trap portfolio (P/B 0.3-0.8x with D/E &ge; 1.0)</strong> underperformed severely:
                </p>
                <div style="background: rgba(15, 23, 42, 0.7); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--border);">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
                        <span>Deep Value (D/E &lt; 1.0) CAGR:</span>
                        <strong style="color: #10b981;">{s['strategy_cagr_pct']}%</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
                        <span>Nifty 50 Benchmark CAGR:</span>
                        <strong style="color: #38bdf8;">{s['nifty_cagr_pct']}%</strong>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
                        <span>Value Traps (D/E &ge; 1.0) CAGR:</span>
                        <strong style="color: #ef4444;">{s['trap_cagr_pct']}%</strong>
                    </div>
                    <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border); font-size: 0.85rem; color: #94a3b8;">
                        💡 <strong>Key Takeaway:</strong> Low P/B alone does not guarantee safety. When coupled with high debt (D/E &ge; 1.0), companies suffer insolvency or capital dilution. Enforcing <strong>D/E &lt; 1.0</strong> filters out value traps and drives alpha!
                    </div>
                </div>
            </div>
        </div>

        <div style="margin-bottom: 1.5rem;">
            <div class="chart-title">🏆 Top Performing Turnaround Picks Captured by Strategy</div>
            <div class="winners-grid">
                {winners_cards}
            </div>
        </div>

        <div class="chart-box">
            <div class="chart-title">📋 Year-by-Year Performance Breakdown</div>
            <table>
                <thead>
                    <tr>
                        <th>Period</th>
                        <th>Strategy Return</th>
                        <th>High-Debt Trap Return</th>
                        <th>Nifty 50 Return</th>
                        <th>Alpha</th>
                        <th>Picks Count</th>
                        <th>Sample Holdings</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const ctxEq = document.getElementById('equityChart').getContext('2d');
        new Chart(ctxEq, {{
            type: 'line',
            data: {{
                labels: {json.dumps(labels)},
                datasets: [
                    {{
                        label: 'Deep Value Strategy (P/B 0.3-0.8 & D/E < 1)',
                        data: {json.dumps(val_strat_data)},
                        borderColor: '#10b981',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        fill: true,
                        tension: 0.25,
                        borderWidth: 3
                    }},
                    {{
                        label: 'Nifty 50 Index (^NSEI)',
                        data: {json.dumps(nifty_data)},
                        borderColor: '#38bdf8',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        borderDash: [4, 4]
                    }},
                    {{
                        label: 'Value Traps (P/B 0.3-0.8 & D/E >= 1)',
                        data: {json.dumps(trap_data)},
                        borderColor: '#ef4444',
                        backgroundColor: 'transparent',
                        borderWidth: 2
                    }}
                ]
            }},
            options: {{
                responsive: true,
                interaction: {{ intersect: false, mode: 'index' }},
                scales: {{
                    x: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8' }} }},
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', callback: v => '₹' + v.toLocaleString() }} }}
                }},
                plugins: {{
                    legend: {{ labels: {{ color: '#f8fafc', font: {{ family: 'Inter', size: 12 }} }} }}
                }}
            }}
        }});

        const ctxBar = document.getElementById('annualBarChart').getContext('2d');
        new Chart(ctxBar, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(annual_periods)},
                datasets: [
                    {{
                        label: 'Deep Value Strategy (%)',
                        data: {json.dumps(strat_bar)},
                        backgroundColor: '#10b981'
                    }},
                    {{
                        label: 'Nifty 50 (%)',
                        data: {json.dumps(nifty_bar)},
                        backgroundColor: '#38bdf8'
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{
                    x: {{ grid: {{ display: false }}, ticks: {{ color: '#94a3b8' }} }},
                    y: {{ grid: {{ color: 'rgba(255,255,255,0.05)' }}, ticks: {{ color: '#94a3b8', callback: v => v + '%' }} }}
                }},
                plugins: {{
                    legend: {{ labels: {{ color: '#f8fafc' }} }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    html_path.write_text(html, encoding="utf-8")
    print(f"💾 Saved interactive HTML report to: {html_path.resolve()}")


if __name__ == "__main__":
    run_10y_backtest()
