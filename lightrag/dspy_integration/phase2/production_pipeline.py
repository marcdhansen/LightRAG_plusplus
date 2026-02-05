"""
DSPy Phase 2: Production Data Pipeline

This module handles large-scale evaluation of DSPy prompts using production data,
enabling data-driven optimization and automated prompt replacement decisions.
"""

import asyncio
import json
import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from ..config import get_dspy_config
from ..evaluators.prompt_evaluator import DSPyPromptEvaluator
from ..optimizers.ab_integration import DSPyABIntegration


@dataclass
class ProductionExample:
    """Single production example for evaluation."""

    example_id: str
    text: str
    model: str
    timestamp: datetime
    source_prompt: str
    expected_output: str | None = None
    actual_output: str | None = None
    metrics: dict[str, float] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        if isinstance(self.timestamp, datetime):
            data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProductionExample":
        """Create from dictionary."""
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class EvaluationBatch:
    """Batch of production examples for evaluation."""

    batch_id: str
    examples: list[ProductionExample]
    dspy_variants: list[str]
    models: list[str]
    created_at: datetime
    status: str = "pending"  # pending, running, completed, failed

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "batch_id": self.batch_id,
            "examples": [ex.to_dict() for ex in self.examples],
            "dspy_variants": self.dspy_variants,
            "models": self.models,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
        }


