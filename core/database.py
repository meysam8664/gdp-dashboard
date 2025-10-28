"""
Database layer for storing historical arbitrage data
Uses SQLite for simplicity and portability
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ArbitrageDatabase:
    """Database for storing and querying arbitrage opportunities"""
    
    def __init__(self, db_path: str = "data/arbitrage.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create directory if needed
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize connection
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # Create tables
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables"""
        
        # Opportunities table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_id TEXT UNIQUE NOT NULL,
                arbitrage_type TEXT NOT NULL,
                asset TEXT NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                profit_percentage REAL NOT NULL,
                profit_absolute REAL NOT NULL,
                buy_price REAL NOT NULL,
                sell_price REAL NOT NULL,
                confidence REAL NOT NULL,
                risk_level TEXT NOT NULL,
                required_capital REAL NOT NULL,
                fees_estimated REAL NOT NULL,
                path TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                executed BOOLEAN DEFAULT 0,
                execution_result TEXT
            )
        """)
        
        # Scans table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS scans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                opportunities_found INTEGER NOT NULL,
                max_profit_percentage REAL,
                avg_profit_percentage REAL,
                scan_duration REAL NOT NULL,
                exchanges_scanned INTEGER NOT NULL,
                assets_scanned INTEGER NOT NULL
            )
        """)
        
        # Exchange health table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS exchange_health (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exchange TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                status TEXT NOT NULL,
                success_rate REAL NOT NULL,
                error_count INTEGER NOT NULL,
                response_time REAL
            )
        """)
        
        # User preferences table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                updated_at DATETIME NOT NULL
            )
        """)
        
        # Create indexes
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_opportunities_timestamp 
            ON opportunities(timestamp DESC)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_opportunities_profit 
            ON opportunities(profit_percentage DESC)
        """)
        
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_scans_timestamp 
            ON scans(timestamp DESC)
        """)
        
        self.conn.commit()
        logger.info("Database tables created/verified")
    
    def save_opportunity(self, opportunity) -> bool:
        """
        Save arbitrage opportunity to database
        
        Args:
            opportunity: ArbitrageOpportunity object
            
        Returns:
            True if successful
        """
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO opportunities 
                (opportunity_id, arbitrage_type, asset, source, destination,
                 profit_percentage, profit_absolute, buy_price, sell_price,
                 confidence, risk_level, required_capital, fees_estimated,
                 path, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                opportunity.opportunity_id,
                opportunity.arbitrage_type.value,
                opportunity.asset,
                opportunity.source,
                opportunity.destination,
                opportunity.profit_percentage,
                opportunity.profit_absolute,
                opportunity.buy_price,
                opportunity.sell_price,
                opportunity.confidence,
                opportunity.risk_level,
                opportunity.required_capital,
                opportunity.fees_estimated,
                json.dumps(opportunity.path),
                opportunity.timestamp
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving opportunity: {e}")
            return False
    
    def save_scan_result(self, opportunities_count: int, max_profit: float,
                        avg_profit: float, duration: float, 
                        exchanges: int, assets: int) -> bool:
        """Save scan results"""
        try:
            self.cursor.execute("""
                INSERT INTO scans 
                (timestamp, opportunities_found, max_profit_percentage,
                 avg_profit_percentage, scan_duration, exchanges_scanned,
                 assets_scanned)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                opportunities_count,
                max_profit,
                avg_profit,
                duration,
                exchanges,
                assets
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving scan result: {e}")
            return False
    
    def save_exchange_health(self, exchange: str, status: str,
                            success_rate: float, error_count: int,
                            response_time: float = None) -> bool:
        """Save exchange health data"""
        try:
            self.cursor.execute("""
                INSERT INTO exchange_health
                (exchange, timestamp, status, success_rate, error_count, response_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                exchange,
                datetime.now(),
                status,
                success_rate,
                error_count,
                response_time
            ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving exchange health: {e}")
            return False
    
    def get_recent_opportunities(self, limit: int = 100, 
                                min_profit: float = 0) -> List[Dict]:
        """Get recent opportunities"""
        try:
            self.cursor.execute("""
                SELECT * FROM opportunities
                WHERE profit_percentage >= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (min_profit, limit))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching opportunities: {e}")
            return []
    
    def get_opportunities_by_asset(self, asset: str, limit: int = 50) -> List[Dict]:
        """Get opportunities for specific asset"""
        try:
            self.cursor.execute("""
                SELECT * FROM opportunities
                WHERE asset = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (asset, limit))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching opportunities for {asset}: {e}")
            return []
    
    def get_statistics(self, days: int = 7) -> Dict:
        """Get statistics for past N days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Total opportunities
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM opportunities
                WHERE timestamp >= ?
            """, (cutoff_date,))
            total_opps = self.cursor.fetchone()['count']
            
            # Average profit
            self.cursor.execute("""
                SELECT AVG(profit_percentage) as avg_profit,
                       MAX(profit_percentage) as max_profit,
                       MIN(profit_percentage) as min_profit
                FROM opportunities
                WHERE timestamp >= ?
            """, (cutoff_date,))
            profit_stats = dict(self.cursor.fetchone())
            
            # By type
            self.cursor.execute("""
                SELECT arbitrage_type, COUNT(*) as count
                FROM opportunities
                WHERE timestamp >= ?
                GROUP BY arbitrage_type
            """, (cutoff_date,))
            by_type = {row['arbitrage_type']: row['count'] 
                      for row in self.cursor.fetchall()}
            
            # By risk
            self.cursor.execute("""
                SELECT risk_level, COUNT(*) as count
                FROM opportunities
                WHERE timestamp >= ?
                GROUP BY risk_level
            """, (cutoff_date,))
            by_risk = {row['risk_level']: row['count'] 
                      for row in self.cursor.fetchall()}
            
            return {
                'total_opportunities': total_opps,
                'avg_profit': profit_stats.get('avg_profit', 0),
                'max_profit': profit_stats.get('max_profit', 0),
                'min_profit': profit_stats.get('min_profit', 0),
                'by_type': by_type,
                'by_risk': by_risk,
                'days': days
            }
            
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def get_scan_history(self, limit: int = 50) -> List[Dict]:
        """Get scan history"""
        try:
            self.cursor.execute("""
                SELECT * FROM scans
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Error fetching scan history: {e}")
            return []
    
    def save_preference(self, key: str, value: str) -> bool:
        """Save user preference"""
        try:
            self.cursor.execute("""
                INSERT OR REPLACE INTO preferences (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.now()))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving preference: {e}")
            return False
    
    def get_preference(self, key: str, default: str = None) -> Optional[str]:
        """Get user preference"""
        try:
            self.cursor.execute("""
                SELECT value FROM preferences WHERE key = ?
            """, (key,))
            
            row = self.cursor.fetchone()
            return row['value'] if row else default
            
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return default
    
    def export_to_csv(self, output_path: str, days: int = 7) -> bool:
        """Export opportunities to CSV"""
        try:
            import pandas as pd
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            self.cursor.execute("""
                SELECT * FROM opportunities
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """, (cutoff_date,))
            
            rows = self.cursor.fetchall()
            df = pd.DataFrame([dict(row) for row in rows])
            
            df.to_csv(output_path, index=False)
            logger.info(f"Exported {len(df)} opportunities to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting to CSV: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        self.conn.close()
        logger.info("Database connection closed")
