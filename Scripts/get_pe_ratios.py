#!/usr/bin/env python3
"""
Fetch Stock P/E, PEG, and PEGY ratios for a list of companies from Screener.in.
Reads company names from a text file, searches for their symbols,
scrapes their P/E, profit growth, and dividend yield, calculates PEG and PEGY,
and saves the output to a CSV file.
"""

import sys
import os
import re
import time
import csv
from datetime import date
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def build_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    return session

def find_latest_input_file(directory: Path = Path("output")) -> Optional[Path]:
    """Find the latest date-formatted txt file in the directory (e.g., YYYY-MM-DD.txt)"""
    if not directory.exists():
        return None
    
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\.txt$")
    files = [f for f in directory.iterdir() if f.is_file() and date_pattern.match(f.name)]
    if not files:
        return None
    
    # Sort files by name (which corresponds to date) and return the latest
    files.sort(reverse=True)
    return files[0]

def search_company_slug(session: requests.Session, company_name: str) -> Optional[str]:
    """Search for a company on Screener and return its URL slug/code."""
    url = "https://www.screener.in/api/company/search/"
    try:
        response = session.get(url, params={"q": company_name}, timeout=15)
        if response.status_code != 200:
            return None
        
        results = response.json()
        if not results:
            return None
        
        # Pick the first search result URL, e.g., "/company/FDC/consolidated/" or "/company/544809/"
        target_path = results[0].get("url", "")
        if not target_path:
            return None
        
        # Extract the slug between "/company/" and the next "/"
        parts = target_path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] == "company":
            return parts[1]
        
    except Exception as e:
        print(f"⚠️ Error searching for '{company_name}': {e}", file=sys.stderr)
        
    return None

def parse_profit_growth(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    """Parse 3-Year and 5-Year Compounded Profit Growth from ranges tables."""
    growth_3y = None
    growth_5y = None
    for table in soup.select("table.ranges-table"):
        header = table.find("th")
        if header and "Compounded Profit Growth" in header.get_text():
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all(["td", "th"])]
                if len(cells) >= 2:
                    label = cells[0]
                    value_str = cells[1].replace("%", "").strip()
                    if not value_str:
                        value_str = "N/A"
                    if "3 Years:" in label:
                        growth_3y = value_str
                    elif "5 Years:" in label:
                        growth_5y = value_str
            break
    return growth_3y, growth_5y

def compute_vlrt_score(peg_str: str, pegy_str: str, mcap_str: str, growth_str: str, div_str: str, pe_str: str) -> dict:
    """
    Computes Quant AMC's VLRT (Valuation, Liquidity, Risk Appetite, Timing) Score (0.0 to 10.0).
    """
    v_score = 1.0
    try:
        peg_val = float(peg_str.strip())
        pegy_val = float(pegy_str.strip())
        if peg_val < 0.6 and pegy_val < 0.6:
            v_score = 2.5
        elif peg_val < 1.0:
            v_score = 2.1
        elif peg_val <= 1.5:
            v_score = 1.6
        elif peg_val <= 2.0:
            v_score = 1.1
        else:
            v_score = 0.5
    except ValueError:
        if "Negative" in peg_str or "Negative" in pegy_str:
            v_score = 0.2
        else:
            v_score = 1.0

    l_score = 1.0
    try:
        mcap_val = float(mcap_str.replace(",", "").strip())
        if mcap_val >= 20000:
            l_score = 2.5
        elif mcap_val >= 5000:
            l_score = 2.2
        elif mcap_val >= 1000:
            l_score = 1.8
        elif mcap_val >= 500:
            l_score = 1.4
        else:
            l_score = 1.0
    except ValueError:
        l_score = 1.0

    r_score = 1.0
    try:
        g_val = float(growth_str.replace("%", "").strip())
        d_val = float(div_str.replace("%", "").strip())
        if g_val > 25 and d_val > 0.5:
            r_score = 2.5
        elif g_val > 15:
            r_score = 2.1
        elif g_val > 0:
            r_score = 1.6
        elif g_val == 0:
            r_score = 1.1
        else:
            r_score = 0.5
    except ValueError:
        r_score = 1.0

    t_score = 1.0
    try:
        pe_val = float(pe_str.replace(",", "").strip())
        if pe_val < 25 and v_score >= 1.6:
            t_score = 2.5
        elif pe_val < 50 and v_score >= 1.5:
            t_score = 2.1
        elif pe_val < 100:
            t_score = 1.5
        else:
            t_score = 0.8
    except ValueError:
        t_score = 1.0

    total_score = round(v_score + l_score + r_score + t_score, 1)
    
    if total_score >= 8.0:
        status = "Strong"
        badge_class = "badge-success"
    elif total_score >= 6.0:
        status = "Moderate"
        badge_class = "badge-warning"
    else:
        status = "Weak"
        badge_class = "badge-danger"

    return {
        "score": total_score,
        "v": round(v_score * 4, 1),
        "l": round(l_score * 4, 1),
        "r": round(r_score * 4, 1),
        "t": round(t_score * 4, 1),
        "status": status,
        "badge_class": badge_class,
        "breakdown": f"V:{round(v_score*4,1)} L:{round(l_score*4,1)} R:{round(r_score*4,1)} T:{round(t_score*4,1)}"
    }

