"""
REST API Service for Arbitrage Opportunity Finder
================================================

Provides REST API endpoints for accessing arbitrage opportunities,
statistics, and control functionality.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import uvicorn

from arbitrage_engine import arbitrage_monitor, ArbitrageOpportunity, ArbitrageType
from error_handler import error_handler, exchange_error_handler, performance_monitor
from config import config

# Pydantic models for API
class OpportunityResponse(BaseModel):
    id: str
    type: str
    buy_exchange: str
    sell_exchange: str
    symbol: str
    buy_price: float
    sell_price: float
    profit_percentage: float
    profit_absolute: float
    volume: float
    confidence: float
    timestamp: datetime
    risk_score: float
    execution_time_estimate: float

class StatisticsResponse(BaseModel):
    total_opportunities: int
    avg_profit: float
    max_profit: float
    min_profit: float
    active_exchanges: int
    monitoring_symbols: int
    last_scan: Optional[str]
    error_summary: Dict[str, Any]
    performance_stats: Dict[str, Any]

class MonitoringStatusResponse(BaseModel):
    is_monitoring: bool
    symbols: List[str]
    exchanges: List[str]
    scan_interval: int
    uptime: float

class ConfigUpdateRequest(BaseModel):
    min_profit_percentage: Optional[float] = None
    min_volume: Optional[float] = None
    max_spread: Optional[float] = None
    max_risk_score: Optional[float] = None
    symbols: Optional[List[str]] = None
    scan_interval: Optional[int] = None

# Initialize FastAPI app
app = FastAPI(
    title="Arbitrage Opportunity Finder API",
    description="Professional arbitrage opportunity detection and monitoring API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
monitoring_task = None
start_time = datetime.now()

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global monitoring_task
    try:
        # Start monitoring in background
        monitoring_task = asyncio.create_task(arbitrage_monitor.start_monitoring())
        error_handler.log_performance("API startup", 0)
        print("🚀 Arbitrage API started successfully")
    except Exception as e:
        error_handler.log_error(e, "API startup")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global monitoring_task
    try:
        if monitoring_task:
            monitoring_task.cancel()
            await arbitrage_monitor.stop_monitoring()
        print("🛑 Arbitrage API stopped")
    except Exception as e:
        error_handler.log_error(e, "API shutdown")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": (datetime.now() - start_time).total_seconds(),
        "monitoring": arbitrage_monitor.monitoring
    }

# Opportunities endpoints
@app.get("/opportunities", response_model=List[OpportunityResponse])
async def get_opportunities(
    limit: int = 50,
    symbol: Optional[str] = None,
    min_profit: Optional[float] = None,
    max_risk: Optional[float] = None
):
    """Get current arbitrage opportunities"""
    try:
        opportunities = arbitrage_monitor.get_opportunities(limit)
        
        # Apply filters
        if symbol:
            opportunities = [op for op in opportunities if op.symbol == symbol]
        
        if min_profit is not None:
            opportunities = [op for op in opportunities if op.profit_percentage >= min_profit]
        
        if max_risk is not None:
            opportunities = [op for op in opportunities if op.risk_score <= max_risk]
        
        return [
            OpportunityResponse(
                id=op.id,
                type=op.type.value,
                buy_exchange=op.buy_exchange,
                sell_exchange=op.sell_exchange,
                symbol=op.symbol,
                buy_price=op.buy_price,
                sell_price=op.sell_price,
                profit_percentage=op.profit_percentage,
                profit_absolute=op.profit_absolute,
                volume=op.volume,
                confidence=op.confidence,
                timestamp=op.timestamp,
                risk_score=op.risk_score,
                execution_time_estimate=op.execution_time_estimate
            )
            for op in opportunities
        ]
    except Exception as e:
        error_handler.log_error(e, "Get opportunities")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/opportunities/{symbol}", response_model=List[OpportunityResponse])
async def get_opportunities_by_symbol(symbol: str, limit: int = 50):
    """Get opportunities for specific symbol"""
    try:
        opportunities = arbitrage_monitor.get_opportunities_by_symbol(symbol)
        return [
            OpportunityResponse(
                id=op.id,
                type=op.type.value,
                buy_exchange=op.buy_exchange,
                sell_exchange=op.sell_exchange,
                symbol=op.symbol,
                buy_price=op.buy_price,
                sell_price=op.sell_price,
                profit_percentage=op.profit_percentage,
                profit_absolute=op.profit_absolute,
                volume=op.volume,
                confidence=op.confidence,
                timestamp=op.timestamp,
                risk_score=op.risk_score,
                execution_time_estimate=op.execution_time_estimate
            )
            for op in opportunities[:limit]
        ]
    except Exception as e:
        error_handler.log_error(e, f"Get opportunities for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoint
@app.get("/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Get monitoring statistics"""
    try:
        stats = arbitrage_monitor.get_statistics()
        error_summary = error_handler.get_error_summary()
        performance_stats = performance_monitor.get_all_performance_stats()
        
        return StatisticsResponse(
            total_opportunities=stats.get('total_opportunities', 0),
            avg_profit=stats.get('avg_profit', 0),
            max_profit=stats.get('max_profit', 0),
            min_profit=stats.get('min_profit', 0),
            active_exchanges=stats.get('active_exchanges', 0),
            monitoring_symbols=stats.get('monitoring_symbols', 0),
            last_scan=stats.get('last_scan'),
            error_summary=error_summary,
            performance_stats=performance_stats
        )
    except Exception as e:
        error_handler.log_error(e, "Get statistics")
        raise HTTPException(status_code=500, detail=str(e))

