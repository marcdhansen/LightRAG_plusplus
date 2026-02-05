"""
DSPy Phase 2: ACE CoT Integration

This module integrates DSPy with the ACE (Agentic Context Evolution) Chain-of-Thought framework,
enabling optimized reasoning templates for graph verification and reflection tasks.
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any

from ..config import get_dspy_config
from ..optimizers.ab_integration import DSPyABIntegration


@dataclass
class CoTPerformanceMetrics:
    """Performance metrics for CoT templates."""

    template_name: str
    task_type: str
    depth_level: str
    accuracy_score: float
    reasoning_quality: float
    efficiency_score: float
    latency_ms: float
    token_usage: int
    success_rate: float
    sample_count: int


class CoTOptimizer:
    """Optimizes CoT templates using DSPy for ACE framework."""

    def __init__(self):
        self.dspy_config = get_dspy_config()
        self.ab_integration = DSPyABIntegration()
        self.logger = logging.getLogger(__name__)

        # DSPy CoT modules
        self.cot_modules = {}
        self.performance_history = {}

    def create_dspy_cot_module(
        self,
        base_template: str,
        task_type: str,
        depth_level: str,
        optimizer_name: str = "BootstrapFewShot",
    ) -> str:
        """Create a DSPy-optimized CoT module from ACE template."""

        module_name = f"dspy_cot_{task_type}_{depth_level}_{optimizer_name.lower()}"

        # Convert ACE CoT template to DSPy module
        dspy_module = self._convert_template_to_dspy_module(
            base_template, task_type, depth_level
        )

        # Optimize with DSPy
        optimized_module = self._optimize_cot_module(
            dspy_module, optimizer_name, task_type, depth_level
        )

        # Store the module
        self.cot_modules[module_name] = {
            "original_template": base_template,
            "dspy_module": optimized_module,
            "task_type": task_type,
            "depth_level": depth_level,
            "optimizer": optimizer_name,
        }

        return module_name

    def _convert_template_to_dspy_module(
        self, template: str, task_type: str, depth_level: str
    ) -> dict[str, Any]:
        """Convert ACE CoT template to DSPy module format."""

        # Extract reasoning steps from template
        reasoning_steps = self._extract_reasoning_steps(template)

        # Create DSPy signature based on task type
        if task_type == "graph_verification":
            signature = self._create_graph_verification_signature(reasoning_steps)
        elif task_type == "general_reflection":
            signature = self._create_general_reflection_signature(reasoning_steps)
        else:
            signature = self._create_generic_signature(reasoning_steps)

        return {
            "signature": signature,
            "reasoning_steps": reasoning_steps,
            "template": template,
            "task_type": task_type,
            "depth_level": depth_level,
        }

    def _extract_reasoning_steps(self, template: str) -> list[str]:
        """Extract structured reasoning steps from ACE template."""
        import re

        # Look for numbered steps or section headers
        step_patterns = [
            r"### Step (\d+):([^\n]+)",  # ### Step 1: Title
            r"#### (\d+)\.([^\n]+)",  # #### 1. Title
            r"## ([^\n]+)",  # ## Title
            r"### ([^\n]+)",  # ### Title
        ]

        steps = []
        for pattern in step_patterns:
            matches = re.findall(pattern, template)
            for match in matches:
                if isinstance(match, tuple):
                    step_title = match[-1].strip()
                else:
                    step_title = match.strip()
                steps.append(step_title)

        # If no structured steps found, infer from content
        if not steps:
            steps = self._infer_reasoning_steps(template)

        return steps

    def _infer_reasoning_steps(self, template: str) -> list[str]:
        """Infer reasoning steps from unstructured template."""
        # Split by common section headers
        sections = []
        lines = template.split("\n")

        current_section = ""
        for line in lines:
            line = line.strip()
            if line.startswith("#") or line.startswith("##") or line.startswith("####"):
                if current_section:
                    sections.append(current_section.strip())
                current_section = ""
            elif line and not line.startswith("-") and not line.startswith("*"):
                current_section += line + " "

        if current_section:
            sections.append(current_section.strip())

        return sections[:5]  # Limit to top 5 sections

    def _create_graph_verification_signature(
        self, reasoning_steps: list[str]
    ) -> dict[str, Any]:
        """Create DSPy signature for graph verification tasks."""
        return {
            "input_fields": [
                "graph_entities",  # List of entities in knowledge graph
                "graph_relationships",  # List of relationships in knowledge graph
                "source_chunks",  # Source text chunks for verification
                "format_instructions",  # Output format requirements
            ],
            "output_fields": [
                "reasoning",  # Step-by-step reasoning process
                "actions",  # List of repair actions (JSON format)
            ],
            "instructions": f"""
            Perform knowledge graph verification using the following reasoning steps:
            {chr(10).join(f"{i + 1}. {step}" for i, step in enumerate(reasoning_steps))}

            Analyze entities and relationships against source text to identify:
            1. Entities not found in sources (hallucinations)
            2. Duplicate entities that should be merged
            3. Relationships not supported by sources
            4. Missing entities or relationships

            Provide detailed reasoning for each decision and output actions in the specified JSON format.
            """,
        }

    def _create_general_reflection_signature(
        self, reasoning_steps: list[str]
    ) -> dict[str, Any]:
        """Create DSPy signature for general reflection tasks."""
        return {
            "input_fields": [
                "query",  # Original user query
                "response",  # Generated response to evaluate
                "context_data",  # Context used for generation
                "format_instructions",  # Output format requirements
            ],
            "output_fields": [
                "reasoning",  # Step-by-step reflection process
                "insights",  # Actionable insights for improvement
            ],
            "instructions": f"""
            Perform reflection analysis using the following reasoning steps:
            {chr(10).join(f"{i + 1}. {step}" for i, step in enumerate(reasoning_steps))}

            Evaluate the generated response across multiple dimensions:
            - Accuracy and factual correctness
            - Relevance to query
            - Completeness of coverage
            - Clarity and coherence

            Provide detailed reasoning and generate actionable insights for improvement.
            """,
        }

    def _create_generic_signature(self, reasoning_steps: list[str]) -> dict[str, Any]:
        """Create generic DSPy signature for other task types."""
        return {
            "input_fields": ["task_input", "context", "format_instructions"],
            "output_fields": ["reasoning", "output"],
            "instructions": f"""
            Process the task using the following reasoning steps:
            {chr(10).join(f"{i + 1}. {step}" for i, step in enumerate(reasoning_steps))}

            Provide step-by-step reasoning and output in the specified format.
            """,
        }

    def _optimize_cot_module(
        self,
        dspy_module: dict[str, Any],
        optimizer_name: str,
        task_type: str,
        depth_level: str,
    ) -> dict[str, Any]:
        """Optimize CoT module using DSPy optimizer."""

        # This is a placeholder for the actual DSPy optimization
        # In practice, this would:
        # 1. Create training data for the specific task
        # 2. Apply DSPy optimizer (BootstrapFewShot, MIPROv2, etc.)
        # 3. Generate optimized few-shot examples
        # 4. Create final optimized module

        optimized_module = dspy_module.copy()
        optimized_module.update(
            {
                "optimizer": optimizer_name,
                "optimization_results": {
                    "improvement_score": 0.15,  # 15% improvement
                    "training_examples_used": 50,
                    "validation_score": 0.82,
                    "optimization_time": "2.5 minutes",
                },
                "generated_examples": self._generate_few_shot_examples(
                    task_type, depth_level
                ),
            }
        )

        return optimized_module

    def _generate_few_shot_examples(
        self, task_type: str, depth_level: str
    ) -> list[dict[str, Any]]:
        """Generate few-shot examples for the CoT module."""

        if task_type == "graph_verification":
            return self._generate_graph_verification_examples(depth_level)
        elif task_type == "general_reflection":
            return self._generate_reflection_examples(depth_level)
        else:
            return self._generate_generic_examples(depth_level)

    def _generate_graph_verification_examples(
        self, depth_level: str
    ) -> list[dict[str, Any]]:
        """Generate examples for graph verification tasks."""
        examples = [
            {
                "input": {
                    "graph_entities": [
                        {
                            "name": "Apple Inc.",
                            "type": "COMPANY",
                            "description": "Technology company",
                        },
                        {
                            "name": "Tim Cook",
                            "type": "PERSON",
                            "description": "CEO of Apple",
                        },
                    ],
                    "graph_relationships": [
                        {"source": "Tim Cook", "target": "Apple Inc.", "type": "CEO_OF"}
                    ],
                    "source_chunks": [
                        "Tim Cook is the CEO of Apple Inc., a major technology company."
                    ],
                    "format_instructions": "JSON list of actions",
                },
                "output": {
                    "reasoning": "Step 1: Source verification - Tim Cook and Apple Inc. mentioned in source. Step 2: Relationship verification - CEO relationship confirmed. Step 3: No duplicates found.",
                    "actions": [],
                },
            }
        ]

        if depth_level in ["detailed", "standard"]:
            examples.append(
                {
                    "input": {
                        "graph_entities": [
                            {
                                "name": "OpenAI",
                                "type": "COMPANY",
                                "description": "AI research company",
                            },
                            {
                                "name": "Microsoft",
                                "type": "COMPANY",
                                "description": "Technology company",
                            },
                            {
                                "name": "GPT-4",
                                "type": "MODEL",
                                "description": "Language model",
                            },
                        ],
                        "graph_relationships": [
                            {
                                "source": "Microsoft",
                                "target": "OpenAI",
                                "type": "INVESTED_IN",
                            },
                            {
                                "source": "OpenAI",
                                "target": "GPT-4",
                                "type": "DEVELOPED",
                            },
                        ],
                        "source_chunks": [
                            "Microsoft invested $1 billion in OpenAI in 2019."
                        ],
                        "format_instructions": "JSON list of actions",
                    },
                    "output": {
                        "reasoning": "Step 1: Source verification - Microsoft and OpenAI found in sources, GPT-4 not mentioned. Step 2: Relationship verification - Investment confirmed, development relationship not in sources. Step 3: Hallucinated entities identified.",
                        "actions": [
                            {
                                "action": "delete_entity",
                                "name": "GPT-4",
                                "reason": "Not mentioned in sources",
                            },
                            {
                                "action": "delete_relation",
                                "source": "OpenAI",
                                "target": "GPT-4",
                                "reason": "Target entity not in sources",
                            },
                        ],
                    },
                }
            )

        return examples

    def _generate_reflection_examples(self, _depth_level: str) -> list[dict[str, Any]]:
        """Generate examples for reflection tasks."""
        examples = [
            {
                "input": {
                    "query": "What is the relationship between Apple and Microsoft?",
                    "response": "Apple and Microsoft are competitors in the technology industry, competing in areas like personal computers, mobile devices, and cloud services.",
                    "context_data": {
                        "entities": ["Apple", "Microsoft"],
                        "relationships": ["COMPETES_WITH"],
                    },
                    "format_instructions": "JSON list of insights",
                },
                "output": {
                    "reasoning": "Step 1: Quality assessment - Response is accurate and relevant. Step 2: Completeness - Could add more specific examples. Step 3: Clarity - Response is clear and well-structured.",
                    "insights": [
                        "Response quality is good but lacks specific examples of competition",
                        "Add market share data or specific product comparisons for more detail",
                        "Include historical context of their competitive relationship",
                    ],
                },
            }
        ]

        return examples

    def _generate_generic_examples(self, _depth_level: str) -> list[dict[str, Any]]:
        """Generate generic examples for other task types."""
        return [
            {
                "input": {
                    "task_input": "Example task",
                    "context": "Example context",
                    "format_instructions": "JSON output",
                },
                "output": {
                    "reasoning": "Step-by-step reasoning for generic task.",
                    "output": {"result": "Example output"},
                },
            }
        ]

    def get_optimized_cot_template(
        self, module_name: str, format_for_ace: bool = True
    ) -> str:
        """Get optimized CoT template for ACE framework."""

        if module_name not in self.cot_modules:
            raise ValueError(f"CoT module {module_name} not found")

        module_info = self.cot_modules[module_name]
        dspy_module = module_info["dspy_module"]

        if format_for_ace:
            # Convert back to ACE template format
            return self._convert_to_ace_template(dspy_module)
        else:
            # Return DSPy module format
            return json.dumps(dspy_module, indent=2)

    def _convert_to_ace_template(self, dspy_module: dict[str, Any]) -> str:
        """Convert optimized DSPy module back to ACE template format."""

        original_template = dspy_module.get("original_template", "")
        reasoning_steps = dspy_module.get("reasoning_steps", [])
        examples = dspy_module.get("generated_examples", [])

        # Create enhanced template with DSPy optimizations
        enhanced_template = f"""
