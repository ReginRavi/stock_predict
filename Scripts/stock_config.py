"""
Configuration Settings for Stock Analysis System

This module provides centralized configuration management for all stock analysis
components including caching, retry policies, API settings, and more.
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import json
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """Configuration for caching system"""
    # Cache TTL settings (in seconds)
    default_ttl: int = 3600  # 1 hour
    screener_ttl: int = 1800  # 30 minutes
    trendlyne_ttl: int = 1800  # 30 minutes
    news_ttl: int = 300  # 5 minutes
    sentiment_ttl: int = 600  # 10 minutes
    
    # Cache storage settings
    cache_dir: str = "cache"
    use_redis: bool = False
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    
    # Cache cleanup settings
    max_cache_size_mb: int = 100
    cleanup_interval_hours: int = 24

@dataclass
class RetryConfig:
    """Configuration for retry policies"""
    # General retry settings
    max_retries: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    
    # Request-specific settings
    request_timeout: float = 30.0  # seconds
    connect_timeout: float = 10.0  # seconds
    read_timeout: float = 20.0  # seconds
    
    # Retry conditions
    retry_on_status_codes: list = field(default_factory=lambda: [429, 500, 502, 503, 504])
    retry_on_exceptions: list = field(default_factory=lambda: [
        "requests.exceptions.Timeout",
        "requests.exceptions.ConnectionError",
        "requests.exceptions.HTTPError"
    ])

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern"""
    failure_threshold: int = 5
    recovery_timeout: int = 60  # seconds
    expected_exception: str = "requests.exceptions.RequestException"
    fallback_function: Optional[str] = None

@dataclass
class APIConfig:
    """Configuration for external APIs"""
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # User agent and headers
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    default_headers: Dict[str, str] = field(default_factory=dict)
    
    # API endpoints
    screener_base_url: str = "https://www.screener.in"
    trendlyne_base_url: str = "https://trendlyne.com"
    
    # API keys (if needed for future enhancements)
    news_api_key: Optional[str] = None
    alpha_vantage_key: Optional[str] = None

