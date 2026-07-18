#!/usr/bin/env python3
"""
Market Sentiment Detection Automation Script

This script analyzes market sentiment by monitoring news, social media trends,
and analyst recommendations to provide sentiment insights for stocks and sectors.
"""

import json
import sys
import argparse
import logging
import time
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import requests
from bs4 import BeautifulSoup
import os
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sentiment_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analyzes market sentiment from various sources"""
    
    def __init__(self, cache_dir: str = "sentiment_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        
        # Sentiment keywords
        self.positive_keywords = [
            "bullish", "buy", "strong", "outperform", "upgrade", "growth", "rally",
            "surge", "jump", "gain", "profit", "positive", "optimistic", "rally",
            "momentum", "breakout", "opportunity", "undervalued", "potential"
        ]
        
        self.negative_keywords = [
            "bearish", "sell", "weak", "underperform", "downgrade", "decline",
            "fall", "drop", "loss", "negative", "pessimistic", "crash", "slump",
            "concern", "risk", "overvalued", "caution", "warning", "volatile"
        ]
        
        self.neutral_keywords = [
            "hold", "neutral", "maintain", "stable", "steady", "unchanged",
            "mixed", "cautious", "wait", "monitor", "observe"
        ]
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of a given text using keyword-based approach"""
        if not text:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        text_lower = text.lower()
        
        # Count sentiment keywords
        positive_count = sum(1 for word in self.positive_keywords if word in text_lower)
        negative_count = sum(1 for word in self.negative_keywords if word in text_lower)
        neutral_count = sum(1 for word in self.neutral_keywords if word in text_lower)
        
        total_sentiment_words = positive_count + negative_count + neutral_count
        
        if total_sentiment_words == 0:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        # Calculate sentiment score (-1 to 1)
        score = (positive_count - negative_count) / max(1, total_sentiment_words)
        
        # Determine sentiment label
        if score > 0.2:
            sentiment = "positive"
        elif score < -0.2:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Calculate confidence based on total sentiment words
        confidence = min(1.0, total_sentiment_words / 10.0)
        
        return {
            "sentiment": sentiment,
            "score": round(score, 3),
            "confidence": round(confidence, 3),
            "positive_words": positive_count,
            "negative_words": negative_count,
            "neutral_words": neutral_count,
            "total_words": total_sentiment_words
        }
    
    def fetch_financial_news(self, symbol: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch financial news headlines (mock implementation)"""
        # In a real implementation, this would call news APIs
        # For now, we'll return mock data based on common market themes
        
        mock_news = [
            {
                "title": "Market shows positive momentum amid strong earnings",
                "source": "Financial Times",
                "timestamp": datetime.now().isoformat(),
                "url": "https://example.com/news1"
            },
            {
                "title": "Analysts upgrade tech sector on growth prospects",
                "source": "Bloomberg",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "url": "https://example.com/news2"
            },
            {
                "title": "Concerns over inflation impact market sentiment",
                "source": "Reuters",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "url": "https://example.com/news3"
            },
            {
                "title": "Banking stocks rally on positive economic data",
                "source": "Economic Times",
                "timestamp": (datetime.now() - timedelta(hours=6)).isoformat(),
                "url": "https://example.com/news4"
            },
            {
                "title": "Market volatility expected as investors remain cautious",
                "source": "CNBC",
                "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
                "url": "https://example.com/news5"
            }
        ]
        
        if symbol:
            # Add symbol-specific mock news
            symbol_news = [
                {
                    "title": f"{symbol} reports strong quarterly earnings, beats expectations",
                    "source": "Business Standard",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "url": f"https://example.com/{symbol.lower()}-news1"
                },
                {
                    "title": f"Analysts maintain buy rating on {symbol} with positive outlook",
                    "source": "Moneycontrol",
                    "timestamp": (datetime.now() - timedelta(hours=3)).isoformat(),
                    "url": f"https://example.com/{symbol.lower()}-news2"
                }
            ]
            mock_news.extend(symbol_news)
        
        return mock_news[:limit]
    
    def fetch_analyst_recommendations(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch analyst recommendations for multiple symbols"""
        recommendations = {}
        
        for symbol in symbols:
            # Mock analyst recommendations
            mock_recs = {
                "symbol": symbol,
                "recommendations": [
                    {"broker": "Motilal Oswal", "rating": "Buy", "target": "₹2,500", "date": "2024-01-28"},
                    {"broker": "Kotak Securities", "rating": "Hold", "target": "₹2,200", "date": "2024-01-27"},
                    {"broker": "ICICI Direct", "rating": "Buy", "target": "₹2,450", "date": "2024-01-26"},
                    {"broker": "HDFC Securities", "rating": "Strong Buy", "target": "₹2,600", "date": "2024-01-25"},
                    {"broker": "Sharekhan", "rating": "Buy", "target": "₹2,400", "date": "2024-01-24"}
                ],
                "consensus": "Buy",
                "price_targets": {"min": 2200, "max": 2600, "average": 2430},
                "last_updated": datetime.now().isoformat()
            }
            
            recommendations[symbol] = mock_recs
        
        return recommendations
    
    def calculate_recommendation_sentiment(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate sentiment from analyst recommendations"""
        if not recommendations:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        rating_counts = Counter()
        for rec in recommendations:
            rating_counts[rec["rating"].lower()] += 1
        
        # Map ratings to sentiment scores
        rating_scores = {
            "strong buy": 1.0,
            "buy": 0.75,
            "outperform": 0.5,
            "hold": 0.0,
            "neutral": 0.0,
            "underperform": -0.5,
            "sell": -0.75,
            "strong sell": -1.0
        }
        
        total_score = 0
        total_weight = 0
        
        for rating, count in rating_counts.items():
            score = rating_scores.get(rating, 0.0)
            total_score += score * count
            total_weight += count
        
        if total_weight == 0:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0}
        
        avg_score = total_score / total_weight
        
        if avg_score > 0.3:
            sentiment = "positive"
        elif avg_score < -0.3:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        confidence = min(1.0, total_weight / 5.0)  # More recommendations = higher confidence
        
        return {
            "sentiment": sentiment,
            "score": round(avg_score, 3),
            "confidence": round(confidence, 3),
            "rating_distribution": dict(rating_counts),
            "total_recommendations": total_weight
        }
    
    def analyze_market_sentiment(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Perform comprehensive market sentiment analysis"""
        logger.info("Starting market sentiment analysis")
        
        # Fetch news
        news = self.fetch_financial_news(limit=20)
        
        # Analyze news sentiment
        news_sentiments = []
        for article in news:
            sentiment = self.analyze_text_sentiment(article["title"])
            sentiment["article"] = {
                "title": article["title"],
                "source": article["source"],
                "timestamp": article["timestamp"]
            }
            news_sentiments.append(sentiment)
        
        # Calculate overall news sentiment
        news_scores = [s["score"] for s in news_sentiments]
        overall_news_sentiment = {
            "sentiment": "positive" if sum(news_scores) > 0 else "negative" if sum(news_scores) < 0 else "neutral",
            "average_score": round(sum(news_scores) / len(news_scores), 3) if news_scores else 0.0,
            "total_articles": len(news_sentiments),
            "positive_articles": len([s for s in news_sentiments if s["sentiment"] == "positive"]),
            "negative_articles": len([s for s in news_sentiments if s["sentiment"] == "negative"]),
            "neutral_articles": len([s for s in news_sentiments if s["sentiment"] == "neutral"])
        }
        
        # Analyze symbol-specific sentiment if symbols provided
        symbol_sentiments = {}
        if symbols:
            recommendations = self.fetch_analyst_recommendations(symbols)
            
            for symbol in symbols:
                symbol_news = self.fetch_financial_news(symbol, limit=5)
                symbol_news_sentiments = [self.analyze_text_sentiment(article["title"]) for article in symbol_news]
                
                symbol_recs = recommendations.get(symbol, {}).get("recommendations", [])
                rec_sentiment = self.calculate_recommendation_sentiment(symbol_recs)
                
                # Combine news and recommendation sentiment
                news_score = sum([s["score"] for s in symbol_news_sentiments]) / len(symbol_news_sentiments) if symbol_news_sentiments else 0.0
                rec_score = rec_sentiment["score"]
                
                # Weight recommendations more heavily (70% rec, 30% news)
                combined_score = (rec_score * 0.7) + (news_score * 0.3)
                
                symbol_sentiments[symbol] = {
                    "symbol": symbol,
                    "combined_sentiment": {
                        "sentiment": "positive" if combined_score > 0.2 else "negative" if combined_score < -0.2 else "neutral",
                        "score": round(combined_score, 3),
                        "confidence": round(rec_sentiment["confidence"] * 0.7 + (sum([s["confidence"] for s in symbol_news_sentiments]) / len(symbol_news_sentiments)) * 0.3, 3) if symbol_news_sentiments else rec_sentiment["confidence"]
                    },
                    "news_sentiment": {
                        "sentiment": "positive" if news_score > 0.2 else "negative" if news_score < -0.2 else "neutral",
                        "score": round(news_score, 3),
                        "articles_analyzed": len(symbol_news_sentiments)
                    },
                    "recommendation_sentiment": rec_sentiment,
                    "last_updated": datetime.now().isoformat()
                }
        
        # Generate market insights
        insights = self._generate_market_insights(overall_news_sentiment, symbol_sentiments)
        
        return {
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis_type": "market_sentiment",
                "symbols_analyzed": symbols or [],
                "data_sources": ["news_headlines", "analyst_recommendations"]
            },
            "overall_market_sentiment": overall_news_sentiment,
            "symbol_sentiments": symbol_sentiments,
            "news_analysis": {
                "articles": news_sentiments,
                "trending_topics": self._extract_trending_topics(news)
            },
            "insights": insights,
            "sentiment_trend": "improving" if overall_news_sentiment["average_score"] > 0 else "declining" if overall_news_sentiment["average_score"] < 0 else "stable"
        }
    
    def _extract_trending_topics(self, news: List[Dict[str, Any]]) -> List[str]:
        """Extract trending topics from news headlines"""
        all_words = []
        
        for article in news:
            # Extract keywords from headlines
            words = re.findall(r'\b\w+\b', article["title"].lower())
            # Filter out common words
            filtered_words = [w for w in words if w not in ["the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must"]]
            all_words.extend(filtered_words)
        
        word_counts = Counter(all_words)
        return [word for word, count in word_counts.most_common(10)]
    
    def _generate_market_insights(self, overall_sentiment: Dict[str, Any], symbol_sentiments: Dict[str, Any]) -> List[str]:
        """Generate market insights based on sentiment analysis"""
        insights = []
        
        # Overall market insights
        if overall_sentiment["average_score"] > 0.3:
            insights.append("Market sentiment is strongly positive with bullish momentum")
        elif overall_sentiment["average_score"] < -0.3:
            insights.append("Market sentiment is negative with bearish pressure")
        else:
            insights.append("Market sentiment is neutral with mixed signals")
        
        # News distribution insights
        if overall_sentiment["positive_articles"] > overall_sentiment["negative_articles"] * 2:
            insights.append("News coverage is predominantly positive")
        elif overall_sentiment["negative_articles"] > overall_sentiment["positive_articles"] * 2:
            insights.append("News coverage is predominantly negative")
        
        # Symbol-specific insights
        if symbol_sentiments:
            positive_symbols = [s for s, data in symbol_sentiments.items() if data["combined_sentiment"]["sentiment"] == "positive"]
            negative_symbols = [s for s, data in symbol_sentiments.items() if data["combined_sentiment"]["sentiment"] == "negative"]
            
            if positive_symbols:
                insights.append(f"Positive sentiment detected for: {', '.join(positive_symbols)}")
            if negative_symbols:
                insights.append(f"Negative sentiment detected for: {', '.join(negative_symbols)}")
        
        # Add general market advice
        if overall_sentiment["sentiment"] == "positive":
            insights.append("Current conditions favor equity investments with proper risk management")
        elif overall_sentiment["sentiment"] == "negative":
            insights.append("Consider defensive positioning and wait for clearer market signals")
        else:
            insights.append("Maintain balanced portfolio with selective opportunities")
        
        return insights
    
    def export_sentiment_report(self, analysis: Dict[str, Any], format: str = "json") -> str:
        """Export sentiment analysis to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format.lower() == "json":
            filename = f"sentiment_analysis_{timestamp}.json"
            filepath = self.cache_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(analysis, f, indent=2)
        
        elif format.lower() == "txt":
            filename = f"sentiment_report_{timestamp}.txt"
            filepath = self.cache_dir / filename
            
            with open(filepath, 'w') as f:
                f.write("MARKET SENTIMENT ANALYSIS REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {analysis['metadata']['analysis_timestamp']}\n\n")
                
                f.write("OVERALL MARKET SENTIMENT:\n")
                f.write(f"  Sentiment: {analysis['overall_market_sentiment']['sentiment'].upper()}\n")
                f.write(f"  Score: {analysis['overall_market_sentiment']['average_score']}\n")
                f.write(f"  Articles Analyzed: {analysis['overall_market_sentiment']['total_articles']}\n\n")
                
                if analysis['symbol_sentiments']:
                    f.write("SYMBOL-SPECIFIC SENTIMENT:\n")
                    for symbol, data in analysis['symbol_sentiments'].items():
                        f.write(f"  {symbol}: {data['combined_sentiment']['sentiment'].upper()} (Score: {data['combined_sentiment']['score']})\n")
                    f.write("\n")
                
                f.write("MARKET INSIGHTS:\n")
                for insight in analysis['insights']:
                    f.write(f"  • {insight}\n")
        
        logger.info(f"Exported sentiment report to {filepath}")
        return str(filepath)

def main():
    parser = argparse.ArgumentParser(
        description="Market Sentiment Detection Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --symbols HDFCBANK RELIANCE TCS
  %(prog)s --export-json --export-txt
  %(prog)s --symbols HDFCBANK --verbose
        """
    )
    
    parser.add_argument("--symbols", nargs="*", help="Stock symbols for sentiment analysis")
    parser.add_argument("--export-json", action="store_true", help="Export results to JSON")
    parser.add_argument("--export-txt", action="store_true", help="Export results to text report")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize sentiment analyzer
    analyzer = SentimentAnalyzer()
    
    # Perform sentiment analysis
    start_time = time.time()
    analysis = analyzer.analyze_market_sentiment(args.symbols)
    analysis_time = time.time() - start_time
    
    # Display results
    print(f"\n{'='*60}")
    print("MARKET SENTIMENT ANALYSIS RESULTS")
    print(f"{'='*60}")
    
    # Overall market sentiment
    overall = analysis["overall_market_sentiment"]
    print(f"\nOVERALL MARKET SENTIMENT: {overall['sentiment'].upper()}")
    print(f"Score: {overall['average_score']:.3f}")
    print(f"Articles Analyzed: {overall['total_articles']}")
    print(f"Positive: {overall['positive_articles']} | Negative: {overall['negative_articles']} | Neutral: {overall['neutral_articles']}")
    
    # Symbol-specific sentiment
    if analysis["symbol_sentiments"]:
        print(f"\n{'='*60}")
        print("SYMBOL-SPECIFIC SENTIMENT")
        print(f"{'='*60}")
        for symbol, data in analysis["symbol_sentiments"].items():
            combined = data["combined_sentiment"]
            print(f"\n{symbol}: {combined['sentiment'].upper()} (Score: {combined['score']:.3f})")
            print(f"  News: {data['news_sentiment']['sentiment']} (Score: {data['news_sentiment']['score']:.3f})")
            print(f"  Recommendations: {data['recommendation_sentiment']['sentiment']} (Score: {data['recommendation_sentiment']['score']:.3f})")
    
    # Market insights
    print(f"\n{'='*60}")
    print("MARKET INSIGHTS")
    print(f"{'='*60}")
    for i, insight in enumerate(analysis["insights"], 1):
        print(f"{i}. {insight}")
    
    # Trending topics
    if analysis["news_analysis"]["trending_topics"]:
        print(f"\n{'='*60}")
        print("TRENDING TOPICS")
        print(f"{'='*60}")
        for topic in analysis["news_analysis"]["trending_topics"][:5]:
            print(f"  • {topic}")
    
    print(f"\nAnalysis completed in {analysis_time:.2f} seconds")
    
    # Export results
    exported_files = []
    if args.export_json:
        json_file = analyzer.export_sentiment_report(analysis, "json")
        exported_files.append(json_file)
    
    if args.export_txt:
        txt_file = analyzer.export_sentiment_report(analysis, "txt")
        exported_files.append(txt_file)
    
    if exported_files:
        print(f"\n{'='*60}")
        print("EXPORTED FILES")
        print(f"{'='*60}")
        for file in exported_files:
            print(f"  - {file}")

if __name__ == "__main__":
    main()