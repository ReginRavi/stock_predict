#!/usr/bin/env python3
"""
Comparative Stock Analysis Automation Script

This script analyzes multiple stocks and generates comparative reports
including fundamental metrics, analyst recommendations, and performance rankings.
"""

import json
import sys
import argparse
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import pandas as pd
from pathlib import Path

# Add the skill directory to path for imports
# Get the project root directory (parent of Scripts/)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(project_root, '.agent', 'skills', 'analyse_stock'))

try:
    from analyse_enhanced import fetch_analysis, clear_cache
except ImportError as e:
    print(f"Error: Could not import analyse_enhanced module: {e}")
    print(f"Attempted path: {os.path.join(project_root, '.agent', 'skills', 'analyse_stock')}")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('comparative_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ComparativeAnalyzer:
    """Handles comparative analysis of multiple stocks"""
    
    def __init__(self, output_dir: str = "analysis_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.analyses = {}
        
    def analyze_stocks(self, symbols: List[str], use_cache: bool = True) -> Dict[str, Any]:
        """Analyze multiple stocks and return comparative data"""
        logger.info(f"Starting comparative analysis for {len(symbols)} symbols")
        
        results = {}
        failed_symbols = []
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Analyzing {symbol} ({i}/{len(symbols)})")
            
            try:
                analysis = fetch_analysis(symbol)
                
                if "error" in analysis:
                    logger.warning(f"Failed to analyze {symbol}: {analysis['error']}")
                    failed_symbols.append({"symbol": symbol, "error": analysis["error"]})
                    continue
                
                results[symbol] = analysis
                time.sleep(1)  # Rate limiting to avoid overwhelming sources
                
            except Exception as e:
                logger.error(f"Unexpected error analyzing {symbol}: {e}")
                failed_symbols.append({"symbol": symbol, "error": str(e)})
        
        self.analyses = results
        return {
            "successful_analyses": results,
            "failed_symbols": failed_symbols,
            "summary": self._generate_summary(results, failed_symbols)
        }
    
    def _generate_summary(self, results: Dict[str, Any], failed_symbols: List[Dict]) -> Dict[str, Any]:
        """Generate summary statistics for the analysis"""
        total_symbols = len(results) + len(failed_symbols)
        success_rate = (len(results) / total_symbols * 100) if total_symbols > 0 else 0
        
        # Count analyst recommendations
        recommendation_counts = {}
        for symbol, analysis in results.items():
            rec = analysis.get("analyst_recommendations", {}).get("consensus_rating", "N/A")
            if rec != "N/A":
                recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        return {
            "total_symbols_analyzed": total_symbols,
            "successful_analyses": len(results),
            "failed_analyses": len(failed_symbols),
            "success_rate_percent": round(success_rate, 2),
            "recommendation_distribution": recommendation_counts,
            "analysis_timestamp": datetime.now().isoformat()
        }
    
    def generate_comparison_table(self, metrics: List[str] = None) -> pd.DataFrame:
        """Generate pandas DataFrame with key metrics for comparison"""
        if not self.analyses:
            logger.warning("No analyses available for comparison")
            return pd.DataFrame()
        
        if metrics is None:
            metrics = [
                "market_cap", "pe_ratio", "pb_ratio", "roe", "debt_to_equity",
                "recommendation", "target_price", "analyst_count"
            ]
        
        comparison_data = []
        
        for symbol, analysis in self.analyses.items():
            row = {"symbol": symbol, "company": analysis.get("metadata", {}).get("company", symbol)}
            
            # Extract fundamental ratios
            ratios = analysis.get("fundamentals", {}).get("ratios", {})
            
            # Map common ratio names to standard fields
            ratio_mapping = {
                "Market Cap": "market_cap",
                "Stock P/E": "pe_ratio", 
                "PB Ratio": "pb_ratio",
                "ROE": "roe",
                "Debt to Equity": "debt_to_equity",
                "Dividend Yield": "dividend_yield"
            }
            
            for display_name, field_name in ratio_mapping.items():
                if display_name in ratios:
                    row[field_name] = ratios[display_name]
            
            # Extract analyst recommendations
            recs = analysis.get("analyst_recommendations", {})
            row["recommendation"] = recs.get("consensus_rating", "N/A")
            row["target_price"] = recs.get("target_price", "N/A")
            row["analyst_count"] = recs.get("analyst_count", "N/A")
            
            comparison_data.append(row)
        
        return pd.DataFrame(comparison_data)
    
    def rank_stocks(self, criteria: str = "pe_ratio") -> List[Dict[str, Any]]:
        """Rank stocks based on specified criteria"""
        if not self.analyses:
            return []
        
        df = self.generate_comparison_table()
        
        if df.empty or criteria not in df.columns:
            logger.warning(f"Criteria '{criteria}' not available for ranking")
            return []
        
        # Clean numeric columns for ranking
        numeric_columns = ["market_cap", "pe_ratio", "pb_ratio", "roe", "debt_to_equity", "analyst_count"]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')
        
        # Sort based on criteria (lower is better for PE, PB, Debt; higher is better for ROE, Market Cap)
        ascending = criteria in ["pe_ratio", "pb_ratio", "debt_to_equity"]
        
        ranked_df = df.sort_values(by=criteria, ascending=ascending, na_position='last')
        
        return ranked_df.to_dict('records')
    
    def export_to_excel(self, filename: str = None) -> str:
        """Export comparative analysis to Excel file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparative_analysis_{timestamp}.xlsx"
        
        filepath = self.output_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = {
                "Metric": ["Total Symbols", "Successful Analyses", "Failed Analyses", "Success Rate %"],
                "Value": [
                    len(self.analyses) + len(getattr(self, 'failed_symbols', [])),
                    len(self.analyses),
                    len(getattr(self, 'failed_symbols', [])),
                    f"{(len(self.analyses) / max(1, len(self.analyses) + len(getattr(self, 'failed_symbols', [])))) * 100:.1f}%"
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
            
            # Comparison table
            comparison_df = self.generate_comparison_table()
            if not comparison_df.empty:
                comparison_df.to_excel(writer, sheet_name='Comparison', index=False)
            
            # Rankings by different criteria
            ranking_criteria = ["pe_ratio", "pb_ratio", "roe", "market_cap"]
            for criteria in ranking_criteria:
                try:
                    ranked_data = self.rank_stocks(criteria)
                    if ranked_data:
                        pd.DataFrame(ranked_data).to_excel(
                            writer, sheet_name=f'Ranking_{criteria.upper()}', index=False
                        )
                except Exception as e:
                    logger.warning(f"Could not create ranking for {criteria}: {e}")
        
        logger.info(f"Exported analysis to {filepath}")
        return str(filepath)
    
    def export_to_json(self, filename: str = None) -> str:
        """Export full analysis to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comparative_analysis_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        export_data = {
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "total_symbols": len(self.analyses),
                "output_format": "comparative_analysis_v2.0"
            },
            "analyses": self.analyses,
            "comparison_table": self.generate_comparison_table().to_dict('records') if not self.generate_comparison_table().empty else [],
            "rankings": {
                criteria: self.rank_stocks(criteria) 
                for criteria in ["pe_ratio", "pb_ratio", "roe", "market_cap"]
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported analysis to {filepath}")
        return str(filepath)

def load_symbols_from_file(filepath: str) -> List[str]:
    """Load stock symbols from a text file (one symbol per line)"""
    try:
        with open(filepath, 'r') as f:
            symbols = [line.strip() for line in f if line.strip()]
        logger.info(f"Loaded {len(symbols)} symbols from {filepath}")
        return symbols
    except Exception as e:
        logger.error(f"Failed to load symbols from {filepath}: {e}")
        return []

def main():
    parser = argparse.ArgumentParser(
        description="Comparative Stock Analysis Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s HDFCBANK RELIANCE TCS
  %(prog)s --file symbols.txt
  %(prog)s HDFCBANK RELIANCE --export-excel --export-json
  %(prog)s --file symbols.txt --clear-cache --rank-by pe_ratio
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("symbols", nargs="*", help="Stock symbols to analyze")
    input_group.add_argument("--file", help="File containing stock symbols (one per line)")
    
    # Analysis options
    parser.add_argument("--clear-cache", action="store_true", help="Clear cache before analysis")
    parser.add_argument("--use-cache", action="store_true", default=True, help="Use cached data (default: True)")
    parser.add_argument("--no-cache", action="store_true", help="Skip cached data")
    
    # Output options
    parser.add_argument("--output-dir", default="analysis_reports", help="Output directory for reports")
    parser.add_argument("--export-excel", action="store_true", help="Export to Excel format")
    parser.add_argument("--export-json", action="store_true", help="Export to JSON format")
    parser.add_argument("--rank-by", choices=["pe_ratio", "pb_ratio", "roe", "market_cap"], 
                       help="Rank stocks by specified criteria")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Handle cache options
    if args.no_cache:
        args.use_cache = False
    
    # Get symbols to analyze
    if args.file:
        symbols = load_symbols_from_file(args.file)
        if not symbols:
            print("Error: No symbols found in file")
            sys.exit(1)
    else:
        symbols = [s.upper() for s in args.symbols]
    
    # Clear cache if requested
    if args.clear_cache:
        logger.info("Clearing cache...")
        for symbol in symbols:
            clear_cache(symbol)
    
    # Perform comparative analysis
    analyzer = ComparativeAnalyzer(args.output_dir)
    
    start_time = time.time()
    results = analyzer.analyze_stocks(symbols, use_cache=args.use_cache)
    analysis_time = time.time() - start_time
    
    # Display results
    print(f"\n{'='*60}")
    print("COMPARATIVE STOCK ANALYSIS RESULTS")
    print(f"{'='*60}")
    print(f"Symbols analyzed: {len(results['successful_analyses'])}")
    print(f"Failed analyses: {len(results['failed_symbols'])}")
    print(f"Success rate: {results['summary']['success_rate_percent']}%")
    print(f"Analysis time: {analysis_time:.2f} seconds")
    
    if results['failed_symbols']:
        print(f"\nFailed analyses:")
        for failed in results['failed_symbols']:
            print(f"  - {failed['symbol']}: {failed['error']}")
    
    # Show comparison table
    comparison_df = analyzer.generate_comparison_table()
    if not comparison_df.empty:
        print(f"\n{'='*60}")
        print("COMPARISON TABLE")
        print(f"{'='*60}")
        print(comparison_df.to_string(index=False))
    
    # Show rankings if requested
    if args.rank_by:
        rankings = analyzer.rank_stocks(args.rank_by)
        if rankings:
            print(f"\n{'='*60}")
            print(f"RANKINGS BY {args.rank_by.upper()}")
            print(f"{'='*60}")
            for i, stock in enumerate(rankings[:10], 1):  # Top 10
                print(f"{i:2d}. {stock['symbol']} - {stock.get(args.rank_by, 'N/A')}")
    
    # Export results
    exported_files = []
    if args.export_excel:
        excel_file = analyzer.export_to_excel()
        exported_files.append(excel_file)
    
    if args.export_json:
        json_file = analyzer.export_to_json()
        exported_files.append(json_file)
    
    if exported_files:
        print(f"\n{'='*60}")
        print("EXPORTED FILES")
        print(f"{'='*60}")
        for file in exported_files:
            print(f"  - {file}")
    
    print(f"\nAnalysis completed successfully!")

if __name__ == "__main__":
    main()