@dataclass
class LoggingConfig:
    """Configuration for logging system"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = "stock_analysis.log"
    max_file_size_mb: int = 10
    backup_count: int = 5
    console_output: bool = True

@dataclass
class AnalysisConfig:
    """Configuration for analysis parameters"""
    # Sentiment analysis
    sentiment_confidence_threshold: float = 0.3
    max_news_articles: int = 20
    max_analyst_recommendations: int = 10
    
    # Comparative analysis
    max_symbols_per_analysis: int = 50
    default_ranking_criteria: list = field(default_factory=lambda: ["pe_ratio", "pb_ratio", "roe", "market_cap"])
    
    # Output formats
    include_metadata: bool = True
    include_performance_metrics: bool = True
    decimal_places: int = 3

@dataclass
class StockAnalysisConfig:
    """Main configuration class for the entire stock analysis system"""
    cache: CacheConfig = field(default_factory=CacheConfig)
    retry: RetryConfig = field(default_factory=RetryConfig)
    circuit_breaker: CircuitBreakerConfig = field(default_factory=CircuitBreakerConfig)
    api: APIConfig = field(default_factory=APIConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    
    # Environment and deployment settings
    environment: str = "development"
    debug: bool = False
    config_file: Optional[str] = None
    
    def __post_init__(self):
        """Post-initialization setup"""
        # Load from config file if specified
        if self.config_file and os.path.exists(self.config_file):
            self.load_from_file(self.config_file)
        
        # Override with environment variables
        self.load_from_environment()
        
        # Setup logging
        self.setup_logging()
        
        # Create cache directory if needed
        if not self.cache.use_redis:
            Path(self.cache.cache_dir).mkdir(parents=True, exist_ok=True)
    
    def load_from_file(self, config_file: str) -> None:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Update configuration with file data
            for section_name, section_data in config_data.items():
                if hasattr(self, section_name):
                    section = getattr(self, section_name)
                    for key, value in section_data.items():
                        if hasattr(section, key):
                            setattr(section, key, value)
            
            logger.info(f"Configuration loaded from {config_file}")
            
        except Exception as e:
            logger.warning(f"Failed to load config from {config_file}: {e}")
    
    def load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            # Cache settings
            "STOCK_ANALYSIS_CACHE_TTL": ("cache.default_ttl", int),
            "STOCK_ANALYSIS_CACHE_DIR": ("cache.cache_dir", str),
            "STOCK_ANALYSIS_USE_REDIS": ("cache.use_redis", bool),
            "STOCK_ANALYSIS_REDIS_HOST": ("cache.redis_host", str),
            "STOCK_ANALYSIS_REDIS_PORT": ("cache.redis_port", int),
            
            # Retry settings
            "STOCK_ANALYSIS_MAX_RETRIES": ("retry.max_retries", int),
            "STOCK_ANALYSIS_REQUEST_TIMEOUT": ("retry.request_timeout", float),
            
            # API settings
            "STOCK_ANALYSIS_REQUESTS_PER_MINUTE": ("api.requests_per_minute", int),
            "STOCK_ANALYSIS_NEWS_API_KEY": ("api.news_api_key", str),
            
            # Logging settings
            "STOCK_ANALYSIS_LOG_LEVEL": ("logging.level", str),
            "STOCK_ANALYSIS_LOG_FILE": ("logging.file_path", str),
            
            # General settings
            "STOCK_ANALYSIS_DEBUG": ("debug", bool),
            "STOCK_ANALYSIS_ENVIRONMENT": ("environment", str),
        }
        
        for env_var, (config_path, value_type) in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                try:
                    if value_type == bool:
                        env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                    elif value_type == int:
                        env_value = int(env_value)
                    elif value_type == float:
                        env_value = float(env_value)
                    
                    # Set the nested attribute
                    section_name, attr_name = config_path.split('.')
                    section = getattr(self, section_name)
                    setattr(section, attr_name, env_value)
                    
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to set {config_path} from {env_var}: {e}")
    
    def setup_logging(self) -> None:
        """Setup logging configuration"""
        log_level = getattr(logging, self.logging.level.upper(), logging.INFO)
        
        # Create formatters
        formatter = logging.Formatter(self.logging.format)
        
        # Setup root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear existing handlers
        root_logger.handlers.clear()
        
        # Console handler
        if self.logging.console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # File handler
        if self.logging.file_path:
            try:
                from logging.handlers import RotatingFileHandler
                file_handler = RotatingFileHandler(
                    self.logging.file_path,
                    maxBytes=self.logging.max_file_size_mb * 1024 * 1024,
                    backupCount=self.logging.backup_count
                )
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Failed to setup file logging: {e}")
    
    def save_to_file(self, config_file: str) -> None:
        """Save current configuration to JSON file"""
        config_data = {}
        
        for section_name in ["cache", "retry", "circuit_breaker", "api", "logging", "analysis"]:
            section = getattr(self, section_name)
            config_data[section_name] = {}
            
            for key, value in section.__dict__.items():
                if not key.startswith('_'):
                    config_data[section_name][key] = value
        
        # Add main config fields
        config_data["environment"] = self.environment
        config_data["debug"] = self.debug
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            logger.info(f"Configuration saved to {config_file}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_file}: {e}")
    
    def get_cache_ttl(self, source: str) -> int:
        """Get cache TTL for specific source"""
        ttl_mapping = {
            "screener": self.cache.screener_ttl,
            "trendlyne": self.cache.trendlyne_ttl,
            "news": self.cache.news_ttl,
            "sentiment": self.cache.sentiment_ttl
        }
        return ttl_mapping.get(source, self.cache.default_ttl)
    
    def validate(self) -> bool:
        """Validate configuration settings"""
        errors = []
        
        # Validate cache settings
        if self.cache.default_ttl <= 0:
            errors.append("Cache TTL must be positive")
        
        if self.cache.max_cache_size_mb <= 0:
            errors.append("Max cache size must be positive")
        
        # Validate retry settings
        if self.retry.max_retries < 0:
            errors.append("Max retries cannot be negative")
        
        if self.retry.request_timeout <= 0:
            errors.append("Request timeout must be positive")
        
        # Validate API settings
        if self.api.requests_per_minute <= 0:
            errors.append("Requests per minute must be positive")
        
        # Validate logging settings
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.logging.level.upper() not in valid_log_levels:
            errors.append(f"Log level must be one of: {valid_log_levels}")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration validation error: {error}")
            return False
        
        logger.info("Configuration validation passed")
        return True

# Global configuration instance
_config: Optional[StockAnalysisConfig] = None

@lru_cache(maxsize=1)
def get_config(config_file: Optional[str] = None) -> StockAnalysisConfig:
    """Get global configuration instance"""
    global _config
    
    if _config is None:
        if config_file:
            _config = StockAnalysisConfig(config_file=config_file)
        else:
            # Try to load from default locations
            default_config_files = [
                "stock_analysis_config.json",
                "config/stock_analysis.json",
                os.path.expanduser("~/.stock_analysis/config.json")
            ]
            
            for default_file in default_config_files:
                if os.path.exists(default_file):
                    _config = StockAnalysisConfig(config_file=default_file)
                    break
            
            if _config is None:
                _config = StockAnalysisConfig()
        
        # Validate configuration
        _config.validate()
    
    return _config

def create_default_config_file(filepath: str = "stock_analysis_config.json") -> None:
    """Create a default configuration file"""
    config = StockAnalysisConfig()
    config.save_to_file(filepath)
    print(f"Default configuration file created: {filepath}")

def main():
    """CLI for configuration management"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Stock Analysis Configuration Management")
    parser.add_argument("--create-default", help="Create default configuration file")
    parser.add_argument("--validate", action="store_true", help="Validate current configuration")
    parser.add_argument("--config-file", help="Configuration file to use")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    
    args = parser.parse_args()
    
    if args.create_default:
        create_default_config_file(args.create_default)
    
    elif args.validate:
        config = get_config(args.config_file)
        if config.validate():
            print("✅ Configuration is valid")
        else:
            print("❌ Configuration validation failed")
    
    elif args.show:
        config = get_config(args.config_file)
        print("\nCurrent Configuration:")
        print("=" * 50)
        print(f"Environment: {config.environment}")
        print(f"Debug: {config.debug}")
        print(f"\nCache Settings:")
        print(f"  TTL: {config.cache.default_ttl}s")
        print(f"  Directory: {config.cache.cache_dir}")
        print(f"  Use Redis: {config.cache.use_redis}")
        print(f"\nRetry Settings:")
        print(f"  Max Retries: {config.retry.max_retries}")
        print(f"  Timeout: {config.retry.request_timeout}s")
        print(f"\nLogging:")
        print(f"  Level: {config.logging.level}")
        print(f"  File: {config.logging.file_path}")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()