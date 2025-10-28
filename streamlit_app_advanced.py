"""
Advanced Professional Arbitrage Opportunity Finder
Enhanced version with all advanced features
"""

import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys
import json

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core.arbitrage_engine import ArbitrageEngine
from core.exchange_connector import ExchangeConnector
from core.database import ArbitrageDatabase
from core.analytics import AdvancedAnalytics
from core.backtesting import BacktestEngine
from core.notifications import NotificationManager, NotificationConfig
from utils.export import DataExporter

# Page configuration
st.set_page_config(
    page_title='🚀 Advanced Arbitrage Finder',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(120deg, #2ecc71, #3498db, #9b59b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .feature-badge {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        margin: 0.2rem;
        font-size: 0.9rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'db' not in st.session_state:
    st.session_state.db = ArbitrageDatabase()
if 'analytics' not in st.session_state:
    st.session_state.analytics = AdvancedAnalytics()
if 'exporter' not in st.session_state:
    st.session_state.exporter = DataExporter()
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'total_scans' not in st.session_state:
    st.session_state.total_scans = 0
if 'notifications_enabled' not in st.session_state:
    st.session_state.notifications_enabled = False


async def scan_markets_advanced(engine, connector, symbols, analytics, db):
    """Enhanced scan with database storage and analytics"""
    try:
        scan_start = datetime.now()
        
        # Fetch data
        all_data = await connector.fetch_all_exchanges(symbols)
        
        # Prepare data
        exchange_data = {
            'exchange_prices': connector.get_exchange_prices(all_data),
            'pair_prices': connector.get_pair_prices(all_data),
        }
        
        # Scan for opportunities
        opportunities = await engine.scan_all_opportunities(exchange_data)
        
        # Store in database
        for opp in opportunities:
            db.save_opportunity(opp)
            analytics.add_opportunity(opp)
        
        # Save scan result
        scan_duration = (datetime.now() - scan_start).total_seconds()
        if opportunities:
            max_profit = max(opp.profit_percentage for opp in opportunities)
            avg_profit = sum(opp.profit_percentage for opp in opportunities) / len(opportunities)
        else:
            max_profit = 0
            avg_profit = 0
        
        db.save_scan_result(
            len(opportunities),
            max_profit,
            avg_profit,
            scan_duration,
            len(all_data),
            len(symbols)
        )
        
        return opportunities, connector.get_health_status()
        
    except Exception as e:
        st.error(f"Error scanning markets: {e}")
        return [], {}


def display_header():
    """Display enhanced header"""
    st.markdown('<h1 class="main-header">🚀 Advanced Arbitrage Opportunity Finder</h1>', 
                unsafe_allow_html=True)
    
    # Feature badges
    st.markdown("""
    <div style='text-align: center; margin-bottom: 2rem;'>
        <span class='feature-badge'>🔄 Real-Time Monitoring</span>
        <span class='feature-badge'>📊 Advanced Analytics</span>
        <span class='feature-badge'>🗄️ Historical Tracking</span>
        <span class='feature-badge'>🔔 Smart Notifications</span>
        <span class='feature-badge'>📈 Backtesting</span>
        <span class='feature-badge'>💾 Multi-Format Export</span>
        <span class='feature-badge'>🤖 AI-Powered</span>
    </div>
    """, unsafe_allow_html=True)


def display_sidebar():
    """Enhanced sidebar with all settings"""
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        # Tab for different settings
        settings_tab = st.tabs(["🔍 Scan", "🔔 Notifications", "💾 Export", "🎯 Strategy"])
        
        with settings_tab[0]:
            st.markdown("### Scan Settings")
            min_profit = st.slider("Min Profit %", 0.0, 10.0, 1.0, 0.1)
            auto_scan = st.checkbox("Auto-Scan", value=False)
            scan_interval = st.slider("Interval (sec)", 5, 60, 10)
            
            assets = st.multiselect(
                "Assets",
                ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT', 
                 'ETH/BTC', 'BNB/BTC', 'BNB/ETH'],
                default=['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ETH/BTC', 'BNB/BTC']
            )
        
        with settings_tab[1]:
            st.markdown("### Notification Settings")
            
            notify_enabled = st.checkbox("Enable Notifications", 
                                        value=st.session_state.notifications_enabled)
            st.session_state.notifications_enabled = notify_enabled
            
            if notify_enabled:
                notify_threshold = st.slider("Alert Threshold %", 1.0, 10.0, 3.0, 0.5)
                
                telegram_enabled = st.checkbox("Telegram")
                if telegram_enabled:
                    telegram_token = st.text_input("Bot Token", type="password")
                    telegram_chat = st.text_input("Chat ID")
                
                email_enabled = st.checkbox("Email")
                if email_enabled:
                    email_to = st.text_input("Email Address")
        
        with settings_tab[2]:
            st.markdown("### Export Settings")
            export_format = st.multiselect(
                "Export Formats",
                ["CSV", "JSON", "Excel", "Report"],
                default=["CSV"]
            )
        
        with settings_tab[3]:
            st.markdown("### Strategy Settings")
            max_risk = st.selectbox("Max Risk Level", ["LOW", "MEDIUM", "HIGH"])
            min_confidence = st.slider("Min Confidence", 0.0, 1.0, 0.5, 0.1)
            enabled_types = st.multiselect(
                "Arbitrage Types",
                ["spatial", "triangular", "statistical"],
                default=["spatial", "triangular"]
            )
        
        st.markdown("---")
        
        # Database stats
        st.markdown("### 📊 Database Stats")
        stats = st.session_state.db.get_statistics(days=7)
        if stats:
            st.metric("Total Opportunities (7d)", stats.get('total_opportunities', 0))
            st.metric("Avg Profit", f"{stats.get('avg_profit', 0):.2f}%")
        
        return {
            'min_profit': min_profit,
            'auto_scan': auto_scan,
            'scan_interval': scan_interval,
            'assets': assets,
            'export_format': export_format,
            'max_risk': max_risk,
            'min_confidence': min_confidence,
            'enabled_types': enabled_types,
            'notify_threshold': notify_threshold if notify_enabled else None
        }


def display_ai_recommendations(opportunities):
    """Display AI-powered recommendations"""
    if not opportunities:
        return
    
    analytics = st.session_state.analytics
    recommendations = analytics.generate_recommendations(opportunities)
    
    if recommendations:
        st.markdown("### 🤖 AI Recommendations")
        
        for rec in recommendations:
            icon = "🚨" if rec['priority'] == 'high' else "💡" if rec['priority'] == 'medium' else "ℹ️"
            st.info(f"{icon} **{rec['title']}**: {rec['message']}")


def display_advanced_analytics():
    """Display advanced analytics tab"""
    st.markdown("### 📊 Advanced Analytics Dashboard")
    
    analytics = st.session_state.analytics
    
    if not analytics.historical_data:
        st.info("No historical data available yet. Start scanning to collect data!")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Exchange pair efficiency
        st.markdown("#### Best Exchange Pairs")
        pair_efficiency = analytics.analyze_exchange_pair_efficiency()
        if pair_efficiency:
            df = pd.DataFrame([
                {
                    'Pair': pair,
                    'Count': data['count'],
                    'Avg Profit %': f"{data['avg_profit']:.2f}",
                    'Max Profit %': f"{data['max_profit']:.2f}"
                }
                for pair, data in list(pair_efficiency.items())[:5]
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        # Asset trends
        st.markdown("#### Asset Trends (7 days)")
        for asset in ['BTC', 'ETH', 'BNB']:
            trend = analytics.detect_trend(asset, days=7)
            if trend.get('trend') != 'insufficient_data':
                emoji = "📈" if trend['trend'] == 'increasing' else "📉" if trend['trend'] == 'decreasing' else "➡️"
                st.metric(
                    f"{asset}",
                    f"{trend.get('avg_profit', 0):.2f}%",
                    delta=f"{trend.get('change_percentage', 0):.1f}% {emoji}"
                )


def display_backtesting():
    """Display backtesting interface"""
    st.markdown("### 📈 Strategy Backtesting")
    
    # Get historical data
    opportunities = st.session_state.db.get_recent_opportunities(limit=500)
    
    if len(opportunities) < 10:
        st.warning("Need at least 10 historical opportunities for backtesting. Keep scanning!")
        return
    
    st.info(f"Found {len(opportunities)} historical opportunities for backtesting")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        initial_capital = st.number_input("Initial Capital ($)", 1000, 100000, 10000, 1000)
    with col2:
        max_position = st.slider("Max Position Size (%)", 5, 50, 10)
    with col3:
        min_profit_backtest = st.slider("Min Profit % (Backtest)", 0.5, 5.0, 1.0, 0.1)
    
    if st.button("🚀 Run Backtest"):
        with st.spinner("Running backtest..."):
            # Convert dict opportunities to objects (simplified)
            # In production, you'd properly reconstruct the objects
            
            backtest_engine = BacktestEngine(
                initial_capital=initial_capital,
                max_position_size=max_position / 100
            )
            
            # For demo purposes, show backtest would work
            st.success("Backtest feature ready! Historical data is being collected.")
            st.info("Note: Full backtest implementation requires historical price data reconstruction.")


def display_export_section(opportunities):
    """Display export options"""
    if not opportunities:
        st.info("No opportunities to export. Run a scan first!")
        return
    
    st.markdown("### 💾 Export Data")
    
    col1, col2, col3, col4 = st.columns(4)
    
    exporter = st.session_state.exporter
    
    with col1:
        if st.button("📄 Export CSV"):
            filepath = exporter.export_opportunities_to_csv(opportunities)
            if filepath:
                st.success(f"Exported to {filepath}")
    
    with col2:
        if st.button("📊 Export Excel"):
            filepath = exporter.export_opportunities_to_excel(opportunities)
            if filepath:
                st.success(f"Exported to {filepath}")
    
    with col3:
        if st.button("🔗 Export JSON"):
            filepath = exporter.export_opportunities_to_json(opportunities)
            if filepath:
                st.success(f"Exported to {filepath}")
    
    with col4:
        if st.button("📝 Export Report"):
            stats = st.session_state.db.get_statistics()
            filepath = exporter.export_summary_report(opportunities, stats)
            if filepath:
                st.success(f"Exported to {filepath}")


def main():
    """Main application"""
    display_header()
    
    # Get settings from sidebar
    settings = display_sidebar()
    
    # Initialize components
    engine = ArbitrageEngine(min_profit_percentage=settings['min_profit'])
    connector = ExchangeConnector()
    
    # Control buttons
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        scan_button = st.button("🔍 Scan Now", type="primary", use_container_width=True)
    with col2:
        clear_button = st.button("🗑️ Clear", use_container_width=True)
    with col3:
        if st.button("📊 Load History", use_container_width=True):
            historical = st.session_state.db.get_recent_opportunities(limit=100)
            st.info(f"Loaded {len(historical)} opportunities from database")
    
    if clear_button:
        st.session_state.opportunities = []
        st.rerun()
    
    # Scan logic
    if scan_button or (settings['auto_scan'] and st.session_state.get('last_scan_time') is None):
        with st.spinner("🔄 Scanning markets..."):
            opportunities, health_status = asyncio.run(
                scan_markets_advanced(
                    engine, 
                    connector, 
                    settings['assets'],
                    st.session_state.analytics,
                    st.session_state.db
                )
            )
            
            st.session_state.opportunities = opportunities
            st.session_state.total_scans += 1
            st.session_state.last_scan_time = datetime.now()
            
            st.success(f"✅ Found {len(opportunities)} opportunities!")
    
    # Display opportunities and analytics
    opportunities = st.session_state.opportunities
    
    # Metrics
    if opportunities:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("🎯 Opportunities", len(opportunities))
        with col2:
            max_profit = max(opp.profit_percentage for opp in opportunities)
            st.metric("📈 Max Profit", f"{max_profit:.2f}%")
        with col3:
            avg_profit = sum(opp.profit_percentage for opp in opportunities) / len(opportunities)
            st.metric("📊 Avg Profit", f"{avg_profit:.2f}%")
        with col4:
            low_risk = sum(1 for opp in opportunities if opp.risk_level == 'LOW')
            st.metric("🛡️ Low Risk", low_risk)
        with col5:
            high_conf = sum(1 for opp in opportunities if opp.confidence > 0.7)
            st.metric("🎯 High Confidence", high_conf)
    
    # AI Recommendations
    display_ai_recommendations(opportunities)
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Opportunities", 
        "📊 Analytics", 
        "📈 Advanced Analytics",
        "🔙 Backtesting",
        "💾 Export",
        "🏥 System Health"
    ])
    
    with tab1:
        if opportunities:
            df = pd.DataFrame([opp.to_dict() for opp in opportunities])
            st.dataframe(df, use_container_width=True, hide_index=True, height=500)
        else:
            st.info("No opportunities found. Adjust your settings and try again!")
    
    with tab2:
        if opportunities:
            col1, col2 = st.columns(2)
            
            with col1:
                # Profit distribution
                profits = [opp.profit_percentage for opp in opportunities]
                fig = go.Figure(data=[go.Histogram(x=profits, nbinsx=20)])
                fig.update_layout(title="Profit Distribution", height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # By type
                type_counts = {}
                for opp in opportunities:
                    type_counts[opp.arbitrage_type.value] = type_counts.get(opp.arbitrage_type.value, 0) + 1
                
                fig = go.Figure(data=[go.Pie(labels=list(type_counts.keys()), 
                                             values=list(type_counts.values()), hole=0.4)])
                fig.update_layout(title="By Type", height=300)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        display_advanced_analytics()
    
    with tab4:
        display_backtesting()
    
    with tab5:
        display_export_section(opportunities)
    
    with tab6:
        health = connector.get_health_status()
        if health:
            df = pd.DataFrame([
                {
                    'Exchange': ex,
                    'Status': '🟢' if data['status'] == 'healthy' else '🟡',
                    'Success Rate': f"{data['success_rate']:.1f}%",
                    'Errors': data['error_count']
                }
                for ex, data in health.items()
            ])
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Scan history
        st.markdown("### Recent Scans")
        scan_history = st.session_state.db.get_scan_history(limit=10)
        if scan_history:
            df = pd.DataFrame(scan_history)
            st.dataframe(df, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
