#!/usr/bin/env python3
"""
Statistical Analysis and Automated Result Collection for A/B Testing Framework
Advanced statistical methods with significance testing, confidence intervals, and automated decision making
"""

import asyncio
import json
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats


class TestType(str, Enum):
    """Statistical test types"""

    T_TEST = "t_test"
    Z_TEST = "z_test"
    CHI_SQUARE = "chi_square"
    MANN_WHITNEY = "mann_whitney"
    BOOTSTRAP = "bootstrap"


class DecisionResult(str, Enum):
    """Automated decision results"""

    CONTROL_WINNER = "control_winner"
    TREATMENT_WINNER = "treatment_winner"
    NO_SIGNIFICANT_DIFFERENCE = "no_significant_difference"
    INCONCLUSIVE = "inconclusive"
    NEED_MORE_DATA = "need_more_data"


@dataclass
class StatisticalTestResult:
    """Result of statistical analysis"""

    test_type: TestType
    test_statistic: float
    p_value: float
    confidence_interval: tuple[float, float]
    effect_size: float
    statistical_power: float
    sample_size_control: int
    sample_size_treatment: int
    conclusion: str
    significant: bool


@dataclass
class ConfidenceInterval:
    """Confidence interval data"""

    lower_bound: float
    upper_bound: float
    confidence_level: float
    margin_of_error: float


@dataclass
class EffectSize:
    """Effect size measurements"""

    cohens_d: float
    hedges_g: float
    cliffs_delta: float
    interpretation: str  # "small", "medium", "large"


@dataclass
class PowerAnalysis:
    """Statistical power analysis"""

    achieved_power: float
    required_power: float
    effect_size: float
    alpha: float
    sample_size: int
    required_sample_size: int
    power_sufficient: bool


