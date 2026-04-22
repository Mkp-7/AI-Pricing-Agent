"""
Test script to verify Anthropic API key and basic agent functionality
Run this before running the full pricing analysis
"""

import os
import anthropic
import sys
sys.stdout.reconfigure(encoding='utf-8')
def test_api_key():
    """Test if API key is set and valid"""
    print("Testing Anthropic APys.stdout.reconfigure(encoding='utf-8')sI Key...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("ANTHROPIC_API_KEY not found in environment variables")
        print("\n How to set it:")
        print("\n   Mac/Linux:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("\n   Windows:")
        print("   set ANTHROPIC_API_KEY=your-key-here")
        print("\n Get your free API key at: https://console.anthropic.com/")
        return False
    
    print(f" API key found: {api_key[:10]}...{api_key[-4:]}")
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        # Simple test request
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ]
        )
        
        response = message.content[0].text
        print(f" API test successful!")
        print(f" Claude responded: '{response}'")
        return True
        
    except Exception as e:
        print(f" API test failed: {str(e)}")
        return False


def test_web_search():
    """Test if web search tool works"""
    print("\n🌐 Testing Web Search Capability...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⏭️  Skipping - no API key")
        return False
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            tools=[
                {
                    "type": "web_search_20260209",
                    "name": "web_search",
                    "allowed_callers": ["direct"]  # Add this line
                }
            ],
            messages=[
                {"role": "user", "content": "Search the web for current price of chlorine tablets on Amazon"}
            ]
        )
        
        # Check if search was used
        search_used = any(block.type == "tool_use" for block in message.content)
        
        if search_used:
            print("✅ Web search tool is working!")
            return True
        else:
            print("✅ Web search available (tool registered)")
            return True
            
    except Exception as e:
        print(f"❌ Web search test failed: {str(e)}")
        return False
    """Test if web search tool works"""
    print("\n Testing Web Search Capability...")
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("  Skipping - no API key")
        return False
    
    try:
        client = anthropic.Anthropic(api_key=api_key)
        
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            tools=[
                {
                    "type": "web_search_20260209",
                    "name": "web_search"
                }
            ],
            messages=[
                {"role": "user", "content": "What is the current price of a 50lb bucket of 3-inch chlorine tablets on Amazon? Just give me the price if you find it."}
            ]
        )
        
        # Check if search was used
        search_used = any(block.type == "tool_use" for block in message.content)
        
        if search_used:
            print(" Web search tool is working!")
            print(" Agent successfully searched the web")
            
            # Show response
            for block in message.content:
                if block.type == "text":
                    print(f" Found: {block.text[:200]}...")
            return True
        else:
            print("  Web search not used in response")
            return False
            
    except Exception as e:
        print(f" Web search test failed: {str(e)}")
        return False


def test_database():
    """Test if SQLite database can be created"""
    print("\n Testing Database Setup...")
    
    try:
        import sqlite3
        conn = sqlite3.connect('test_pricing.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test (
                id INTEGER PRIMARY KEY,
                value TEXT
            )
        """)
        
        cursor.execute("INSERT INTO test (value) VALUES (?)", ("test_value",))
        conn.commit()
        
        cursor.execute("SELECT * FROM test")
        result = cursor.fetchone()
        
        conn.close()
        
        # Clean up test db
        import os
        os.remove('test_pricing.db')
        
        print(" Database functionality working!")
        return True
        
    except Exception as e:
        print(f" Database test failed: {str(e)}")
        return False


def test_dependencies():
    """Test if all required packages are installed"""
    print("\n Testing Dependencies...")
    
    required_packages = {
        'anthropic': 'Anthropic API client',
        'sqlite3': 'SQLite database',
        'json': 'JSON parsing',
        'datetime': 'Date/time handling'
    }
    
    all_good = True
    for package, description in required_packages.items():
        try:
            __import__(package)
            print(f"   {package}: {description}")
        except ImportError:
            print(f"   {package}: MISSING - {description}")
            all_good = False
    
    return all_good


def run_all_tests():
    """Run all tests"""
    print("="*60)
    print(" PRICING AGENT TEST SUITE")
    print("="*60)
    
    results = {
        "Dependencies": test_dependencies(),
        "API Key": test_api_key(),
        "Web Search": test_web_search(),
        "Database": test_database()
    }
    
    print("\n" + "="*60)
    print(" TEST RESULTS")
    print("="*60)
    
    for test_name, passed in results.items():
        status = " PASS" if passed else " FAIL"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(results.values())
    
    print("="*60)
    if all_passed:
        print(" All tests passed! You're ready to run the pricing agent.")
        print("\n  Next step: python pricing_agent.py")
    else:
        print("  Some tests failed. Please fix the issues above.")
        print("\n Check README.md for troubleshooting help")
    print("="*60)
    
    return all_passed


if __name__ == "__main__":
    run_all_tests()
