#!/usr/bin/env python3
"""
Test suite for TDD Gate System
Ensures the TDD gate system itself follows TDD principles
"""

import subprocess
import tempfile
import json
import sys
from pathlib import Path


def test_tdd_gate_validator():
    """Test the TDD gate validator functionality"""
    print("🧪 Testing TDD Gate Validator...")

    # Test bypass functionality
    try:
        result = subprocess.run(
            [
                "python",
                ".agent/scripts/tdd_gate_validator.py",
                "--bypass-justification",
                "Test bypass",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and "EMERGENCY BYPASS ACTIVATED" in result.stdout:
            print("✅ Bypass functionality works")
            return True
        else:
            print(f"❌ Bypass test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Bypass test error: {e}")
        return False


def test_tdd_validation():
    """Test normal TDD validation"""
    print("🧪 Testing TDD Validation...")

    # Create test file to validate
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("""
def test_sample():
    assert True
""")
        temp_test_path = f.name

    # Test validation with missing test file (should pass)
    try:
        result = subprocess.run(
            [
                "python",
                ".agent/scripts/tdd_gate_validator.py",
                "--project-root",
                ".",
                "--task-id",
                "test",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should pass because we have a test file
        if result.returncode == 0:
            print("✅ Validation correctly passes when test file exists")
            return True
        else:
            print(f"❌ Validation failed unexpectedly: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        return False

    # Test validation with NO test file (should fail)
    try:
        result = subprocess.run(
            [
                "python",
                ".agent/scripts/tdd_gate_validator.py",
                "--project-root",
                ".",
                "--task-id",
                "no_test",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        # Should fail because no test file
        if result.returncode != 0 and "No test files found" in result.stdout:
            print("✅ Validation correctly detects missing test files")
            return True
        else:
            print(f"❌ Validation failed to detect missing tests: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Missing test validation error: {e}")
        return False

        # Should fail because no test file for our sample
        if result.returncode != 0 and "No test files found" in result.stdout:
            print("✅ Validation correctly detects missing test files")
            return True
        else:
            print(f"❌ Unexpected validation result: {result.stdout}")
            return False
    except Exception as e:
        print(f"❌ Validation test error: {e}")
        return False


def test_baseline_framework():
    """Test baseline framework functionality"""
    print("🧪 Testing Baseline Framework...")

    try:
        result = subprocess.run(
            [
                "python",
                ".agent/scripts/tdd_gate_validator.py",
                "--project-root",
                ".",
                "--task-id",
                "test",
            ],
            capture_output=True,
            text=True,
            timeout=10,
            env={"TEST_FILE_PATH": test_file_path},
        )

        if result.returncode == 0 and "baseline_framework.py" in result.stdout:
            print("✅ Baseline framework is accessible")
            return True
        else:
            print(f"❌ Baseline framework test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Baseline framework test error: {e}")
        return False


def main():
    """Run all TDD system tests"""
    print("🧪 TDD Gate System Self-Test Suite")
    print("=" * 50)

    tests = [
        ("TDD Gate Validator", test_tdd_gate_validator),
        ("TDD Validation Logic", test_tdd_validation),
        ("Baseline Framework", test_baseline_framework),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        success = test_func()
        results.append((test_name, success))

    print(f"\n{'=' * 50}")
    print("🧪 Test Results Summary:")
    print("=" * 50)

    passed = 0
    failed = 0

    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if success:
            passed += 1
        else:
            failed += 1

    print(f"\n📊 Summary: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All TDD system tests passed!")
        return 0
    else:
        print("🚨 Some TDD system tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
