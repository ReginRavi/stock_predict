---
name: fetch_stock_names
description: Retrieves bearish crossover stocks from Screener.in screener
---

# fetch_stock_names

This skill retrieves a list of stock names currently identified as "bearish crossovers" from Screener.in. It can also save this list to a file for persistence.

## Usage

When the user asks for the latest stock list or bearish crossover stocks, you can run this skill to get the most recent data. If the user wants to keep a record, use the saving functionality.

### Examples

**Fetch list only:**
User: "What are the latest bearish crossover stocks?"
Agent: "I'll check the latest list for you. [Runs fetch_stock_names]"

**Fetch and save list:**
User: "Fetch the bearish crossover stocks and save them."
Agent: "I'll fetch the list and save it to the output folder for you. [Runs fetch_stock_names with --save]"

## Scripts

### [get_stocks.py](file:///Users/reginravi/Documents/googlesheet/.agent/skills/fetch_stock_names/get_stocks.py)

This script fetches the stock list and returns it as a JSON object.

```bash
# To just get the list in JSON:
python3 /Users/reginravi/Documents/googlesheet/.agent/skills/fetch_stock_names/get_stocks.py

# To get the list and save it in the 'output' folder:
python3 /Users/reginravi/Documents/googlesheet/.agent/skills/fetch_stock_names/get_stocks.py --save
```

## Data Sources
- **Screener.in**: Bearish crossover screener results

## Dependencies
This skill provides stock lists for:
- `master-equity-analyst` - Stock screening universe
- `stock-comparative-analysis` - Comparison candidates

## Error Handling
- If screener returns empty list: Notify user and suggest alternative screeners
- If network error: Retry up to 3 times with 2-second delays
- If save fails: Return data to user and warn about save failure
