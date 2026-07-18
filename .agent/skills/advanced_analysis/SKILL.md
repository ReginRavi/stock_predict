---
name: advanced_analysis
description: Deep-dive financial analysis framework for comprehensive stock evaluation
---

# advanced_analysis

This skill performs a deep-dive financial analysis of a stock using a highly structured framework. It covers everything from fundamental strength scores and business moats to market dynamics, risk matrices, and technical triggers.

## Instructions for the Agent

When this skill is triggered, you MUST follow the framework below strictly. Use the `analyse_stock` skill or the `analyse.py` script (if available) to gather the raw data (ratios, pros/cons, recommendations) for the stock symbol. Then, synthesize that data into the comprehensive report format described.

---

### Analysis Framework: Analyze {stock_symbol}

#### QUICK SNAPSHOT
Provide instant overview:
• Current Rating: [0-10]
• Buy/Hold/Sell Signal
• Risk Level: [Low/Medium/High]
• One-line verdict
• Key alert flags (if any)

#### FUNDAMENTAL STRENGTH SCORE (Rate 0-10):
**A. Financial Power**
• Balance Sheet Health: Debt/Equity Ratio, Current Ratio, Quick Ratio, Asset Quality.
• Profit Machine: Margin Trends, Revenue Growth, Earnings Quality, Cash Flow Strength.
• Efficiency Metrics: ROE/ROA/ROIC, Asset Turnover, Working Capital Management.

**B. Business Moat Analysis**
• Competitive Advantages, Market Share Trends, Brand Value, Entry Barriers, Innovation Pipeline.

**C. Management Quality**
• Track Record, Capital Allocation, Insider Trading, Corporate Governance.

#### MARKET DYNAMICS RATING (0-10):
• **Technical Signals**: Price Action (Multiple timeframes), Volume Analysis, Momentum Indicators, Support/Resistance Levels.
• **Market Sentiment**: Institutional Holdings, Analyst Coverage, Social Sentiment, Options Flow.
• **Industry Position**: Sector Strength, Peer Comparison, Market Share Trends.

#### RISK ASSESSMENT MATRIX:
Rate each risk (0-10) and provide mitigation:
• Market Risk, Business Risk, Financial Risk, Management Risk, Regulatory Risk, Economic Risk, Competition Risk, Valuation Risk.

#### GROWTH CATALYST IDENTIFICATION:
List and rate potential catalysts (0-10):
• Short-term (0-6 months)
• Medium-term (6-18 months)
• Long-term (18+ months)

#### VALUATION ANALYSIS:
Generate 3 scenarios with probability scores:
**Bear Case**: Target Price, Key Assumptions, Probability (%), Risk Factors.
**Base Case**: Target Price, Key Assumptions, Probability (%), Risk Factors.
**Bull Case**: Target Price, Key Assumptions, Probability (%), Risk Factors.

#### SMART MONEY ANALYSIS:
• Institutional Movements, Insider Trading patterns, Options Flow Analysis, Hedge Fund Positions.

#### TECHNICAL TRIGGER SYSTEM:
Create alert system for:
• **Entry Points**: Primary, Secondary, Aggressive.
• **Exit Points**: Profit Targets, Stop Losses, Warning Signals.

#### POSITION MANAGEMENT:
• Suggested Position Size, Scaling Strategy, Hedging Opportunities, Portfolio Fit Analysis.

#### MONITORING DASHBOARD:
Key Metrics to Track: Daily Checks, Weekly Reviews, Monthly Assessments, Quarterly Deep Dives.

#### FINAL VERDICT:
Provide weighted scores (0-10):
• Overall Rating, Risk-Adjusted Return Potential, Timeline Confidence, Quality Score, Growth Score, Value Score, Momentum Score.

#### ACTION PLAN:
List 3 specific actions with: Impact Rating, Urgency Level, Execution Difficulty, Expected Outcome.

---

### After analysis, always provide:
1. Three highest-conviction insights
2. Three biggest risk factors
3. Three key monitoring triggers

### End with:
"Would you like to:
A) Explore any component in detail
B) See comparison with competitors
C) Get specific entry/exit strategies
D) Analyze different time frames
E) Review alternative scenarios
F) Generate monitoring checklist"

## Data Sources
- **analyse_stock**: Raw fundamental data, analyst recommendations
- **Technical Analysis Tools**: Chart patterns, momentum indicators
- **Market Intelligence**: Institutional flows, options data, insider trading

## Dependencies
This skill uses:
- `analyse_stock` - For fetching raw fundamental data
- `fetch_stock_names` - For getting stock lists (optional)
- Market sentiment data - For contextual analysis

## Error Handling
- If fundamental data unavailable: Use cached data if <24h old, else notify user
- If technical indicators missing: Focus on fundamental analysis with reduced technical weight
- If incomplete data: Proceed with available information, clearly mark gaps in analysis

*(Note: All numbers and ratings should include brief explanations for context.)*
