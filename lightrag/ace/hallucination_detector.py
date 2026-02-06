"""
Hallucination Detection System for ACE Reflector
Provides specialized heuristics and pattern recognition for detecting model hallucinations,
particularly optimized for small models (1.5B/3B) in knowledge graph extraction.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..ace.config import ACEConfig


class HallucinationType(Enum):
    """Types of hallucinations that can occur in knowledge graph extraction."""

    ABSTRACT_CONCEPT = "abstract_concept"
    FALSE_RELATIONSHIP = "false_relationship"
    OVER_SPECIFIC = "over_specific"
    FALSE_CATEGORY = "false_category"
    CROSS_DOMAIN = "cross_domain"
    CONCRETE_ABSTRACT = "concrete_abstract"
    FALSE_EQUIVALENCE = "false_equivalence"
    OVER_GENERALIZATION = "over_generalization"


@dataclass
class HallucinationDetection:
    """Result of hallucination analysis."""

    is_hallucinated: bool
    confidence: float
    hallucination_type: HallucinationType | None
    evidence: str
    reasoning: str
    model_risk_factors: list[str]


class HallucinationDetector:
    """
    Advanced hallucination detection system for ACE Reflector.
    Optimized for detecting common patterns in small model outputs.
    """

    def __init__(self, config: ACEConfig | None = None):
        self.config = config
        self._initialize_patterns()

    def _initialize_patterns(self):
        """Initialize hallucination detection patterns for different model sizes."""

        # Abstract concepts that small models often hallucinate
        self.abstract_concept_patterns = [
            r"\b(intelligence|consciousness|awareness|perception|cognition|understanding)\b",
            r"\b(complexity|sophistication|advancement|innovation|progress)\b",
            r"\b(nature|essence|quality|characteristic|property|attribute)\b",
            r"\b(relationship|connection|interaction|association|correlation)\b",
            r"\b(system|framework|structure|architecture|organization)\b",
        ]

        # False relationship indicators
        self.false_relationship_patterns = [
            r"\b(enables|allows|permits|facilitates|supports)\b.*\b(abstract|philosophical|theoretical)\b",
            r"\b(represents|symbolizes|embodies|manifests)\b.*\b(concept|idea|notion)\b",
            r"\b(influences|affects|impacts|shapes)\b.*\b(fundamental|basic|essential)\b",
        ]

        # Over-specific attributes (beyond source text)
        self.over_specific_patterns = [
            r"\b(exactly|precisely|specifically|particularly|especially)\b.*\b(\d+%|\d+.\d+|approximately)\b",
            r"\b(highly|extremely|remarkably|exceptionally|unusually)\b.*\b(advanced|developed|sophisticated)\b",
        ]

        # False category indicators
        self.false_category_patterns = [
            r"\b(type|kind|sort|variety|class|category)\b.*\b(of|from)\b.*\b(abstract|metaphysical|philosophical)\b",
            r"\b(form|mode|style|way|method)\b.*\b(of|for)\b.*\b(conceptual|theoretical)\b",
        ]

        # Cross-domain confusion indicators
        self.cross_domain_patterns = [
            r"\b(scientific|technical|technological)\b.*\b(philosophical|metaphysical|spiritual)\b",
            r"\b(biological|physical|chemical)\b.*\b(abstract|conceptual|theoretical)\b",
            r"\b(historical|cultural|social)\b.*\b(mathematical|logical|computational)\b",
        ]

        # Small model risk factors
        self.small_model_risk_factors = [
            "entity_length_too_long",  # Very long entity names
            "description_too_abstract",  # Highly abstract descriptions
            "relationship_too_complex",  # Complex causal chains
            "entity_type_mismatch",  # Entity type doesn't match description
            "lack_of_concrete_anchors",  # No concrete examples
            "overuse_of_adverbs",  # Too many qualifying adverbs
            "circular_reasoning",  # Self-referential definitions
        ]

    def detect_entity_hallucination(
        self,
        entity_name: str,
        entity_type: str,
        entity_description: str,
        source_chunks: list[str],
        model_size: str = "7b",
    ) -> HallucinationDetection:
        """
        Detect if an entity is likely hallucinated.

        Args:
            entity_name: Name of the entity to check
            entity_type: Type of the entity
            entity_description: Description of the entity
            source_chunks: Source text chunks for verification
            model_size: Size of the model that generated this entity

        Returns:
            HallucinationDetection with detailed analysis
        """

        risk_factors = []
        confidence = 0.0
        hallucination_type = None
        evidence = ""
        reasoning = ""

        # Check 1: Source Text Verification
        source_evidence = self._check_source_text_support(
            entity_name, entity_description, source_chunks
        )
        if not source_evidence["found"]:
            risk_factors.append("no_source_support")
            confidence += 0.3
            evidence += "No source support found. "

        # Check 2: Abstract Concept Detection
        abstract_analysis = self._detect_abstract_concepts(
            entity_name, entity_description
        )
        if abstract_analysis["is_abstract"]:
            risk_factors.append("abstract_concept")
            confidence += 0.4
            hallucination_type = HallucinationType.ABSTRACT_CONCEPT
            evidence += (
                f"Abstract concept detected: {abstract_analysis['matched_patterns']}. "
            )

        # Check 3: Small Model Risk Factors
        if model_size in ["1.5b", "3b"]:
            small_model_risks = self._analyze_small_model_risks(
                entity_name, entity_type, entity_description
            )
            risk_factors.extend(small_model_risks)
            confidence += len(small_model_risks) * 0.1

        # Check 4: False Category Detection
        category_analysis = self._detect_false_category(entity_type, entity_description)
        if category_analysis["is_false_category"]:
            risk_factors.append("false_category")
            confidence += 0.3
            hallucination_type = HallucinationType.FALSE_CATEGORY
            evidence += f"False category detected: {category_analysis['reasoning']}. "

        # Check 5: Over-Specific Attributes
        specificity_analysis = self._detect_over_specific_attributes(entity_description)
        if specificity_analysis["is_over_specific"]:
            risk_factors.append("over_specific")
            confidence += 0.2
            hallucination_type = HallucinationType.OVER_SPECIFIC
            evidence += f"Over-specific attributes detected: {specificity_analysis['matched_patterns']}. "

        # Generate reasoning
        reasoning = self._generate_entity_reasoning(
            entity_name, entity_type, entity_description, risk_factors, source_evidence
        )

        # Final determination
        is_hallucinated = confidence > 0.6 and len(risk_factors) >= 2

        return HallucinationDetection(
            is_hallucinated=is_hallucinated,
            confidence=min(confidence, 1.0),
            hallucination_type=hallucination_type,
            evidence=evidence.strip(),
            reasoning=reasoning,
            model_risk_factors=risk_factors,
        )

    def detect_relationship_hallucination(
        self,
        source_entity: str,
        target_entity: str,
        relationship_description: str,
        source_chunks: list[str],
        model_size: str = "7b",
    ) -> HallucinationDetection:
        """
        Detect if a relationship is likely hallucinated.

        Args:
            source_entity: Source entity name
            target_entity: Target entity name
            relationship_description: Description of the relationship
            source_chunks: Source text chunks for verification
            model_size: Size of the model that generated this relationship

        Returns:
            HallucinationDetection with detailed analysis
        """

        risk_factors = []
        confidence = 0.0
        hallucination_type = None
        evidence = ""

        # Check 1: Source Text Verification
        source_evidence = self._check_relationship_source_support(
            source_entity, target_entity, relationship_description, source_chunks
        )
        if not source_evidence["found"]:
            risk_factors.append("no_source_support")
            confidence += 0.4
            evidence += "No source support found. "

        # Check 2: False Relationship Patterns
        false_rel_analysis = self._detect_false_relationships(relationship_description)
        if false_rel_analysis["is_false_relationship"]:
            risk_factors.append("false_relationship_pattern")
            confidence += 0.3
            hallucination_type = HallucinationType.FALSE_RELATIONSHIP
            evidence += f"False relationship pattern: {false_rel_analysis['matched_patterns']}. "

        # Check 3: Cross-Domain Confusion
        cross_domain_analysis = self._detect_cross_domain_confusion(
            source_entity, target_entity, relationship_description
        )
        if cross_domain_analysis["is_cross_domain"]:
            risk_factors.append("cross_domain_confusion")
            confidence += 0.3
            hallucination_type = HallucinationType.CROSS_DOMAIN
            evidence += (
                f"Cross-domain confusion: {cross_domain_analysis['reasoning']}. "
            )

        # Check 4: Concrete-Abstract Confusion
        concrete_abstract_analysis = self._detect_concrete_abstract_confusion(
            source_entity, target_entity
        )
        if concrete_abstract_analysis["is_confused"]:
            risk_factors.append("concrete_abstract_confusion")
            confidence += 0.2
            hallucination_type = HallucinationType.CONCRETE_ABSTRACT
            evidence += "Concrete-abstract confusion detected. "

        # Check 5: Small Model Complexity Analysis
        if model_size in ["1.5b", "3b"]:
            complexity_risk = self._analyze_relationship_complexity(
                source_entity, target_entity, relationship_description
            )
            if complexity_risk["is_too_complex"]:
                risk_factors.append("relationship_too_complex")
                confidence += 0.2
                evidence += f"Relationship too complex for {model_size} model. "

        # Generate reasoning
        reasoning = self._generate_relationship_reasoning(
            source_entity,
            target_entity,
            relationship_description,
            risk_factors,
            source_evidence,
        )

        # Final determination
        is_hallucinated = confidence > 0.6 and len(risk_factors) >= 2

        return HallucinationDetection(
            is_hallucinated=is_hallucinated,
            confidence=min(confidence, 1.0),
            hallucination_type=hallucination_type,
            evidence=evidence.strip(),
            reasoning=reasoning,
            model_risk_factors=risk_factors,
        )

    def _check_source_text_support(
        self, entity_name: str, entity_description: str, source_chunks: list[str]
    ) -> dict[str, Any]:
        """Check if entity has support in source text."""

        found = False
        matches = []

        # Exact name matches
        for chunk in source_chunks:
            if entity_name.lower() in chunk.lower():
                found = True
                matches.append("Exact name match in chunk")

        # Description matches (semantic)
        desc_words = set(re.findall(r"\b\w+\b", entity_description.lower()))
        for chunk in source_chunks:
            chunk_words = set(re.findall(r"\b\w+\b", chunk.lower()))
            overlap = len(desc_words & chunk_words) / max(len(desc_words), 1)
            if overlap > 0.3:  # 30% word overlap
                found = True
                matches.append(f"Semantic overlap: {overlap:.2f}")

        return {"found": found, "matches": matches}

    def _detect_abstract_concepts(
        self, entity_name: str, entity_description: str
    ) -> dict[str, Any]:
        """Detect if entity represents abstract concepts commonly hallucinated."""

        matched_patterns = []
        text_to_check = f"{entity_name} {entity_description}".lower()

        for pattern in self.abstract_concept_patterns:
            matches = re.findall(pattern, text_to_check, re.IGNORECASE)
            if matches:
                matched_patterns.extend(matches)

        # Additional abstract concept indicators
        abstract_indicators = [
            "concept",
            "idea",
            "notion",
            "principle",
            "theory",
            "framework",
            "paradigm",
            "methodology",
            "approach",
            "strategy",
            "philosophy",
        ]

        for indicator in abstract_indicators:
            if indicator in text_to_check:
                matched_patterns.append(indicator)

        return {
            "is_abstract": len(matched_patterns) > 0,
            "matched_patterns": matched_patterns,
        }

    def _analyze_small_model_risks(
        self, entity_name: str, entity_type: str, entity_description: str
    ) -> list[str]:
        """Analyze risk factors specific to small models."""

        risks = []

        # Entity length risk
        if len(entity_name) > 50:
            risks.append("entity_length_too_long")

        # Description abstractness
        abstract_words = [
            "concept",
            "abstract",
            "theoretical",
            "philosophical",
            "metaphysical",
        ]
        desc_word_count = len(entity_description.split())
        abstract_word_count = sum(
            1 for word in abstract_words if word in entity_description.lower()
        )

        if desc_word_count > 0 and abstract_word_count / desc_word_count > 0.2:
            risks.append("description_too_abstract")

        # Lack of concrete examples
        concrete_indicators = ["example", "instance", "case", "specifically", "such as"]
        has_concrete = any(
            indicator in entity_description.lower() for indicator in concrete_indicators
        )

        if not has_concrete and len(entity_description) > 100:
            risks.append("lack_of_concrete_anchors")

        # Overuse of adverbs
        adverb_pattern = r"\b\w+ly\b"
        adverbs = re.findall(adverb_pattern, entity_description.lower())
        if len(adverbs) > 3:
            risks.append("overuse_of_adverbs")

        return risks

    def _detect_false_category(
        self, entity_type: str, entity_description: str
    ) -> dict[str, Any]:
        """Detect false category assignments."""

        # Known entity type mismatches
        type_description_mismatches = {
            "person": ["concept", "idea", "theory", "principle"],
            "location": ["framework", "system", "methodology"],
            "organization": ["philosophy", "paradigm", "approach"],
            "concept": ["physical", "tangible", "concrete"],
        }

        is_false_category = False
        reasoning = ""

        if entity_type.lower() in type_description_mismatches:
            mismatched_words = type_description_mismatches[entity_type.lower()]
            for word in mismatched_words:
                if word in entity_description.lower():
                    is_false_category = True
                    reasoning = f"Entity type '{entity_type}' conflicts with description containing '{word}'"
                    break

        return {"is_false_category": is_false_category, "reasoning": reasoning}

    def _detect_over_specific_attributes(
        self, entity_description: str
    ) -> dict[str, Any]:
        """Detect over-specific attributes beyond source text."""

        matched_patterns = []

        for pattern in self.over_specific_patterns:
            matches = re.findall(pattern, entity_description, re.IGNORECASE)
            if matches:
                matched_patterns.extend(matches)

        return {
            "is_over_specific": len(matched_patterns) > 0,
            "matched_patterns": matched_patterns,
        }

    def _check_relationship_source_support(
        self,
        source_entity: str,
        target_entity: str,
        relationship_description: str,
        source_chunks: list[str],
    ) -> dict[str, Any]:
        """Check if relationship has support in source text."""

        found = False
        matches = []

        # Look for both entities in same chunk
        for chunk in source_chunks:
            if (
                source_entity.lower() in chunk.lower()
                and target_entity.lower() in chunk.lower()
            ):
                found = True
                matches.append("Both entities found in same chunk")

                # Check for relationship indicators
                rel_indicators = [
                    "is",
                    "are",
                    "was",
                    "were",
                    "has",
                    "have",
                    "causes",
                    "leads to",
                ]
                for indicator in rel_indicators:
                    if indicator in chunk.lower():
                        matches.append(f"Relationship indicator '{indicator}' found")
                        break

        return {"found": found, "matches": matches}

    def _detect_false_relationships(
        self, relationship_description: str
    ) -> dict[str, Any]:
        """Detect false relationship patterns."""

        matched_patterns = []

        for pattern in self.false_relationship_patterns:
            matches = re.findall(pattern, relationship_description, re.IGNORECASE)
            if matches:
                matched_patterns.extend(matches)

        return {
            "is_false_relationship": len(matched_patterns) > 0,
            "matched_patterns": matched_patterns,
        }

    def _detect_cross_domain_confusion(
        self, source_entity: str, target_entity: str, relationship_description: str
    ) -> dict[str, Any]:
        """Detect cross-domain confusion."""

        domain_keywords = {
            "scientific": ["experiment", "hypothesis", "theory", "research", "study"],
            "philosophical": ["concept", "idea", "notion", "principle", "philosophy"],
            "technical": ["system", "process", "method", "technique", "technology"],
            "biological": ["organism", "cell", "gene", "evolution", "species"],
            "mathematical": ["equation", "formula", "theorem", "calculation", "number"],
        }

        source_domains = []
        target_domains = []

        # Detect domains for entities
        all_text = f"{source_entity} {target_entity} {relationship_description}".lower()

        for domain, keywords in domain_keywords.items():
            if any(keyword in all_text for keyword in keywords):
                if any(keyword in source_entity.lower() for keyword in keywords):
                    source_domains.append(domain)
                if any(keyword in target_entity.lower() for keyword in keywords):
                    target_domains.append(domain)

        # Check for cross-domain patterns
        is_cross_domain = False
        reasoning = ""

        cross_domain_pairs = [
            ("scientific", "philosophical"),
            ("technical", "biological"),
            ("mathematical", "philosophical"),
        ]

        for source_domain in source_domains:
            for target_domain in target_domains:
                if (source_domain, target_domain) in cross_domain_pairs or (
                    target_domain,
                    source_domain,
                ) in cross_domain_pairs:
                    is_cross_domain = True
                    reasoning = (
                        f"Cross-domain relationship: {source_domain} ↔ {target_domain}"
                    )
                    break

        return {"is_cross_domain": is_cross_domain, "reasoning": reasoning}

    def _detect_concrete_abstract_confusion(
        self, source_entity: str, target_entity: str
    ) -> dict[str, Any]:
        """Detect concrete-abstract confusion."""

        concrete_indicators = [
            "person",
            "place",
            "object",
            "thing",
            "physical",
            "material",
        ]
        abstract_indicators = [
            "concept",
            "idea",
            "theory",
            "principle",
            "abstract",
            "metaphysical",
        ]

        source_is_concrete = any(
            indicator in source_entity.lower() for indicator in concrete_indicators
        )
        source_is_abstract = any(
            indicator in source_entity.lower() for indicator in abstract_indicators
        )
        target_is_concrete = any(
            indicator in target_entity.lower() for indicator in concrete_indicators
        )
        target_is_abstract = any(
            indicator in target_entity.lower() for indicator in abstract_indicators
        )

        # Check for confusing patterns
        is_confused = False

        # Concrete entity causing abstract concept
        if source_is_concrete and target_is_abstract:
            is_confused = True
        # Abstract concept having concrete properties
        elif source_is_abstract and target_is_concrete:
            is_confused = True

        return {"is_confused": is_confused}

    def _analyze_relationship_complexity(
        self, source_entity: str, target_entity: str, relationship_description: str
    ) -> dict[str, Any]:
        """Analyze if relationship is too complex for small models."""

        complexity_indicators = [
            len(relationship_description) > 100,  # Long description
            relationship_description.count(" ") > 15,  # Many words
            "because" in relationship_description.lower(),  # Causal reasoning
            "although" in relationship_description.lower(),  # Complex reasoning
            relationship_description.count(",") > 2,  # Multiple clauses
        ]

        complexity_score = sum(complexity_indicators)

        return {
            "is_too_complex": complexity_score >= 3,
            "complexity_score": complexity_score,
        }

    def _generate_entity_reasoning(
        self,
        entity_name: str,
        entity_type: str,
        entity_description: str,
        risk_factors: list[str],
        source_evidence: dict[str, Any],
    ) -> str:
        """Generate detailed reasoning for entity hallucination detection."""

        reasoning_parts = []

        # Evidence section
        reasoning_parts.append("EVIDENCE:")
        if source_evidence["found"]:
            reasoning_parts.append(
                f"- Source support: {', '.join(source_evidence['matches'])}"
            )
        else:
            reasoning_parts.append("- No source support found in provided chunks")

        # Analysis section
        reasoning_parts.append("ANALYSIS:")
        if "abstract_concept" in risk_factors:
            reasoning_parts.append(
                "- Entity represents abstract concept commonly hallucinated by small models"
            )
        if "false_category" in risk_factors:
            reasoning_parts.append("- Entity type conflicts with description content")
        if "over_specific" in risk_factors:
            reasoning_parts.append(
                "- Entity contains over-specific attributes beyond source text"
            )
        if "entity_length_too_long" in risk_factors:
            reasoning_parts.append(
                "- Entity name unusually long, potential fabrication"
            )
        if "description_too_abstract" in risk_factors:
            reasoning_parts.append(
                "- Description overly abstract without concrete anchors"
            )

        # Conclusion section
        reasoning_parts.append("CONCLUSION:")
        if len(risk_factors) >= 3:
            reasoning_parts.append("- High confidence hallucination detection")
        elif len(risk_factors) >= 2:
            reasoning_parts.append("- Medium confidence hallucination detection")
        else:
            reasoning_parts.append("- Low confidence, requires human review")

        return "\n".join(reasoning_parts)

    def _generate_relationship_reasoning(
        self,
        source_entity: str,
        target_entity: str,
        relationship_description: str,
        risk_factors: list[str],
        source_evidence: dict[str, Any],
    ) -> str:
        """Generate detailed reasoning for relationship hallucination detection."""

        reasoning_parts = []

        # Evidence section
        reasoning_parts.append("EVIDENCE:")
        if source_evidence["found"]:
            reasoning_parts.append(
                f"- Source support: {', '.join(source_evidence['matches'])}"
            )
        else:
            reasoning_parts.append("- No source support found for relationship")

        # Analysis section
        reasoning_parts.append("ANALYSIS:")
        if "false_relationship_pattern" in risk_factors:
            reasoning_parts.append(
                "- Relationship matches known false pattern hallucinations"
            )
        if "cross_domain_confusion" in risk_factors:
            reasoning_parts.append(
                "- Relationship confuses concepts from different domains"
            )
        if "concrete_abstract_confusion" in risk_factors:
            reasoning_parts.append(
                "- Relationship inappropriately mixes concrete and abstract concepts"
            )
        if "relationship_too_complex" in risk_factors:
            reasoning_parts.append(
                "- Relationship too complex for small model reasoning capacity"
            )

        # Conclusion section
        reasoning_parts.append("CONCLUSION:")
        if len(risk_factors) >= 2:
            reasoning_parts.append("- High confidence hallucination detection")
        elif len(risk_factors) >= 1:
            reasoning_parts.append("- Medium confidence hallucination detection")
        else:
            reasoning_parts.append("- Low confidence, likely valid relationship")

        return "\n".join(reasoning_parts)
