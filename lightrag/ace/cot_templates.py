"""
Chain-of-Thought (CoT) Template System for ACE Reflector
Provides configurable reasoning templates for different CoT depths and use cases.
"""

from enum import Enum

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
## Chain-of-Thought Graph Analysis (Enhanced for Small Models)

### Step 1: Quick Source Check
- Scan source chunks for key entities and relationships
- Flag any items not found in sources
- **HALLUCINATION ALERT**: Check for entities that seem too abstract/complex for 1.5B models

### Step 2: Critical Decisions
- DELETE: Items completely absent from sources
- MERGE: Duplicate entities
- KEEP: Items verified in sources
- **SPECIAL FOCUS**: Abstract concepts often hallucinated by small models

### Final Action Plan
Provide JSON list of required actions:
{{format_instructions}}
"""

    def _get_standard_graph_template(self) -> str:
        return """
## Chain-of-Thought Graph Verification Analysis (Enhanced for Small Models)

### Step 1: Source Text Analysis
Analyze each source chunk for:
- Key entities mentioned
- Explicit relationships stated
- Logical inferences that can be made
- **SMALL MODEL WARNING**: Note complex/abstract concepts that 1.5B models often hallucinate

### Step 2: Entity Verification with Hallucination Detection
For each entity:
1. **EVIDENCE**: Find exact text support in sources
2. **ANALYSIS**:
   - Does entity appear in source text (exact or semantic match)?
   - Is entity type appropriate for source description?
   - **HALLUCINATION RISK**: Is this an abstract concept small models struggle with?
3. **CONCLUSION**: VERIFIED, HALLUCINATED, or UNCERTAIN
4. **SPECIAL CHECK**: Concepts like "intelligence", "consciousness", "complexity" often hallucinated

### Step 3: Relationship Verification with Structured Reasoning
For each relationship:
1. **EVIDENCE**: Locate supporting text in sources
2. **ANALYSIS**:
   - Do both source and target entities exist in sources?
   - Is relationship explicitly stated or logically inferred?
   - **HALLUCINATION RISK**: Is this connection too complex for small models?
3. **CONCLUSION**: SUPPORTED, HALLUCINATED, or UNCERTAIN
4. **PATTERN CHECK**: Small models often create false relationships between abstract concepts

### Step 4: Deduplication Analysis
Identify entities that refer to the same real-world object:
- Different names for same concept (e.g., "AI" vs "Artificial Intelligence")
- Abbreviations vs full names
- Synonyms or variations
- **SMALL MODEL ISSUE**: Watch for over-merging of distinct but related concepts

### Step 5: Hallucination Detection Summary
**Common 1.5B Model Hallucination Patterns:**
- Abstract concepts without concrete anchors
- Relationships between philosophical ideas
- Overly complex entity descriptions
- Entities that sound plausible but lack source support

### Step 6: Reasoning Summary
Document key decisions with evidence-based justifications:
- Which entities/relationships to delete and why
- Which entities to merge and reasoning
- Hallucination detections with specific evidence
- Any ambiguous cases requiring careful consideration

### Final Action Plan
Based on the evidence-based analysis above, provide JSON list of actions:
{{format_instructions}}

## Reasoning Output
[Provide structured reasoning: EVIDENCE → ANALYSIS → CONCLUSION for major decisions]
"""

    def _get_detailed_graph_template(self) -> str:
        return """
## Detailed Chain-of-Thought Graph Verification Analysis (Enhanced for Small Model Hallucination Detection)

### Phase 1: Source Text Comprehension & Model Capability Assessment
#### 1.1 Content Analysis
- Parse each source chunk for semantic meaning
- Identify domain-specific terminology
- Note context and temporal aspects
- **MODEL CAPABILITY ASSESSMENT**: Identify concepts that exceed 1.5B model reasoning capacity

#### 1.2 Entity Extraction from Sources
- List all explicitly mentioned entities in each chunk
- Identify implicit entities through context
- Note entity attributes and relationships described
- **COMPLEXITY RATING**: Rate each entity by extraction difficulty (1-5 scale for small models)

#### 1.3 Relationship Mapping
- Map explicit relationships stated in text
- Identify implicit relationships through logical inference
- Note relationship types and directions
- **INFERENCE RISK**: Flag relationships requiring complex reasoning beyond small model capacity

### Phase 2: Systematic Entity Verification with Enhanced Hallucination Detection
#### 2.1 Existence Verification (Evidence-Based)
For each entity from graph:
- **Step 2.1.1**: EVIDENCE - Search for exact string matches in sources
- **Step 2.1.2**: EVIDENCE - Search for semantic equivalents and synonyms
- **Step 2.1.3**: ANALYSIS - Evaluate context relevance and model capability
- **Step 2.1.4**: ANALYSIS - **HALLUCINATION RISK ASSESSMENT**:
  - Is this an abstract concept requiring sophisticated understanding?
  - Does this entity appear in similar contexts across training data?
  - Would a 1.5B model have the reasoning capacity to extract this accurately?
