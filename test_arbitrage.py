"""
Comprehensive Test Suite for Arbitrage Opportunity Finder
========================================================

Tests all components of the arbitrage system including:
- Exchange connections
- Opportunity detection
- Error handling
- API endpoints
- Performance monitoring
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from arbitrage_engine import (
    ArbitrageMonitor, 
    ArbitrageDetector, 
    ExchangeManager, 
    PriceData, 
    ArbitrageOpportunity,
    ArbitrageType
)
from error_handler import ErrorHandler, ExchangeErrorHandler, PerformanceMonitor
from api_service import app
from fastapi.testclient import TestClient

class TestPriceData:
    """Test PriceData class"""
    
    def test_price_data_creation(self):
        """Test PriceData object creation"""
        price_data = PriceData(
            exchange="binance",
            symbol="BTC/USDT",
            bid=50000.0,
            ask=50010.0,
            timestamp=datetime.now(),
            volume_24h=1000000.0,
            spread=0.02
        )
        
        assert price_data.exchange == "binance"
        assert price_data.symbol == "BTC/USDT"
        assert price_data.bid == 50000.0
        assert price_data.ask == 50010.0
        assert price_data.volume_24h == 1000000.0
        assert price_data.spread == 0.02

class TestArbitrageDetector:
    """Test ArbitrageDetector class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.exchange_manager = Mock()
        self.detector = ArbitrageDetector(self.exchange_manager)
    
    def test_detect_simple_arbitrage_no_opportunities(self):
        """Test simple arbitrage detection with no opportunities"""
        price_data = [
            PriceData("binance", "BTC/USDT", 50000, 50010, datetime.now(), 1000, 0.02),
            PriceData("coinbase", "BTC/USDT", 50005, 50015, datetime.now(), 1000, 0.02)
        ]
        
        opportunities = self.detector.detect_simple_arbitrage(price_data)
        assert len(opportunities) == 0
    
    def test_detect_simple_arbitrage_with_opportunities(self):
        """Test simple arbitrage detection with opportunities"""
        price_data = [
            PriceData("binance", "BTC/USDT", 50000, 50010, datetime.now(), 10000, 0.02),
            PriceData("coinbase", "BTC/USDT", 50100, 50110, datetime.now(), 10000, 0.02)
        ]
        
        opportunities = self.detector.detect_simple_arbitrage(price_data)
        assert len(opportunities) > 0
        
        opportunity = opportunities[0]
        assert opportunity.buy_exchange == "binance"
        assert opportunity.sell_exchange == "coinbase"
        assert opportunity.profit_percentage > 0
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        buy_data = PriceData("binance", "BTC/USDT", 50000, 50010, datetime.now(), 1000000, 0.01)
        sell_data = PriceData("coinbase", "BTC/USDT", 50100, 50110, datetime.now(), 1000000, 0.01)
        
        confidence = self.detector._calculate_confidence(buy_data, sell_data)
        assert 0 <= confidence <= 100
    
    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        buy_data = PriceData("binance", "BTC/USDT", 50000, 50010, datetime.now(), 1000000, 0.01)
        sell_data = PriceData("coinbase", "BTC/USDT", 50100, 50110, datetime.now(), 1000000, 0.01)
        
        risk_score = self.detector._calculate_risk_score(buy_data, sell_data)
        assert 0 <= risk_score <= 100

