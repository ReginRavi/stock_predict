---
name: analyse_stock
description: Fetches fundamental data and analyst recommendations for single stock analysis
---

# analyse_stock

This skill provides a comprehensive analysis of a stock using fundamental data from Screener.in and analyst recommendations from Trendlyne. It extracts key ratios like PE, ROCE, and ROE, along with qualitative pros/cons and a consensus Buy/Sell/Hold rating.

## Usage

Use this skill when a user asks for an analysis, recommendation, or a summary of a specific stock.

### Example

User: "What is the recommendation for HDFC Bank?"
Agent: "I'll fetch the latest analyst consensus and fundamental data for HDFC Bank. [Runs analyse_stock with symbol HDFCBANK]"

## Scripts

### [analyse.py](file:///Users/reginravi/Documents/googlesheet/.agent/skills/analyse_stock/analyse.py)

The core script that performs the scraping and data extraction.

```bash
# Usage: python3 analyse.py <SYMBOL>
python3 /Users/reginravi/Documents/googlesheet/.agent/skills/analyse_stock/analyse.py HDFCBANK
```

## Data Sources
- **Screener.in**: Fundamental financial data (P/E, ROE, ROCE, debt ratios)
- **Trendlyne**: Analyst recommendations, price targets, pros/cons

## Dependencies
This skill provides raw data for:
- `advanced_analysis` - Deep-dive fundamental analysis
- `stock-comparative-analysis` - Multi-stock comparison

## Error Handling
- If Screener.in unavailable: Return error with retry suggestion
- If Trendlyne unavailable: Provide fundamental data only, mark analyst data as "N/A"
- If symbol not found: Suggest similar symbols based on name matching