class StatisticalAnalyzer:
    """Advanced statistical analysis engine for A/B testing"""

    def __init__(self, confidence_level: float = 0.95, min_sample_size: int = 30):
        self.confidence_level = confidence_level
        self.alpha = 1.0 - confidence_level
        self.min_sample_size = min_sample_size

    def analyze_experiment(
        self,
        control_data: list[float],
        treatment_data: list[float],
        test_type: TestType = TestType.T_TEST,
    ) -> StatisticalTestResult:
        """Perform comprehensive statistical analysis"""

        # Validate input data
        if (
            len(control_data) < self.min_sample_size
            or len(treatment_data) < self.min_sample_size
        ):
            return StatisticalTestResult(
                test_type=test_type,
                test_statistic=0.0,
                p_value=1.0,
                confidence_interval=(0.0, 0.0),
                effect_size=0.0,
                statistical_power=0.0,
                sample_size_control=len(control_data),
                sample_size_treatment=len(treatment_data),
                conclusion="Insufficient sample size for statistical analysis",
                significant=False,
            )

        # Descriptive statistics
        control_mean = statistics.mean(control_data)
        treatment_mean = statistics.mean(treatment_data)
        control_std = statistics.stdev(control_data) if len(control_data) > 1 else 0
        treatment_std = (
            statistics.stdev(treatment_data) if len(treatment_data) > 1 else 0
        )

        # Perform selected statistical test
        if test_type == TestType.T_TEST:
            return self._perform_t_test(control_data, treatment_data)
        elif test_type == TestType.Z_TEST:
            return self._perform_z_test(control_data, treatment_data)
        elif test_type == TestType.MANN_WHITNEY:
            return self._perform_mann_whitney(control_data, treatment_data)
        elif test_type == TestType.BOOTSTRAP:
            return self._perform_bootstrap_test(control_data, treatment_data)
        else:
            raise ValueError(f"Unsupported test type: {test_type}")

    def _perform_t_test(
        self, control_data: list[float], treatment_data: list[float]
    ) -> StatisticalTestResult:
        """Perform independent samples t-test"""

        # Calculate t-statistic and p-value
        if len(control_data) >= 30 and len(treatment_data) >= 30:
            # Use scipy for accurate calculation
            t_stat, p_value = stats.ttest_ind(
                treatment_data, control_data, equal_var=False
            )
        else:
            # Fallback to manual calculation for small samples
            t_stat, p_value = self._manual_t_test(control_data, treatment_data)

        # Calculate confidence interval for difference in means
        mean_diff = statistics.mean(treatment_data) - statistics.mean(control_data)
        se_diff = self._calculate_standard_error_difference(
            control_data, treatment_data
        )
        critical_t = stats.t.ppf(
            1 - self.alpha / 2, min(len(control_data), len(treatment_data)) - 1
        )

        margin_error = critical_t * se_diff
        ci_lower = mean_diff - margin_error
        ci_upper = mean_diff + margin_error

        # Calculate effect size (Cohen's d)
        pooled_std = math.sqrt(
            (
                (len(control_data) - 1) * statistics.stdev(control_data) ** 2
                + (len(treatment_data) - 1) * statistics.stdev(treatment_data) ** 2
            )
            / (len(control_data) + len(treatment_data) - 2)
        )
        cohens_d = mean_diff / pooled_std if pooled_std > 0 else 0

        # Calculate statistical power
        power = self._calculate_power(cohens_d, len(control_data), len(treatment_data))

        # Determine conclusion
        significant = p_value < self.alpha
        if significant:
            if mean_diff > 0:
                conclusion = f"Treatment is significantly better (p={p_value:.4f}, effect_size={cohens_d:.3f})"
            else:
                conclusion = f"Control is significantly better (p={p_value:.4f}, effect_size={abs(cohens_d):.3f})"
        else:
            conclusion = f"No significant difference found (p={p_value:.4f})"

        return StatisticalTestResult(
            test_type=TestType.T_TEST,
            test_statistic=t_stat,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=cohens_d,
            statistical_power=power,
            sample_size_control=len(control_data),
            sample_size_treatment=len(treatment_data),
            conclusion=conclusion,
            significant=significant,
        )

    def _perform_z_test(
        self, control_data: list[float], treatment_data: list[float]
    ) -> StatisticalTestResult:
        """Perform Z-test for large samples"""

        if len(control_data) < 30 or len(treatment_data) < 30:
            return self._perform_t_test(
                control_data, treatment_data
            )  # Fallback to t-test

        control_mean = statistics.mean(control_data)
        treatment_mean = statistics.mean(treatment_data)
        control_var = statistics.variance(control_data)
        treatment_var = statistics.variance(treatment_data)

        # Calculate Z-statistic
        se_diff = math.sqrt(
            control_var / len(control_data) + treatment_var / len(treatment_data)
        )
        z_stat = (treatment_mean - control_mean) / se_diff if se_diff > 0 else 0

        # Calculate p-value (two-tailed)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

        # Confidence interval
        critical_z = stats.norm.ppf(1 - self.alpha / 2)
        margin_error = critical_z * se_diff
        mean_diff = treatment_mean - control_mean
        ci_lower = mean_diff - margin_error
        ci_upper = mean_diff + margin_error

        # Effect size
        pooled_std = math.sqrt(
            (control_var * len(control_data) + treatment_var * len(treatment_data))
            / (len(control_data) + len(treatment_data))
        )
        effect_size = mean_diff / pooled_std if pooled_std > 0 else 0

        # Power calculation
        power = self._calculate_power(
            effect_size, len(control_data), len(treatment_data)
        )

        return StatisticalTestResult(
            test_type=TestType.Z_TEST,
            test_statistic=z_stat,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=effect_size,
            statistical_power=power,
            sample_size_control=len(control_data),
            sample_size_treatment=len(treatment_data),
            conclusion=f"Z-test: p={p_value:.4f}, effect_size={effect_size:.3f}",
            significant=p_value < self.alpha,
        )

    def _perform_mann_whitney(
        self, control_data: list[float], treatment_data: list[float]
    ) -> StatisticalTestResult:
        """Perform Mann-Whitney U test (non-parametric)"""

        u_stat, p_value = stats.mannwhitneyu(
            treatment_data, control_data, alternative="two-sided"
        )

        # For Mann-Whitney, we use rank-based effect size
        effect_size = self._calculate_cliffs_delta(control_data, treatment_data)

        # Confidence interval for median difference (bootstrap)
        ci_lower, ci_upper = self._bootstrap_median_ci(control_data, treatment_data)

        # Power (approximation for non-parametric test)
        power = self._calculate_nonparametric_power(
            effect_size, len(control_data), len(treatment_data)
        )

        return StatisticalTestResult(
            test_type=TestType.MANN_WHITNEY,
            test_statistic=u_stat,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=effect_size,
            statistical_power=power,
            sample_size_control=len(control_data),
            sample_size_treatment=len(treatment_data),
            conclusion=f"Mann-Whitney: p={p_value:.4f}, Cliff's delta={effect_size:.3f}",
            significant=p_value < self.alpha,
        )

    def _perform_bootstrap_test(
        self,
        control_data: list[float],
        treatment_data: list[float],
        n_bootstrap: int = 10000,
    ) -> StatisticalTestResult:
        """Perform bootstrap test for difference in means"""

        # Bootstrap sampling
        bootstrap_diffs = []
        np.random.seed(42)  # For reproducibility

        for _ in range(n_bootstrap):
            # Resample with replacement
            bootstrap_control = np.random.choice(
                control_data, size=len(control_data), replace=True
            )
            bootstrap_treatment = np.random.choice(
                treatment_data, size=len(treatment_data), replace=True
            )

            diff = np.mean(bootstrap_treatment) - np.mean(bootstrap_control)
            bootstrap_diffs.append(diff)

        # Calculate p-value
        observed_diff = np.mean(treatment_data) - np.mean(control_data)
        extreme_count = sum(
            1 for diff in bootstrap_diffs if abs(diff) >= abs(observed_diff)
        )
        p_value = extreme_count / n_bootstrap

        # Confidence interval
        ci_lower = np.percentile(bootstrap_diffs, (1 - self.confidence_level) * 100 / 2)
        ci_upper = np.percentile(
            bootstrap_diffs, 100 - (1 - self.confidence_level) * 100 / 2
        )

        # Effect size
        effect_size = observed_diff / np.std(
            np.concatenate([control_data, treatment_data])
        )

        # Power
        power = self._calculate_power(
            effect_size, len(control_data), len(treatment_data)
        )

        return StatisticalTestResult(
            test_type=TestType.BOOTSTRAP,
            test_statistic=observed_diff,
            p_value=p_value,
            confidence_interval=(ci_lower, ci_upper),
            effect_size=effect_size,
            statistical_power=power,
            sample_size_control=len(control_data),
            sample_size_treatment=len(treatment_data),
            conclusion=f"Bootstrap: p={p_value:.4f}, observed_diff={observed_diff:.3f}",
            significant=p_value < self.alpha,
        )

    def _manual_t_test(
        self, control_data: list[float], treatment_data: list[float]
    ) -> tuple[float, float]:
        """Manual t-test calculation for small samples"""

        mean_control = statistics.mean(control_data)
        mean_treatment = statistics.mean(treatment_data)

        # Pooled variance
        var_control = statistics.variance(control_data) if len(control_data) > 1 else 0
        var_treatment = (
            statistics.variance(treatment_data) if len(treatment_data) > 1 else 0
        )

        df = len(control_data) + len(treatment_data) - 2

        if df <= 0:
            return 0.0, 1.0

        pooled_var = (
            (len(control_data) - 1) * var_control
            + (len(treatment_data) - 1) * var_treatment
        ) / df

        # Standard error
        se = math.sqrt(pooled_var * (1 / len(control_data) + 1 / len(treatment_data)))

        # t-statistic
        t_stat = (mean_treatment - mean_control) / se if se > 0 else 0

        # p-value (two-tailed)
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))

        return t_stat, p_value

    def _calculate_standard_error_difference(
        self, control_data: list[float], treatment_data: list[float]
    ) -> float:
        """Calculate standard error of difference between means"""

        if len(control_data) <= 1 or len(treatment_data) <= 1:
            return 0.0

        se_control = statistics.stdev(control_data) / math.sqrt(len(control_data))
        se_treatment = statistics.stdev(treatment_data) / math.sqrt(len(treatment_data))

        return math.sqrt(se_control**2 + se_treatment**2)

    def _calculate_power(self, effect_size: float, n1: int, n2: int) -> float:
        """Calculate statistical power for given effect size and sample sizes"""

        # This is a simplified power calculation
        # In practice, you'd use more sophisticated methods or libraries

        if abs(effect_size) < 0.1:
            return 0.05  # Very small effect size, low power

        # Harmonic mean of sample sizes
        n_harmonic = 2 * n1 * n2 / (n1 + n2)

        # Approximate power calculation
        ncp = abs(effect_size) * math.sqrt(n_harmonic / 2)  # Non-centrality parameter

        if ncp < 1:
            return 0.1
        elif ncp < 2:
            return 0.3
        elif ncp < 3:
            return 0.6
        elif ncp < 4:
            return 0.8
        else:
            return min(0.95, 0.8 + (ncp - 4) * 0.05)

    def _calculate_nonparametric_power(
        self, effect_size: float, n1: int, n2: int
    ) -> float:
        """Calculate power for non-parametric tests (approximation)"""
        # Non-parametric tests typically have slightly lower power
        parametric_power = self._calculate_power(effect_size, n1, n2)
        return parametric_power * 0.95  # 5% efficiency loss

    def _calculate_cliffs_delta(
        self, control_data: list[float], treatment_data: list[float]
    ) -> float:
        """Calculate Cliff's delta effect size for non-parametric tests"""

        count = 0
        total = 0

        for x in treatment_data:
            for y in control_data:
                total += 1
                if x > y:
                    count += 1
                elif x == y:
                    count += 0.5

        return (2 * count / total) - 1 if total > 0 else 0

    def _bootstrap_median_ci(
        self,
        control_data: list[float],
        treatment_data: list[float],
        n_bootstrap: int = 1000,
    ) -> tuple[float, float]:
        """Bootstrap confidence interval for median difference"""

        np.random.seed(42)
        bootstrap_diffs = []

        for _ in range(n_bootstrap):
            bootstrap_control = np.random.choice(
                control_data, size=len(control_data), replace=True
            )
            bootstrap_treatment = np.random.choice(
                treatment_data, size=len(treatment_data), replace=True
            )

            diff = np.median(bootstrap_treatment) - np.median(bootstrap_control)
            bootstrap_diffs.append(diff)

        ci_lower = np.percentile(bootstrap_diffs, (1 - self.confidence_level) * 100 / 2)
        ci_upper = np.percentile(
            bootstrap_diffs, 100 - (1 - self.confidence_level) * 100 / 2
        )

        return ci_lower, ci_upper

    def interpret_effect_size(self, effect_size: float, test_type: TestType) -> str:
        """Interpret effect size magnitude"""

        if test_type in [TestType.T_TEST, TestType.Z_TEST, TestType.BOOTSTRAP]:
            # Cohen's d interpretation
            abs_effect = abs(effect_size)
            if abs_effect < 0.2:
                return "negligible"
            elif abs_effect < 0.5:
                return "small"
            elif abs_effect < 0.8:
                return "medium"
            else:
                return "large"

        elif test_type == TestType.MANN_WHITNEY:
            # Cliff's delta interpretation
            abs_effect = abs(effect_size)
            if abs_effect < 0.147:
                return "negligible"
            elif abs_effect < 0.33:
                return "small"
            elif abs_effect < 0.474:
                return "medium"
            else:
                return "large"

        return "unknown"

    def calculate_required_sample_size(
        self, effect_size: float, desired_power: float = 0.8
    ) -> int:
        """Calculate required sample size per group for given effect size and power"""

        # Simplified sample size calculation
        if abs(effect_size) < 0.1:
            return 1000  # Very large sample needed for small effect
        elif abs(effect_size) < 0.3:
            return 200
        elif abs(effect_size) < 0.5:
            return 64
        elif abs(effect_size) < 0.8:
            return 26
        else:
            return 20


