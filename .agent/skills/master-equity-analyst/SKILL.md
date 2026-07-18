---
name: master-equity-analyst
description: A high-fidelity equity research tool with adaptive market logic and explicit Buy/Sell/Hold execution criteria.
---

# Master Equity Research Analyst

Use this skill to perform deep-dive stock analysis. This skill adapts to market regimes and provides clear, logic-based investment ratings.

## 1. Contextual Awareness (Market Adaptation)
Identify the current market cycle before scoring. Weighting shifts as follows:
* **Bull Market:** Prioritize Growth (60%), Technicals (30%), Value (10%).
* **Bear Market:** Prioritize Solvency/Debt (60%), Dividends (30%), Technicals (10%).
* **Sideways/Chop:** Prioritize Valuation (50%), Support levels (30%), Quality (20%).

## 2. Multi-Factor Screening & Comparison
* **Fundamentals:** P/E vs Peers, YoY Revenue growth, Debt-to-Equity, ROE.
* **Technicals:** RSI (14), 50/200-day Moving Average crossovers, Volume confirmation.
* **Quality:** Moat strength, management track record, and ESG risk.

## 3. Rating Logic & Execution
For every stock, assign one of the following ratings based on the total score and market context:

| Rating | Score | Criteria | Action |
| :--- | :--- | :--- | :--- |
| **STRONG BUY** | 9-10 | Undervalued, high growth, positive momentum. | Immediate entry. |
| **BUY** | 7-8 | Solid fundamentals, fair valuation, healthy trend. | Accumulate on dips. |
| **HOLD** | 5-6 | Great company but overvalued, or sideways trend. | Do not sell; wait for entry. |
| **UNDERPERFORM**| 3-4 | Weakening fundamentals or bearish technicals. | Reduce position size. |
| **SELL** | 1-2 | High debt, negative growth, or broken support levels. | Exit position. |

## 4. Decision Intelligence Output
1.  **Market Regime Note:** State the current market mood (e.g., "Currently in a high-interest rate regime; prioritizing cash flow.")
2.  **Executive Summary Table:** Ticker | Quality Score | **Rating** | Price vs. Target.
3.  **The "Why":** For each stock, provide one **Bull Case** and one **Bear Case**.
4.  **Portfolio Strategy:** Suggested allocation (e.g., 2% for speculative, 5% for core) and an "Entry Trigger" price point.

## Data Sources
- **analyse_stock**: Fundamental metrics and analyst recommendations
- **market-sentiment**: Market regime and macro context
- **Technical Indicators**: RSI, moving averages, volume analysis

## Dependencies
This skill orchestrates:
- `analyse_stock` - For fundamental data extraction
- `market-sentiment` - For market regime determination
- Internal scoring logic - Applies adaptive weighting based on market cycle

## Error Handling
- If fundamental data incomplete: Use available metrics, adjust score weighting
- If market sentiment unclear: Default to "sideways" regime with balanced weighting
- If technical indicators missing: Focus on fundamentals with reduced technical weight

## Examples
- "Evaluate NVDA and MSFT. Should I buy the dip or wait?"
- "Compare the top 5 energy stocks and give me Buy/Sell ratings for a 1-year horizon."