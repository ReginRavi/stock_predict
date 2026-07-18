# Stock Analysis Skills

## Quick Reference

| Skill | Purpose | Use When |
|-------|---------|----------|
| `fetch_stock_names` | Get stock lists from screeners | Starting analysis, need stock universe |
| `analyse_stock` | Fetch fundamental data | Need raw data for single stock |
| `stock-comparative-analysis` | Compare multiple stocks | Choosing between 2-5 stocks |
| `market-sentiment` | Indian market mood | Understanding macro context |
| `master-equity-analyst` | Quick screening & rating | Need buy/sell/hold decision |
| `advanced_analysis` | Deep-dive single stock | Portfolio allocation, risk assessment |

## Recommended Workflow

```
1. fetch_stock_names → Get stock list
   ↓
2. market-sentiment → Understand market regime
   ↓
3. master-equity-analyst → Screen and rate stocks
   ↓
4. stock-comparative-analysis → Compare top picks
   ↓
5. advanced_analysis → Deep-dive on final choice
```

## Skill Dependencies

### fetch_stock_names
- **Output**: Stock list for analysis
- **Used by**: master-equity-analyst, stock-comparative-analysis

### analyse_stock
- **Dependencies**: None (primary data source)
- **Used by**: advanced_analysis, stock-comparative-analysis

### market-sentiment
- **Dependencies**: None (macro analysis)
- **Used by**: master-equity-analyst (for market regime)

### master-equity-analyst
- **Dependencies**: analyse_stock, market-sentiment
- **Output**: Rated stock list with buy/sell/hold signals

### stock-comparative-analysis
- **Dependencies**: analyse_stock
- **Used by**: Users comparing multiple options

### advanced_analysis
- **Dependencies**: analyse_stock
- **Used by**: Portfolio managers, risk assessment

## Data Sources

- **Screener.in**: Fundamental financial data
- **Trendlyne**: Analyst recommendations and targets
- **NSE India**: Market data, FII/DII flows
- **Yahoo Finance**: Price history, technical indicators

## Error Handling Standards

- If data source unavailable: Use cached data if <24h old, else notify user
- If symbol not found: Suggest similar symbols
- If partial data: Proceed with available data, mark missing fields as "N/A"

## Output Formats

- **Single Stock**: Comprehensive fundamental + technical analysis
- **Comparison**: Tabular format with key metrics side-by-side
- **Sentiment**: Emoji-based categorization with market heatmap
- **Screening**: Rated list with clear buy/sell/hold signals