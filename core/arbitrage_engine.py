"""
Core Arbitrage Detection Engine
Supports multiple arbitrage models with intelligent error handling
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ArbitrageType(Enum):
    """Types of arbitrage opportunities"""
    SPATIAL = "spatial"  # Same asset, different exchanges
    TRIANGULAR = "triangular"  # Three-way trades on same exchange
    STATISTICAL = "statistical"  # Based on statistical models
    CROSS_EXCHANGE = "cross_exchange"  # Complex multi-exchange arbitrage


@dataclass
class ArbitrageOpportunity:
    """Represents a detected arbitrage opportunity"""
    opportunity_id: str
    arbitrage_type: ArbitrageType
    profit_percentage: float
    profit_absolute: float
    source: str
    destination: str
    asset: str
    buy_price: float
    sell_price: float
    timestamp: datetime
    path: List[str]  # Trading path
    confidence: float  # 0-1 confidence score
    risk_level: str  # LOW, MEDIUM, HIGH
    estimated_execution_time: float  # seconds
    required_capital: float
    fees_estimated: float
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for display"""
        return {
            'ID': self.opportunity_id,
            'Type': self.arbitrage_type.value,
            'Profit %': f"{self.profit_percentage:.2f}%",
            'Profit $': f"${self.profit_absolute:.2f}",
            'Source': self.source,
            'Destination': self.destination,
            'Asset': self.asset,
            'Buy Price': f"${self.buy_price:.4f}",
            'Sell Price': f"${self.sell_price:.4f}",
            'Path': ' → '.join(self.path),
            'Confidence': f"{self.confidence*100:.0f}%",
            'Risk': self.risk_level,
            'Time': self.timestamp.strftime('%H:%M:%S'),
            'Capital': f"${self.required_capital:.2f}",
            'Fees': f"${self.fees_estimated:.4f}"
        }


