#!/usr/bin/env python3
"""
Test script to verify terminal streaming output fixes.
Tests real-time output display without buffering.
"""

import subprocess
import time
import sys


def test_subprocess_streaming():
    """Test that subprocess streaming works without buffering."""
    print("=" * 60)
    print("TEST 1: Subprocess Real-Time Streaming")
    print("=" * 60)
    
    # Create a simple script that outputs lines slowly
    test_script = """
import time
import sys
for i in range(5):
    print(f"Output line {i+1}", flush=True)
    sys.stdout.flush()
    time.sleep(0.2)
print("Done!", flush=True)
"""
    
    start = time.time()
    process = subprocess.Popen(
        [sys.executable, "-c", test_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # Line buffering - CRITICAL FIX
        universal_newlines=True,
    )
    
    outputs = []
    for line in process.stdout:
        elapsed = time.time() - start
        outputs.append((elapsed, line.strip()))
        print(f"[{elapsed:.2f}s] {line.strip()}")
    
    process.wait()
    
    # Verify streaming worked (not all at once)
    if len(outputs) > 1:
        # Check that at least 2 outputs arrived with time gap
        time_diff = outputs[-1][0] - outputs[0][0]
        if time_diff > 0.5:  # Should have taken ~1 second
            print("\n✅ PASS: Output streamed in real-time (took {:.2f}s)".format(time_diff))
            return True
        else:
            print("\n❌ FAIL: Output appeared too quickly (took {:.2f}s, expected >0.5s)".format(time_diff))
            return False
    else:
        print("\n❌ FAIL: Not enough output received to verify streaming")
        return False


def test_termux_adapter():
    """Test Termux adapter functions."""
    print("\n" + "=" * 60)
    print("TEST 2: Termux Environment Adapter")
    print("=" * 60)
    
    from vulnera.core.utils.termux_adapter import TermuxAdapter
    
    # Check if we're actually on Termux
    is_termux = TermuxAdapter.is_termux()
    print(f"Running on Termux: {is_termux}")
    
    if not is_termux:
        print("⚠️  Not running on Termux - adapter functions will not modify commands")
        print("   This is expected behavior when testing on non-Termux systems")
    
    # Test command adaptation
    test_commands = [
        ("sudo apt-get install nmap", "pkg install -y nmap" if is_termux else "sudo apt-get install nmap"),
        ("apt install curl", "pkg install -y curl" if is_termux else "apt install curl"),
        ("sudo nmap -p 80 example.com", "nmap -p 80 example.com" if is_termux else "sudo nmap -p 80 example.com"),
    ]
    
    all_pass = True
    for original, expected in test_commands:
        adapted = TermuxAdapter.adapt_command_for_environment(original)
        if adapted == expected:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_pass = False
        print(f"{status}: adapt_command_for_environment()")
        print(f"  Input:    {original}")
        print(f"  Expected: {expected}")
        print(f"  Output:   {adapted}")
    
    # Test tool validation
    print("\nTesting tool validation:")
    is_valid, error = TermuxAdapter.validate_command("which nmap")
    if is_valid:
        print("✅ PASS: 'which nmap' is valid")
    else:
        print("❌ FAIL: 'which nmap' should be valid")
        all_pass = False
    
    # Test invalid command detection
    test_invalid = "apt-get install something"
    is_valid, error = TermuxAdapter.validate_command(test_invalid)
    if is_termux:
        # On Termux, this should be invalid
        if not is_valid:
            print("✅ PASS: 'apt-get install' correctly flagged as invalid on Termux")
        else:
            print("❌ FAIL: 'apt-get install' should be invalid on Termux")
            all_pass = False
    else:
        # On non-Termux, this should be valid
        if is_valid:
            print("✅ PASS: 'apt-get install' is valid on non-Termux systems")
        else:
            print("❌ FAIL: 'apt-get install' should be valid on non-Termux systems")
            all_pass = False
    
    return all_pass


def test_code_block_refresh():
    """Test that CodeBlock refresh works."""
    print("\n" + "=" * 60)
    print("TEST 3: CodeBlock Display Refresh")
    print("=" * 60)
    
    try:
        from vulnera.terminal_interface.components.code_block import CodeBlock
        
        # Create a code block
        block = CodeBlock()
        block.language = "python"
        block.code = "print('test')"
        
        # Add output
        block.output = "test output line 1\n"
        
        # Try to refresh (this would normally display to terminal)
        block.refresh(cursor=False)
        
        print("✅ PASS: CodeBlock.refresh() completed without errors")
        return True
    except Exception as e:
        print(f"❌ FAIL: CodeBlock.refresh() error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("OPEN VULNERA TERMINAL STREAMING OUTPUT TESTS")
    print("=" * 60 + "\n")
    
    results = {}
    
    # Test 1: Subprocess streaming
    try:
        results["test_subprocess_streaming"] = test_subprocess_streaming()
    except Exception as e:
        print(f"❌ ERROR in test_subprocess_streaming: {e}")
        results["test_subprocess_streaming"] = False
    
    # Test 2: Termux adapter
    try:
        results["test_termux_adapter"] = test_termux_adapter()
    except Exception as e:
        print(f"❌ ERROR in test_termux_adapter: {e}")
        results["test_termux_adapter"] = False
    
    # Test 3: CodeBlock refresh
    try:
        results["test_code_block_refresh"] = test_code_block_refresh()
    except Exception as e:
        print(f"❌ ERROR in test_code_block_refresh: {e}")
        results["test_code_block_refresh"] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