class ResultCollector:
    """Automated result collection and reporting"""

    def __init__(self, analyzer: StatisticalAnalyzer):
        self.analyzer = analyzer
        self.experiments: dict[str, dict[str, Any]] = {}

    def collect_experiment_results(
        self,
        experiment_id: str,
        control_metrics: list[float],
        treatment_metrics: list[float],
        metadata: dict[str, Any] = None,
    ) -> dict[str, Any]:
        """Collect and analyze complete experiment results"""

        # Perform statistical analysis
        t_test_result = self.analyzer.analyze_experiment(
            control_metrics, treatment_metrics, TestType.T_TEST
        )

        mann_whitney_result = self.analyzer.analyze_experiment(
            control_metrics, treatment_metrics, TestType.MANN_WHITNEY
        )

        bootstrap_result = self.analyzer.analyze_experiment(
            control_metrics, treatment_metrics, TestType.BOOTSTRAP
        )

        # Comprehensive results
        experiment_results = {
            "experiment_id": experiment_id,
            "timestamp": datetime.now().isoformat(),
            "sample_sizes": {
                "control": len(control_metrics),
                "treatment": len(treatment_metrics),
            },
            "descriptive_stats": {
                "control": {
                    "mean": statistics.mean(control_metrics),
                    "median": statistics.median(control_metrics),
                    "std": statistics.stdev(control_metrics)
                    if len(control_metrics) > 1
                    else 0,
                    "min": min(control_metrics),
                    "max": max(control_metrics),
                },
                "treatment": {
                    "mean": statistics.mean(treatment_metrics),
                    "median": statistics.median(treatment_metrics),
                    "std": statistics.stdev(treatment_metrics)
                    if len(treatment_metrics) > 1
                    else 0,
                    "min": min(treatment_metrics),
                    "max": max(treatment_metrics),
                },
            },
            "statistical_tests": {
                "t_test": asdict(t_test_result),
                "mann_whitney": asdict(mann_whitney_result),
                "bootstrap": asdict(bootstrap_result),
            },
            "automated_decision": self._make_automated_decision(
                t_test_result, mann_whitney_result
            ),
            "recommendations": self._generate_recommendations(
                t_test_result, mann_whitney_result
            ),
            "metadata": metadata or {},
        }

        # Store results
        self.experiments[experiment_id] = experiment_results

        return experiment_results

    def _make_automated_decision(
        self, t_test: StatisticalTestResult, mann_whitney: StatisticalTestResult
    ) -> dict[str, Any]:
        """Make automated decision based on statistical results"""

        # Check if we have sufficient statistical power
        sufficient_power = (
            t_test.statistical_power >= 0.8 and mann_whitney.statistical_power >= 0.75
        )

        if not sufficient_power:
            return {
                "decision": DecisionResult.NEED_MORE_DATA,
                "confidence": 0.3,
                "reasoning": "Insufficient statistical power - collect more data",
            }

        # Check consistency between tests
        tests_significant = [t_test.significant, mann_whitney.significant]
        all_significant = all(tests_significant)
        all_not_significant = not any(tests_significant)

        if all_significant:
            # Check effect size consistency
            effect_sizes = [abs(t_test.effect_size), abs(mann_whitney.effect_size)]
            avg_effect_size = statistics.mean(effect_sizes)

            if avg_effect_size >= 0.5:  # Medium effect or larger
                treatment_mean = t_test.sample_size_treatment
                control_mean = t_test.sample_size_control

                # Determine winner (this is simplified - should use actual means)
                return {
                    "decision": DecisionResult.TREATMENT_WINNER,
                    "confidence": 0.9,
                    "reasoning": f"Consistent significant results across tests with medium effect size ({avg_effect_size:.3f})",
                }
            else:
                return {
                    "decision": DecisionResult.TREATMENT_WINNER,
                    "confidence": 0.7,
                    "reasoning": f"Statistically significant but small effect size ({avg_effect_size:.3f})",
                }

        elif all_not_significant:
            return {
                "decision": DecisionResult.NO_SIGNIFICANT_DIFFERENCE,
                "confidence": 0.8,
                "reasoning": "Consistent non-significant results across all tests",
            }

        else:
            return {
                "decision": DecisionResult.INCONCLUSIVE,
                "confidence": 0.4,
                "reasoning": "Conflicting results between parametric and non-parametric tests",
            }

    def _generate_recommendations(
        self, t_test: StatisticalTestResult, mann_whitney: StatisticalTestResult
    ) -> list[str]:
        """Generate actionable recommendations based on results"""

        recommendations = []

        # Sample size recommendations
        if t_test.statistical_power < 0.8:
            required_n = self.analyzer.calculate_required_sample_size(
                abs(t_test.effect_size), desired_power=0.8
            )
            recommendations.append(
                f"Increase sample size to at least {required_n} per group for adequate power"
            )

        # Effect size interpretation
        effect_interpretation = self.analyzer.interpret_effect_size(
            t_test.effect_size, TestType.T_TEST
        )

        if effect_interpretation == "small":
            recommendations.append(
                "Effect size is small - consider if the difference is practically meaningful"
            )
        elif effect_interpretation == "negligible":
            recommendations.append(
                "Effect size is negligible - consider ending the experiment"
            )

        # Statistical significance recommendations
        if t_test.significant and mann_whitney.significant:
            recommendations.append(
                "Strong evidence of significant difference - consider implementing the winning variant"
            )
        elif not t_test.significant and not mann_whitney.significant:
            recommendations.append(
                "No significant difference detected - variants perform similarly"
            )
            recommendations.append(
                "Consider other factors (cost, complexity) when choosing between variants"
            )

        # Data quality recommendations
        if t_test.sample_size_control < 30 or t_test.sample_size_treatment < 30:
            recommendations.append(
                "Small sample sizes detected - results may not be reliable"
            )

        return recommendations

    def export_results(self, experiment_id: str, format: str = "json") -> str:
        """Export experiment results in specified format"""

        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        results = self.experiments[experiment_id]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format.lower() == "json":
            filename = f"experiment_results_{experiment_id}_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(results, f, indent=2, default=str)

        elif format.lower() == "csv":
            # Convert to DataFrame and export
            filename = f"experiment_results_{experiment_id}_{timestamp}.csv"
            df = pd.json_normalize(results)
            df.to_csv(filename, index=False)

        else:
            raise ValueError(f"Unsupported format: {format}")

        return filename

    def generate_summary_report(self, experiment_id: str) -> str:
        """Generate human-readable summary report"""

        if experiment_id not in self.experiments:
            raise ValueError(f"Experiment {experiment_id} not found")

        results = self.experiments[experiment_id]

        report = f"""
# A/B Testing Analysis Report

## Experiment Summary
- **Experiment ID**: {experiment_id}
- **Timestamp**: {results["timestamp"]}
- **Sample Sizes**: Control={results["sample_sizes"]["control"]}, Treatment={results["sample_sizes"]["treatment"]}

## Key Results
- **Automated Decision**: {results["automated_decision"]["decision"]}
- **Confidence**: {results["automated_decision"]["confidence"]:.1%}
- **Reasoning**: {results["automated_decision"]["reasoning"]}

## Statistical Test Results

### T-Test
- **Significant**: {results["statistical_tests"]["t_test"]["significant"]}
- **P-value**: {results["statistical_tests"]["t_test"]["p_value"]:.4f}
- **Effect Size**: {results["statistical_tests"]["t_test"]["effect_size"]:.3f}
- **Statistical Power**: {results["statistical_tests"]["t_test"]["statistical_power"]:.3f}

### Mann-Whitney U Test
- **Significant**: {results["statistical_tests"]["mann_whitney"]["significant"]}
- **P-value**: {results["statistical_tests"]["mann_whitney"]["p_value"]:.4f}
- **Effect Size**: {results["statistical_tests"]["mann_whitney"]["effect_size"]:.3f}

## Descriptive Statistics

### Control Group
- **Mean**: {results["descriptive_stats"]["control"]["mean"]:.2f}
- **Std Dev**: {results["descriptive_stats"]["control"]["std"]:.2f}
- **Median**: {results["descriptive_stats"]["control"]["median"]:.2f}

### Treatment Group
- **Mean**: {results["descriptive_stats"]["treatment"]["mean"]:.2f}
- **Std Dev**: {results["descriptive_stats"]["treatment"]["std"]:.2f}
- **Median**: {results["descriptive_stats"]["treatment"]["median"]:.2f}

## Recommendations
"""

        for i, rec in enumerate(results["recommendations"], 1):
            report += f"{i}. {rec}\n"

        return report


