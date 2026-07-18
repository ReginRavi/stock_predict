---
description: Run sequential equity research chain on bearish crossover stocks
---

# Full Equity Research Chain

This workflow chains all 6 stock analysis skills sequentially to perform comprehensive equity research.

## Workflow Steps

### Step 1: Fetch Stock List
**Skill:** `fetch_stock_names`
**Location:** `.agent/skills/fetch_stock_names/SKILL.md`

// turbo
```bash
python3 /Users/reginravi/Documents/googlesheet/.agent/skills/fetch_stock_names/get_stocks.py --save
```

**Output:** List of stock symbols saved to `output/YYYY-MM-DD.txt`

---

### Step 2: Market Sentiment Analysis
**Skill:** `market-sentiment` (indian-market-sentiment-analyst)
**Location:** `.agent/skills/market-sentiment/skill.md`

Read the skill instructions and apply the framework:
- Assess overall market mood (🟢 Bullish / 🟡 Neutral / 🔴 Bearish)
- Analyze FII/DII flows using web search
- Identify RBI policy stance and sectoral rotation
- Create sentiment scorecard table

**Output:** Market heatmap, sentiment emoji for each stock, technical triggers

---

### Step 3: Fundamental Analysis
**Skill:** `analyse_stock`
**Location:** `.agent/skills/analyse_stock/SKILL.md`

For each stock from Step 1, run:

// turbo
```bash
python3 /Users/reginravi/Documents/googlesheet/.agent/skills/analyse_stock/analyse.py <SYMBOL>
```

**Output:** P/E, ROCE, ROE, dividend yield, pros/cons, analyst recommendations

---

### Step 4: Multi-Factor Screening
**Skill:** `stock-multi-factor-screener` (master-equity-analyst)
**Location:** `.agent/skills/stock-multi-factor-screener/SKILL.md`

Read the skill instructions and apply the rating logic:
1. Identify current market regime (Bull/Bear/Sideways)
2. Adjust scoring weights based on regime
3. Score each stock (0-10) on fundamentals, technicals, quality
4. Assign rating: STRONG BUY (9-10) / BUY (7-8) / HOLD (5-6) / UNDERPERFORM (3-4) / SELL (1-2)

**Output:** Rating table with scores and actionable signals

---

### Step 5: Comparative Analysis
**Skill:** `stock-comparative-analysis`
**Location:** `.agent/skills/stock-comparative-analysis/SKILL.md`

Read the skill instructions and perform deep-dive comparison:
- Compare price performance (1M, 3M, 6M, 1Y)
- Compare financial metrics (P/E, P/B, ROE, D/E)
- Assess sector positioning and risk (Beta, dividends)
- Rank by risk-adjusted return potential

**Output:** Ranking table with allocation weights and investment horizon

---

### Step 6: Advanced Deep-Dive Analysis
**Skill:** `advanced_analysis`
**Location:** `.agent/skills/advanced_analysis/SKILL.md`

For top-ranked stocks, read the skill instructions and apply the full framework:
- Quick Snapshot with overall rating
- Fundamental Strength Score (0-10)
- Market Dynamics Rating (0-10)
- Risk Assessment Matrix
- Valuation scenarios (Bear/Base/Bull cases)
- Technical trigger system (entry/exit points)

**Output:** Comprehensive research report with action plan

## Output
Create a walkthrough artifact with:
1. Sentiment Scorecard table
2. Fundamental comparison table
3. Final ranking with ratings and action items
4. Entry/exit strategies for top picks