class ProductionDataPipeline:
    """Production data pipeline for large-scale DSPy evaluation."""

    def __init__(self, db_path: str | None = None):
        self.config = get_dspy_config()
        self.evaluator = DSPyPromptEvaluator()
        self.ab_integration = DSPyABIntegration()

        # Database setup
        if db_path is None:
            db_path = self.config.get_working_directory() / "production_evaluation.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._init_database()
        self.logger = logging.getLogger(__name__)

    def _init_database(self):
        """Initialize SQLite database for production data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS production_examples (
                    example_id TEXT PRIMARY KEY,
                    text TEXT NOT NULL,
                    model TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    source_prompt TEXT NOT NULL,
                    expected_output TEXT,
                    actual_output TEXT,
                    metrics TEXT,  # JSON blob
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_batches (
                    batch_id TEXT PRIMARY KEY,
                    examples TEXT NOT NULL,  -- JSON array of example IDs
                    dspy_variants TEXT NOT NULL,  -- JSON array
                    models TEXT NOT NULL,  -- JSON array
                    created_at DATETIME NOT NULL,
                    started_at DATETIME,
                    completed_at DATETIME,
                    status TEXT NOT NULL DEFAULT 'pending',
                    results TEXT  -- JSON blob with evaluation results
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS variant_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    variant TEXT NOT NULL,
                    model TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    sample_size INTEGER NOT NULL,
                    evaluated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    batch_id TEXT,
                    FOREIGN KEY (batch_id) REFERENCES evaluation_batches (batch_id)
                )
            """)

            conn.commit()

    async def collect_production_data(
        self,
        hours_back: int = 24,
        models: list[str] | None = None,
        _min_text_length: int = 100,
    ) -> list[ProductionExample]:
        """Collect production data for evaluation.

        This is a placeholder implementation. In practice, this would:
        1. Query production logs/databases
        2. Filter by time window and model
        3. Extract text inputs and outputs
        4. Validate data quality

        For now, we'll generate synthetic production-like data.
        """
        if models is None:
            models = ["1.5b", "3b", "7b"]

        examples = []
        current_time = datetime.now()

        # Generate synthetic production data
        for i in range(100):  # Generate 100 examples
            example_id = f"prod_{current_time.strftime('%Y%m%d_%H%M%S')}_{i:03d}"

            # Generate realistic text content
            text_content = self._generate_production_text()

            # Random timestamp within the window
            timestamp = current_time - timedelta(
                hours=np.random.randint(0, hours_back),
                minutes=np.random.randint(0, 60),
                seconds=np.random.randint(0, 60),
            )

            # Random model and source prompt
            model = np.random.choice(models)
            source_prompt = np.random.choice(
                [
                    "entity_extraction_default",
                    "entity_extraction_lite",
                    "entity_extraction_detailed",
                ]
            )

            example = ProductionExample(
                example_id=example_id,
                text=text_content,
                model=model,
                timestamp=timestamp,
                source_prompt=source_prompt,
            )

            examples.append(example)

        return examples

    def _generate_production_text(self) -> str:
        """Generate realistic production text content."""
        templates = [
            "Apple Inc. is headquartered in Cupertino, California. Tim Cook serves as the CEO and has led the company since 2011.",
            "The partnership between Microsoft and OpenAI was announced in 2019, involving a $1 billion investment from Microsoft.",
            "Tesla's Gigafactory in Nevada produces batteries for electric vehicles and employs over 7,000 workers.",
            "Amazon Web Services launched in 2006 and has since become the dominant cloud computing platform globally.",
            "Google's parent company Alphabet reorganized its structure in 2015 to separate core businesses from experimental projects.",
        ]

        base_text = np.random.choice(templates)

        # Add some variation
        variations = [
            "",
            " This represents a significant milestone in the industry.",
            " The announcement was made during the quarterly earnings call.",
            " Analysts view this development positively.",
        ]

        return base_text + np.random.choice(variations)

    async def create_evaluation_batch(
        self,
        examples: list[ProductionExample],
        dspy_variants: list[str] | None = None,
        batch_size: int = 50,
    ) -> list[EvaluationBatch]:
        """Create evaluation batches from production examples."""
        if dspy_variants is None:
            dspy_variants = ["DSPY_A", "DSPY_B", "DSPY_C", "DSPY_D"]

        # Get unique models from examples
        models = list({ex.model for ex in examples})

        # Split examples into batches
        batches = []
        for i in range(0, len(examples), batch_size):
            batch_examples = examples[i : i + batch_size]
            batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{i // batch_size:03d}"

            batch = EvaluationBatch(
                batch_id=batch_id,
                examples=batch_examples,
                dspy_variants=dspy_variants,
                models=models,
                created_at=datetime.now(),
            )

            batches.append(batch)

        return batches

    async def run_evaluation_batch(
        self, batch: EvaluationBatch, max_workers: int = 4
    ) -> dict[str, Any]:
        """Run evaluation on a batch of production examples."""
        batch.status = "running"
        self._save_batch(batch)

        results = {
            "batch_id": batch.batch_id,
            "started_at": datetime.now().isoformat(),
            "variant_results": {},
            "summary": {},
        }

        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {}

                # Submit evaluation tasks for each variant
                for variant in batch.dspy_variants:
                    for model in batch.models:
                        task_key = f"{variant}_{model}"
                        future = executor.submit(
                            self._evaluate_variant_on_batch,
                            variant,
                            model,
                            batch.examples,
                        )
                        futures[task_key] = future

                # Collect results
                for task_key, future in as_completed(futures.items()):
                    try:
                        variant_results = future.result(timeout=300)  # 5 minute timeout
                        results["variant_results"][task_key] = variant_results

                        # Store individual variant performance
                        self._store_variant_performance(
                            task_key, variant_results, batch.batch_id
                        )

                    except Exception as e:
                        self.logger.error(f"Error evaluating {task_key}: {e}")
                        results["variant_results"][task_key] = {"error": str(e)}

            # Generate summary
            results["summary"] = self._generate_batch_summary(
                results["variant_results"]
            )
            results["completed_at"] = datetime.now().isoformat()

            batch.status = "completed"
            self._save_batch(batch, results)

            return results

        except Exception as e:
            batch.status = "failed"
            self._save_batch(batch, {"error": str(e)})
            raise

    def _evaluate_variant_on_batch(
        self, variant: str, model: str, examples: list[ProductionExample]
    ) -> dict[str, Any]:
        """Evaluate a specific DSPy variant on a batch of examples."""
        results = {
            "variant": variant,
            "model": model,
            "total_examples": len(examples),
            "successful_evaluations": 0,
            "metrics": {
                "entity_f1": [],
                "relationship_f1": [],
                "format_compliance": [],
                "hallucination_rate": [],
                "overall_score": [],
            },
            "latency_stats": {"min": float("inf"), "max": 0, "total": 0},
        }

        # Get DSPy prompt for variant
        prompt = self.ab_integration.get_dspy_prompt(variant)
        if not prompt:
            return {"error": f"Variant {variant} not found"}

        for example in examples:
            try:
                # Evaluate this example
                eval_result = self.evaluator.evaluate_prompt(
                    prompt=prompt,
                    test_text=example.text,
                    model_name=model,
                    expected_output=example.expected_output,
                )

                if eval_result.get("success", False):
                    results["successful_evaluations"] += 1

                    # Collect metrics
                    for metric in results["metrics"]:
                        if metric in eval_result.get("metrics", {}):
                            results["metrics"][metric].append(
                                eval_result["metrics"][metric]
                            )

                    # Track latency
                    latency = eval_result.get("latency_ms", 0)
                    results["latency_stats"]["total"] += latency
                    results["latency_stats"]["min"] = min(
                        results["latency_stats"]["min"], latency
                    )
                    results["latency_stats"]["max"] = max(
                        results["latency_stats"]["max"], latency
                    )

            except Exception as e:
                self.logger.warning(
                    f"Failed to evaluate example {example.example_id}: {e}"
                )
                continue

        # Calculate statistics
        for metric in results["metrics"]:
            values = results["metrics"][metric]
            if values:
                results["metrics"][metric] = {
                    "mean": np.mean(values),
                    "std": np.std(values),
                    "min": np.min(values),
                    "max": np.max(values),
                }
            else:
                results["metrics"][metric] = {"mean": 0, "std": 0, "min": 0, "max": 0}

        if results["successful_evaluations"] > 0:
            results["latency_stats"]["mean"] = (
                results["latency_stats"]["total"] / results["successful_evaluations"]
            )
            results["latency_stats"]["min"] = (
                results["latency_stats"]["min"]
                if results["latency_stats"]["min"] != float("inf")
                else 0
            )

        return results

    def _store_variant_performance(
        self, task_key: str, variant_results: dict[str, Any], batch_id: str
    ):
        """Store variant performance metrics in database."""
        if "error" in variant_results:
            return

        variant, model = task_key.split("_", 1)
        sample_size = variant_results.get("successful_evaluations", 0)

        with sqlite3.connect(self.db_path) as conn:
            for metric_name, stats in variant_results.get("metrics", {}).items():
                if isinstance(stats, dict) and "mean" in stats:
                    conn.execute(
                        """
                        INSERT INTO variant_performance
                        (variant, model, metric_name, metric_value, sample_size, batch_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (
                            variant,
                            model,
                            metric_name,
                            stats["mean"],
                            sample_size,
                            batch_id,
                        ),
                    )
            conn.commit()

    def _generate_batch_summary(
        self, variant_results: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate summary statistics for the batch."""
        summary = {
            "total_variants_evaluated": len(variant_results),
            "successful_evaluations": 0,
            "best_variants": {},
            "performance_comparison": {},
        }

        variant_scores = {}

        for task_key, result in variant_results.items():
            if "error" not in result:
                summary["successful_evaluations"] += 1

                # Calculate overall score for this variant/model combo
                overall_score = (
                    result.get("metrics", {}).get("overall_score", {}).get("mean", 0)
                )
                variant_scores[task_key] = overall_score

        if variant_scores:
            # Find best performing variants
            sorted_variants = sorted(
                variant_scores.items(), key=lambda x: x[1], reverse=True
            )
            summary["best_variants"] = {
                "overall": sorted_variants[0] if sorted_variants else None,
                "top_3": sorted_variants[:3],
            }

            # Group by variant (across models)
            variant_grouped = {}
            for task_key, score in variant_scores.items():
                variant = task_key.split("_")[0]
                if variant not in variant_grouped:
                    variant_grouped[variant] = []
                variant_grouped[variant].append(score)

            summary["performance_comparison"] = {
                variant: {
                    "mean_score": np.mean(scores),
                    "std_score": np.std(scores),
                    "model_count": len(scores),
                }
                for variant, scores in variant_grouped.items()
            }

        return summary

    def _save_batch(
        self, batch: EvaluationBatch, results: dict[str, Any] | None = None
    ):
        """Save batch status and results to database."""
        with sqlite3.connect(self.db_path) as conn:
            # Update batch status
            update_data = {
                "batch_id": batch.batch_id,
                "examples": json.dumps([ex.example_id for ex in batch.examples]),
                "dspy_variants": json.dumps(batch.dspy_variants),
                "models": json.dumps(batch.models),
                "created_at": batch.created_at.isoformat(),
                "status": batch.status,
            }

            if batch.status == "running":
                update_data["started_at"] = datetime.now().isoformat()
            elif batch.status in ["completed", "failed"]:
                update_data["completed_at"] = datetime.now().isoformat()

            conn.execute(
                """
                INSERT OR REPLACE INTO evaluation_batches
                (batch_id, examples, dspy_variants, models, created_at, started_at, completed_at, status, results)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    update_data["batch_id"],
                    update_data["examples"],
                    update_data["dspy_variants"],
                    update_data["models"],
                    update_data["created_at"],
                    update_data.get("started_at"),
                    update_data.get("completed_at"),
                    update_data["status"],
                    json.dumps(results) if results else None,
                ),
            )

            conn.commit()

    async def get_top_performing_variants(
        self,
        metric: str = "overall_score",
        days_back: int = 7,
        min_sample_size: int = 50,
    ) -> list[dict[str, Any]]:
        """Get top performing DSPy variants from recent evaluations."""
        cutoff_date = datetime.now() - timedelta(days=days_back)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT
                    variant,
                    model,
                    AVG(metric_value) as avg_metric,
                    SUM(sample_size) as total_samples,
                    COUNT(*) as evaluation_count
                FROM variant_performance
                WHERE metric_name = ?
                AND evaluated_at >= ?
                AND total_samples >= ?
                GROUP BY variant, model
                ORDER BY avg_metric DESC
                LIMIT 20
            """,
                (metric, cutoff_date.isoformat(), min_sample_size),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "variant": row[0],
                        "model": row[1],
                        "avg_metric": row[2],
                        "total_samples": row[3],
                        "evaluation_count": row[4],
                    }
                )

            return results

    async def run_production_evaluation(
        self,
        hours_back: int = 24,
        models: list[str] | None = None,
        batch_size: int = 50,
        max_workers: int = 4,
    ) -> dict[str, Any]:
        """Run complete production evaluation pipeline."""
        self.logger.info(f"Starting production evaluation for last {hours_back} hours")

        # Step 1: Collect production data
        examples = await self.collect_production_data(hours_back, models)
        self.logger.info(f"Collected {len(examples)} production examples")

        # Step 2: Store examples in database
        await self._store_examples(examples)

        # Step 3: Create evaluation batches
        batches = await self.create_evaluation_batch(examples, batch_size=batch_size)
        self.logger.info(f"Created {len(batches)} evaluation batches")

        # Step 4: Run evaluations
        batch_results = []
        for batch in batches:
            try:
                result = await self.run_evaluation_batch(batch, max_workers)
                batch_results.append(result)
                self.logger.info(f"Completed batch {batch.batch_id}")
            except Exception as e:
                self.logger.error(f"Failed to evaluate batch {batch.batch_id}: {e}")
                batch_results.append({"batch_id": batch.batch_id, "error": str(e)})

        # Step 5: Get top performing variants
        top_variants = await self.get_top_performing_variants()

        summary = {
            "evaluation_id": f"prod_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "data_collection": {
                "hours_back": hours_back,
                "examples_collected": len(examples),
                "models": models or ["all"],
            },
            "batch_processing": {
                "batches_created": len(batches),
                "batches_completed": len(
                    [r for r in batch_results if "error" not in r]
                ),
                "batch_results": batch_results,
            },
            "top_variants": top_variants,
            "completed_at": datetime.now().isoformat(),
        }

        self.logger.info(
            f"Production evaluation completed. Top variant: {top_variants[0] if top_variants else 'None'}"
        )

        return summary

    async def _store_examples(self, examples: list[ProductionExample]):
        """Store production examples in database."""
        with sqlite3.connect(self.db_path) as conn:
            for example in examples:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO production_examples
                    (example_id, text, model, timestamp, source_prompt, expected_output, actual_output, metrics)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        example.example_id,
                        example.text,
                        example.model,
                        example.timestamp.isoformat(),
                        example.source_prompt,
                        example.expected_output,
                        example.actual_output,
                        json.dumps(example.metrics) if example.metrics else None,
                    ),
                )
            conn.commit()


# CLI interface for production evaluation
async def main():
    """Run production evaluation from command line."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Run DSPy Phase 2 Production Evaluation"
    )
    parser.add_argument(
        "--hours", type=int, default=24, help="Hours of production data to evaluate"
    )
    parser.add_argument("--models", nargs="+", default=None, help="Models to evaluate")
    parser.add_argument(
        "--batch-size", type=int, default=50, help="Batch size for evaluation"
    )
    parser.add_argument("--workers", type=int, default=4, help="Maximum worker threads")
    parser.add_argument("--db-path", type=str, default=None, help="Database path")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Create pipeline and run evaluation
    pipeline = ProductionDataPipeline(db_path=args.db_path)
    results = await pipeline.run_production_evaluation(
        hours_back=args.hours,
        models=args.models,
        batch_size=args.batch_size,
        max_workers=args.workers,
    )

    # Save results
    results_path = Path("production_evaluation_results.json")
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)

    print("✅ Production evaluation completed!")
    print(f"📊 Results saved to: {results_path}")
    print(
        f"🏆 Top performing variant: {results['top_variants'][0] if results['top_variants'] else 'None'}"
    )


if __name__ == "__main__":
    asyncio.run(main())