# Monitoring control endpoints
@app.post("/monitoring/start")
async def start_monitoring():
    """Start arbitrage monitoring"""
    try:
        if not arbitrage_monitor.monitoring:
            await arbitrage_monitor.start_monitoring()
            return {"message": "Monitoring started successfully"}
        else:
            return {"message": "Monitoring is already running"}
    except Exception as e:
        error_handler.log_error(e, "Start monitoring")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/monitoring/stop")
async def stop_monitoring():
    """Stop arbitrage monitoring"""
    try:
        if arbitrage_monitor.monitoring:
            await arbitrage_monitor.stop_monitoring()
            return {"message": "Monitoring stopped successfully"}
        else:
            return {"message": "Monitoring is not running"}
    except Exception as e:
        error_handler.log_error(e, "Stop monitoring")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/monitoring/status", response_model=MonitoringStatusResponse)
async def get_monitoring_status():
    """Get monitoring status"""
    try:
        uptime = (datetime.now() - start_time).total_seconds()
        
        return MonitoringStatusResponse(
            is_monitoring=arbitrage_monitor.monitoring,
            symbols=arbitrage_monitor.symbols,
            exchanges=list(arbitrage_monitor.exchange_manager.exchanges.keys()),
            scan_interval=config.arbitrage.scan_interval,
            uptime=uptime
        )
    except Exception as e:
        error_handler.log_error(e, "Get monitoring status")
        raise HTTPException(status_code=500, detail=str(e))