- **Step 2.1.5**: CONCLUSION - Decision: VERIFIED, HALLUCINATED, or UNCERTAIN with confidence score

#### 2.2 Attribute Verification with Model Limitation Awareness
For verified entities:
- **EVIDENCE**: Check if entity type matches source description
- **ANALYSIS**: Verify attributes are accurate according to sources
- **MODEL CONSTRAINT**: Consider if 1.5B model could accurately distinguish these attributes
- **CONCLUSION**: Note any discrepancies or missing information

#### 2.3 Deduplication Analysis with Small Model Considerations
- **Step 2.3.1**: EVIDENCE - Group potentially duplicate entities
- **Step 2.3.2**: ANALYSIS - Analyze semantic similarity and context
- **Step 2.3.3**: ANALYSIS - **SMALL MODEL PATTERN RECOGNITION**:
  - Small models often over-merge distinct but related concepts
  - Small models under-merge due to limited semantic understanding
  - Check for false positives in similarity detection
- **Step 2.3.4**: CONCLUSION - Determine canonical representation
- **Step 2.3.5**: CONCLUSION - Document merge decisions with model-aware reasoning

### Phase 3: Comprehensive Relationship Verification with Hallucination Pattern Recognition
#### 3.1 Structural Verification
For each relationship:
- **EVIDENCE**: Verify source entity exists and is verified
- **EVIDENCE**: Verify target entity exists and is verified
- **ANALYSIS**: Check relationship type is valid for entity types
- **MODEL CAPABILITY**: Assess if 1.5B model can understand this relationship type

#### 3.2 Content Verification with Sophisticated Hallucination Detection
- **Step 3.2.1**: EVIDENCE - Search for explicit relationship mentions in sources
- **Step 3.2.2**: ANALYSIS - Evaluate logical inference validity
- **Step 3.2.3**: ANALYSIS - **HALLUCINATION PATTERN DETECTION**:
  - **Abstract Concept Connections**: Small models often create false relationships between philosophical ideas
  - **Over-Specific Relationships**: Relationships that are too precise for limited context
  - **Causal Inference Errors**: Small models struggle with complex causal reasoning
  - **Temporal Relationship Errors**: Small models confuse temporal sequences
- **Step 3.2.4**: ANALYSIS - Check relationship directionality
- **Step 3.2.5**: CONCLUSION - Verify relationship description accuracy with model-aware confidence

#### 3.3 Logical Coherence with Small Model Error Pattern Recognition
- **Step 3.3.1**: EVIDENCE - Check for logical contradictions
- **Step 3.3.2**: ANALYSIS - Evaluate temporal consistency
- **Step 3.3.3**: ANALYSIS - Assess domain-specific plausibility
- **Step 3.3.4**: ANALYSIS - **SMALL MODEL ERROR PATTERN RECOGNITION**:
  - **False Equivalence**: Equating concepts that seem similar but are distinct
  - **Over-Generalization**: Making broad claims from limited evidence
  - **Concrete-Abstract Confusion**: Mixing concrete entities with abstract concepts inappropriately
  - **Circular Reasoning**: Creating self-referential relationships
- **Step 3.3.5**: CONCLUSION - Identify potentially circular or problematic reasoning

### Phase 4: Quality Assurance with Model-Specific Thresholds
#### 4.1 Confidence Assessment with Model Capability Adjustment
- **EVIDENCE**: Assign confidence scores to each verification decision
- **ANALYSIS**: Note sources of uncertainty or ambiguity
- **MODEL ADJUSTMENT**: Apply stricter confidence thresholds for 1.5B model outputs
- **CONCLUSION**: Flag items requiring human review or higher-capacity model verification

#### 4.2 Impact Analysis with Downstream Effect Modeling
- **EVIDENCE**: Analyze potential consequences of each action
- **ANALYSIS**: Consider downstream effects on graph integrity
- **MODEL IMPACT**: Assess how small model errors propagate through the graph
- **CONCLUSION**: Prioritize actions by impact, confidence, and model capability requirements

### Phase 5: Hallucination Detection Framework for Small Models
#### 5.1 Common 1.5B Model Hallucination Patterns
- **Abstract Concept Generation**: Creating philosophical/abstract entities without concrete anchors
- **Complex Relationship Fabrication**: Inventing sophisticated relationships between ideas
- **Over-Specific Attribute Assignment**: Adding detailed attributes beyond source text
- **False Category Creation**: Inventing entity types that sound plausible but don't exist
- **Cross-Domain Confusion**: Mixing concepts from different domains incorrectly

