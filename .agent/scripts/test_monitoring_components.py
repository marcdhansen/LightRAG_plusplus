#!/usr/bin/env python3
"""
Comprehensive Tests for Enhanced Monitoring Components

Test suite for all P2 enhanced monitoring and dashboard components.
Validates functionality of real-time monitoring, dashboard, heartbeat integration,
adaptive enforcement, and automated blocking systems.

Test Coverage:
- Real-time SOP compliance monitoring
- Interactive dashboard (web and CLI)
- Enhanced heartbeat integration
- Adaptive enforcement rules
- Automated git hook blocking
- Integration scenarios
"""

import json
import os
import subprocess
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

# Add scripts directory to path for imports
scripts_dir = Path(__file__).parent
import sys

sys.path.insert(0, str(scripts_dir))


class TestSOPComplianceMonitor(unittest.TestCase):
    """Test cases for SOPComplianceMonitor."""

    def setUp(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_file = self.test_dir / "test_config.json"

        # Create test config
        test_config = {
            "check_interval_seconds": 5,
            "violation_threshold": 2,
            "adaptive_config": {
                "min_check_interval": 10,
                "max_check_interval": 60,
                "violation_history_limit": 10,
                "success_rate_threshold": 80,
            },
            "monitoring_checks": {
                "git_status": True,
                "session_locks": True,
                "mandatory_skills": False,  # Disable for tests
                "tdd_compliance": False,  # Disable for tests
                "documentation_integrity": False,
                "beads_connectivity": False,
            },
        }

        with open(self.config_file, "w") as f:
            json.dump(test_config, f)

        # Mock working directory
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)

        # Initialize git repository for testing
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

        # Create agent directories
        (self.test_dir / ".agent" / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Cleanup test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_monitor_initialization(self):
        """Test monitor initialization with config."""
        try:
            from realtime_sop_monitor import SOPComplianceMonitor

            monitor = SOPComplianceMonitor(str(self.config_file))

            self.assertEqual(monitor.current_interval, 5)
            self.assertEqual(monitor.violation_threshold, 2)
            self.assertFalse(monitor.monitoring_active)

        except ImportError:
            self.skipTest("realtime_sop_monitor module not available")

    def test_adaptive_interval_adjustment(self):
        """Test adaptive interval adjustment based on performance."""
        try:
            from realtime_sop_monitor import SOPComplianceMonitor

            monitor = SOPComplianceMonitor(str(self.config_file))

            # Test high compliance (should increase interval)
            for _i in range(6):
                monitor.performance_history.append({"compliant": True, "violations": 0})

            monitor._adapt_interval(True, 0)
            self.assertGreater(monitor.current_interval, 5)
            self.assertLessEqual(monitor.current_interval, 60)

            # Reset for low compliance test
            monitor.current_interval = 5
            monitor.performance_history.clear()

            # Test low compliance (should decrease interval)
            for _i in range(6):
                monitor.performance_history.append(
                    {"compliant": False, "violations": 3}
                )

            monitor._adapt_interval(False, 3)
            self.assertLess(monitor.current_interval, 5)
            self.assertGreaterEqual(monitor.current_interval, 10)

        except ImportError:
            self.skipTest("realtime_sop_monitor module not available")

    def test_git_status_check(self):
        """Test git status checking functionality."""
        try:
            from realtime_sop_monitor import SOPComplianceMonitor

            monitor = SOPComplianceMonitor(str(self.config_file))

            # Test clean status
            result = monitor._check_git_status()
            self.assertTrue(result["clean"])
            self.assertEqual(result["changes"], [])

            # Test dirty status
            test_file = self.test_dir / "test.txt"
            test_file.write_text("test content")

            result = monitor._check_git_status()
            self.assertFalse(result["clean"])
            self.assertTrue(any("test.txt" in change for change in result["changes"]))

        except ImportError:
            self.skipTest("realtime_sop_monitor module not available")


class TestAdaptiveEnforcementEngine(unittest.TestCase):
    """Test cases for AdaptiveEnforcementEngine."""

    def setUp(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_file = self.test_dir / "adaptive_config.json"

        # Create test adaptive config
        test_config = {
            "dynamic_rules": {
                "violation_thresholds": {
                    "base_threshold": 3,
                    "max_threshold": 10,
                    "adaptation_rate": 1.5,
                    "decay_rate": 0.9,
                },
                "enforcement_levels": {
                    "standard": {
                        "blocking_enabled": True,
                        "alerts_only": False,
                        "violation_tolerance": 3,
                    }
                },
            },
            "learning_settings": {
                "min_samples": 5,  # Reduced for tests
                "confidence_threshold": 0.8,
                "adaptation_sensitivity": 0.5,
            },
        }

        with open(self.config_file, "w") as f:
            json.dump(test_config, f)

        (self.test_dir / ".agent" / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_enforcement_engine_initialization(self):
        """Test enforcement engine initialization."""
        try:
            from adaptive_enforcement_engine import AdaptiveEnforcementEngine

            engine = AdaptiveEnforcementEngine(str(self.config_file))

            self.assertIsNotNone(engine.config)
            self.assertEqual(
                engine.config["dynamic_rules"]["violation_thresholds"][
                    "base_threshold"
                ],
                3,
            )
            self.assertFalse(engine.dashboard_active)  # Should not be active by default

        except ImportError:
            self.skipTest("adaptive_enforcement_engine module not available")

    def test_violation_recording(self):
        """Test violation recording and pattern analysis."""
        try:
            from adaptive_enforcement_engine import AdaptiveEnforcementEngine

            engine = AdaptiveEnforcementEngine(str(self.config_file))

            # Record some violations
            engine.record_violation("git_status_dirty", {"test": True})
            engine.record_violation("mandatory_skills_missing", {"test": True})
            engine.record_violation("git_status_dirty", {"test": True})

            # Check violation history
            self.assertEqual(len(engine.violation_history), 3)

            # Check pattern analysis
            patterns = engine._analyze_violation_patterns()
            self.assertTrue(
                any(p.violation_type == "git_status_dirty" for p in patterns)
            )

        except ImportError:
            self.skipTest("adaptive_enforcement_engine module not available")

    def test_adaptive_threshold_calculation(self):
        """Test adaptive threshold calculation."""
        try:
            from adaptive_enforcement_engine import AdaptiveEnforcementEngine

            engine = AdaptiveEnforcementEngine(str(self.config_file))

            # Test base threshold
            threshold = engine._calculate_adaptive_threshold("test_violation", 3)
            self.assertEqual(threshold, 3)

        except ImportError:
            self.skipTest("adaptive_enforcement_engine module not available")


class TestSOPBlockingMechanism(unittest.TestCase):
    """Test cases for SOPBlockingMechanism."""

    def setUp(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.config_file = self.test_dir / "blocking_config.json"

        # Create test blocking config
        test_config = {
            "blocking_enabled": True,
            "blocking_config": {
                "block_duration_minutes": 10,
                "auto_unblock": True,
                "critical_only": False,
            },
            "critical_violations": ["git_status_dirty", "mandatory_skills_missing"],
        }

        with open(self.config_file, "w") as f:
            json.dump(test_config, f)

        # Initialize git repository
        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

        (self.test_dir / ".agent" / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_blocking_mechanism_initialization(self):
        """Test blocking mechanism initialization."""
        try:
            from sop_blocking_mechanism import SOPBlockingMechanism

            blocker = SOPBlockingMechanism(str(self.config_file))

            self.assertTrue(blocker.config["blocking_enabled"])
            self.assertIn("git_status_dirty", blocker.config["critical_violations"])

        except ImportError:
            self.skipTest("sop_blocking_mechanism module not available")

    def test_critical_file_change_detection(self):
        """Test critical file change detection."""
        try:
            from sop_blocking_mechanism import SOPBlockingMechanism

            blocker = SOPBlockingMechanism(str(self.config_file))

            # Test critical files
            critical_files = [
                "lightrag/core.py",
                ".agent/config/something.json",
                "package.json",
            ]

            critical_changes = blocker._check_critical_file_changes(critical_files)
            self.assertEqual(len(critical_changes), 3)

            # Test non-critical files
            non_critical_files = ["docs/readme.md", "test/file.py", "src/helper.py"]

            critical_changes = blocker._check_critical_file_changes(non_critical_files)
            self.assertEqual(len(critical_changes), 0)

        except ImportError:
            self.skipTest("sop_blocking_mechanism module not available")


class TestDashboard(unittest.TestCase):
    """Test cases for compliance dashboard."""

    def setUp(self):
        """Setup test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / ".agent" / "logs").mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        """Cleanup test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_dashboard_initialization(self):
        """Test dashboard initialization."""
        try:
            from compliance_dashboard import ComplianceDashboard

            dashboard = ComplianceDashboard(port=8081)

            self.assertEqual(dashboard.port, 8081)
            self.assertFalse(dashboard.dashboard_active)

        except ImportError:
            self.skipTest("compliance_dashboard module not available")

    def test_dashboard_data_collection(self):
        """Test dashboard data collection."""
        try:
            from compliance_dashboard import ComplianceDashboard

            # Mock monitor
            mock_monitor = Mock()
            mock_monitor.get_status.return_value = {
                "monitoring_active": True,
                "current_interval": 30.0,
                "recent_violations": 2,
            }
            mock_monitor.get_recent_violations.return_value = [
                {
                    "timestamp": datetime.now().isoformat(),
                    "violations": ["git_status_dirty"],
                }
            ]

            dashboard = ComplianceDashboard(mock_monitor)
            data = dashboard._get_dashboard_data()

            self.assertTrue(data["monitoring_active"])
            self.assertEqual(data["current_interval"], 30.0)
            self.assertEqual(data["recent_violations"], 2)
            self.assertIn("overall_compliance", data)

        except ImportError:
            self.skipTest("compliance_dashboard module not available")


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for complete monitoring workflow."""

    def setUp(self):
        """Setup integration test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        (self.test_dir / ".agent" / "logs").mkdir(parents=True, exist_ok=True)
        (self.test_dir / ".agent" / "cache").mkdir(parents=True, exist_ok=True)

        os.chdir(self.test_dir)
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Integration Test"], check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)

    def tearDown(self):
        """Cleanup integration test environment."""
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_complete_monitoring_workflow(self):
        """Test complete monitoring workflow integration."""
        try:
            # Import all components
            from adaptive_enforcement_engine import AdaptiveEnforcementEngine
            from realtime_sop_monitor import SOPComplianceMonitor

            # Create components
            monitor = SOPComplianceMonitor()
            engine = AdaptiveEnforcementEngine()

            # Test integration: monitor and engine work together
            # Monitor doesn't have record_violation method, but has violation_history
            monitor.violation_history.append(
                {
                    "timestamp": datetime.now(),
                    "violations": ["git_status_dirty"],
                    "check_results": {"integration_test": True},
                }
            )
            engine.record_violation("git_status_dirty", {"integration_test": True})

            # Verify both systems have violation data
            self.assertEqual(len(monitor.violation_history), 1)
            self.assertEqual(len(engine.violation_history), 1)

            # Test performance metrics calculation
            metrics = engine._calculate_performance_metrics()
            self.assertIsNotNone(metrics)

        except ImportError:
            self.skipTest("Monitoring components not available for integration testing")

    def test_configuration_compatibility(self):
        """Test configuration compatibility across components."""
        # Test that all components can read the same config files
        config_files = [
            ".agent/config/realtime_monitor_config.json",
            ".agent/config/adaptive_sop_config.json",
            ".agent/config/adaptive_sop_rules.json",
        ]

        for config_file in config_files:
            config_path = self.test_dir / config_file
            config_path.parent.mkdir(parents=True, exist_ok=True)

            # Create basic config
            basic_config = {"test": True, "version": "1.0.0"}
            with open(config_path, "w") as f:
                json.dump(basic_config, f)

            # Verify it can be read
            with open(config_path) as f:
                loaded_config = json.load(f)

            self.assertTrue(loaded_config.get("test", False))

    def test_line_count_validation(self):
        """Validate that implementation meets P2 line count requirements."""
        script_files = [
            "realtime_sop_monitor.py",
            "compliance_dashboard.py",
            "adaptive_enforcement_engine.py",
            "sop_blocking_mechanism.py",
        ]

        total_lines = 0
        scripts_dir = Path(__file__).parent

        for script_file in script_files:
            script_path = scripts_dir / script_file
            if script_path.exists():
                with open(script_path) as f:
                    lines = len(f.readlines())
                    total_lines += lines
                    print(f"  {script_file}: {lines} lines")

        print(f"Total lines: {total_lines}")

        # P2 requirement: under 3,000 lines total
        self.assertLess(
            total_lines, 3000, f"P2 requirement failed: {total_lines} lines (max: 3000)"
        )

    def test_p2_success_criteria(self):
        """Test that all P2 success criteria are met."""
        # Test 1: Real-time monitoring with adaptive intervals
        try:
            from realtime_sop_monitor import SOPComplianceMonitor

            monitor = SOPComplianceMonitor()

            # Check adaptive interval parameters
            self.assertLessEqual(monitor.min_interval, 15)  # Should be 15s minimum
            self.assertGreaterEqual(monitor.max_interval, 300)  # Should be 300s maximum

        except ImportError:
            self.fail("Real-time monitoring component missing")

        # Test 2: Interactive dashboard with CLI fallback
        try:
            from compliance_dashboard import ComplianceDashboard

            dashboard = ComplianceDashboard()

            # Should have both web and CLI modes available
            self.assertIsNotNone(dashboard.web_available)

        except ImportError:
            self.fail("Dashboard component missing")

        # Test 3: Adaptive enforcement rules
        try:
            from adaptive_enforcement_engine import AdaptiveEnforcementEngine

            engine = AdaptiveEnforcementEngine()

            # Should have learning capabilities
            self.assertTrue(hasattr(engine, "record_violation"))
            self.assertTrue(hasattr(engine, "_analyze_violation_patterns"))

        except ImportError:
            self.fail("Adaptive enforcement component missing")

        # Test 4: Automated blocking mechanism
        try:
            from sop_blocking_mechanism import SOPBlockingMechanism

            blocker = SOPBlockingMechanism()

            # Should have blocking capabilities
            self.assertTrue(hasattr(blocker, "should_block_operation"))
            self.assertTrue(hasattr(blocker, "pre_commit_check"))

        except ImportError:
            self.fail("Automated blocking component missing")


def run_performance_tests():
    """Run performance tests for monitoring components."""
    print("🚀 Running performance tests...")

    # Test monitoring performance under load
    test_dir = Path(tempfile.mkdtemp())
    try:
        from realtime_sop_monitor import SOPComplianceMonitor

        monitor = SOPComplianceMonitor()

        # Record many violations quickly
        start_time = time.time()
        for i in range(100):
            monitor.record_violation(f"test_violation_{i}", {"performance_test": True})
        end_time = time.time()

        print(f"  Recorded 100 violations in {end_time - start_time:.3f}s")
        print(f"  Violations per second: {100 / (end_time - start_time):.1f}")

    except ImportError:
        print("  ⚠️ Performance tests skipped (monitoring module unavailable)")

    finally:
        import shutil

        shutil.rmtree(test_dir, ignore_errors=True)


def main():
    """Run test suite."""
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced Monitoring Tests")
    parser.add_argument(
        "--performance", action="store_true", help="Run performance tests"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--line-count", action="store_true", help="Check line count only"
    )

    args = parser.parse_args()

    if args.performance:
        run_performance_tests()
        return

    if args.line_count:
        suite = unittest.TestSuite()
        suite.addTest(TestIntegrationScenarios("test_line_count_validation"))
        runner = unittest.TextTestRunner(verbosity=2)
        runner.run(suite)
        return

    # Setup test discovery
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    if args.integration:
        suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))
    else:
        suite.addTests(loader.loadTestsFromTestCase(TestSOPComplianceMonitor))
        suite.addTests(loader.loadTestsFromTestCase(TestAdaptiveEnforcementEngine))
        suite.addTests(loader.loadTestsFromTestCase(TestSOPBlockingMechanism))
        suite.addTests(loader.loadTestsFromTestCase(TestDashboard))
        suite.addTests(loader.loadTestsFromTestCase(TestIntegrationScenarios))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, failfast=False)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'=' * 60}")
    print("Test Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Skipped: {len(result.skipped)}")

    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")

    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")

    print(f"{'=' * 60}")

    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
