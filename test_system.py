"""
Test script for Arbitrage Finder
Run this to verify the system is working correctly
"""

import asyncio
from core.arbitrage_engine import ArbitrageEngine
from core.exchange_connector import ExchangeConnector


async def test_system():
    """Test the arbitrage detection system"""
    
    print("🚀 Starting Arbitrage Finder System Test\n")
    print("=" * 80)
    
    # Initialize components
    print("\n1️⃣  Initializing components...")
    engine = ArbitrageEngine(min_profit_percentage=1.0)
    connector = ExchangeConnector()
    print("   ✓ Engine and connector initialized\n")
    
    # Test exchange connectivity
    print("2️⃣  Testing exchange connectivity...")
    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ETH/BTC', 'BNB/BTC', 'BNB/ETH']
    all_data = await connector.fetch_all_exchanges(symbols)
    print(f"   ✓ Connected to {len(all_data)} exchanges")
    
    for exchange, data in all_data.items():
        print(f"   📊 {exchange}: {len(data)} trading pairs")
    print()
    
    # Test price extraction
    print("3️⃣  Extracting market data...")
    exchange_prices = connector.get_exchange_prices(all_data)
    pair_prices = connector.get_pair_prices(all_data)
    
    total_prices = sum(len(prices) for prices in exchange_prices.values())
    print(f"   ✓ Extracted {total_prices} asset prices")
    
    total_pairs = sum(len(pairs) for pairs in pair_prices.values())
    print(f"   ✓ Extracted {total_pairs} trading pair prices\n")
    
    # Test arbitrage detection
    print("4️⃣  Scanning for arbitrage opportunities...")
    exchange_data = {
        'exchange_prices': exchange_prices,
        'pair_prices': pair_prices,
    }
    
    opportunities = await engine.scan_all_opportunities(exchange_data)
    print(f"   ✓ Scan complete: {len(opportunities)} opportunities detected\n")
    
    # Display opportunities
    if opportunities:
        print("5️⃣  Top Opportunities Detected:")
        print("=" * 80)
        
        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n   🎯 Opportunity #{i}")
            print(f"   ├─ Type: {opp.arbitrage_type.value.upper()}")
            print(f"   ├─ Asset: {opp.asset}")
            print(f"   ├─ Path: {' → '.join(opp.path)}")
            print(f"   ├─ Profit: {opp.profit_percentage:.2f}% (${opp.profit_absolute:.2f})")
            print(f"   ├─ Buy: ${opp.buy_price:.4f} | Sell: ${opp.sell_price:.4f}")
            print(f"   ├─ Risk: {opp.risk_level} | Confidence: {opp.confidence*100:.0f}%")
            print(f"   └─ Capital Required: ${opp.required_capital:.2f}")
    else:
        print("5️⃣  No opportunities found")
        print("   💡 Try lowering the minimum profit threshold\n")
    
    print("\n" + "=" * 80)
    
    # Test health monitoring
    print("\n6️⃣  Exchange Health Status:")
    health = connector.get_health_status()
    
    for exchange, status in health.items():
        status_emoji = "🟢" if status['status'] == 'healthy' else "🟡" if status['status'] == 'degraded' else "🔴"
        print(f"   {status_emoji} {exchange}: {status['success_rate']:.1f}% uptime | {status['error_count']} errors")
    
    print("\n" + "=" * 80)
    print("\n✅ System test completed successfully!")
    print("\n📝 Next steps:")
    print("   1. Run: streamlit run streamlit_app.py")
    print("   2. Open: http://localhost:8501")
    print("   3. Click 'Scan Now' to find real opportunities")
    print("\n" + "=" * 80 + "\n")
    
    return opportunities


if __name__ == "__main__":
    try:
        asyncio.run(test_system())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        raise