#### 5.2 Evidence-Based Hallucination Detection Heuristics
- **Concrete Anchor Test**: Does the entity have concrete text evidence?
- **Complexity Threshold**: Is this concept too complex for 1.5B model capacity?
- **Source Proximity**: Is the entity/relationship close to actual source content?
- **Plausibility Check**: Does this seem like something a 1.5B model would hallucinate?
- **Pattern Recognition**: Does this match known small model hallucination patterns?

### Phase 6: Action Formulation with Model-Aware Reasoning
Based on the detailed evidence-based analysis above:

#### 6.1 Delete Actions with Enhanced Reasoning
Format: `{"action": "delete_relation", "source": "Node A", "target": "Node B", "reason": "HALLUCINATED: [Evidence → Analysis → Conclusion]"}`
Format: `{"action": "delete_entity", "name": "Node X", "reason": "HALLUCINATED: [Evidence → Analysis → Conclusion]"}`

#### 6.2 Merge Actions with Small Model Considerations
Format: `{"action": "merge_entities", "sources": ["Entity1", "Entity2"], "target": "CanonicalName", "reason": "SMALL MODEL OVER-MERGE: [Evidence → Analysis → Conclusion]"}`

### Final Action Plan
Provide JSON list of all actions with evidence-based reasoning:
{{format_instructions}}

### Detailed Reasoning Report
[Comprehensive evidence-based reasoning for each decision: EVIDENCE → ANALYSIS → CONCLUSION, including model capability assessments and hallucination pattern detection]
"""

    def _get_minimal_reflection_template(self) -> str:
        return """
## Quick Reflection Analysis (Evidence-Based)

### Key Observations
- **EVIDENCE**: Response quality indicators from query/response
- **ANALYSIS**: Quality assessment: [GOOD/NEEDS_IMPROVEMENT/POOR]
- **CONCLUSION**: Main issues identified

### Lessons Learned
- **EVIDENCE**: Specific examples from response
- **ANALYSIS**: What went wrong/right and why
- **CONCLUSION**: Actionable insights for improvement

### Output Format
{{format_instructions}}
"""

    def _get_standard_reflection_template(self) -> str:
        return """
## Chain-of-Thought Reflection Analysis (Evidence-Based Structured Reasoning)

### Step 1: Quality Assessment with Evidence
Evaluate the response across multiple dimensions:
- **EVIDENCE**: Specific examples from response text
- **ANALYSIS**:
  - **Accuracy**: Are facts correct according to query?
  - **Relevance**: Does response address the query directly?
  - **Completeness**: Are all aspects of the query addressed?
  - **Clarity**: Is the response well-structured and understandable?
- **CONCLUSION**: Overall quality assessment with supporting evidence

### Step 2: Error Analysis with Structured Reasoning
Identify specific issues with evidence-based reasoning:
- **EVIDENCE**: Quote specific problematic text from response
- **ANALYSIS**:
  - Factual errors or misconceptions
  - Missing important information
  - Irrelevant or off-topic content
  - Unclear or confusing explanations
- **CONCLUSION**: Categorize errors by severity and impact

### Step 3: Instruction Adherence Verification
Check if response follows given instructions:
- **EVIDENCE**: Compare response against specific instructions
- **ANALYSIS**:
  - Formatting requirements compliance
  - Scope limitations adherence
  - Specific constraints or guidelines followed
- **CONCLUSION**: Overall instruction adherence score

### Step 4: Performance Factor Analysis
Analyze what contributed to success or failure:
- **EVIDENCE**: Observable performance indicators
- **ANALYSIS**:
  - Model capabilities and limitations
  - Prompt clarity and effectiveness
  - Context availability and relevance
  - Task complexity and difficulty
- **CONCLUSION**: Key success/failure factors identified

### Step 5: Actionable Insights with Implementation Guidance
Generate specific, actionable lessons:
- **EVIDENCE**: Examples from current interaction
- **ANALYSIS**:
  - **Prompt improvements**: How to guide the model better
  - **Process enhancements**: What steps to add or modify
  - **Quality checks**: What to verify before finalizing
  - **Capability adjustments**: When to use different approaches
- **CONCLUSION**: Priority-ranked actionable insights

### Summary Insights
- **EVIDENCE**: Top 3 examples from analysis
- **ANALYSIS**: Most impactful lessons learned
- **CONCLUSION**: 1-3 most important insights for future improvement

### Output Format
{{format_instructions}}

### Reasoning Summary
[Evidence-based explanation: EVIDENCE → ANALYSIS → CONCLUSION for major decisions]
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
