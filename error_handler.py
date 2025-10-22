"""
Comprehensive Error Handling and Logging System
==============================================

Provides robust error handling, logging, and debugging capabilities
for the arbitrage opportunity finder.
"""

import logging
import traceback
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from functools import wraps
import json
import asyncio
from contextlib import asynccontextmanager

from loguru import logger
import ccxt

class ErrorHandler:
    """Centralized error handling and logging"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.max_error_history = 1000
        
        # Configure logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup comprehensive logging configuration"""
        # Remove default handler
        logger.remove()
        
        # Console logging
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # File logging
        logger.add(
            "logs/arbitrage_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            compression="zip"
        )
        
        # Error-specific logging
        logger.add(
            "logs/errors_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{traceback}",
            filter=lambda record: record["level"].name == "ERROR"
        )
        
        # Performance logging
        logger.add(
            "logs/performance_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="7 days",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            filter=lambda record: "PERF" in record["message"]
        )
    
    def log_error(self, error: Exception, context: str = "", extra_data: Dict[str, Any] = None):
        """Log an error with context and extra data"""
        error_type = type(error).__name__
        error_message = str(error)
        
        # Update error counts
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        
        # Create error record
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "traceback": traceback.format_exc(),
            "extra_data": extra_data or {}
        }
        
        # Add to history
        self.error_history.append(error_record)
        if len(self.error_history) > self.max_error_history:
            self.error_history.pop(0)
        
        # Log the error
        logger.error(f"Error in {context}: {error_type} - {error_message}")
        if extra_data:
            logger.error(f"Extra data: {json.dumps(extra_data, indent=2)}")
        
        return error_record
    
    def log_performance(self, operation: str, duration: float, extra_data: Dict[str, Any] = None):
        """Log performance metrics"""
        logger.info(f"PERF: {operation} took {duration:.3f}s")
        if extra_data:
            logger.info(f"PERF: {operation} extra data: {json.dumps(extra_data, indent=2)}")
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors"""
        return {
            "total_errors": sum(self.error_counts.values()),
            "error_types": self.error_counts,
            "recent_errors": self.error_history[-10:] if self.error_history else [],
            "most_common_error": max(self.error_counts.items(), key=lambda x: x[1]) if self.error_counts else None
        }
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_counts.clear()
        logger.info("Error history cleared")

def error_handler(context: str = "", reraise: bool = False):
    """Decorator for error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler_instance = ErrorHandler()
                error_handler_instance.log_error(e, f"{context} - {func.__name__}")
                if reraise:
                    raise
                return None
        return wrapper
    return decorator

