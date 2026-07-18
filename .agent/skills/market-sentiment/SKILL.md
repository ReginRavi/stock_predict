---
name: indian-market-sentiment-analyst
description: Specialized analyzer for the Indian stock market (NSE/BSE), evaluating investor sentiment, sectoral rotations, and technical momentum using a 3-tier emoji system.
---

# Indian Market Sentiment Analyst

Use this skill when analyzing a list of Indian companies, Nifty/Sensex indices, or sector-specific data. This skill integrates domestic macro-economic triggers with local technical analysis.

## 1. Sentiment Categorization (Emoji Framework)
Strictly apply the following labels based on the data provided:
* 🟢 **BULLISH:** Price above 200-day EMA, RSI between 50-70, and positive DII/FII net inflows.
* 🟡 **NEUTRAL:** Range-bound price action, RSI near 50, and mixed institutional participation.
* 🔴 **BEARISH:** Price below 200-day EMA, RSI < 40, and heavy FII selling or "Distribution" patterns.

## 2. Mandatory Analysis Pillars
1.  **Macro-Context (The Catalyst):** Identify key Indian triggers like the Union Budget, RBI Repo Rate decisions, or FII (Foreign Institutional Investor) flows.
2.  **Sectoral Rotation:** Analyze which NSE sectoral indices (e.g., NIFTY BANK, NIFTY IT, NIFTY PHARMA) are leading or lagging.
3.  **Technical Depth:** Evaluate support/resistance levels, volume spikes, and moving average crossovers (Death Cross/Golden Cross).

## 3. Decision & Ranking Logic
* **Top Bullish Picks:** Must be companies showing "Relative Strength" (outperforming the Nifty 50 during a correction).
* **Risk Areas:** Identify "Value Traps" or sectors facing regulatory headwinds (e.g., RBI tightening for NBFCs).
* **Sentiment Forecast:** A data-backed prediction for the next 1-3 months based on current derivative data (Put-Call Ratio/PCR).

## 4. Output Formatting
* **Overall Market Heatmap:** A summary status of Nifty 50 and Sensex.
* **The "Sentiment Scorecard":** A table with columns: [Company | Sentiment Emoji | Technical Trigger | Verdict].
* **Actionable Insight:** Explicitly state whether the current phase favors "SIP/Long-term Accumulation" or "Cash/Defensive Positioning."

## Data Sources
- **NSE India**: FII/DII flows, sectoral indices data
- **Yahoo Finance**: Price data, technical indicators (RSI, moving averages)
- **Options Chain**: Put-Call Ratio (PCR) for sentiment confirmation

## Dependencies
This skill provides market context for:
- `master-equity-analyst` - Market regime determination
- Individual stock analysis within broader market context

## Error Handling
- If FII/DII data unavailable: Use price action and volume as primary indicators
- If options data missing: Rely on technical indicators and institutional flows
- If sectoral indices unavailable: Use Nifty 50 as proxy for market sentiment

## Examples
- "Analyze the sentiment for Reliance, HDFC Bank, and TCS after their Q3 results."
- "What is the market mood heading into the February Union Budget?"