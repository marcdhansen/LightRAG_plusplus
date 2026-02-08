#!/usr/bin/env python3
"""
Comprehensive Test Suite for Multi-Phase Detection Engine
Tests detection accuracy, false positive prevention, and threshold calibration
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Add the script directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from multi_phase_detector import FalsePositivePrevention, MultiPhaseDetector


class TestMultiPhaseDetection(unittest.TestCase):
    """
    Comprehensive test suite for multi-phase detection
    """

    def setUp(self):
        """Set up test environment"""
        self.detector = MultiPhaseDetector()
        self.test_repo = None

    def tearDown(self):
        """Clean up test environment"""
        if self.test_repo and Path(self.test_repo).exists():
            import shutil

            shutil.rmtree(self.test_repo)

    def create_test_repository(self, scenario_name: str) -> str:
        """Create a test git repository for scenario testing"""
        test_dir = tempfile.mkdtemp(prefix=f"multi_phase_test_{scenario_name}_")

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=test_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=test_dir,
            check=True,
        )

        return test_dir

    def test_known_breach_case_detection(self):
        """
        Test detection against the known CI_CD_P0_RESOLUTION_PLAYBOOK.md breach
        """
        print("\n🧪 Testing known breach case detection...")

        # Test in current repository (contains the breach)
        detector = MultiPhaseDetector()

        # Run detection
        results = detector.run_detection()

        # Should detect minimum 3 indicators
        self.assertGreaterEqual(
            results["total_indicators"],
            3,
            f"Expected >=3 indicators for breach case, got {results['total_indicators']}",
        )

        # Should specifically detect terminology indicators
        self.assertGreaterEqual(
            results["indicators"]["terminology"],
            1,
            "Should detect 'Hybrid Approach' terminology",
        )

        # Should detect documentation structure
        self.assertGreaterEqual(
            results["indicators"]["documentation"],
            1,
            "Should detect '3 PR groups' structure",
        )

        # Should be flagged as multi-phase
        self.assertTrue(
            results["is_multi_phase"],
            "Known breach case should be detected as multi-phase",
        )

        print(f"   ✅ Breach case detected: {results['total_indicators']} indicators")

    def test_terminology_detection_patterns(self):
        """
        Test various phase terminology patterns
        """
        print("\n🧪 Testing terminology detection patterns...")

        terminology_tests = [
            ("Phase 1 implementation complete", True),
            ("PR Group 2: Pre-commit resilience", True),
            ("Hybrid Approach for optimal risk management", True),
            ("Stage 2 deployment preparation", True),
            ("Implementation Group A: Core changes", True),
            ("Simple bug fix", False),
            ("Performance optimization", False),
            ("Documentation update", False),
        ]

        for test_text, should_detect in terminology_tests:
            with self.subTest(text=test_text):
                # Create test content
                test_content = f"# Test Document\n\n{test_text}\n\nMore content here."

                # Count pattern matches
                matches = 0
                for pattern in self.detector.config["terminology_patterns"]:
                    import re

                    if re.search(pattern, test_content):
                        matches += 1

                detected = matches > 0

                if should_detect:
                    self.assertTrue(
                        detected, f"Should detect phase terminology in: {test_text}"
                    )
                else:
                    self.assertFalse(
                        detected, f"Should not detect phase terminology in: {test_text}"
                    )

                print(
                    f"   {'✅' if detected == should_detect else '❌'} '{test_text[:30]}...' -> {'Detected' if detected else 'Not detected'}"
                )

    def test_threshold_calibration(self):
        """
        Test detection threshold calibration
        """
        print("\n🧪 Testing threshold calibration...")

        # Test exactly at threshold (3 indicators)
        self.detector.indicators = {
            "terminology": 1,
            "git_patterns": 1,
            "documentation": 1,
            "file_modifications": 0,
            "complexity_signals": 0,
        }
        self.assertTrue(
            self.detector.is_multi_phase_detected(), "Should detect at threshold (3)"
        )

        # Test just below threshold (2 indicators)
        self.detector.indicators = {
            "terminology": 1,
            "git_patterns": 1,
            "documentation": 0,
            "file_modifications": 0,
            "complexity_signals": 0,
        }
        self.assertFalse(
            self.detector.is_multi_phase_detected(),
            "Should not detect below threshold (2)",
        )

        # Test well above threshold (5 indicators)
        self.detector.indicators = {
            "terminology": 2,
            "git_patterns": 1,
            "documentation": 1,
            "file_modifications": 1,
            "complexity_signals": 0,
        }
        self.assertTrue(
            self.detector.is_multi_phase_detected(),
            "Should detect well above threshold (5)",
        )

        print("   ✅ Threshold calibration working correctly")

    def test_false_positive_prevention(self):
        """
        Test prevention of false positives for legitimate single-phase work
        """
        print("\n🧪 Testing false positive prevention...")

        # Test scenarios that should NOT be detected
        false_positive_scenarios = [
            {
                "name": "Simple bug fix",
                "indicators": {
                    "terminology": 0,
                    "git_patterns": 1,
                    "documentation": 0,
                    "file_modifications": 1,
                    "complexity_signals": 0,
                },
                "should_detect": False,
            },
            {
                "name": "Documentation only",
                "indicators": {
                    "terminology": 0,
                    "git_patterns": 0,
                    "documentation": 1,
                    "file_modifications": 0,
                    "complexity_signals": 0,
                },
                "should_detect": False,
            },
            {
                "name": "Performance optimization",
                "indicators": {
                    "terminology": 0,
                    "git_patterns": 1,
                    "documentation": 0,
                    "file_modifications": 1,
                    "complexity_signals": 1,
                },
                "should_detect": False,
            },
            {
                "name": "Code refactoring",
                "indicators": {
                    "terminology": 0,
                    "git_patterns": 1,
                    "documentation": 0,
                    "file_modifications": 1,
                    "complexity_signals": 0,
                },
                "should_detect": False,
            },
        ]

        for scenario in false_positive_scenarios:
            with self.subTest(scenario=scenario["name"]):
                self.detector.indicators = scenario["indicators"]
                detected = self.detector.is_multi_phase_detected()

                if scenario["should_detect"]:
                    self.assertTrue(detected, f"Should detect {scenario['name']}")
                else:
                    self.assertFalse(
                        detected, f"Should not detect {scenario['name']} as multi-phase"
                    )

                total_indicators = sum(scenario["indicators"].values())
                status = "DETECTED" if detected else "CLEAR"
                print(
                    f"   {'✅' if detected == scenario['should_detect'] else '❌'} {scenario['name']} ({total_indicators} indicators) -> {status}"
                )

    def test_detection_categories(self):
        """
        Test individual detection categories
        """
        print("\n🧪 Testing individual detection categories...")

        # Test each category individually
        categories = [
            "terminology",
            "git_patterns",
            "documentation",
            "file_modifications",
            "complexity_signals",
        ]

        for category in categories:
            with self.subTest(category=category):
                # Set only this category to have indicators
                test_indicators = {cat: 0 for cat in categories}
                test_indicators[category] = 3  # Max value for this category

                self.detector.indicators = test_indicators
                detected = self.detector.is_multi_phase_detected()

                # Single category should not trigger detection (below threshold)
                self.assertFalse(
                    detected,
                    f"Single category ({category}) should not trigger detection",
                )

                print(f"   ✅ {category}: 3 indicators -> Not detected (correct)")

    def test_multi_category_combination(self):
        """
        Test combinations of multiple categories
        """
        print("\n🧪 Testing multi-category combinations...")

        # Test various combinations
        combinations = [
            # (terminology, git_patterns, documentation, file_modifications, complexity_signals, should_detect)
            (1, 1, 1, 0, 0, True),  # Exactly at threshold
            (2, 1, 0, 0, 0, True),  # Above threshold
            (1, 0, 1, 0, 0, False),  # Below threshold
            (0, 1, 1, 0, 0, False),  # Below threshold
            (1, 1, 0, 1, 0, True),  # Above threshold
            (0, 0, 0, 1, 1, False),  # Below threshold
            (2, 2, 0, 0, 0, True),  # Well above threshold
        ]

        for combo in combinations:
            with self.subTest(combo=combo):
                indicators = {
                    "terminology": combo[0],
                    "git_patterns": combo[1],
                    "documentation": combo[2],
                    "file_modifications": combo[3],
                    "complexity_signals": combo[4],
                }

                self.detector.indicators = indicators
                detected = self.detector.is_multi_phase_detected()

                total_indicators = sum(indicators.values())
                expected = combo[5]

                self.assertEqual(
                    detected,
                    expected,
                    f"Combination {indicators} (total: {total_indicators}) should {'detect' if expected else 'not detect'}",
                )

                status = "DETECTED" if detected else "CLEAR"
                print(f"   ✅ {indicators} (total: {total_indicators}) -> {status}")

    def test_configuration_loading(self):
        """
        Test configuration loading and defaults
        """
        print("\n🧪 Testing configuration loading...")

        # Test default configuration
        detector = MultiPhaseDetector()

        self.assertEqual(detector.threshold, 3, "Default threshold should be 3")
        self.assertIsInstance(
            detector.config["terminology_patterns"],
            list,
            "Should have terminology patterns",
        )
        self.assertGreater(
            len(detector.config["terminology_patterns"]),
            0,
            "Should have terminology patterns",
        )

        # Test custom configuration
        custom_config = {
            "threshold": 5,
            "terminology_patterns": [r"(?i)(custom.*pattern)"],
        }

        config_file = Path(tempfile.mkdtemp()) / "custom_config.json"
        with open(config_file, "w") as f:
            json.dump(custom_config, f)

        custom_detector = MultiPhaseDetector(str(config_file))

        self.assertEqual(custom_detector.threshold, 5, "Should load custom threshold")
        self.assertEqual(
            len(custom_detector.config["terminology_patterns"]),
            1,
            "Should load custom patterns",
        )

        print("   ✅ Configuration loading working correctly")

    def test_error_handling(self):
        """
        Test error handling in various scenarios
        """
        print("\n🧪 Testing error handling...")

        # Test with invalid git repository
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "git")

            detector = MultiPhaseDetector()
            results = detector.run_detection()

            # Should handle errors gracefully
            self.assertIsInstance(
                results, dict, "Should return results even with errors"
            )
            self.assertIn("timestamp", results, "Should have timestamp in results")

        print("   ✅ Error handling working correctly")

    def test_performance_characteristics(self):
        """
        Test performance characteristics of detection engine
        """
        print("\n🧪 Testing performance characteristics...")

        import time

        # Measure detection time
        start_time = time.time()
        detector = MultiPhaseDetector()
        results = detector.run_detection()
        end_time = time.time()

        execution_time = end_time - start_time

        # Should complete within reasonable time (adjust as needed)
        self.assertLess(
            execution_time,
            10.0,
            f"Detection should complete within 10 seconds, took {execution_time:.2f}s",
        )

        print(f"   ✅ Performance: {execution_time:.2f}s (acceptable)")

    def test_logging_functionality(self):
        """
        Test detection logging functionality
        """
        print("\n🧪 Testing logging functionality...")

        detector = MultiPhaseDetector()
        results = detector.run_detection()

        # Check if log file was created
        log_dir = Path(".agent/logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("multi_phase_detection_*.json"))

            if log_files:
                # Check log file content
                with open(log_files[0]) as f:
                    log_data = json.load(f)

                self.assertIn("timestamp", log_data, "Log should have timestamp")
                self.assertIn("indicators", log_data, "Log should have indicators")
                self.assertIn(
                    "total_indicators", log_data, "Log should have total indicators"
                )

                print(f"   ✅ Logging working: {log_files[0].name}")
            else:
                print("   ⚠️  No log files found (may be expected in test environment)")
        else:
            print("   ⚠️  Log directory not found (may be expected in test environment)")

    def test_indicator_capping(self):
        """
        Test that indicators are properly capped at maximum values
        """
        print("\n🧪 Testing indicator capping...")

        # Test that individual categories are capped at 3
        detector = MultiPhaseDetector()

        # This should result in capped values
        results = detector.run_detection()

        for category, count in results["indicators"].items():
            self.assertLessEqual(
                count, 3, f"Category {category} should be capped at 3, got {count}"
            )

        print("   ✅ Indicator capping working correctly")


class TestFalsePositivePrevention(unittest.TestCase):
    """
    Test false positive prevention mechanisms
    """

    def setUp(self):
        """Set up false positive prevention tests"""
        self.fpp = FalsePositivePrevention()

    def test_legitimate_patterns(self):
        """
        Test legitimate pattern recognition
        """
        print("\n🧪 Testing legitimate pattern recognition...")

        legitimate_texts = [
            "Refactor the code for better maintainability",
            "Performance optimization for faster execution",
            "Update documentation for new API",
            "Fix bug in user authentication",
            "Improve test coverage for core modules",
        ]

        for text in legitimate_texts:
            with self.subTest(text=text):
                # Check if text matches legitimate patterns
                matches_legitimate = False
                for pattern in self.fpp.legitimate_patterns.values():
                    import re

                    if re.search(pattern, text):
                        matches_legitimate = True
                        break

                # Most legitimate texts should match patterns
                print(
                    f"   {'✅' if matches_legitimate else '⚠️'} '{text[:30]}...' -> {'Legitimate' if matches_legitimate else 'Unknown'}"
                )


def run_comprehensive_test():
    """
    Run comprehensive test suite with detailed reporting
    """
    print("🚨 Multi-Phase Detection Engine - Comprehensive Test Suite")
    print("=" * 60)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestMultiPhaseDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestFalsePositivePrevention))

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)

    # Summary
    print(f"\n{'=' * 60}")
    print("📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(
        f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print("\n🚨 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('Exception:')[-1].strip()}")

    if result.wasSuccessful():
        print(
            "\n✅ All tests passed! Multi-phase detection engine is working correctly."
        )
        return 0
    else:
        print("\n❌ Some tests failed. Review the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(run_comprehensive_test())