class ArbitrageEngine:
    """Main arbitrage detection engine"""
    
    def __init__(self, min_profit_percentage: float = 1.0):
        self.min_profit_percentage = min_profit_percentage
        self.opportunities: List[ArbitrageOpportunity] = []
        self.exchange_data: Dict = {}
        self.running = False
        
    def calculate_profit(self, buy_price: float, sell_price: float, 
                        amount: float, fees: float = 0.002) -> Tuple[float, float]:
        """
        Calculate profit with fees
        
        Args:
            buy_price: Price to buy at
            sell_price: Price to sell at
            amount: Amount to trade
            fees: Total fees (default 0.2% per trade)
            
        Returns:
            Tuple of (profit_percentage, profit_absolute)
        """
        buy_cost = buy_price * amount * (1 + fees)
        sell_revenue = sell_price * amount * (1 - fees)
        profit_absolute = sell_revenue - buy_cost
        profit_percentage = (profit_absolute / buy_cost) * 100
        
        return profit_percentage, profit_absolute
    
    def assess_risk(self, profit_percentage: float, exchange_reliability: float,
                   volume: float) -> str:
        """
        Assess risk level of opportunity
        
        Args:
            profit_percentage: Expected profit
            exchange_reliability: Exchange reliability score (0-1)
            volume: Trading volume
            
        Returns:
            Risk level: LOW, MEDIUM, HIGH
        """
        risk_score = 0
        
        # Higher profit might indicate higher risk
        if profit_percentage > 5:
            risk_score += 2
        elif profit_percentage > 2:
            risk_score += 1
            
        # Exchange reliability
        if exchange_reliability < 0.7:
            risk_score += 2
        elif exchange_reliability < 0.9:
            risk_score += 1
            
        # Volume
        if volume < 10000:
            risk_score += 2
        elif volume < 50000:
            risk_score += 1
            
        if risk_score >= 4:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"
    
    def calculate_confidence(self, spread: float, volume: float, 
                           exchange_uptime: float) -> float:
        """
        Calculate confidence score for opportunity
        
        Args:
            spread: Price spread
            volume: Trading volume
            exchange_uptime: Exchange uptime percentage
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5
        
        # Higher spread = higher confidence
        if spread > 3:
            confidence += 0.2
        elif spread > 1.5:
            confidence += 0.1
            
        # Higher volume = higher confidence
        if volume > 100000:
            confidence += 0.2
        elif volume > 50000:
            confidence += 0.1
            
        # Exchange reliability
        confidence += (exchange_uptime - 0.9) * 0.5
        
        return min(max(confidence, 0), 1)
    
    async def detect_spatial_arbitrage(self, exchange_prices: Dict[str, Dict[str, float]],
                                       asset: str) -> List[ArbitrageOpportunity]:
        """
        Detect spatial arbitrage (same asset on different exchanges)
        
        Args:
            exchange_prices: Dict of {exchange_name: {asset: price}}
            asset: Asset to check
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        exchanges = list(exchange_prices.keys())
        
        for i, source_exchange in enumerate(exchanges):
            for dest_exchange in exchanges[i+1:]:
                if asset not in exchange_prices[source_exchange] or \
                   asset not in exchange_prices[dest_exchange]:
                    continue
                    
                buy_price = exchange_prices[source_exchange][asset]
                sell_price = exchange_prices[dest_exchange][asset]
                
                # Check both directions
                for buy_ex, sell_ex, buy_p, sell_p in [
                    (source_exchange, dest_exchange, buy_price, sell_price),
                    (dest_exchange, source_exchange, sell_price, buy_price)
                ]:
                    if sell_p <= buy_p:
                        continue
                        
                    amount = 1.0  # Calculate for 1 unit
                    profit_pct, profit_abs = self.calculate_profit(
                        buy_p, sell_p, amount
                    )
                    
                    if profit_pct >= self.min_profit_percentage:
                        risk = self.assess_risk(profit_pct, 0.95, 50000)
                        confidence = self.calculate_confidence(
                            profit_pct, 50000, 0.99
                        )
                        
                        opportunity = ArbitrageOpportunity(
                            opportunity_id=f"SPATIAL_{buy_ex}_{sell_ex}_{asset}_{datetime.now().timestamp()}",
                            arbitrage_type=ArbitrageType.SPATIAL,
                            profit_percentage=profit_pct,
                            profit_absolute=profit_abs,
                            source=buy_ex,
                            destination=sell_ex,
                            asset=asset,
                            buy_price=buy_p,
                            sell_price=sell_p,
                            timestamp=datetime.now(),
                            path=[buy_ex, asset, sell_ex],
                            confidence=confidence,
                            risk_level=risk,
                            estimated_execution_time=30.0,
                            required_capital=buy_p * amount,
                            fees_estimated=buy_p * amount * 0.004
                        )
                        opportunities.append(opportunity)
                        
        return opportunities
    
    async def detect_triangular_arbitrage(self, exchange: str, 
                                         prices: Dict[str, float]) -> List[ArbitrageOpportunity]:
        """
        Detect triangular arbitrage on a single exchange
        
        Args:
            exchange: Exchange name
            prices: Dict of trading pair prices
            
        Returns:
            List of arbitrage opportunities
        """
        opportunities = []
        
        # Common triangular paths
        paths = [
            ('BTC/USDT', 'ETH/BTC', 'ETH/USDT'),
            ('BTC/USDT', 'BNB/BTC', 'BNB/USDT'),
            ('ETH/USDT', 'BNB/ETH', 'BNB/USDT'),
        ]
        
        for path in paths:
            pair1, pair2, pair3 = path
            
            if not all(p in prices for p in path):
                continue
                
            try:
                # Start with 1000 USDT
                amount = 1000.0
                
                # Buy BTC with USDT
                btc_amount = amount / prices[pair1]
                
                # Buy ETH with BTC
                eth_amount = btc_amount / prices[pair2]
                
                # Sell ETH for USDT
                final_usdt = eth_amount * prices[pair3]
                
                # Apply fees (0.1% per trade)
                final_usdt *= (0.999 ** 3)
                
                profit_abs = final_usdt - amount
                profit_pct = (profit_abs / amount) * 100
                
                if profit_pct >= self.min_profit_percentage:
                    risk = self.assess_risk(profit_pct, 0.98, 100000)
                    confidence = self.calculate_confidence(profit_pct, 100000, 0.99)
                    
                    opportunity = ArbitrageOpportunity(
                        opportunity_id=f"TRIANGULAR_{exchange}_{'-'.join(path)}_{datetime.now().timestamp()}",
                        arbitrage_type=ArbitrageType.TRIANGULAR,
                        profit_percentage=profit_pct,
                        profit_absolute=profit_abs,
                        source=exchange,
                        destination=exchange,
                        asset=path[0].split('/')[0],
                        buy_price=prices[pair1],
                        sell_price=prices[pair3],
                        timestamp=datetime.now(),
                        path=list(path),
                        confidence=confidence,
                        risk_level=risk,
                        estimated_execution_time=10.0,
                        required_capital=amount,
                        fees_estimated=amount * 0.003
                    )
                    opportunities.append(opportunity)
                    
            except (ZeroDivisionError, KeyError) as e:
                logger.warning(f"Error calculating triangular arbitrage: {e}")
                continue
                
        return opportunities
    
    async def scan_all_opportunities(self, exchange_data: Dict) -> List[ArbitrageOpportunity]:
        """
        Scan for all types of arbitrage opportunities
        
        Args:
            exchange_data: Market data from all exchanges
            
        Returns:
            List of all detected opportunities
        """
        all_opportunities = []
        
        try:
            # Detect spatial arbitrage
            if 'exchange_prices' in exchange_data:
                for asset in ['BTC', 'ETH', 'BNB', 'SOL', 'ADA']:
                    spatial_opps = await self.detect_spatial_arbitrage(
                        exchange_data['exchange_prices'], asset
                    )
                    all_opportunities.extend(spatial_opps)
            
            # Detect triangular arbitrage
            if 'pair_prices' in exchange_data:
                for exchange, prices in exchange_data['pair_prices'].items():
                    triangular_opps = await self.detect_triangular_arbitrage(
                        exchange, prices
                    )
                    all_opportunities.extend(triangular_opps)
                    
        except Exception as e:
            logger.error(f"Error scanning opportunities: {e}")
            
        # Sort by profit percentage
        all_opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
        
        return all_opportunities