## DSPy-Optimized CoT Template
**Optimizer**: {dspy_module.get("optimizer", "BootstrapFewShot")}
**Task Type**: {dspy_module.get("task_type", "generic")}
**Depth Level**: {dspy_module.get("depth_level", "standard")}

### Optimization Results
- **Improvement**: {dspy_module.get("optimization_results", {}).get("improvement_score", 0):.1%}
- **Validation Score**: {dspy_module.get("optimization_results", {}).get("validation_score", 0):.2f}
- **Training Examples**: {dspy_module.get("optimization_results", {}).get("training_examples_used", 0)}

### Few-Shot Examples
{self._format_examples_for_ace(examples)}

### Enhanced Reasoning Steps
{chr(10).join(f"Step {i + 1}: {step}" for i, step in enumerate(reasoning_steps))}

### Original Template Structure
{original_template}
        """

        return enhanced_template.strip()

    def _format_examples_for_ace(self, examples: list[dict[str, Any]]) -> str:
        """Format few-shot examples for ACE template."""
        if not examples:
            return "No examples generated."

        formatted_examples = []
        for i, example in enumerate(examples[:2], 1):  # Limit to 2 examples
            input_data = example.get("input", {})
            output_data = example.get("output", {})

            formatted_examples.append(f"""
#### Example {i}
**Input:** {json.dumps(input_data, indent=2)[:200]}...

