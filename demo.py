#!/usr/bin/env python3
"""
SABER Education Dashboard - Demo Launcher
Launches the professional dashboard for demonstration purposes
"""

import sys
import os
import webbrowser
from threading import Timer

# ASCII Art Banner
BANNER = """
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ███████╗ █████╗ ██████╗ ███████╗██████╗                          ║
║   ██╔════╝██╔══██╗██╔══██╗██╔════╝██╔══██╗                         ║
║   ███████╗███████║██████╔╝█████╗  ██████╔╝                         ║
║   ╚════██║██╔══██║██╔══██╗██╔══╝  ██╔══██╗                         ║
║   ███████║██║  ██║██████╔╝███████╗██║  ██║                         ║
║   ╚══════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝  ╚═╝                         ║
║                                                                      ║
║            Educational Analytics Platform - DEMO MODE               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

def print_banner():
    """Print welcome banner"""
    print("\033[94m" + BANNER + "\033[0m")  # Blue color
    print("\n")

def print_info():
    """Print demo information"""
    print("=" * 74)
    print("                    DEMO INFORMATION                                ")
    print("=" * 74)
    print("\n📊 Dashboard Features:")
    print("   • Professional landing page with platform overview")
    print("   • National-level analytics and visualizations")
    print("   • Department and municipality analysis")
    print("   • School-level performance tracking")
    print("   • Socioeconomic impact analysis")
    print("   • Predictive analytics with ML models")
    print("   • Educational Equity KPIs with multi-level filtering")
    print("\n🔧 Demo Configuration:")
    print("   • Port: 8052")
    print("   • URL: http://localhost:8052/")
    print("   • Environment: Development")
    print("   • Debug Mode: Enabled")
    print("\n🎯 Navigation Guide:")
    print("   1. Landing page loads first (professional overview)")
    print("   2. Click 'Explore Dashboard' to access analytics")
    print("   3. Use tabs to navigate between different analyses")
    print("   4. Apply filters to customize your view")
    print("   5. Hover over charts for interactive details")
    print("\n" + "=" * 74)
    print("\n")

def open_browser():
    """Open browser after a short delay"""
    webbrowser.open('http://localhost:8052/')

def check_data_files():
    """Check if data files exist"""
    required_files = [
        'Examen_Saber_11_SS_20241.parquet',
        'Examen_Saber_11_SS_20242.parquet'
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)

    if missing_files:
        print("\n⚠️  WARNING: Some data files are missing:")
        for file in missing_files:
            print(f"   • {file}")
        print("\n   The demo will still run but may show limited data.")
        print("   Place Saber 11 Parquet files in the current directory for full demo.\n")
        return False
    return True

def main():
    """Main demo launcher"""
    print_banner()
    print_info()

    # Check for data files
    has_data = check_data_files()

    print("🚀 Starting SABER Education Dashboard Demo...\n")

    # Set environment for demo
    os.environ['FLASK_ENV'] = 'development'

    # Schedule browser opening
    print("📱 Opening browser in 3 seconds...")
    timer = Timer(3.0, open_browser)
    timer.start()

    print("\n" + "=" * 74)
    print("                    DEMO IS RUNNING                                 ")
    print("=" * 74)
    print("\n✨ Demo Tips:")
    print("   • Start at the landing page to see the professional design")
    print("   • Explore each tab to see different analytics capabilities")
    print("   • Try the KPI dashboard with different filters")
    print("   • Check out the predictive analytics for ML insights")
    print("   • Press Ctrl+C to stop the demo")
    print("\n" + "=" * 74 + "\n")

    # Import and run the app
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=8052)
    except KeyboardInterrupt:
        print("\n\n✅ Demo stopped successfully!")
        print("   Thank you for exploring SABER Educational Analytics Platform!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error starting demo: {e}")
        print("   Please ensure all dependencies are installed:")
        print("   pip install -r requirements_auth.txt\n")
        sys.exit(1)

if __name__ == '__main__':
    main()
