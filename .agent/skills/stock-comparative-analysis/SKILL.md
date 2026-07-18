---
name: stock-comparative-analysis
description: Performs a deep-dive comparison between a list of stocks, covering performance, financials, sector positioning, and risk-return profiles.
---

# Stock Comparative Analysis

Use this skill when the user provides a list of stock tickers or names for comparison. Ensure all data is as of the current date provided in the context.

## Performance Comparison
Analyze and compare the following for all listed stocks:
* **Price Performance:** Compare returns over 1M, 3M, 6M, and 1Y intervals.
* **Market Cap:** Rank stocks by market capitalization.
* **Trading Volume:** Analyze liquidity and recent volume trends.

## Financial Metrics Comparison
Evaluate the fundamental health of each company:
* **Growth:** Revenue and profit growth (YoY/QoQ).
* **Valuation:** Compare P/E, P/B, and EV/EBITDA ratios.
* **Profitability:** Compare ROE, ROA, and EBITDA margins.
* **Health:** Assess Debt-to-Equity and Current ratios.

## Sector Analysis & Risk
* **Positioning:** Identify market share and competitive "moats."
* **Beta:** Compare volatility relative to the broader market.
* **Dividends:** Note yield and payout consistency.
* **Risk:** Identify specific business or regulatory risks.

## Investment Recommendation
Rank the stocks from best to worst investment potential based on:
1.  **Risk-Adjusted Return:** Potential vs. Volatility.
2.  **Allocation:** Suggested weight in a diversified portfolio.
3.  **Horizon:** Recommended holding period (Short/Medium/Long term).

## Data Sources
- **analyse_stock**: Fundamental and technical data for each stock
- **Market Data APIs**: Price history, volume, market cap information
- **Sector Reports**: Industry positioning and competitive landscape

## Dependencies
This skill requires:
- `analyse_stock` - For comprehensive data on each comparison candidate
- Market data sources - For current pricing and performance metrics

## Error Handling
- If stock data incomplete: Proceed with available data, mark missing fields as "N/A"
- If comparison candidate not found: Suggest alternative stocks with similar profiles
- If sector data unavailable: Use available company data for relative comparison

## Output Formatting
* Use clear Markdown headings.
* Use bullet points for readability.
* Create a summary table for the primary Financial Metrics for quick comparison.