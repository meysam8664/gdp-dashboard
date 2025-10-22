"""
Professional Arbitrage Opportunity Finder - Streamlit Dashboard
==============================================================

A comprehensive real-time arbitrage monitoring dashboard that displays
profitable trading opportunities across multiple cryptocurrency exchanges.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
import time
from datetime import datetime, timedelta
import numpy as np
from typing import List, Dict, Any
import json

# Import our arbitrage engine
from arbitrage_engine import (
    arbitrage_monitor, 
    ArbitrageOpportunity, 
    ArbitrageType,
    ExchangeType
)

# Configure Streamlit page
st.set_page_config(
    page_title='Arbitrage Opportunity Finder',
    page_icon='💰',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .opportunity-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
    }
    .profit-positive {
        color: #28a745;
        font-weight: bold;
    }
    .profit-negative {
        color: #dc3545;
        font-weight: bold;
    }
    .status-running {
        color: #28a745;
        font-weight: bold;
    }
    .status-stopped {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'monitoring' not in st.session_state:
    st.session_state.monitoring = False
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'statistics' not in st.session_state:
    st.session_state.statistics = {}

def get_opportunities_data() -> List[Dict]:
    """Get current opportunities data for display"""
    opportunities = arbitrage_monitor.get_opportunities(100)
    return [
        {
            'ID': op.id,
            'Symbol': op.symbol,
            'Buy Exchange': op.buy_exchange,
            'Sell Exchange': op.sell_exchange,
            'Buy Price': f"${op.buy_price:.4f}",
            'Sell Price': f"${op.sell_price:.4f}",
            'Profit %': f"{op.profit_percentage:.2f}%",
            'Profit $': f"${op.profit_absolute:.4f}",
            'Volume': f"${op.volume:,.0f}",
            'Confidence': f"{op.confidence:.1f}%",
            'Risk Score': f"{op.risk_score:.1f}%",
            'Timestamp': op.timestamp.strftime('%H:%M:%S'),
            'Execution Time': f"{op.execution_time_estimate:.1f}s"
        }
        for op in opportunities
    ]

def get_statistics_data() -> Dict[str, Any]:
    """Get current statistics data"""
    return arbitrage_monitor.get_statistics()

def create_profit_distribution_chart(opportunities: List[ArbitrageOpportunity]):
    """Create profit distribution chart"""
    if not opportunities:
        return None
    
    profits = [op.profit_percentage for op in opportunities]
    
    fig = px.histogram(
        x=profits,
        nbins=20,
        title="Profit Distribution",
        labels={'x': 'Profit Percentage (%)', 'y': 'Count'},
        color_discrete_sequence=['#667eea']
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_exchange_activity_chart(opportunities: List[ArbitrageOpportunity]):
    """Create exchange activity chart"""
    if not opportunities:
        return None
    
    exchange_counts = {}
    for op in opportunities:
        buy_ex = op.buy_exchange
        sell_ex = op.sell_exchange
        
        exchange_counts[buy_ex] = exchange_counts.get(buy_ex, 0) + 1
        exchange_counts[sell_ex] = exchange_counts.get(sell_ex, 0) + 1
    
    exchanges = list(exchange_counts.keys())
    counts = list(exchange_counts.values())
    
    fig = px.bar(
        x=exchanges,
        y=counts,
        title="Exchange Activity",
        labels={'x': 'Exchange', 'y': 'Opportunities'},
        color=counts,
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_profit_timeline_chart(opportunities: List[ArbitrageOpportunity]):
    """Create profit timeline chart"""
    if not opportunities:
        return None
    
    # Group opportunities by minute
    timeline_data = {}
    for op in opportunities:
        minute_key = op.timestamp.replace(second=0, microsecond=0)
        if minute_key not in timeline_data:
            timeline_data[minute_key] = []
        timeline_data[minute_key].append(op.profit_percentage)
    
    # Calculate average profit per minute
    minutes = sorted(timeline_data.keys())
    avg_profits = [np.mean(timeline_data[minute]) for minute in minutes]
    
    fig = px.line(
        x=minutes,
        y=avg_profits,
        title="Average Profit Over Time",
        labels={'x': 'Time', 'y': 'Average Profit (%)'},
        color_discrete_sequence=['#28a745']
    )
    
    fig.update_layout(
        showlegend=False,
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

# Main dashboard
st.markdown('<h1 class="main-header">💰 Professional Arbitrage Opportunity Finder</h1>', unsafe_allow_html=True)

# Sidebar controls
st.sidebar.header("🎛️ Control Panel")

# Monitoring controls
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("▶️ Start Monitoring", disabled=st.session_state.monitoring):
        st.session_state.monitoring = True
        st.success("Monitoring started!")
        st.rerun()

with col2:
    if st.button("⏹️ Stop Monitoring", disabled=not st.session_state.monitoring):
        st.session_state.monitoring = False
        st.success("Monitoring stopped!")
        st.rerun()

# Configuration
st.sidebar.header("⚙️ Configuration")

min_profit = st.sidebar.slider(
    "Minimum Profit %", 
    min_value=0.01, 
    max_value=5.0, 
    value=0.1, 
    step=0.01
)

min_volume = st.sidebar.slider(
    "Minimum Volume ($)", 
    min_value=100, 
    max_value=1000000, 
    value=1000, 
    step=100
)

max_risk = st.sidebar.slider(
    "Maximum Risk Score", 
    min_value=0, 
    max_value=100, 
    value=50, 
    step=5
)

# Symbol selection
symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ADA/USDT', 'SOL/USDT', 'DOT/USDT', 'LINK/USDT']
selected_symbols = st.sidebar.multiselect(
    "Select Symbols",
    symbols,
    default=symbols[:5]
)

# Update monitor configuration
arbitrage_monitor.detector.min_profit_percentage = min_profit
arbitrage_monitor.detector.min_volume = min_volume
arbitrage_monitor.symbols = selected_symbols

# Main content area
if st.session_state.monitoring:
    st.markdown('<p class="status-running">🟢 Monitoring Active</p>', unsafe_allow_html=True)
else:
    st.markdown('<p class="status-stopped">🔴 Monitoring Stopped</p>', unsafe_allow_html=True)

# Auto-refresh
if st.session_state.monitoring:
    time.sleep(2)  # Refresh every 2 seconds
    st.rerun()

# Get current data
opportunities = arbitrage_monitor.get_opportunities(100)
statistics = get_statistics_data()

# Filter opportunities based on settings
filtered_opportunities = [
    op for op in opportunities 
    if op.profit_percentage >= min_profit 
    and op.volume >= min_volume 
    and op.risk_score <= max_risk
]

# Statistics cards
st.header("📊 Live Statistics", divider='gray')

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Total Opportunities",
        value=statistics.get('total_opportunities', 0),
        delta=f"Last scan: {statistics.get('last_scan', 'Never')}"
    )

with col2:
    avg_profit = statistics.get('avg_profit', 0)
    st.metric(
        label="Average Profit",
        value=f"{avg_profit:.2f}%",
        delta=f"Max: {statistics.get('max_profit', 0):.2f}%"
    )

with col3:
    st.metric(
        label="Active Exchanges",
        value=statistics.get('active_exchanges', 0),
        delta=f"Monitoring {statistics.get('monitoring_symbols', 0)} symbols"
    )

with col4:
    st.metric(
        label="Filtered Opportunities",
        value=len(filtered_opportunities),
        delta=f"Risk ≤ {max_risk}%"
    )

# Charts section
st.header("📈 Analytics", divider='gray')

if filtered_opportunities:
    col1, col2 = st.columns(2)
    
    with col1:
        profit_chart = create_profit_distribution_chart(filtered_opportunities)
        if profit_chart:
            st.plotly_chart(profit_chart, use_container_width=True)
    
    with col2:
        exchange_chart = create_exchange_activity_chart(filtered_opportunities)
        if exchange_chart:
            st.plotly_chart(exchange_chart, use_container_width=True)
    
    # Timeline chart
    timeline_chart = create_profit_timeline_chart(filtered_opportunities)
    if timeline_chart:
        st.plotly_chart(timeline_chart, use_container_width=True)

# Opportunities table
st.header("🎯 Current Opportunities", divider='gray')

if filtered_opportunities:
    # Sort options
    sort_option = st.selectbox(
        "Sort by:",
        ["Profit % (High to Low)", "Profit % (Low to High)", "Volume (High to Low)", "Confidence (High to Low)", "Risk (Low to High)"]
    )
    
    # Sort opportunities
    if "Profit % (High to Low)" in sort_option:
        filtered_opportunities.sort(key=lambda x: x.profit_percentage, reverse=True)
    elif "Profit % (Low to High)" in sort_option:
        filtered_opportunities.sort(key=lambda x: x.profit_percentage)
    elif "Volume (High to Low)" in sort_option:
        filtered_opportunities.sort(key=lambda x: x.volume, reverse=True)
    elif "Confidence (High to Low)" in sort_option:
        filtered_opportunities.sort(key=lambda x: x.confidence, reverse=True)
    elif "Risk (Low to High)" in sort_option:
        filtered_opportunities.sort(key=lambda x: x.risk_score)
    
    # Display opportunities
    opportunities_data = get_opportunities_data()
    filtered_data = [op for op in opportunities_data if any(
        op['Symbol'] == filtered_op.symbol and 
        op['Buy Exchange'] == filtered_op.buy_exchange and 
        op['Sell Exchange'] == filtered_op.sell_exchange
        for filtered_op in filtered_opportunities
    )]
    
    if filtered_data:
        df = pd.DataFrame(filtered_data)
        
        # Style the dataframe
        def highlight_profit(val):
            if isinstance(val, str) and '%' in val:
                profit = float(val.replace('%', ''))
                if profit > 1.0:
                    return 'background-color: #d4edda; color: #155724; font-weight: bold'
                elif profit > 0.5:
                    return 'background-color: #fff3cd; color: #856404; font-weight: bold'
            return ''
        
        styled_df = df.style.applymap(highlight_profit, subset=['Profit %'])
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Opportunities CSV",
            data=csv,
            file_name=f"arbitrage_opportunities_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No opportunities match your current filters.")
else:
    st.info("No arbitrage opportunities found. Start monitoring to see opportunities.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🚀 Professional Arbitrage Opportunity Finder | Real-time monitoring across multiple exchanges</p>
        <p>⚠️ This tool is for educational purposes. Always verify opportunities before trading.</p>
    </div>
    """, 
    unsafe_allow_html=True
)