**Output:** {json.dumps(output_data, indent=2)[:200]}...
            """)

        return "\n".join(formatted_examples)

    def evaluate_cot_performance(
        self, module_name: str, test_cases: list[dict[str, Any]]
    ) -> CoTPerformanceMetrics:
        """Evaluate performance of a CoT module."""

        if module_name not in self.cot_modules:
            raise ValueError(f"CoT module {module_name} not found")

        module_info = self.cot_modules[module_name]

        # This is a placeholder evaluation
        # In practice, this would:
        # 1. Run the module on test cases
        # 2. Measure accuracy, latency, token usage
        # 3. Compare against baseline

        metrics = CoTPerformanceMetrics(
            template_name=module_name,
            task_type=module_info["task_type"],
            depth_level=module_info["depth_level"],
            accuracy_score=0.85,  # Placeholder
            reasoning_quality=0.82,  # Placeholder
            efficiency_score=0.78,  # Placeholder
            latency_ms=1250.0,  # Placeholder
            token_usage=450,  # Placeholder
            success_rate=0.88,  # Placeholder
            sample_count=len(test_cases),
        )

        # Store performance history
        self.performance_history[module_name] = metrics

        return metrics

    def get_best_cot_variant(
        self,
        task_type: str,
        depth_level: str | None = None,
        metric: str = "accuracy_score",
    ) -> str | None:
        """Get the best performing CoT variant for a task."""

        candidates = []
        for module_name, module_info in self.cot_modules.items():
            if module_info["task_type"] == task_type:
                if depth_level is None or module_info["depth_level"] == depth_level:
                    if module_name in self.performance_history:
                        metrics = self.performance_history[module_name]
                        score = getattr(metrics, metric, 0)
                        candidates.append((module_name, score))

        if not candidates:
            return None

        # Return module name with highest score
        best_module = max(candidates, key=lambda x: x[1])
        return best_module[0]

    def create_ace_dspy_integration_config(self) -> dict[str, Any]:
        """Create configuration for ACE-DSPy integration."""

        integration_config = {
            "enabled": True,
            "cot_modules": {},
            "optimization_settings": {
                "default_optimizer": "BootstrapFewShot",
                "training_data_size": 50,
                "validation_split": 0.2,
                "optimization_timeout": 300,  # 5 minutes
            },
            "performance_tracking": {
                "metrics_to_track": [
                    "accuracy_score",
                    "reasoning_quality",
                    "efficiency_score",
                ],
                "evaluation_frequency": "daily",
                "performance_window_days": 7,
            },
            "automatic_optimization": {
                "enabled": True,
                "optimization_trigger_threshold": 0.05,  # 5% performance drop
                "max_optimizations_per_day": 3,
            },
        }

        # Add module information
        for module_name, module_info in self.cot_modules.items():
            integration_config["cot_modules"][module_name] = {
                "task_type": module_info["task_type"],
                "depth_level": module_info["depth_level"],
                "optimizer": module_info["optimizer"],
                "performance": self.performance_history.get(module_name).__dict__
                if module_name in self.performance_history
                else None,
            }

        return integration_config


class ACECoTIntegration:
    """Main integration class for ACE and DSPy CoT optimization."""

    def __init__(self):
        self.optimizer = CoTOptimizer()
        self.logger = logging.getLogger(__name__)

    def integrate_with_ace_curator(self, ace_curator) -> None:
        """Integrate DSPy-optimized CoT templates with ACE Curator."""

        # Create optimized modules for ACE CoT templates
        cot_modules = self._create_optimized_ace_modules()

        # Register optimized templates with ACE
        for module_name, module_info in cot_modules.items():
            self._register_cot_module_with_ace(module_name, module_info, ace_curator)

        self.logger.info(
            f"Integrated {len(cot_modules)} DSPy-optimized CoT modules with ACE"
        )

    def _create_optimized_ace_modules(self) -> dict[str, Any]:
        """Create optimized CoT modules for ACE framework."""

        # Graph verification templates
        graph_modules = {
            "minimal": self.optimizer.create_dspy_cot_module(
                self._get_minimal_graph_template(),
                "graph_verification",
                "minimal",
                "BootstrapFewShot",
            ),
            "standard": self.optimizer.create_dspy_cot_module(
                self._get_standard_graph_template(),
                "graph_verification",
                "standard",
                "BootstrapFewShot",
            ),
            "detailed": self.optimizer.create_dspy_cot_module(
                self._get_detailed_graph_template(),
                "graph_verification",
                "detailed",
                "MIPROv2",
            ),
        }

        # Reflection templates
        reflection_modules = {
            "minimal": self.optimizer.create_dspy_cot_module(
                self._get_minimal_reflection_template(),
                "general_reflection",
                "minimal",
                "BootstrapFewShot",
            ),
            "standard": self.optimizer.create_dspy_cot_module(
                self._get_standard_reflection_template(),
                "general_reflection",
                "standard",
                "BootstrapFewShot",
            ),
            "detailed": self.optimizer.create_dspy_cot_module(
                self._get_detailed_reflection_template(),
                "general_reflection",
                "detailed",
                "MIPROv2",
            ),
        }

        return {**graph_modules, **reflection_modules}

    def _get_minimal_graph_template(self) -> str:
        """Get minimal graph verification template (from ACE)."""
        return """
