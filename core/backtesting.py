"""
Backtesting engine for arbitrage strategies
Test historical performance and optimize parameters
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import statistics

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Results from a backtest run"""
    start_date: datetime
    end_date: datetime
    total_opportunities: int
    executed_trades: int
    successful_trades: int
    failed_trades: int
    total_profit: float
    total_fees: float
    net_profit: float
    profit_percentage: float
    win_rate: float
    avg_profit_per_trade: float
    max_profit: float
    max_loss: float
    sharpe_ratio: float
    max_drawdown: float
    total_capital_used: float
    roi: float
    trades: List[Dict]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'total_opportunities': self.total_opportunities,
            'executed_trades': self.executed_trades,
            'successful_trades': self.successful_trades,
            'failed_trades': self.failed_trades,
            'total_profit': round(self.total_profit, 2),
            'total_fees': round(self.total_fees, 2),
            'net_profit': round(self.net_profit, 2),
            'profit_percentage': round(self.profit_percentage, 2),
            'win_rate': round(self.win_rate * 100, 2),
            'avg_profit_per_trade': round(self.avg_profit_per_trade, 2),
            'max_profit': round(self.max_profit, 2),
            'max_loss': round(self.max_loss, 2),
            'sharpe_ratio': round(self.sharpe_ratio, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'total_capital_used': round(self.total_capital_used, 2),
            'roi': round(self.roi, 2)
        }


