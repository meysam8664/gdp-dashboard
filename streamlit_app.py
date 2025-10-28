"""
Professional Arbitrage Opportunity Finder
Real-time monitoring of arbitrage opportunities across multiple exchanges
"""

import streamlit as st
import pandas as pd
import asyncio
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import sys

# Add core modules to path
sys.path.insert(0, str(Path(__file__).parent))

from core.arbitrage_engine import ArbitrageEngine, ArbitrageType
from core.exchange_connector import ExchangeConnector

# Page configuration
st.set_page_config(
    page_title='🚀 Professional Arbitrage Finder',
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
        background: linear-gradient(120deg, #2ecc71, #3498db);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .opportunity-card {
        border-left: 4px solid #2ecc71;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f8f9fa;
        border-radius: 5px;
    }
    .high-profit {
        border-left-color: #27ae60 !important;
        background: #d5f4e6 !important;
    }
    .stAlert {
        background-color: #d1ecf1;
        border-color: #bee5eb;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'opportunities' not in st.session_state:
    st.session_state.opportunities = []
if 'scanning' not in st.session_state:
    st.session_state.scanning = False
if 'total_scans' not in st.session_state:
    st.session_state.total_scans = 0
if 'last_scan_time' not in st.session_state:
    st.session_state.last_scan_time = None
if 'historical_profits' not in st.session_state:
    st.session_state.historical_profits = []


async def scan_markets(engine: ArbitrageEngine, connector: ExchangeConnector, symbols: list):
    """Scan markets for arbitrage opportunities"""
    try:
        # Fetch data from all exchanges
        all_data = await connector.fetch_all_exchanges(symbols)
        
        # Prepare data for engine
        exchange_data = {
            'exchange_prices': connector.get_exchange_prices(all_data),
            'pair_prices': connector.get_pair_prices(all_data),
        }
        
        # Scan for opportunities
        opportunities = await engine.scan_all_opportunities(exchange_data)
        
        return opportunities, connector.get_health_status()
        
    except Exception as e:
        st.error(f"Error scanning markets: {e}")
        return [], {}


def display_header():
    """Display application header"""
    st.markdown('<h1 class="main-header">💰 Professional Arbitrage Opportunity Finder</h1>', 
                unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align: center; color: #666; margin-bottom: 2rem;'>
        <p>Intelligent multi-exchange arbitrage detection system with real-time monitoring</p>
        <p>🔍 Spatial Arbitrage | 🔺 Triangular Arbitrage | 📊 Statistical Analysis | 🤖 AI-Powered</p>
    </div>
    """, unsafe_allow_html=True)


def display_metrics(opportunities, health_status):
    """Display key metrics"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_opps = len(opportunities)
        st.metric(
            "🎯 Active Opportunities", 
            total_opps,
            delta=f"+{total_opps}" if total_opps > 0 else None
        )
    
    with col2:
        if opportunities:
            max_profit = max(opp.profit_percentage for opp in opportunities)
            st.metric("📈 Max Profit", f"{max_profit:.2f}%", delta="High")
        else:
            st.metric("📈 Max Profit", "0.00%")
    
    with col3:
        if opportunities:
            avg_profit = sum(opp.profit_percentage for opp in opportunities) / len(opportunities)
            st.metric("📊 Avg Profit", f"{avg_profit:.2f}%")
        else:
            st.metric("📊 Avg Profit", "0.00%")
    
    with col4:
        healthy_exchanges = sum(1 for status in health_status.values() 
                               if status['status'] == 'healthy')
        st.metric("🏥 Healthy Exchanges", f"{healthy_exchanges}/5")
    
    with col5:
        total_scans = st.session_state.total_scans
        st.metric("🔄 Total Scans", total_scans)


def display_opportunities(opportunities):
    """Display arbitrage opportunities"""
    st.markdown("### 🎯 Detected Opportunities")
    
    if not opportunities:
        st.info("👀 No arbitrage opportunities detected at the moment. Keep scanning!")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        arb_type = st.selectbox(
            "Filter by Type",
            ["All"] + [t.value for t in ArbitrageType]
        )
    
    with col2:
        risk_level = st.selectbox(
            "Filter by Risk",
            ["All", "LOW", "MEDIUM", "HIGH"]
        )
    
    with col3:
        min_profit = st.slider(
            "Min Profit %",
            0.0, 10.0, 0.0, 0.1
        )
    
    # Apply filters
    filtered_opps = opportunities
    
    if arb_type != "All":
        filtered_opps = [opp for opp in filtered_opps 
                        if opp.arbitrage_type.value == arb_type]
    
    if risk_level != "All":
        filtered_opps = [opp for opp in filtered_opps 
                        if opp.risk_level == risk_level]
    
    filtered_opps = [opp for opp in filtered_opps 
                    if opp.profit_percentage >= min_profit]
    
    st.markdown(f"**Showing {len(filtered_opps)} of {len(opportunities)} opportunities**")
    
    # Display as cards and table
    if filtered_opps:
        # Convert to dataframe
        df = pd.DataFrame([opp.to_dict() for opp in filtered_opps])
        
        # Styled dataframe
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        # Detailed cards for top opportunities
        st.markdown("#### 🏆 Top 3 Opportunities")
        
        for i, opp in enumerate(filtered_opps[:3]):
            card_class = "high-profit" if opp.profit_percentage > 2 else ""
            
            with st.expander(f"💎 Opportunity #{i+1} - {opp.profit_percentage:.2f}% Profit", 
                           expanded=(i == 0)):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"""
                    **Type:** {opp.arbitrage_type.value.title()}  
                    **Asset:** {opp.asset}  
                    **Path:** {' → '.join(opp.path)}
                    """)
                
                with col2:
                    st.markdown(f"""
                    **Buy Price:** ${opp.buy_price:,.4f}  
                    **Sell Price:** ${opp.sell_price:,.4f}  
                    **Spread:** {opp.profit_percentage:.2f}%
                    """)
                
                with col3:
                    st.markdown(f"""
                    **Required Capital:** ${opp.required_capital:,.2f}  
                    **Est. Profit:** ${opp.profit_absolute:,.2f}  
                    **Risk:** {opp.risk_level} | **Confidence:** {opp.confidence*100:.0f}%
                    """)
                
                # Action buttons
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
                with btn_col1:
                    st.button("📋 Copy Details", key=f"copy_{i}")
                with btn_col2:
                    st.button("⚡ Execute", key=f"exec_{i}", type="primary")


def display_analytics(opportunities):
    """Display analytics and charts"""
    st.markdown("### 📊 Analytics Dashboard")
    
    if not opportunities:
        st.info("Analytics will appear once opportunities are detected.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Profit distribution
        profit_data = [opp.profit_percentage for opp in opportunities]
        fig = go.Figure(data=[go.Histogram(x=profit_data, nbinsx=20)])
        fig.update_layout(
            title="Profit Distribution",
            xaxis_title="Profit %",
            yaxis_title="Count",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Opportunities by type
        type_counts = {}
        for opp in opportunities:
            type_counts[opp.arbitrage_type.value] = type_counts.get(opp.arbitrage_type.value, 0) + 1
        
        fig = go.Figure(data=[go.Pie(
            labels=list(type_counts.keys()),
            values=list(type_counts.values()),
            hole=0.4
        )])
        fig.update_layout(
            title="Opportunities by Type",
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Risk vs Profit scatter
    risk_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
    scatter_data = pd.DataFrame([
        {
            'Profit %': opp.profit_percentage,
            'Confidence': opp.confidence * 100,
            'Risk': opp.risk_level,
            'Risk_num': risk_map[opp.risk_level],
            'Type': opp.arbitrage_type.value
        }
        for opp in opportunities
    ])
    
    fig = px.scatter(
        scatter_data,
        x='Confidence',
        y='Profit %',
        color='Risk',
        size='Profit %',
        hover_data=['Type'],
        title="Risk vs Profit Analysis",
        color_discrete_map={'LOW': 'green', 'MEDIUM': 'orange', 'HIGH': 'red'}
    )
    st.plotly_chart(fig, use_container_width=True)


def display_exchange_health(health_status):
    """Display exchange health status"""
    st.markdown("### 🏥 Exchange Health Monitor")
    
    if not health_status:
        st.info("Exchange health data will appear after first scan.")
        return
    
    health_df = pd.DataFrame([
        {
            'Exchange': exchange,
            'Status': '🟢' if data['status'] == 'healthy' else '🟡' if data['status'] == 'degraded' else '🔴',
            'Success Rate': f"{data['success_rate']:.1f}%",
            'Errors': data['error_count'],
        }
        for exchange, data in health_status.items()
    ])
    
    st.dataframe(health_df, use_container_width=True, hide_index=True)


def display_sidebar():
    """Display sidebar with settings"""
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # Scan settings
        st.markdown("### 🔍 Scan Configuration")
        
        min_profit = st.slider(
            "Minimum Profit %",
            0.0, 10.0, 1.0, 0.1,
            help="Only show opportunities with profit above this threshold"
        )
        
        auto_scan = st.checkbox(
            "🔄 Auto-Scan",
            value=False,
            help="Automatically scan every few seconds"
        )
        
        scan_interval = st.slider(
            "Scan Interval (seconds)",
            5, 60, 10,
            disabled=not auto_scan
        )
        
        # Assets to monitor
        st.markdown("### 💎 Assets to Monitor")
        
        assets = st.multiselect(
            "Select Assets",
            ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT', 
             'ETH/BTC', 'BNB/BTC', 'BNB/ETH'],
            default=['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'ETH/BTC', 'BNB/BTC', 'BNB/ETH']
        )
        
        # System info
        st.markdown("### 📊 System Info")
        
        if st.session_state.last_scan_time:
            time_ago = (datetime.now() - st.session_state.last_scan_time).seconds
            st.info(f"Last scan: {time_ago}s ago")
        
        st.markdown("---")
        st.markdown("""
        **🚀 Features:**
        - ✅ Multi-exchange monitoring
        - ✅ Spatial arbitrage
        - ✅ Triangular arbitrage
        - ✅ Intelligent error handling
        - ✅ Real-time updates
        - ✅ Risk assessment
        """)
        
        return min_profit, auto_scan, scan_interval, assets


def main():
    """Main application"""
    display_header()
    
    # Sidebar
    min_profit, auto_scan, scan_interval, assets = display_sidebar()
    
    # Initialize components
    engine = ArbitrageEngine(min_profit_percentage=min_profit)
    connector = ExchangeConnector()
    
    # Control buttons
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        scan_button = st.button("🔍 Scan Now", type="primary", use_container_width=True)
    
    with col2:
        clear_button = st.button("🗑️ Clear Results", use_container_width=True)
    
    if clear_button:
        st.session_state.opportunities = []
        st.session_state.total_scans = 0
        st.session_state.historical_profits = []
        st.rerun()
    
    # Scan on button press or auto-scan
    if scan_button or (auto_scan and (
        st.session_state.last_scan_time is None or 
        (datetime.now() - st.session_state.last_scan_time).seconds >= scan_interval
    )):
        with st.spinner("🔄 Scanning markets for arbitrage opportunities..."):
            # Run async scan
            opportunities, health_status = asyncio.run(
                scan_markets(engine, connector, assets)
            )
            
            st.session_state.opportunities = opportunities
            st.session_state.total_scans += 1
            st.session_state.last_scan_time = datetime.now()
            
            if opportunities:
                st.session_state.historical_profits.append({
                    'time': datetime.now(),
                    'count': len(opportunities),
                    'max_profit': max(opp.profit_percentage for opp in opportunities)
                })
            
            st.success(f"✅ Scan complete! Found {len(opportunities)} opportunities")
            
            if auto_scan:
                st.rerun()
    
    # Display metrics
    opportunities = st.session_state.opportunities
    health_status = connector.get_health_status() if opportunities else {}
    
    display_metrics(opportunities, health_status)
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Opportunities", "📊 Analytics", "🏥 Exchange Health"])
    
    with tab1:
        display_opportunities(opportunities)
    
    with tab2:
        display_analytics(opportunities)
    
    with tab3:
        display_exchange_health(health_status)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #888; padding: 1rem;'>
        <p>💡 <b>Professional Arbitrage Finder</b> - Intelligent Multi-Exchange Monitoring System</p>
        <p>⚠️ Trading involves risk. Always do your own research and trade responsibly.</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