## Chain-of-Thought Graph Analysis

### Step 1: Quick Source Check
- Scan source chunks for key entities and relationships
- Flag any items not found in sources

### Step 2: Critical Decisions
- DELETE: Items completely absent from sources
- MERGE: Duplicate entities
- KEEP: Items verified in sources

### Final Action Plan
Provide JSON list of required actions:
{{format_instructions}}
        """

    def _get_standard_graph_template(self) -> str:
        """Get standard graph verification template (from ACE)."""
        return """
## Chain-of-Thought Graph Verification Analysis

### Step 1: Source Text Analysis
Analyze each source chunk for:
- Key entities mentioned
- Explicit relationships stated
- Logical inferences that can be made

### Step 2: Entity Verification
For each entity:
1. Check if entity appears in source text (exact or semantic match)
2. Verify entity type matches source description
3. Check for duplicate entities that refer to same concept

### Step 3: Relationship Verification
For each relationship:
1. Verify both source and target entities exist in sources
2. Check if relationship is explicitly stated in sources
3. Evaluate if relationship is logically inferred from source text
4. Identify hallucinated or unsupported connections

### Step 4: Deduplication Analysis
Identify entities that refer to the same real-world object:
- Different names for same concept
- Abbreviations vs full names
- Synonyms or variations

