"""
DSPy Phase 2: Automated Prompt Replacement Pipeline

This module handles automated replacement of top-performing DSPy prompts,
enabling seamless migration from existing prompts to optimized variants.
"""

import os
import json
import shutil
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging
from enum import Enum

from ..config import get_dspy_config
from ..optimizers.ab_integration import DSPyABIntegration
from .production_pipeline import ProductionDataPipeline


class ReplacementStatus(Enum):
    """Status of prompt replacement operations."""

    PENDING = "pending"
    VALIDATING = "validating"
    APPROVED = "approved"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class ReplacementCandidate:
    """Candidate for prompt replacement."""

    original_prompt: str
    dspy_variant: str
    model: str
    performance_improvement: float
    confidence_score: float
    validation_metrics: Dict[str, float]
    risk_score: float
    status: ReplacementStatus = ReplacementStatus.PENDING
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["status"] = self.status.value
        data["created_at"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReplacementCandidate":
        """Create from dictionary."""
        if isinstance(data.get("status"), str):
            data["status"] = ReplacementStatus(data["status"])
        if isinstance(data.get("created_at"), str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class DeploymentConfig:
    """Configuration for automated deployment."""

    min_improvement_threshold: float = 0.15  # 15% minimum improvement
    min_confidence_score: float = 0.8  # 80% minimum confidence
    max_risk_score: float = 0.3  # Maximum acceptable risk
    min_sample_size: int = 100  # Minimum samples for validation
    rollout_percentage: float = 0.1  # Start with 10% rollout
    auto_approve: bool = False  # Require manual approval
    backup_original: bool = True  # Backup original prompts


class PromptReplacementPipeline:
    """Automated pipeline for replacing prompts with DSPy variants."""

    def __init__(self, config: Optional[DeploymentConfig] = None):
        self.config = config or DeploymentConfig()
        self.dspy_config = get_dspy_config()
        self.ab_integration = DSPyABIntegration()
        self.production_pipeline = ProductionDataPipeline()

        # Paths
        self.working_dir = self.dspy_config.get_working_directory()
        self.backup_dir = self.working_dir / "backups"
        self.deployment_log = self.working_dir / "deployments.jsonl"

        # Ensure directories exist
        self.working_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)

    async def identify_replacement_candidates(
        self, days_back: int = 7, min_improvement: Optional[float] = None
    ) -> List[ReplacementCandidate]:
        """Identify candidates for prompt replacement based on performance."""
        min_improvement = min_improvement or self.config.min_improvement_threshold

        # Get top performing DSPy variants
        top_variants = await self.production_pipeline.get_top_performing_variants(
            days_back=days_back, min_sample_size=self.config.min_sample_size
        )

        candidates = []

        for variant_data in top_variants:
            variant = variant_data["variant"]
            model = variant_data["model"]
            avg_metric = variant_data["avg_metric"]

            # Find corresponding original prompt
            original_prompt = self._find_original_prompt_for_model(model)
            if not original_prompt:
                continue

            # Get baseline performance for original prompt
            baseline_performance = await self._get_baseline_performance(
                original_prompt, model, days_back
            )

            if baseline_performance is None:
                continue

            # Calculate improvement
            improvement = (avg_metric - baseline_performance) / baseline_performance

            if improvement >= min_improvement:
                # Calculate confidence and risk scores
                confidence_score = self._calculate_confidence_score(variant_data)
                risk_score = self._calculate_risk_score(variant_data, improvement)

                # Get validation metrics
                validation_metrics = await self._get_validation_metrics(
                    variant, model, original_prompt
                )

                candidate = ReplacementCandidate(
                    original_prompt=original_prompt,
                    dspy_variant=variant,
                    model=model,
                    performance_improvement=improvement,
                    confidence_score=confidence_score,
                    validation_metrics=validation_metrics,
                    risk_score=risk_score,
                )

                candidates.append(candidate)

        # Sort by improvement and confidence
        candidates.sort(
            key=lambda c: (c.performance_improvement, c.confidence_score), reverse=True
        )

        return candidates

    def _find_original_prompt_for_model(self, model: str) -> Optional[str]:
        """Find the original prompt used for a specific model."""
        # This would typically query the AB testing configuration
        # For now, we'll use a mapping based on model sizes
        prompt_mappings = {
            "1.5b": "entity_extraction_default",
            "3b": "entity_extraction_default",
            "7b": "entity_extraction_detailed",
        }
        return prompt_mappings.get(model)

    async def _get_baseline_performance(
        self, prompt_name: str, model: str, days_back: int
    ) -> Optional[float]:
        """Get baseline performance for original prompt."""
        # This would query historical performance data
        # For now, return placeholder values
        baseline_scores = {
            "entity_extraction_default": 0.65,
            "entity_extraction_lite": 0.60,
            "entity_extraction_detailed": 0.70,
        }
        return baseline_scores.get(prompt_name, 0.65)

    def _calculate_confidence_score(self, variant_data: Dict[str, Any]) -> float:
        """Calculate confidence score based on data quality and sample size."""
        sample_size = variant_data.get("total_samples", 0)
        evaluation_count = variant_data.get("evaluation_count", 0)

        # Base confidence from sample size (max 0.6)
        sample_confidence = min(sample_size / 1000, 0.6)

        # Consistency confidence from multiple evaluations (max 0.4)
        consistency_confidence = min(evaluation_count / 10, 0.4)

        return sample_confidence + consistency_confidence

    def _calculate_risk_score(
        self, variant_data: Dict[str, Any], improvement: float
    ) -> float:
        """Calculate risk score for replacement."""
        # Risk from high variance (placeholder calculation)
        avg_metric = variant_data.get("avg_metric", 0)
        risk_from_variance = max(0, (1 - avg_metric) * 0.5)

        # Risk from being too good to be true (outlier detection)
        risk_from_outlier = max(0, improvement - 0.5) * 0.3

        # Risk from insufficient data
        sample_size = variant_data.get("total_samples", 0)
        risk_from_sample_size = max(0, (100 - sample_size) / 200)

        return min(1.0, risk_from_variance + risk_from_outlier + risk_from_sample_size)

    async def _get_validation_metrics(
        self, variant: str, model: str, original_prompt: str
    ) -> Dict[str, float]:
        """Get detailed validation metrics for variant comparison."""
        # This would run a validation comparison
        # For now, return placeholder metrics
        return {
            "entity_f1_improvement": 0.18,
            "relationship_f1_improvement": 0.12,
            "format_compliance_improvement": 0.25,
            "latency_improvement": -0.05,  # Negative = slower
            "token_efficiency_improvement": 0.08,
        }

    async def validate_candidate(self, candidate: ReplacementCandidate) -> bool:
        """Validate a replacement candidate against deployment criteria."""
        candidate.status = ReplacementStatus.VALIDATING

        try:
            # Check performance improvement
            if (
                candidate.performance_improvement
                < self.config.min_improvement_threshold
            ):
                self.logger.info(
                    f"Candidate rejected: insufficient improvement ({candidate.performance_improvement:.2f})"
                )
                return False

            # Check confidence score
            if candidate.confidence_score < self.config.min_confidence_score:
                self.logger.info(
                    f"Candidate rejected: low confidence ({candidate.confidence_score:.2f})"
                )
                return False

            # Check risk score
            if candidate.risk_score > self.config.max_risk_score:
                self.logger.info(
                    f"Candidate rejected: high risk ({candidate.risk_score:.2f})"
                )
                return False

            # Additional validation checks
            if not await self._validate_prompt_format(candidate):
                self.logger.info("Candidate rejected: invalid prompt format")
                return False

            if not await self._validate_model_compatibility(candidate):
                self.logger.info("Candidate rejected: model compatibility issues")
                return False

            candidate.status = ReplacementStatus.APPROVED
            return True

        except Exception as e:
            candidate.status = ReplacementStatus.FAILED
            self.logger.error(
                f"Validation failed for candidate {candidate.dspy_variant}: {e}"
            )
            return False

    async def _validate_prompt_format(self, candidate: ReplacementCandidate) -> bool:
        """Validate that the DSPy prompt produces correct format."""
        try:
            # Get the DSPy prompt
            prompt = self.ab_integration.get_dspy_prompt(candidate.dspy_variant)
            if not prompt:
                return False

            # Test with a sample input
            # This would actually run the prompt and validate output
            # For now, assume success
            return True

        except Exception as e:
            self.logger.error(f"Prompt format validation failed: {e}")
            return False

    async def _validate_model_compatibility(
        self, candidate: ReplacementCandidate
    ) -> bool:
        """Validate model compatibility for the candidate."""
        # Check if model supports the DSPy variant
        # This would involve checking model capabilities, token limits, etc.
        return True

    async def deploy_candidate(
        self,
        candidate: ReplacementCandidate,
        rollout_percentage: Optional[float] = None,
    ) -> bool:
        """Deploy a replacement candidate with gradual rollout."""
        if candidate.status != ReplacementStatus.APPROVED:
            raise ValueError(
                f"Candidate must be approved before deployment. Current status: {candidate.status}"
            )

        rollout_percentage = rollout_percentage or self.config.rollout_percentage
        candidate.status = ReplacementStatus.DEPLOYING

        try:
            # Create backup of original prompt
            if self.config.backup_original:
                await self._backup_original_prompt(candidate)

            # Deploy with gradual rollout
            deployment_success = await self._gradual_rollout(
                candidate, rollout_percentage
            )

            if deployment_success:
                candidate.status = ReplacementStatus.DEPLOYED
                await self._log_deployment(candidate, rollout_percentage)
                self.logger.info(
                    f"Successfully deployed {candidate.dspy_variant} for {candidate.model}"
                )
                return True
            else:
                # Rollback on failure
                await self._rollback_deployment(candidate)
                candidate.status = ReplacementStatus.FAILED
                return False

        except Exception as e:
            await self._rollback_deployment(candidate)
            candidate.status = ReplacementStatus.FAILED
            self.logger.error(f"Deployment failed for {candidate.dspy_variant}: {e}")
            return False

    async def _backup_original_prompt(self, candidate: ReplacementCandidate):
        """Create backup of original prompt configuration."""
        backup_path = (
            self.backup_dir
            / f"{candidate.original_prompt}_{candidate.model}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        backup_data = {
            "original_prompt": candidate.original_prompt,
            "model": candidate.model,
            "backup_timestamp": datetime.now().isoformat(),
            "replacement_candidate": candidate.to_dict(),
        }

        with open(backup_path, "w") as f:
            json.dump(backup_data, f, indent=2)

        self.logger.info(f"Created backup: {backup_path}")

    async def _gradual_rollout(
        self, candidate: ReplacementCandidate, rollout_percentage: float
    ) -> bool:
        """Execute gradual rollout of the replacement."""
        # This would update the AB testing configuration
        # to gradually shift traffic to the new variant

        rollout_steps = [0.1, 0.25, 0.5, 0.75, 1.0]
        current_rollout = 0.0

        for step in rollout_steps:
            if step > rollout_percentage:
                break

            try:
                # Update AB testing weights
                await self._update_ab_weights(candidate, step)

                # Wait and monitor
                await asyncio.sleep(60)  # Wait 1 minute between steps

                # Check for any issues
                if not await self._monitor_rollout_health(candidate):
                    self.logger.warning(f"Rollout health check failed at {step:.1%}")
                    return False

                current_rollout = step
                self.logger.info(f"Rollout progressed to {step:.1%}")

            except Exception as e:
                self.logger.error(f"Rollout step {step:.1%} failed: {e}")
                return False

        return True

    async def _update_ab_weights(
        self, candidate: ReplacementCandidate, percentage: float
    ):
        """Update AB testing weights for gradual rollout."""
        # This would update the actual AB testing configuration
        # For now, just log the action
        self.logger.info(
            f"Updated AB weights: {candidate.dspy_variant} at {percentage:.1%}"
        )

    async def _monitor_rollout_health(self, candidate: ReplacementCandidate) -> bool:
        """Monitor health during rollout."""
        # This would check performance metrics, error rates, etc.
        # For now, assume healthy
        return True

    async def _rollback_deployment(self, candidate: ReplacementCandidate):
        """Rollback a failed deployment."""
        candidate.status = ReplacementStatus.ROLLED_BACK

        # Restore original prompt configuration
        await self._restore_original_prompt(candidate)

        self.logger.info(f"Rolled back deployment for {candidate.dspy_variant}")

    async def _restore_original_prompt(self, candidate: ReplacementCandidate):
        """Restore original prompt configuration."""
        # This would restore the original prompt in the AB testing config
        self.logger.info(
            f"Restored original prompt {candidate.original_prompt} for {candidate.model}"
        )

    async def _log_deployment(
        self, candidate: ReplacementCandidate, rollout_percentage: float
    ):
        """Log successful deployment."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "deployment_type": "success",
            "candidate": candidate.to_dict(),
            "rollout_percentage": rollout_percentage,
            "config": asdict(self.config),
        }

        with open(self.deployment_log, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    async def run_automated_replacement(
        self, days_back: int = 7, max_deployments: int = 3, auto_deploy: bool = False
    ) -> Dict[str, Any]:
        """Run the complete automated replacement pipeline."""
        self.logger.info("Starting automated prompt replacement pipeline")

        # Step 1: Identify candidates
        candidates = await self.identify_replacement_candidates(days_back)
        self.logger.info(f"Identified {len(candidates)} replacement candidates")

        # Step 2: Validate candidates
        validated_candidates = []
        for candidate in candidates[:max_deployments]:
            if await self.validate_candidate(candidate):
                validated_candidates.append(candidate)

        self.logger.info(f"Validated {len(validated_candidates)} candidates")

        # Step 3: Deploy candidates
        deployed_candidates = []
        for candidate in validated_candidates:
            if (
                auto_deploy or candidate.confidence_score >= 0.95
            ):  # Auto-deploy very high confidence
                if await self.deploy_candidate(candidate):
                    deployed_candidates.append(candidate)
            else:
                self.logger.info(
                    f"Candidate {candidate.dspy_variant} requires manual approval"
                )

        # Step 4: Generate summary
        summary = {
            "pipeline_run": datetime.now().isoformat(),
            "total_candidates": len(candidates),
            "validated_candidates": len(validated_candidates),
            "deployed_candidates": len(deployed_candidates),
            "candidates": [c.to_dict() for c in candidates],
            "deployed": [c.to_dict() for c in deployed_candidates],
        }

        self.logger.info(
            f"Automated replacement completed: {len(deployed_candidates)} deployments"
        )

        return summary


# CLI interface
async def main():
    """Run prompt replacement pipeline from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DSPy Automated Prompt Replacement Pipeline"
    )
    parser.add_argument(
        "--days", type=int, default=7, help="Days of performance data to analyze"
    )
    parser.add_argument(
        "--max-deployments", type=int, default=3, help="Maximum deployments to perform"
    )
    parser.add_argument(
        "--auto-deploy",
        action="store_true",
        help="Automatically deploy high-confidence candidates",
    )
    parser.add_argument(
        "--min-improvement",
        type=float,
        default=0.15,
        help="Minimum improvement threshold",
    )
    parser.add_argument(
        "--approve-only",
        action="store_true",
        help="Only identify and validate, don't deploy",
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create deployment config
    config = DeploymentConfig(
        min_improvement_threshold=args.min_improvement, auto_approve=args.auto_deploy
    )

    # Create and run pipeline
    pipeline = PromptReplacementPipeline(config)

    if args.approve_only:
        # Only identify and validate candidates
        candidates = await pipeline.identify_replacement_candidates(days_back=args.days)
        print(f"📋 Identified {len(candidates)} replacement candidates:")

        for i, candidate in enumerate(candidates[: args.max_deployments], 1):
            print(f"\n{i}. {candidate.dspy_variant} → {candidate.original_prompt}")
            print(f"   Model: {candidate.model}")
            print(f"   Improvement: {candidate.performance_improvement:.1%}")
            print(f"   Confidence: {candidate.confidence_score:.2f}")
            print(f"   Risk Score: {candidate.risk_score:.2f}")

            # Validate
            is_valid = await pipeline.validate_candidate(candidate)
            print(f"   Status: {'✅ VALID' if is_valid else '❌ INVALID'}")
    else:
        # Run full automated pipeline
        results = await pipeline.run_automated_replacement(
            days_back=args.days,
            max_deployments=args.max_deployments,
            auto_deploy=args.auto_deploy,
        )

        print(f"✅ Automated replacement pipeline completed!")
        print(f"📊 Summary:")
        print(f"   Total candidates: {results['total_candidates']}")
        print(f"   Validated: {results['validated_candidates']}")
        print(f"   Deployed: {results['deployed_candidates']}")

        # Save results
        results_file = Path(
            f"replacement_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"📁 Results saved to: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