class TestExchangeManager:
    """Test ExchangeManager class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = ExchangeManager()
    
    @patch('ccxt.binance')
    def test_exchange_initialization(self, mock_binance):
        """Test exchange initialization"""
        mock_exchange = Mock()
        mock_binance.return_value = mock_exchange
        
        # Reinitialize with mock
        self.manager._initialize_exchanges()
        
        # Verify exchange was created
        assert "binance" in self.manager.exchanges
    
    @pytest.mark.asyncio
    async def test_get_ticker_data_success(self):
        """Test successful ticker data retrieval"""
        mock_exchange = Mock()
        mock_exchange.fetch_ticker = Mock(return_value={
            'bid': 50000.0,
            'ask': 50010.0,
            'quoteVolume': 1000000.0
        })
        
        self.manager.exchanges["test_exchange"] = mock_exchange
        
        result = await self.manager.get_ticker_data("test_exchange", "BTC/USDT")
        
        assert result is not None
        assert result.bid == 50000.0
        assert result.ask == 50010.0
        assert result.volume_24h == 1000000.0
    
    @pytest.mark.asyncio
    async def test_get_ticker_data_failure(self):
        """Test ticker data retrieval failure"""
        mock_exchange = Mock()
        mock_exchange.fetch_ticker = Mock(side_effect=Exception("API Error"))
        
        self.manager.exchanges["test_exchange"] = mock_exchange
        
        result = await self.manager.get_ticker_data("test_exchange", "BTC/USDT")
        
        assert result is None

class TestArbitrageMonitor:
    """Test ArbitrageMonitor class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = ArbitrageMonitor()
    
    def test_initialization(self):
        """Test monitor initialization"""
        assert self.monitor.monitoring == False
        assert len(self.monitor.opportunities) == 0
        assert len(self.monitor.symbols) > 0
    
    def test_get_opportunities(self):
        """Test getting opportunities"""
        # Add mock opportunities
        opportunity = ArbitrageOpportunity(
            id="test_1",
            type=ArbitrageType.SIMPLE,
            buy_exchange="binance",
            sell_exchange="coinbase",
            symbol="BTC/USDT",
            buy_price=50000.0,
            sell_price=50100.0,
            profit_percentage=0.2,
            profit_absolute=100.0,
            volume=1000.0,
            confidence=80.0,
            timestamp=datetime.now(),
            risk_score=20.0,
            execution_time_estimate=2.0
        )
        
        self.monitor.opportunities.append(opportunity)
        
        opportunities = self.monitor.get_opportunities(10)
        assert len(opportunities) == 1
        assert opportunities[0].id == "test_1"
    
    def test_get_opportunities_by_symbol(self):
        """Test getting opportunities by symbol"""
        opportunity = ArbitrageOpportunity(
            id="test_1",
            type=ArbitrageType.SIMPLE,
            buy_exchange="binance",
            sell_exchange="coinbase",
            symbol="BTC/USDT",
            buy_price=50000.0,
            sell_price=50100.0,
            profit_percentage=0.2,
            profit_absolute=100.0,
            volume=1000.0,
            confidence=80.0,
            timestamp=datetime.now(),
            risk_score=20.0,
            execution_time_estimate=2.0
        )
        
        self.monitor.opportunities.append(opportunity)
        
        btc_opportunities = self.monitor.get_opportunities_by_symbol("BTC/USDT")
        assert len(btc_opportunities) == 1
        
        eth_opportunities = self.monitor.get_opportunities_by_symbol("ETH/USDT")
        assert len(eth_opportunities) == 0
    
    def test_get_statistics(self):
        """Test getting statistics"""
        stats = self.monitor.get_statistics()
        
        assert 'total_opportunities' in stats
        assert 'avg_profit' in stats
        assert 'max_profit' in stats
        assert 'active_exchanges' in stats
        assert 'monitoring_symbols' in stats

class TestErrorHandler:
    """Test ErrorHandler class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.error_handler = ErrorHandler()
    
    def test_log_error(self):
        """Test error logging"""
        error = ValueError("Test error")
        context = "test_context"
        extra_data = {"key": "value"}
        
        error_record = self.error_handler.log_error(error, context, extra_data)
        
        assert error_record['error_type'] == 'ValueError'
        assert error_record['error_message'] == 'Test error'
        assert error_record['context'] == context
        assert error_record['extra_data'] == extra_data
    
    def test_get_error_summary(self):
        """Test error summary"""
        # Log some errors
        self.error_handler.log_error(ValueError("Error 1"), "context1")
        self.error_handler.log_error(ValueError("Error 2"), "context2")
        self.error_handler.log_error(RuntimeError("Error 3"), "context3")
        
        summary = self.error_handler.get_error_summary()
        
        assert summary['total_errors'] == 3
        assert summary['error_types']['ValueError'] == 2
        assert summary['error_types']['RuntimeError'] == 1
        assert len(summary['recent_errors']) == 3

class TestExchangeErrorHandler:
    """Test ExchangeErrorHandler class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.handler = ExchangeErrorHandler()
    
    def test_handle_exchange_error(self):
        """Test handling exchange errors"""
        error = Exception("API Error")
        self.handler.handle_exchange_error("binance", error, "fetch_ticker")
        
        assert "binance" in self.handler.exchange_errors
        assert len(self.handler.exchange_errors["binance"]) == 1
        
        error_record = self.handler.exchange_errors["binance"][0]
        assert error_record['error_type'] == 'Exception'
        assert error_record['operation'] == 'fetch_ticker'
    
    def test_exchange_blacklisting(self):
        """Test exchange blacklisting"""
        # Simulate many errors
        for i in range(15):
            error = Exception(f"Error {i}")
            self.handler.handle_exchange_error("binance", error, "fetch_ticker")
        
        # Check if exchange is blacklisted
        assert self.handler.is_exchange_blacklisted("binance")
    
    def test_exchange_health(self):
        """Test exchange health status"""
        error = Exception("API Error")
        self.handler.handle_exchange_error("binance", error, "fetch_ticker")
        
        health = self.handler.get_exchange_health("binance")
        
        assert 'is_blacklisted' in health
        assert 'recent_errors' in health
        assert 'total_errors' in health
        assert health['total_errors'] == 1