def async_error_handler(context: str = "", reraise: bool = False):
    """Decorator for async error handling"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler_instance = ErrorHandler()
                error_handler_instance.log_error(e, f"{context} - {func.__name__}")
                if reraise:
                    raise
                return None
        return wrapper
    return decorator

class ExchangeErrorHandler:
    """Specialized error handler for exchange operations"""
    
    def __init__(self):
        self.exchange_errors: Dict[str, List[Dict[str, Any]]] = {}
        self.exchange_blacklist: Dict[str, datetime] = {}
        self.blacklist_duration = 300  # 5 minutes
    
    def handle_exchange_error(self, exchange_name: str, error: Exception, operation: str = ""):
        """Handle exchange-specific errors"""
        error_type = type(error).__name__
        
        # Log the error
        logger.error(f"Exchange error in {exchange_name} during {operation}: {error_type} - {str(error)}")
        
        # Record the error
        if exchange_name not in self.exchange_errors:
            self.exchange_errors[exchange_name] = []
        
        self.exchange_errors[exchange_name].append({
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": str(error),
            "operation": operation
        })
        
        # Keep only last 100 errors per exchange
        if len(self.exchange_errors[exchange_name]) > 100:
            self.exchange_errors[exchange_name] = self.exchange_errors[exchange_name][-100:]
        
        # Check if exchange should be blacklisted
        if self._should_blacklist_exchange(exchange_name, error):
            self.exchange_blacklist[exchange_name] = datetime.now()
            logger.warning(f"Exchange {exchange_name} blacklisted due to repeated errors")
    
    def _should_blacklist_exchange(self, exchange_name: str, error: Exception) -> bool:
        """Determine if exchange should be blacklisted"""
        # Blacklist for specific error types
        blacklist_errors = [
            "AuthenticationError",
            "PermissionDenied",
            "InvalidNonce",
            "NetworkError"
        ]
        
        if type(error).__name__ in blacklist_errors:
            return True
        
        # Blacklist if too many errors in short time
        recent_errors = [
            err for err in self.exchange_errors.get(exchange_name, [])
            if (datetime.now() - datetime.fromisoformat(err["timestamp"])).seconds < 300
        ]
        
        return len(recent_errors) > 10
    
    def is_exchange_blacklisted(self, exchange_name: str) -> bool:
        """Check if exchange is currently blacklisted"""
        if exchange_name not in self.exchange_blacklist:
            return False
        
        blacklist_time = self.exchange_blacklist[exchange_name]
        if (datetime.now() - blacklist_time).seconds > self.blacklist_duration:
            del self.exchange_blacklist[exchange_name]
            return False
        
        return True
    
    def get_exchange_health(self, exchange_name: str) -> Dict[str, Any]:
        """Get health status of exchange"""
        is_blacklisted = self.is_exchange_blacklisted(exchange_name)
        recent_errors = [
            err for err in self.exchange_errors.get(exchange_name, [])
            if (datetime.now() - datetime.fromisoformat(err["timestamp"])).seconds < 3600
        ]
        
        return {
            "is_blacklisted": is_blacklisted,
            "recent_errors": len(recent_errors),
            "total_errors": len(self.exchange_errors.get(exchange_name, [])),
            "last_error": self.exchange_errors[exchange_name][-1] if self.exchange_errors.get(exchange_name) else None
        }

class PerformanceMonitor:
    """Monitor performance of operations"""
    
    def __init__(self):
        self.operation_times: Dict[str, List[float]] = {}
        self.operation_counts: Dict[str, int] = {}
    
    def time_operation(self, operation_name: str):
        """Context manager for timing operations"""
        return OperationTimer(operation_name, self)
    
    def record_operation(self, operation_name: str, duration: float):
        """Record operation duration"""
        if operation_name not in self.operation_times:
            self.operation_times[operation_name] = []
            self.operation_counts[operation_name] = 0
        
        self.operation_times[operation_name].append(duration)
        self.operation_counts[operation_name] += 1
        
        # Keep only last 1000 measurements
        if len(self.operation_times[operation_name]) > 1000:
            self.operation_times[operation_name] = self.operation_times[operation_name][-1000:]
    
    def get_performance_stats(self, operation_name: str) -> Dict[str, float]:
        """Get performance statistics for operation"""
        if operation_name not in self.operation_times:
            return {}
        
        times = self.operation_times[operation_name]
        return {
            "count": len(times),
            "total": sum(times),
            "average": sum(times) / len(times),
            "min": min(times),
            "max": max(times),
            "median": sorted(times)[len(times) // 2]
        }
    
    def get_all_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all operations"""
        return {
            operation: self.get_performance_stats(operation)
            for operation in self.operation_times.keys()
        }

class OperationTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, monitor: PerformanceMonitor):
        self.operation_name = operation_name
        self.monitor = monitor
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            self.monitor.record_operation(self.operation_name, duration)

# Global instances
error_handler = ErrorHandler()
exchange_error_handler = ExchangeErrorHandler()
performance_monitor = PerformanceMonitor()

# Utility functions
def log_exchange_operation(exchange_name: str, operation: str):
    """Decorator for logging exchange operations"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            with performance_monitor.time_operation(f"{exchange_name}_{operation}"):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    exchange_error_handler.handle_exchange_error(exchange_name, e, operation)
                    raise
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, **kwargs) -> Any:
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.log_error(e, f"Safe execution of {func.__name__}")
        return None

async def safe_execute_async(func: Callable, *args, **kwargs) -> Any:
    """Safely execute an async function with error handling"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        error_handler.log_error(e, f"Safe async execution of {func.__name__}")
        return None