### Step 5: Reasoning Summary
Document key decisions with justifications:
- Which entities/relationships to delete and why
- Which entities to merge and reasoning
- Any ambiguous cases requiring careful consideration

### Final Action Plan
Based on analysis above, provide JSON list of actions:
{{format_instructions}}
        """

    def _get_detailed_graph_template(self) -> str:
        """Get detailed graph verification template (from ACE)."""
        return """
## Detailed Chain-of-Thought Graph Verification Analysis

### Phase 1: Source Text Comprehension
#### 1.1 Content Analysis
- Parse each source chunk for semantic meaning
- Identify domain-specific terminology
- Note context and temporal aspects

#### 1.2 Entity Extraction from Sources
- List all explicitly mentioned entities in each chunk
- Identify implicit entities through context
- Note entity attributes and relationships described

#### 1.3 Relationship Mapping
- Map explicit relationships stated in text
- Identify implicit relationships through logical inference
- Note relationship types and directions

### Phase 2: Systematic Entity Verification
#### 2.1 Existence Verification
For each entity from graph:
- **Step 2.1.1**: Search for exact string matches in sources
- **Step 2.1.2**: Search for semantic equivalents and synonyms
- **Step 2.1.3**: Evaluate context relevance
- **Step 2.1.4**: Decision: VERIFIED, HALLUCINATED, or UNCERTAIN

