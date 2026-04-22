#!/usr/bin/env python3
"""
🏊 PoolSupplies.com Pricing Agent - Easy Starter
Run this to get started quickly!
"""

import os
import sys

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          🏊 POOLSUPPLIES.COM PRICING INTELLIGENCE AGENT          ║
║                                                                  ║
║                  AI-Powered Competitor Analysis                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")

def check_setup():
    """Check if everything is set up"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠️  API Key Not Found")
        print("\n📝 You need to set your Anthropic API key first:")
        print("\n1. Get free API key: https://console.anthropic.com/")
        print("2. Set environment variable:")
        print("\n   Mac/Linux:")
        print("   export ANTHROPIC_API_KEY='sk-ant-your-key-here'")
        print("\n   Windows:")
        print("   set ANTHROPIC_API_KEY=sk-ant-your-key-here")
        print("\n3. Run this script again")
        print("\n💡 Free credits included: Enough for ~200 product analyses!")
        return False
    
    return True

def show_menu():
    """Show interactive menu"""
    print("\nWhat would you like to do?\n")
    print("1. 🧪 Test Setup (recommended first time)")
    print("2. 🔍 Run Pricing Analysis (10 products)")
    print("3. 📊 Open Dashboard (view results)")
    print("4. 📖 View README")
    print("5. ❌ Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    return choice

def run_tests():
    """Run test suite"""
    print("\n" + "="*60)
    print("Running tests...")
    print("="*60 + "\n")
    
    try:
        import test_setup
        test_setup.run_all_tests()
    except Exception as e:
        print(f"❌ Error running tests: {e}")

def run_analysis():
    """Run pricing analysis"""
    print("\n" + "="*60)
    print("Starting pricing analysis...")
    print("="*60 + "\n")
    
    print("⏱️  This will take 2-3 minutes to analyze 10 products")
    print("🌐 Agent will search Amazon, Walmart, and Leslie's")
    print("\nPress Ctrl+C to cancel\n")
    
    try:
        import pricing_agent
        pricing_agent.main()
    except KeyboardInterrupt:
        print("\n\n⏸️  Analysis cancelled by user")
    except Exception as e:
        print(f"\n❌ Error running analysis: {e}")

def open_dashboard():
    """Open Streamlit dashboard"""
    print("\n" + "="*60)
    print("Opening dashboard...")
    print("="*60 + "\n")
    
    # Check if data exists
    if not os.path.exists('pricing_data.db'):
        print("⚠️  No pricing data found!")
        print("📝 Run option 2 (Pricing Analysis) first to generate data")
        return
    
    print("🚀 Launching Streamlit dashboard...")
    print("📊 Dashboard will open in your browser")
    print("\n💡 Press Ctrl+C to stop the dashboard server\n")
    
    os.system("streamlit run dashboard.py")

def view_readme():
    """Show README content"""
    print("\n" + "="*60)
    print("README")
    print("="*60 + "\n")
    
    try:
        with open('README.md', 'r') as f:
            content = f.read()
            # Show first 50 lines
            lines = content.split('\n')[:50]
            print('\n'.join(lines))
            print("\n... (see README.md for full documentation)")
    except FileNotFoundError:
        print("README.md not found")

def main():
    """Main entry point"""
    print_banner()
    
    if not check_setup():
        return
    
    print("✅ API key detected")
    print("✅ Ready to analyze competitor prices\n")
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            run_tests()
        elif choice == '2':
            run_analysis()
        elif choice == '3':
            open_dashboard()
        elif choice == '4':
            view_readme()
        elif choice == '5':
            print("\n👋 Thanks for using PoolSupplies Pricing Agent!")
            break
        else:
            print("\n❌ Invalid choice. Please enter 1-5.")
        
        input("\n⏎ Press Enter to continue...")
        print("\n" * 2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
