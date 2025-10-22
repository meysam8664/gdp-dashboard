"""
Advanced Analytics and ML-based predictions
Statistical analysis and machine learning for arbitrage
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

logger = logging.getLogger(__name__)


class AdvancedAnalytics:
    """Advanced analytics for arbitrage opportunities"""
    
    def __init__(self):
        self.historical_data = []
        self.predictions = {}
    
    def add_opportunity(self, opportunity):
        """Add opportunity to historical data"""
        self.historical_data.append(opportunity)
    
    def calculate_opportunity_score(self, opportunity) -> float:
        """
        Calculate composite score for opportunity
        Combines profit, risk, confidence, and historical performance
        
        Returns:
            Score from 0-100
        """
        score = 0.0
        
        # Profit component (40%)
        profit_score = min(opportunity.profit_percentage / 5.0, 1.0) * 40
        score += profit_score
        
        # Confidence component (30%)
        confidence_score = opportunity.confidence * 30
        score += confidence_score
        
        # Risk component (20%, inverted)
        risk_scores = {'LOW': 20, 'MEDIUM': 13, 'HIGH': 6}
        score += risk_scores.get(opportunity.risk_level, 10)
        
        # Historical success rate component (10%)
        historical_score = self._get_historical_success_rate(
            opportunity.arbitrage_type.value,
            opportunity.asset
        ) * 10
        score += historical_score
        
        return min(score, 100)
    
    def _get_historical_success_rate(self, arb_type: str, asset: str) -> float:
        """Get historical success rate for type/asset combination"""
        if not self.historical_data:
            return 0.8  # Default assumption
        
        similar_opps = [
            opp for opp in self.historical_data
            if opp.arbitrage_type.value == arb_type and opp.asset == asset
        ]
        
        if not similar_opps:
            return 0.8
        
        # Assume higher profit opportunities were more likely successful
        avg_profit = statistics.mean(opp.profit_percentage for opp in similar_opps)
        return min(avg_profit / 5.0, 1.0)
    
    def predict_best_trading_time(self, asset: str) -> Dict:
        """
        Predict best time to find opportunities for an asset
        Based on historical patterns
        
        Returns:
            Dict with hour-by-hour probabilities
        """
        if not self.historical_data:
            return {}
        
        # Group by hour
        hour_opportunities = defaultdict(int)
        hour_profits = defaultdict(list)
        
        for opp in self.historical_data:
            if opp.asset == asset:
                hour = opp.timestamp.hour
                hour_opportunities[hour] += 1
                hour_profits[hour].append(opp.profit_percentage)
        
        # Calculate scores
        predictions = {}
        for hour in range(24):
            count = hour_opportunities.get(hour, 0)
            avg_profit = statistics.mean(hour_profits[hour]) if hour in hour_profits else 0
            
            # Combine frequency and profit
            score = (count * 0.5) + (avg_profit * 0.5)
            
            predictions[hour] = {
                'hour': hour,
                'opportunity_count': count,
                'avg_profit': avg_profit,
                'score': score,
                'recommendation': 'High' if score > 5 else 'Medium' if score > 2 else 'Low'
            }
        
        return predictions
    
    def analyze_exchange_pair_efficiency(self) -> Dict:
        """Analyze which exchange pairs have best arbitrage"""
        if not self.historical_data:
            return {}
        
        pair_stats = defaultdict(lambda: {
            'count': 0,
            'total_profit': 0,
            'avg_profit': 0,
            'max_profit': 0,
            'avg_confidence': 0
        })
        
        for opp in self.historical_data:
            if opp.source != opp.destination:
                pair = f"{opp.source}-{opp.destination}"
                stats = pair_stats[pair]
                
                stats['count'] += 1
                stats['total_profit'] += opp.profit_percentage
                stats['max_profit'] = max(stats['max_profit'], opp.profit_percentage)
                stats['avg_confidence'] += opp.confidence
        
        # Calculate averages
        for pair, stats in pair_stats.items():
            if stats['count'] > 0:
                stats['avg_profit'] = stats['total_profit'] / stats['count']
                stats['avg_confidence'] = stats['avg_confidence'] / stats['count']
        
        # Sort by average profit
        sorted_pairs = sorted(
            pair_stats.items(),
            key=lambda x: x[1]['avg_profit'],
            reverse=True
        )
        
        return dict(sorted_pairs[:10])  # Top 10 pairs
    
    def detect_trend(self, asset: str, days: int = 7) -> Dict:
        """
        Detect trend in arbitrage opportunities for an asset
        
        Returns:
            Trend analysis
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        recent_opps = [
            opp for opp in self.historical_data
            if opp.asset == asset and opp.timestamp >= cutoff_date
        ]
        
        if len(recent_opps) < 2:
            return {'trend': 'insufficient_data'}
        
        # Group by day
        daily_stats = defaultdict(lambda: {'count': 0, 'avg_profit': 0, 'total': 0})
        
        for opp in recent_opps:
            day = opp.timestamp.date()
            daily_stats[day]['count'] += 1
            daily_stats[day]['total'] += opp.profit_percentage
        
        # Calculate daily averages
        daily_data = []
        for day, stats in sorted(daily_stats.items()):
            stats['avg_profit'] = stats['total'] / stats['count'] if stats['count'] > 0 else 0
            daily_data.append({
                'date': day,
                'count': stats['count'],
                'avg_profit': stats['avg_profit']
            })
        
        # Detect trend
        if len(daily_data) >= 2:
            first_half_profit = statistics.mean(d['avg_profit'] for d in daily_data[:len(daily_data)//2])
            second_half_profit = statistics.mean(d['avg_profit'] for d in daily_data[len(daily_data)//2:])
            
            change = ((second_half_profit - first_half_profit) / first_half_profit * 100) if first_half_profit > 0 else 0
            
            if change > 10:
                trend = 'increasing'
            elif change < -10:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_percentage': change if 'change' in locals() else 0,
            'daily_data': daily_data,
            'avg_opportunities_per_day': statistics.mean(d['count'] for d in daily_data),
            'avg_profit': statistics.mean(d['avg_profit'] for d in daily_data)
        }
    
    def calculate_volatility_index(self, asset: str, window: int = 20) -> float:
        """
        Calculate volatility index for an asset
        Higher volatility = more arbitrage opportunities
        
        Returns:
            Volatility index (0-100)
        """
        recent_opps = [
            opp for opp in self.historical_data[-window:]
            if opp.asset == asset
        ]
        
        if len(recent_opps) < 2:
            return 50.0  # Neutral
        
        profits = [opp.profit_percentage for opp in recent_opps]
        
        # Calculate standard deviation
        std_dev = statistics.stdev(profits) if len(profits) > 1 else 0
        
        # Normalize to 0-100 scale
        volatility_index = min(std_dev * 20, 100)
        
        return volatility_index
    
    def predict_profit_probability(self, opportunity) -> Dict[str, float]:
        """
        Predict probability of different profit outcomes
        
        Returns:
            Dict with probability ranges
        """
        # Base probabilities on confidence and risk
        base_success_prob = opportunity.confidence
        
        # Adjust for risk
        if opportunity.risk_level == 'HIGH':
            base_success_prob *= 0.7
        elif opportunity.risk_level == 'MEDIUM':
            base_success_prob *= 0.85
        
        # Calculate probability ranges
        probabilities = {
            'profit_0_1_pct': base_success_prob * 0.3,
            'profit_1_2_pct': base_success_prob * 0.4,
            'profit_2_5_pct': base_success_prob * 0.2,
            'profit_above_5_pct': base_success_prob * 0.1,
            'loss': 1 - base_success_prob
        }
        
        return probabilities
    
    def generate_recommendations(self, opportunities: List) -> List[Dict]:
        """
        Generate AI-powered recommendations
        
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if not opportunities:
            recommendations.append({
                'type': 'info',
                'title': 'No Opportunities',
                'message': 'No arbitrage opportunities found. Try lowering your profit threshold or scanning more assets.',
                'priority': 'low'
            })
            return recommendations
        
        # Check for high-profit opportunities
        high_profit_opps = [opp for opp in opportunities if opp.profit_percentage > 3]
        if high_profit_opps:
            recommendations.append({
                'type': 'alert',
                'title': 'High Profit Alert',
                'message': f'Found {len(high_profit_opps)} opportunities with >3% profit. Act quickly!',
                'priority': 'high',
                'opportunities': high_profit_opps[:3]
            })
        
        # Check for low-risk opportunities
        low_risk_opps = [opp for opp in opportunities 
                        if opp.risk_level == 'LOW' and opp.confidence > 0.7]
        if low_risk_opps:
            recommendations.append({
                'type': 'suggestion',
                'title': 'Safe Opportunities',
                'message': f'Found {len(low_risk_opps)} low-risk, high-confidence opportunities.',
                'priority': 'medium',
                'opportunities': low_risk_opps[:3]
            })
        
        # Analyze asset distribution
        asset_counts = defaultdict(int)
        for opp in opportunities:
            asset_counts[opp.asset] += 1
        
        if asset_counts:
            best_asset = max(asset_counts.items(), key=lambda x: x[1])
            recommendations.append({
                'type': 'info',
                'title': 'Asset Focus',
                'message': f'{best_asset[0]} has the most opportunities ({best_asset[1]}). Consider focusing on this asset.',
                'priority': 'low'
            })
        
        return recommendations
    
    def calculate_correlation_matrix(self, assets: List[str]) -> Dict:
        """
        Calculate correlation between asset arbitrage opportunities
        
        Returns:
            Correlation matrix
        """
        if len(assets) < 2:
            return {}
        
        # Group opportunities by asset and time window
        asset_data = defaultdict(list)
        
        for opp in self.historical_data:
            if opp.asset in assets:
                time_bucket = opp.timestamp.replace(minute=0, second=0, microsecond=0)
                asset_data[opp.asset].append({
                    'time': time_bucket,
                    'profit': opp.profit_percentage
                })
        
        # Calculate correlations (simplified)
        correlations = {}
        for i, asset1 in enumerate(assets):
            for asset2 in assets[i+1:]:
                # This is a simplified correlation
                # In production, use proper statistical correlation
                count1 = len(asset_data[asset1])
                count2 = len(asset_data[asset2])
                
                if count1 > 0 and count2 > 0:
                    correlation = min(count1, count2) / max(count1, count2)
                    correlations[f"{asset1}-{asset2}"] = correlation
        
        return correlations