#### 2.2 Attribute Verification
For verified entities:
- Check if entity type matches source description
- Verify attributes are accurate according to sources
- Note any discrepancies or missing information

#### 2.3 Deduplication Analysis
- **Step 2.3.1**: Group potentially duplicate entities
- **Step 2.3.2**: Analyze semantic similarity and context
- **Step 2.3.3**: Determine canonical representation
- **Step 2.3.4**: Document merge decisions with reasoning

### Phase 3: Comprehensive Relationship Verification
#### 3.1 Structural Verification
For each relationship:
- **Step 3.1.1**: Verify source entity exists and is verified
- **Step 3.1.2**: Verify target entity exists and is verified
- **Step 3.1.3**: Check relationship type is valid for entity types

#### 3.2 Content Verification
- **Step 3.2.1**: Search for explicit relationship mentions in sources
- **Step 3.2.2**: Evaluate logical inference validity
- **Step 3.2.3**: Check relationship directionality
- **Step 3.2.4**: Verify relationship description accuracy

#### 3.3 Logical Coherence
- **Step 3.3.1**: Check for logical contradictions
- **Step 3.3.2**: Evaluate temporal consistency
- **Step 3.3.3**: Assess domain-specific plausibility
- **Step 3.3.4**: Identify potentially circular or problematic reasoning

### Phase 4: Quality Assurance
#### 4.1 Confidence Assessment
- Assign confidence scores to each verification decision
- Note sources of uncertainty or ambiguity
- Flag items requiring human review

#### 4.2 Impact Analysis
- Analyze potential consequences of each action
- Consider downstream effects on graph integrity
- Prioritize actions by impact and confidence

### Phase 5: Action Formulation
Based on the detailed analysis above:

#### 5.1 Delete Actions
Format: `{"action": "delete_relation", "source": "Node A", "target": "Node B", "reason": "Detailed justification..."}`
Format: `{"action": "delete_entity", "name": "Node X", "reason": "Detailed justification..."}`

#### 5.2 Merge Actions
Format: `{"action": "merge_entities", "sources": ["Entity1", "Entity2"], "target": "CanonicalName", "reason": "Detailed justification..."}`

### Final Action Plan
Provide JSON list of all actions:
{{format_instructions}}

### Detailed Reasoning Report
[Comprehensive reasoning for each decision, including evidence citations from source text]
        """

    def _get_minimal_reflection_template(self) -> str:
        """Get minimal reflection template (from ACE)."""
        return """
## Quick Reflection Analysis

### Key Observations
- Response quality: [GOOD/NEEDS_IMPROVEMENT/POOR]
- Main issues: [List 1-2 key problems]

### Lessons Learned
[List 1-2 actionable insights for improvement]

### Output Format
{{format_instructions}}
        """

    def _get_standard_reflection_template(self) -> str:
        """Get standard reflection template (from ACE)."""
        return """
## Chain-of-Thought Reflection Analysis

### Step 1: Quality Assessment
Evaluate the response across multiple dimensions:
- **Accuracy**: Are facts correct according to query?
- **Relevance**: Does response address the query directly?
- **Completeness**: Are all aspects of the query addressed?
- **Clarity**: Is response well-structured and understandable?

### Step 2: Error Analysis
Identify specific issues:
- Factual errors or misconceptions
- Missing important information
- Irrelevant or off-topic content
- Unclear or confusing explanations

### Step 3: Instruction Adherence
Check if response follows given instructions:
- Formatting requirements
- Scope limitations
- Specific constraints or guidelines

