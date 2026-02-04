"""
Chain-of-Thought (CoT) Template System for ACE Reflector
Provides configurable reasoning templates for different CoT depths and use cases.
"""

from enum import Enum
from typing import Dict, List, Any
from ..ace.config import ACEConfig


class CoTDepth(Enum):
    """CoT reasoning depth levels."""

    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"


class CoTTemplates:
    """
    Chain-of-Thought template system for ACE Reflector.
    Provides structured reasoning templates for different analysis types.
    """

    def __init__(self, config: ACEConfig):
        self.config = config
        if config:
            self.depth = CoTDepth(config.cot_depth)
        else:
            self.depth = CoTDepth.STANDARD

    def get_graph_verification_template(self) -> str:
        """
        Returns CoT template for graph verification based on configured depth.
        """
        templates = {
            CoTDepth.MINIMAL: self._get_minimal_graph_template(),
            CoTDepth.STANDARD: self._get_standard_graph_template(),
            CoTDepth.DETAILED: self._get_detailed_graph_template(),
        }
        return templates[self.depth]

    def get_general_reflection_template(self) -> str:
        """
        Returns CoT template for general reflection based on configured depth.
        """
        templates = {
            CoTDepth.MINIMAL: self._get_minimal_reflection_template(),
            CoTDepth.STANDARD: self._get_standard_reflection_template(),
            CoTDepth.DETAILED: self._get_detailed_reflection_template(),
        }
        return templates[self.depth]

    def _get_minimal_graph_template(self) -> str:
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
- Different names for same concept (e.g., "AI" vs "Artificial Intelligence")
- Abbreviations vs full names
- Synonyms or variations

### Step 5: Reasoning Summary
Document key decisions with justifications:
- Which entities/relationships to delete and why
- Which entities to merge and reasoning
- Any ambiguous cases requiring careful consideration

### Final Action Plan
Based on the analysis above, provide JSON list of actions:
{{format_instructions}}

## Reasoning Output
[Provide brief reasoning for each major decision]
"""

    def _get_detailed_graph_template(self) -> str:
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
        return """
## Chain-of-Thought Reflection Analysis

### Step 1: Quality Assessment
Evaluate the response across multiple dimensions:
- **Accuracy**: Are facts correct according to query?
- **Relevance**: Does response address the query directly?
- **Completeness**: Are all aspects of the query addressed?
- **Clarity**: Is the response well-structured and understandable?

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
        return """
## Comprehensive Chain-of-Thought Reflection Analysis

### Phase 1: Multi-Dimensional Quality Assessment
#### 1.1 Factual Accuracy Analysis
- **Fact Verification**: Check all factual claims against query context
- **Source Attribution**: Verify information sources and reliability
- **Temporal Consistency**: Ensure time-sensitive information is current
- **Domain Accuracy**: Assess domain-specific correctness

#### 1.2 Response Quality Dimensions
- **Relevance Score**: How well response matches query intent (1-10)
- **Completeness Score**: How thoroughly query aspects are covered (1-10)
- **Clarity Score**: How understandable and well-structured response is (1-10)
- **Coherence Score**: How logically consistent response flows (1-10)

### Phase 2: Detailed Error Taxonomy
#### 2.1 Content Errors
- **Factual Inaccuracies**: Specific incorrect statements
- **Omission Errors**: Important information missing
- **Commission Errors**: Irrelevant or incorrect additions
- **Misinterpretation Errors**: Understanding query incorrectly

#### 2.2 Structural Issues
- **Organization Problems**: Poor flow or structure
- **Clarity Issues**: Confusing or unclear explanations
- **Completeness Gaps**: Incomplete coverage of query
- **Relevance Problems**: Off-topic or tangential content

#### 2.3 Process Issues
- **Instruction Violations**: Not following given constraints
- **Format Problems**: Incorrect output formatting
- **Scope Issues**: Going beyond or falling short of requirements
- **Style Inconsistencies**: Inappropriate tone or style

### Phase 3: Root Cause Analysis
#### 3.1 Prompt-Related Factors
- Prompt clarity and specificity
- Instruction completeness and accuracy
- Example relevance and quality
- Constraint appropriateness

#### 3.2 Model-Related Factors
- Model capability for task type
- Knowledge domain expertise
- Reasoning and inference abilities
- Language generation quality

#### 3.3 Context-Related Factors
- Information availability and relevance
- Context sufficiency for query
- Source quality and reliability
- Temporal and contextual appropriateness

#### 3.4 Task-Related Factors
- Task complexity and difficulty
- Domain-specific challenges
- Ambiguity levels and interpretations
- Required reasoning depth

### Phase 4: Strategic Improvement Planning
#### 4.1 Immediate Process Improvements
- **Enhanced Prompting**: Specific prompt improvements identified
- **Quality Checks**: Additional verification steps to implement
- **Context Optimization**: Better context selection and preparation
- **Process Refinements**: Workflow improvements for this task type

#### 4.2 Capability Development
- **Skill Gaps**: Areas needing model capability improvement
- **Knowledge Enhancement**: Domain knowledge to develop
- **Tool Integration**: Additional tools or resources needed
- **Training Opportunities**: Specific areas for model fine-tuning

#### 4.3 Systemic Enhancements
- **Template Improvements**: Response template refinements
- **Validation Systems**: Enhanced validation mechanisms
- **Feedback Loops**: Better learning and adaptation systems
- **Quality Assurance**: Comprehensive QA processes

### Phase 5: Actionable Insight Formulation
#### 5.1 Tactical Insights (Immediate Actions)
- Specific, immediately applicable improvements
- Process changes for next similar interaction
- Quality checks to implement immediately
- Prompt adjustments for next use

#### 5.2 Strategic Insights (Long-term Improvements)
- Capability development priorities
- System-level enhancements needed
- Process optimization opportunities
- Quality framework improvements

#### 5.3 Generalization Principles
- Transferable lessons to other similar tasks
- General principles for better performance
- Cross-domain applicable insights
- Scalable improvement strategies

### Phase 6: Learning Synthesis
#### 6.1 Success Factor Identification
- What contributed most to positive outcomes
- Which factors should be replicated
- Best practices identified from this interaction
- Strengths to leverage in future

#### 6.2 Failure Factor Analysis  
- What contributed most to negative outcomes
- Which factors to avoid or mitigate
- Warning signs to watch for
- Weaknesses to address systematically

#### 6.3 Performance Optimization Framework
- **Prevention**: How to prevent identified issues
- **Detection**: How to catch issues early
- **Correction**: How to fix issues when found
- **Learning**: How to improve from each instance

### Final Insights Summary
[Extract 1-3 most impactful, actionable insights for immediate improvement, with clear implementation guidance]

### Output Format
{{format_instructions}}

### Detailed Reasoning Report
[Comprehensive analysis with evidence citations and decision rationale]
"""

    def get_reasoning_output_parser(self) -> str:
        """
        Returns instructions for extracting reasoning output from LLM responses.
        """
        if not self.config or not self.config.cot_include_reasoning_output:
            return ""

        return """

## Reasoning Output Extraction

If you provide detailed reasoning in your response, format it as follows:

```reasoning
[Your step-by-step reasoning process here]
```

The reasoning section should:
1. Document your analysis process step by step
2. Explain key decisions and their justifications  
3. Provide evidence for your conclusions
4. Note any uncertainties or ambiguities
5. Be structured and easy to follow

The JSON action list should come after the reasoning section.
"""
