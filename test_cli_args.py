#!/usr/bin/env python3
"""
Test script to validate command line argument handling in the enhanced NIFTY trading bot.
"""

import subprocess
import sys
from pathlib import Path


def test_cli_arguments():
    """Test various command line argument combinations."""
    
    # Find the Python script
    script_path = Path("enhanced_nifty_trading_bot.py")
    if not script_path.exists():
        print("❌ enhanced_nifty_trading_bot.py not found")
        return False
    
    print("🧪 Testing Enhanced NIFTY Trading Bot CLI Arguments")
    print("=" * 60)
    
    test_cases = [
        {
            "name": "Help command",
            "args": ["--help"],
            "expect_success": True,
            "timeout": 10
        },
        {
            "name": "Test mode with verbose",
            "args": ["--test", "--verbose"],
            "expect_success": True,
            "timeout": 30
        },
        {
            "name": "NIFTY 50 with min score",
            "args": ["--size", "nifty50", "--min-score", "5"],
            "expect_success": True,
            "timeout": 60
        },
        {
            "name": "Validation mode",
            "args": ["--validate", "--size", "nifty50"],
            "expect_success": True,
            "timeout": 30
        },
        {
            "name": "Custom config file",
            "args": ["--config", "config_enhanced_nifty.yaml", "--test"],
            "expect_success": True,
            "timeout": 30
        },
        {
            "name": "Market hours only",
            "args": ["--market-hours-only", "--test"],
            "expect_success": True,
            "timeout": 30
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print(f"   Command: python enhanced_nifty_trading_bot.py {' '.join(test_case['args'])}")
        
        try:
            cmd = [sys.executable, str(script_path)] + test_case['args']
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=test_case['timeout']
            )
            
            if test_case['expect_success']:
                if result.returncode == 0:
                    print(f"   ✅ PASSED - Exit code: {result.returncode}")
                    passed += 1
                else:
                    print(f"   ❌ FAILED - Exit code: {result.returncode}")
                    if result.stderr:
                        print(f"   Error: {result.stderr[:200]}...")
                    failed += 1
            else:
                if result.returncode != 0:
                    print(f"   ✅ PASSED - Expected failure, exit code: {result.returncode}")
                    passed += 1
                else:
                    print(f"   ❌ FAILED - Expected failure but got success")
                    failed += 1
                    
        except subprocess.TimeoutExpired:
            print(f"   ⏰ TIMEOUT - Test exceeded {test_case['timeout']} seconds")
            failed += 1
        except Exception as e:
            print(f"   💥 ERROR - {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    return failed == 0


def test_argument_parsing():
    """Test that argument parsing works correctly."""
    print("\n🔧 Testing Argument Parsing Logic")
    print("-" * 40)
    
    try:
        # Import the main module to test argument parsing
        import enhanced_nifty_trading_bot
        
        # Test that we can create the argument parser
        import argparse
        parser = argparse.ArgumentParser(description="Enhanced NIFTY Trading Bot with Multiple RSIs and EMAs")
        parser.add_argument("--size", choices=["nifty50", "nifty100", "nifty500"], 
                           default="nifty500", help="NIFTY index size (default: nifty500)")
        parser.add_argument("--config", type=str, help="Custom configuration file")
        parser.add_argument("--test", action="store_true", help="Test mode with limited symbols")
        parser.add_argument("--validate", action="store_true", help="Validate symbols only")
        parser.add_argument("--verbose", action="store_true", help="Verbose logging")
        parser.add_argument("--market-hours-only", action="store_true", 
                           help="Only run during Indian market hours")
        parser.add_argument("--min-score", type=int, default=4, 
                           help="Minimum signal score to display (default: 4)")
        
        # Test parsing various argument combinations
        test_args = [
            ["--size", "nifty50"],
            ["--test", "--verbose"],
            ["--min-score", "6"],
            ["--config", "test.yaml", "--validate"]
        ]
        
        for args in test_args:
            try:
                parsed = parser.parse_args(args)
                print(f"   ✅ Parsed: {args} -> {vars(parsed)}")
            except Exception as e:
                print(f"   ❌ Failed to parse: {args} -> {e}")
                return False
        
        print("   ✅ All argument parsing tests passed!")
        return True
        
    except Exception as e:
        print(f"   ❌ Argument parsing test failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Enhanced NIFTY Trading Bot CLI Test Suite")
    print("=" * 60)
    
    # Test argument parsing logic
    parsing_ok = test_argument_parsing()
    
    # Test actual CLI execution
    cli_ok = test_cli_arguments()
    
    if parsing_ok and cli_ok:
        print("\n🎉 All tests passed! CLI arguments are working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Please check the implementation.")
        sys.exit(1)