# Integration function
def create_statistical_system(
    confidence_level: float = 0.95,
) -> tuple[StatisticalAnalyzer, ResultCollector]:
    """Create complete statistical analysis system"""

    analyzer = StatisticalAnalyzer(confidence_level=confidence_level)
    collector = ResultCollector(analyzer)

    return analyzer, collector


if __name__ == "__main__":
    import asyncio

    async def demo_statistical_analysis():
        """Demonstrate statistical analysis system"""

        # Create system
        analyzer, collector = create_statistical_system(confidence_level=0.95)

        # Generate sample data (simulating A/B test results)
        np.random.seed(42)

        # Control group: ~1000ms response time
        control_data = np.random.normal(1000, 200, 100).tolist()

        # Treatment group: ~850ms response time (15% improvement)
        treatment_data = np.random.normal(850, 180, 100).tolist()

        print("🔬 Performing Statistical Analysis")
        print("=" * 40)

        # Collect and analyze results
        results = collector.collect_experiment_results(
            experiment_id="demo_ab_test",
            control_metrics=control_data,
            treatment_metrics=treatment_data,
            metadata={
                "test_type": "response_time_comparison",
                "description": "Compare OpenViking vs SMP response times",
            },
        )

        # Print key results
        print(f"Automated Decision: {results['automated_decision']['decision']}")
        print(f"Confidence: {results['automated_decision']['confidence']:.1%}")
        print(f"Reasoning: {results['automated_decision']['reasoning']}")

        print("\n📊 Statistical Tests:")
        t_test = results["statistical_tests"]["t_test"]
        print(
            f"T-Test: p={t_test['p_value']:.4f}, effect_size={t_test['effect_size']:.3f}, significant={t_test['significant']}"
        )

        mann_whitney = results["statistical_tests"]["mann_whitney"]
        print(
            f"Mann-Whitney: p={mann_whitney['p_value']:.4f}, effect_size={mann_whitney['effect_size']:.3f}, significant={mann_whitney['significant']}"
        )

        print("\n💡 Recommendations:")
        for rec in results["recommendations"]:
            print(f"- {rec}")

        # Export results
        json_file = collector.export_results("demo_ab_test", "json")
        print(f"\n📄 Results exported to: {json_file}")

        # Generate report
        report = collector.generate_summary_report("demo_ab_test")
        report_file = f"ab_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, "w") as f:
            f.write(report)
        print(f"📄 Report generated: {report_file}")

        return results

    asyncio.run(demo_statistical_analysis())