class BacktestEngine:
    """Backtest arbitrage strategies on historical data"""
    
    def __init__(self, initial_capital: float = 10000.0,
                 max_position_size: float = 0.1,
                 slippage: float = 0.001,
                 execution_delay: float = 2.0):
        """
        Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital in USD
            max_position_size: Max % of capital per trade (0-1)
            slippage: Expected price slippage (0.1% default)
            execution_delay: Execution delay in seconds
        """
        self.initial_capital = initial_capital
        self.max_position_size = max_position_size
        self.slippage = slippage
        self.execution_delay = execution_delay
        
        self.current_capital = initial_capital
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(self, opportunities: List, 
                    strategy_config: Dict = None) -> BacktestResult:
        """
        Run backtest on historical opportunities
        
        Args:
            opportunities: List of historical ArbitrageOpportunity objects
            strategy_config: Strategy configuration
            
        Returns:
            BacktestResult object
        """
        if not opportunities:
            logger.warning("No opportunities to backtest")
            return None
        
        # Reset state
        self.current_capital = self.initial_capital
        self.trades = []
        self.equity_curve = [self.initial_capital]
        
        # Default strategy config
        if strategy_config is None:
            strategy_config = {
                'min_profit': 1.0,
                'max_risk': 'HIGH',
                'min_confidence': 0.5,
                'enabled_types': ['spatial', 'triangular']
            }
        
        executed_count = 0
        successful_count = 0
        failed_count = 0
        
        # Simulate trading
        for opp in opportunities:
            # Apply strategy filters
            if not self._should_execute(opp, strategy_config):
                continue
            
            # Calculate position size
            position_size = min(
                opp.required_capital,
                self.current_capital * self.max_position_size
            )
            
            if position_size < opp.required_capital:
                continue  # Not enough capital
            
            # Simulate execution
            result = self._simulate_execution(opp, position_size)
            
            self.trades.append(result)
            executed_count += 1
            
            if result['success']:
                successful_count += 1
                self.current_capital += result['profit']
            else:
                failed_count += 1
                self.current_capital -= result['loss']
            
            self.equity_curve.append(self.current_capital)
        
        # Calculate metrics
        return self._calculate_results(
            opportunities,
            executed_count,
            successful_count,
            failed_count
        )
    
    def _should_execute(self, opportunity, config: Dict) -> bool:
        """Determine if opportunity should be executed"""
        # Check profit threshold
        if opportunity.profit_percentage < config['min_profit']:
            return False
        
        # Check risk level
        risk_levels = ['LOW', 'MEDIUM', 'HIGH']
        if risk_levels.index(opportunity.risk_level) > risk_levels.index(config['max_risk']):
            return False
        
        # Check confidence
        if opportunity.confidence < config['min_confidence']:
            return False
        
        # Check arbitrage type
        if opportunity.arbitrage_type.value not in config['enabled_types']:
            return False
        
        return True
    
    def _simulate_execution(self, opportunity, position_size: float) -> Dict:
        """
        Simulate trade execution with realistic constraints
        
        Args:
            opportunity: ArbitrageOpportunity object
            position_size: Size of position in USD
            
        Returns:
            Trade result dictionary
        """
        # Calculate slippage impact
        slippage_impact = position_size * self.slippage
        
        # Simulated success probability based on confidence and risk
        success_prob = opportunity.confidence
        
        # Risk adjustment
        if opportunity.risk_level == 'HIGH':
            success_prob *= 0.7
        elif opportunity.risk_level == 'MEDIUM':
            success_prob *= 0.85
        
        # Simulate execution
        import random
        success = random.random() < success_prob
        
        if success:
            # Calculate profit
            expected_profit = position_size * (opportunity.profit_percentage / 100)
            actual_profit = expected_profit - slippage_impact - opportunity.fees_estimated
            
            return {
                'timestamp': opportunity.timestamp,
                'opportunity_id': opportunity.opportunity_id,
                'type': opportunity.arbitrage_type.value,
                'asset': opportunity.asset,
                'position_size': position_size,
                'success': True,
                'profit': actual_profit,
                'loss': 0,
                'fees': opportunity.fees_estimated,
                'slippage': slippage_impact,
                'profit_percentage': (actual_profit / position_size) * 100
            }
        else:
            # Failed execution - assume small loss from fees
            loss = opportunity.fees_estimated + slippage_impact
            
            return {
                'timestamp': opportunity.timestamp,
                'opportunity_id': opportunity.opportunity_id,
                'type': opportunity.arbitrage_type.value,
                'asset': opportunity.asset,
                'position_size': position_size,
                'success': False,
                'profit': 0,
                'loss': loss,
                'fees': opportunity.fees_estimated,
                'slippage': slippage_impact,
                'profit_percentage': -(loss / position_size) * 100
            }
    
    def _calculate_results(self, all_opportunities: List,
                          executed: int, successful: int,
                          failed: int) -> BacktestResult:
        """Calculate backtest results and metrics"""
        
        if not self.trades:
            return None
        
        # Basic metrics
        total_profit = sum(t['profit'] for t in self.trades)
        total_fees = sum(t['fees'] for t in self.trades)
        total_loss = sum(t['loss'] for t in self.trades)
        net_profit = total_profit - total_loss
        
        # Trade statistics
        profits = [t['profit'] - t['loss'] for t in self.trades]
        max_profit = max(profits) if profits else 0
        max_loss = min(profits) if profits else 0
        avg_profit = statistics.mean(profits) if profits else 0
        
        # Win rate
        win_rate = successful / executed if executed > 0 else 0
        
        # Sharpe ratio (simplified)
        if len(profits) > 1:
            returns_std = statistics.stdev(profits)
            sharpe_ratio = (avg_profit / returns_std) if returns_std > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Maximum drawdown
        max_drawdown = self._calculate_max_drawdown()
        
        # Total capital used
        total_capital_used = sum(t['position_size'] for t in self.trades)
        
        # ROI
        roi = (net_profit / self.initial_capital) * 100
        
        # Profit percentage
        profit_pct = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100
        
        # Date range
        start_date = min(opp.timestamp for opp in all_opportunities)
        end_date = max(opp.timestamp for opp in all_opportunities)
        
        return BacktestResult(
            start_date=start_date,
            end_date=end_date,
            total_opportunities=len(all_opportunities),
            executed_trades=executed,
            successful_trades=successful,
            failed_trades=failed,
            total_profit=total_profit,
            total_fees=total_fees,
            net_profit=net_profit,
            profit_percentage=profit_pct,
            win_rate=win_rate,
            avg_profit_per_trade=avg_profit,
            max_profit=max_profit,
            max_loss=max_loss,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            total_capital_used=total_capital_used,
            roi=roi,
            trades=self.trades
        )
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity curve"""
        if len(self.equity_curve) < 2:
            return 0
        
        max_drawdown = 0
        peak = self.equity_curve[0]
        
        for value in self.equity_curve:
            if value > peak:
                peak = value
            drawdown = ((peak - value) / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def optimize_parameters(self, opportunities: List,
                          param_ranges: Dict) -> Dict:
        """
        Optimize strategy parameters
        
        Args:
            opportunities: Historical opportunities
            param_ranges: Dict of parameter ranges to test
            
        Returns:
            Best parameters and results
        """
        best_result = None
        best_params = None
        best_roi = float('-inf')
        
        # Generate parameter combinations
        from itertools import product
        
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        for combination in product(*param_values):
            params = dict(zip(param_names, combination))
            
            # Run backtest with these parameters
            result = self.run_backtest(opportunities, params)
            
            if result and result.roi > best_roi:
                best_roi = result.roi
                best_result = result
                best_params = params
        
        logger.info(f"Optimization complete. Best ROI: {best_roi:.2f}%")
        
        return {
            'best_parameters': best_params,
            'best_result': best_result,
            'best_roi': best_roi
        }
    
    def get_equity_curve(self) -> List[float]:
        """Get equity curve data"""
        return self.equity_curve
    
    def get_trade_history(self) -> List[Dict]:
        """Get detailed trade history"""
        return self.trades
