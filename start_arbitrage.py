#!/usr/bin/env python3
"""
Arbitrage Opportunity Finder - Startup Script
============================================

This script provides an easy way to start the arbitrage system
with different configurations and modes.
"""

import argparse
import asyncio
import sys
import os
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'data', 'config']
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Created necessary directories")

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import streamlit
        import pandas
        import numpy
        import requests
        import ccxt
        import plotly
        import fastapi
        import uvicorn
        import loguru
        import pydantic
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def start_streamlit():
    """Start Streamlit dashboard"""
    print("🚀 Starting Streamlit dashboard...")
    os.system("streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0")

def start_api():
    """Start REST API server"""
    print("🚀 Starting REST API server...")
    from api_service import run_api
    run_api(host="0.0.0.0", port=8000)

def start_engine():
    """Start arbitrage engine directly"""
    print("🚀 Starting arbitrage engine...")
    from arbitrage_engine import main
    asyncio.run(main())

def run_tests():
    """Run test suite"""
    print("🧪 Running test suite...")
    os.system("python -m pytest test_arbitrage.py -v")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Arbitrage Opportunity Finder")
    parser.add_argument(
        "mode",
        choices=["dashboard", "api", "engine", "test", "setup"],
        help="Mode to run the application"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port for dashboard/API (default: 8501)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host address (default: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    print("💰 Professional Arbitrage Opportunity Finder")
    print("=" * 50)
    
    # Setup mode
    if args.mode == "setup":
        print("🔧 Setting up the application...")
        create_directories()
        if check_dependencies():
            print("✅ Setup completed successfully!")
            print("\nNext steps:")
            print("1. Configure your API keys in config.py (optional)")
            print("2. Run: python start_arbitrage.py dashboard")
        else:
            print("❌ Setup failed. Please install dependencies first.")
        return
    
    # Check dependencies for other modes
    if not check_dependencies():
        print("❌ Please run setup first: python start_arbitrage.py setup")
        return
    
    # Run selected mode
    if args.mode == "dashboard":
        start_streamlit()
    elif args.mode == "api":
        start_api()
    elif args.mode == "engine":
        start_engine()
    elif args.mode == "test":
        run_tests()

if __name__ == "__main__":
    main()