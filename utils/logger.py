"""
Logging configuration for Arbitrage Finder
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = 'arbitrage_finder', 
                level: int = logging.INFO,
                log_to_file: bool = True) -> logging.Logger:
    """
    Setup logger with console and file handlers
    
    Args:
        name: Logger name
        level: Logging level
        log_to_file: Whether to log to file
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_to_file:
        log_dir = Path(__file__).parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f'arbitrage_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# Create default logger
default_logger = setup_logger()


def log_opportunity(opportunity):
    """Log arbitrage opportunity"""
    default_logger.info(
        f"Opportunity detected: {opportunity.arbitrage_type.value} - "
        f"{opportunity.asset} - Profit: {opportunity.profit_percentage:.2f}% - "
        f"Path: {' → '.join(opportunity.path)}"
    )


def log_error(error: Exception, context: str = ""):
    """Log error with context"""
    default_logger.error(f"{context}: {str(error)}", exc_info=True)


def log_scan_complete(opportunities_count: int, scan_duration: float):
    """Log scan completion"""
    default_logger.info(
        f"Scan complete: {opportunities_count} opportunities found in {scan_duration:.2f}s"
    )


def log_exchange_error(exchange: str, error: str):
    """Log exchange-specific error"""
    default_logger.warning(f"Exchange {exchange} error: {error}")