def fetch_company_metrics(session: requests.Session, slug: str) -> Dict[str, str]:
    """Fetch company details, P/E, Market Cap, Growth, Dividend Yield, and calculate PEG & PEGY ratios."""
    url = f"https://www.screener.in/company/{slug}/"
    metrics = {
        "fullname": slug,
        "pe": "N/A",
        "mcap": "N/A",
        "div_yield": "0.00",
        "growth_3y": "N/A",
        "growth_5y": "N/A",
        "peg_3y": "N/A",
        "peg_5y": "N/A",
        "pegy_3y": "N/A",
        "pegy_5y": "N/A"
    }
    try:
        response = session.get(url, timeout=15)
        if response.status_code != 200:
            return metrics
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract full company name from h1
        h1 = soup.select_one("h1")
        if h1:
            metrics["fullname"] = h1.get_text(strip=True)
        
        # Extract ratios
        ratios = {}
        ratio_items = soup.select("#top-ratios li")
        for item in ratio_items:
            name_el = item.select_one(".name")
            val_el = item.select_one(".number")
            if name_el and val_el:
                name_text = name_el.get_text(strip=True)
                val_text = val_el.get_text(strip=True)
                ratios[name_text] = val_text
        
        metrics["pe"] = ratios.get("Stock P/E", ratios.get("P/E", "N/A"))
        metrics["mcap"] = ratios.get("Market Cap", "N/A")
        
        # Extract Dividend Yield
        div_str = ratios.get("Dividend Yield", "0.00").replace("%", "").strip()
        metrics["div_yield"] = div_str if div_str else "0.00"
        
        # Extract compounded profit growth
        growth_3y, growth_5y = parse_profit_growth(soup)
        metrics["growth_3y"] = growth_3y or "N/A"
        metrics["growth_5y"] = growth_5y or "N/A"
        
        # Calculate PEG and PEGY values
        try:
            pe_clean = metrics["pe"].replace(",", "").strip()
            pe_val = float(pe_clean)
            
            div_val = float(metrics["div_yield"].replace(",", "").strip())
            
            for key_growth, key_peg, key_pegy in [
                ("growth_3y", "peg_3y", "pegy_3y"), 
                ("growth_5y", "peg_5y", "pegy_5y")
            ]:
                g_str = metrics[key_growth]
                if g_str and g_str != "N/A":
                    g_val = float(g_str)
                    
                    # PEG calculation
                    if g_val > 0:
                        metrics[key_peg] = f"{pe_val / g_val:.2f}"
                    elif g_val == 0:
                        metrics[key_peg] = "Zero Growth"
                    else:
                        metrics[key_peg] = "Negative Growth"
                    
                    # PEGY calculation: growth_rate + dividend_yield
                    denominator = g_val + div_val
                    if denominator > 0:
                        metrics[key_pegy] = f"{pe_val / denominator:.2f}"
                    elif denominator == 0:
                        metrics[key_pegy] = "Zero Growth+Yield"
                    else:
                        metrics[key_pegy] = "Negative Growth+Yield"
                        
        except (ValueError, TypeError):
            pass
            
    except Exception as e:
        print(f"⚠️ Error fetching details for slug '{slug}': {e}", file=sys.stderr)
        
    return metrics

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch P/E, PEG, and PEGY ratios for companies listed in text file.")
    parser.add_argument("--file", help="Path to input text file containing company names.")
    parser.add_argument("--output", help="Path to save output CSV file.")
    
    args = parser.parse_args()
    
    # 1. Determine input file
    input_file = None
    if args.file:
        input_file = Path(args.file)
    else:
        # Check current directory first, then root directory
        input_file = find_latest_input_file(Path("output"))
        if not input_file:
            # Try root output dir
            input_file = find_latest_input_file(Path("../output"))
            
    if not input_file or not input_file.exists():
        print("❌ Error: Could not find any valid stock lists in 'output/' directory.", file=sys.stderr)
        print("   Please run getstocklist.py first, or specify the file using --file.", file=sys.stderr)
        sys.exit(1)
        
    print(f"📂 Reading company names from: {input_file.resolve()}")
    
    # Read company names
    with open(input_file, "r", encoding="utf-8") as f:
        company_names = [line.strip() for line in f if line.strip()]
        
    if not company_names:
        print("❌ Error: The input file is empty.")
        sys.exit(1)
        
    print(f"🔎 Found {len(company_names)} companies. Initializing crawler...")
    
    # 2. Determine output file
    output_file = None
    if args.output:
        output_file = Path(args.output)
    else:
        # Default to a CSV inside the same directory as the input file
        output_file = input_file.parent / f"peg_ratios_{date.today().isoformat()}.csv"
        
    session = build_session()
    results: List[Dict[str, str]] = []
    
    # Fetch metrics
    for idx, name in enumerate(company_names, 1):
        print(f"[{idx}/{len(company_names)}] Processing: '{name}'...", end="", flush=True)
        
        # Rate limit friendly sleep
        time.sleep(0.5)
        
        slug = search_company_slug(session, name)
        if not slug:
            print(" ❌ Symbol Search Failed")
            results.append({
                "Company Name": name,
                "Screener Slug": "N/A",
                "Company Full Name": "N/A",
                "Stock P/E": "N/A",
                "Market Cap (Cr)": "N/A",
                "Dividend Yield (%)": "N/A",
                "Profit Growth 3Y (%)": "N/A",
                "Profit Growth 5Y (%)": "N/A",
                "PEG Ratio 3Y": "N/A",
                "PEG Ratio 5Y": "N/A",
                "PEGY Ratio 3Y": "N/A",
                "PEGY Ratio 5Y": "N/A",
                "VLRT Score": "N/A",
                "VLRT Breakdown": "N/A"
            })
            continue
            
        time.sleep(0.5)
        metrics = fetch_company_metrics(session, slug)
        
        if metrics["pe"] != "N/A":
            vlrt = compute_vlrt_score(metrics['peg_3y'], metrics['pegy_3y'], metrics['mcap'], metrics['growth_3y'], metrics['div_yield'], metrics['pe'])
            print(f" ✅ P/E: {metrics['pe']} | PEG 3Y: {metrics['peg_3y']} | VLRT: {vlrt['score']}/10")
            results.append({
                "Company Name": name,
                "Screener Slug": slug,
                "Company Full Name": metrics["fullname"],
                "Stock P/E": metrics["pe"],
                "Market Cap (Cr)": metrics["mcap"],
                "Dividend Yield (%)": metrics["div_yield"],
                "Profit Growth 3Y (%)": metrics["growth_3y"],
                "Profit Growth 5Y (%)": metrics["growth_5y"],
                "PEG Ratio 3Y": metrics["peg_3y"],
                "PEG Ratio 5Y": metrics["peg_5y"],
                "PEGY Ratio 3Y": metrics["pegy_3y"],
                "PEGY Ratio 5Y": metrics["pegy_5y"],
                "VLRT Score": str(vlrt["score"]),
                "VLRT Breakdown": vlrt["breakdown"]
            })
        else:
            print(" ❌ Detail Fetch Failed")
            results.append({
                "Company Name": name,
                "Screener Slug": slug,
                "Company Full Name": "N/A",
                "Stock P/E": "N/A",
                "Market Cap (Cr)": "N/A",
                "Dividend Yield (%)": "N/A",
                "Profit Growth 3Y (%)": "N/A",
                "Profit Growth 5Y (%)": "N/A",
                "PEG Ratio 3Y": "N/A",
                "PEG Ratio 5Y": "N/A",
                "PEGY Ratio 3Y": "N/A",
                "PEGY Ratio 5Y": "N/A",
                "VLRT Score": "N/A",
                "VLRT Breakdown": "N/A"
            })
            
    # Write CSV output
    output_file.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "Company Name", "Screener Slug", "Company Full Name", "Stock P/E", 
        "Market Cap (Cr)", "Dividend Yield (%)", "Profit Growth 3Y (%)", 
        "Profit Growth 5Y (%)", "PEG Ratio 3Y", "PEG Ratio 5Y", "PEGY Ratio 3Y", "PEGY Ratio 5Y",
        "VLRT Score", "VLRT Breakdown"
    ]
    
    try:
        with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)
        print(f"\n💾 Saved results to CSV: {output_file.resolve()}")
    except Exception as e:
        print(f"\n❌ Error writing output CSV: {e}", file=sys.stderr)

    # Print summary table
    print("\n" + "=" * 135)
    print(f"{'Company Name':<25} | {'P/E':<6} | {'Div Yield':<9} | {'3Y Growth':<9} | {'PEG 3Y':<8} | {'PEGY 3Y':<8} | {'Mkt Cap (Cr)':<12}")
    print("=" * 135)
    for r in results:
        print(f"{r['Company Name'][:25]:<25} | {r['Stock P/E']:<6} | {r['Dividend Yield (%)']:<9} | {r['Profit Growth 3Y (%)']:<9} | {r['PEG Ratio 3Y']:<8} | {r['PEGY Ratio 3Y']:<8} | {r['Market Cap (Cr)']:<12}")
    print("=" * 135)

if __name__ == "__main__":
    main()