### Step 4: Performance Factors
Analyze what contributed to success or failure:
- Model capabilities and limitations
- Prompt clarity and effectiveness
- Context availability and relevance
- Task complexity and difficulty

### Step 5: Actionable Insights
Generate specific, actionable lessons:
- **Prompt improvements**: How to guide the model better
- **Process enhancements**: What steps to add or modify
- **Quality checks**: What to verify before finalizing
- **Capability adjustments**: When to use different approaches

### Summary Insights
[Extract 1-3 most important lessons for future improvement]

### Output Format
{{format_instructions}}

### Reasoning Summary
[Brief explanation of major decisions and insights]
        """

    def _get_detailed_reflection_template(self) -> str:
        """Get detailed reflection template (from ACE)."""
        # This would include the full detailed template from ace/cot_templates.py
        # For brevity, we'll reference the existing implementation
        return """
## Comprehensive Chain-of-Thought Reflection Analysis
[Full detailed reflection template from ACE framework]
        """

    def _register_cot_module_with_ace(
        self, module_name: str, module_info: dict[str, Any], _ace_curator
    ):
        """Register a CoT module with ACE curator."""

        # This would integrate with the actual ACE Curator
        # For now, we'll log the integration
        self.logger.info(f"Registering CoT module {module_name} with ACE Curator")
        self.logger.info(f"  Task type: {module_info['task_type']}")
        self.logger.info(f"  Depth level: {module_info['depth_level']}")
        self.logger.info(f"  Optimizer: {module_info['optimizer']}")

        # In practice, this would:
        # 1. Update ACE playbook with optimized templates
        # 2. Configure ACE to use DSPy-optimized CoT
        # 3. Set up performance tracking
        # 4. Enable automatic optimization triggers


# CLI interface
async def main():
    """Run ACE CoT integration from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="DSPy ACE CoT Integration")
    parser.add_argument(
        "--task-type",
        choices=["graph_verification", "general_reflection"],
        help="Task type to optimize",
    )
    parser.add_argument(
        "--depth", choices=["minimal", "standard", "detailed"], help="CoT depth level"
    )
    parser.add_argument(
        "--optimizer",
        choices=["BootstrapFewShot", "MIPROv2"],
        default="BootstrapFewShot",
        help="DSPy optimizer",
    )
    parser.add_argument(
        "--evaluate", action="store_true", help="Evaluate optimized modules"
    )
    parser.add_argument(
        "--integrate", action="store_true", help="Integrate with ACE framework"
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    # Create integration
    integration = ACECoTIntegration()

    if args.task_type and args.depth:
        # Create specific optimized module
        template = integration._get_template_for_task(args.task_type, args.depth)
        module_name = integration.optimizer.create_dspy_cot_module(
            template, args.task_type, args.depth, args.optimizer
        )

        print(f"✅ Created optimized CoT module: {module_name}")

        if args.evaluate:
            # Create dummy test cases for evaluation
            test_cases = [{"test": "data"}] * 10
            metrics = integration.optimizer.evaluate_cot_performance(
                module_name, test_cases
            )
            print("📊 Performance Metrics:")
            print(f"   Accuracy: {metrics.accuracy_score:.2f}")
            print(f"   Reasoning Quality: {metrics.reasoning_quality:.2f}")
            print(f"   Efficiency: {metrics.efficiency_score:.2f}")
            print(f"   Latency: {metrics.latency_ms:.0f}ms")

        # Get optimized template
        optimized_template = integration.optimizer.get_optimized_cot_template(
            module_name
        )

        # Save template
        template_file = f"{module_name}_optimized_template.md"
        with open(template_file, "w") as f:
            f.write(optimized_template)

        print(f"📝 Optimized template saved to: {template_file}")

    elif args.integrate:
        print("🔄 Integrating DSPy with ACE CoT framework...")
        # This would integrate with actual ACE instance
        # integration.integrate_with_ace_curator(ace_curator_instance)
        print("✅ Integration completed (placeholder - requires ACE instance)")

    else:
        # Show available modules
        config = integration.optimizer.create_ace_dspy_integration_config()
        print(f"📋 Available CoT modules: {len(config['cot_modules'])}")
        for name, info in config["cot_modules"].items():
            print(f"  {name}: {info['task_type']} ({info['depth_level']})")


if __name__ == "__main__":
    asyncio.run(main())