class TestPerformanceMonitor:
    """Test PerformanceMonitor class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.monitor = PerformanceMonitor()
    
    def test_operation_timing(self):
        """Test operation timing"""
        with self.monitor.time_operation("test_operation"):
            # Simulate some work
            import time
            time.sleep(0.01)
        
        stats = self.monitor.get_performance_stats("test_operation")
        
        assert stats['count'] == 1
        assert stats['average'] > 0
        assert stats['min'] > 0
        assert stats['max'] > 0
    
    def test_multiple_operations(self):
        """Test multiple operations"""
        # Record multiple operations
        self.monitor.record_operation("op1", 0.1)
        self.monitor.record_operation("op1", 0.2)
        self.monitor.record_operation("op2", 0.3)
        
        stats1 = self.monitor.get_performance_stats("op1")
        stats2 = self.monitor.get_performance_stats("op2")
        
        assert stats1['count'] == 2
        assert stats1['average'] == 0.15
        assert stats2['count'] == 1
        assert stats2['average'] == 0.3

class TestAPI:
    """Test API endpoints"""
    
    def setup_method(self):
        """Setup test environment"""
        self.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert 'status' in data
        assert 'timestamp' in data
        assert 'uptime' in data
    
    def test_get_opportunities(self):
        """Test get opportunities endpoint"""
        response = self.client.get("/opportunities")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_statistics(self):
        """Test get statistics endpoint"""
        response = self.client.get("/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert 'total_opportunities' in data
        assert 'avg_profit' in data
        assert 'active_exchanges' in data
    
    def test_get_monitoring_status(self):
        """Test get monitoring status endpoint"""
        response = self.client.get("/monitoring/status")
        assert response.status_code == 200
        
        data = response.json()
        assert 'is_monitoring' in data
        assert 'symbols' in data
        assert 'exchanges' in data
    
    def test_get_config(self):
        """Test get config endpoint"""
        response = self.client.get("/config")
        assert response.status_code == 200
        
        data = response.json()
        assert 'arbitrage' in data
        assert 'monitoring' in data
    
    def test_update_config(self):
        """Test update config endpoint"""
        config_data = {
            "min_profit_percentage": 0.2,
            "min_volume": 2000
        }
        
        response = self.client.post("/config", json=config_data)
        assert response.status_code == 200
        
        data = response.json()
        assert 'message' in data

# Integration tests
class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.asyncio
    async def test_full_arbitrage_flow(self):
        """Test complete arbitrage detection flow"""
        monitor = ArbitrageMonitor()
        
        # Mock exchange manager
        mock_price_data = [
            PriceData("binance", "BTC/USDT", 50000, 50010, datetime.now(), 10000, 0.02),
            PriceData("coinbase", "BTC/USDT", 50100, 50110, datetime.now(), 10000, 0.02)
        ]
        
        with patch.object(monitor.exchange_manager, 'get_all_tickers', return_value=mock_price_data):
            # Start monitoring briefly
            monitor.monitoring = True
            await monitor._scan_opportunities()
            
            # Check if opportunities were found
            opportunities = monitor.get_opportunities()
            assert len(opportunities) > 0

# Performance tests
class TestPerformance:
    """Performance tests"""
    
    def test_opportunity_detection_performance(self):
        """Test performance of opportunity detection"""
        import time
        
        detector = ArbitrageDetector(Mock())
        
        # Create large dataset
        price_data = []
        for i in range(100):
            price_data.append(PriceData(
                f"exchange_{i}", 
                "BTC/USDT", 
                50000 + i, 
                50010 + i, 
                datetime.now(), 
                1000, 
                0.02
            ))
        
        start_time = time.time()
        opportunities = detector.detect_simple_arbitrage(price_data)
        end_time = time.time()
        
        # Should complete within reasonable time
        assert (end_time - start_time) < 1.0  # Less than 1 second
        assert len(opportunities) >= 0

# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])