# Configuration endpoints
@app.get("/config")
async def get_config():
    """Get current configuration"""
    try:
        return {
            "arbitrage": {
                "min_profit_percentage": config.arbitrage.min_profit_percentage,
                "min_volume": config.arbitrage.min_volume,
                "max_spread": config.arbitrage.max_spread,
                "max_risk_score": config.arbitrage.max_risk_score,
                "scan_interval": config.arbitrage.scan_interval
            },
            "monitoring": {
                "symbols": config.monitoring.symbols,
                "exchanges": config.monitoring.exchanges,
                "auto_start": config.monitoring.auto_start
            }
        }
    except Exception as e:
        error_handler.log_error(e, "Get config")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """Update configuration"""
    try:
        # Update arbitrage config
        if request.min_profit_percentage is not None:
            config.update_arbitrage_config(min_profit_percentage=request.min_profit_percentage)
            arbitrage_monitor.detector.min_profit_percentage = request.min_profit_percentage
        
        if request.min_volume is not None:
            config.update_arbitrage_config(min_volume=request.min_volume)
            arbitrage_monitor.detector.min_volume = request.min_volume
        
        if request.max_spread is not None:
            config.update_arbitrage_config(max_spread=request.max_spread)
            arbitrage_monitor.detector.max_spread = request.max_spread
        
        if request.max_risk_score is not None:
            config.update_arbitrage_config(max_risk_score=request.max_risk_score)
        
        if request.symbols is not None:
            config.update_monitoring_config(symbols=request.symbols)
            arbitrage_monitor.symbols = request.symbols
        
        if request.scan_interval is not None:
            config.update_arbitrage_config(scan_interval=request.scan_interval)
        
        return {"message": "Configuration updated successfully"}
    except Exception as e:
        error_handler.log_error(e, "Update config")
        raise HTTPException(status_code=500, detail=str(e))

# Exchange health endpoints
@app.get("/exchanges/health")
async def get_exchange_health():
    """Get health status of all exchanges"""
    try:
        health_status = {}
        for exchange_name in arbitrage_monitor.exchange_manager.exchanges.keys():
            health_status[exchange_name] = exchange_error_handler.get_exchange_health(exchange_name)
        
        return health_status
    except Exception as e:
        error_handler.log_error(e, "Get exchange health")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/exchanges/{exchange_name}/health")
async def get_exchange_health_by_name(exchange_name: str):
    """Get health status of specific exchange"""
    try:
        if exchange_name not in arbitrage_monitor.exchange_manager.exchanges:
            raise HTTPException(status_code=404, detail="Exchange not found")
        
        health = exchange_error_handler.get_exchange_health(exchange_name)
        return health
    except HTTPException:
        raise
    except Exception as e:
        error_handler.log_error(e, f"Get health for {exchange_name}")
        raise HTTPException(status_code=500, detail=str(e))

# Error handling endpoints
@app.get("/errors/summary")
async def get_error_summary():
    """Get error summary"""
    try:
        return error_handler.get_error_summary()
    except Exception as e:
        error_handler.log_error(e, "Get error summary")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/errors/clear")
async def clear_errors():
    """Clear error history"""
    try:
        error_handler.clear_error_history()
        return {"message": "Error history cleared successfully"}
    except Exception as e:
        error_handler.log_error(e, "Clear errors")
        raise HTTPException(status_code=500, detail=str(e))

# Performance endpoints
@app.get("/performance")
async def get_performance_stats():
    """Get performance statistics"""
    try:
        return performance_monitor.get_all_performance_stats()
    except Exception as e:
        error_handler.log_error(e, "Get performance stats")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates (optional)
@app.websocket("/ws/opportunities")
async def websocket_opportunities(websocket):
    """WebSocket endpoint for real-time opportunity updates"""
    try:
        await websocket.accept()
        
        while True:
            try:
                opportunities = arbitrage_monitor.get_opportunities(10)
                opportunities_data = [
                    {
                        "id": op.id,
                        "symbol": op.symbol,
                        "buy_exchange": op.buy_exchange,
                        "sell_exchange": op.sell_exchange,
                        "profit_percentage": op.profit_percentage,
                        "confidence": op.confidence,
                        "timestamp": op.timestamp.isoformat()
                    }
                    for op in opportunities
                ]
                
                await websocket.send_json({
                    "type": "opportunities",
                    "data": opportunities_data,
                    "timestamp": datetime.now().isoformat()
                })
                
                await asyncio.sleep(5)  # Send updates every 5 seconds
                
            except Exception as e:
                error_handler.log_error(e, "WebSocket opportunities")
                break
                
    except Exception as e:
        error_handler.log_error(e, "WebSocket connection")
    finally:
        await websocket.close()

# Main function to run the API
def run_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """Run the API server"""
    uvicorn.run(
        "api_service:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    run_api()