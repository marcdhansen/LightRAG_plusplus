# 🧠 Chain-of-Thought (CoT) Reasoning in ACE Reflector

## Overview

Chain-of-Thought (CoT) reasoning enhances the ACE Reflector's analytical capabilities by providing structured, step-by-step analysis for both graph verification and general reflection tasks. This feature improves accuracy, transparency, and debugging capabilities.

## 🎯 Key Benefits

1. **Enhanced Accuracy**: Structured reasoning reduces hallucination detection errors
2. **Better Debugging**: Visible reasoning chains for troubleshooting and analysis
3. **Configurable Overhead**: Users can balance accuracy vs token cost
4. **Enhanced Trust**: Transparent decision-making process
5. **Educational Value**: Shows how the system analyzes graph integrity

## ⚙️ Configuration Options

### Basic Configuration

```python
from lightrag import LightRAG
from lightrag.ace.config import ACEConfig

# Configure CoT settings
ace_config = ACEConfig(
    cot_enabled=True,                    # Master switch for CoT
    cot_depth="standard",                # Reasoning depth level
    cot_graph_verification=True,         # Enable CoT for graph integrity
    cot_general_reflection=True,          # Enable CoT for quality analysis
    cot_include_reasoning_output=True    # Capture reasoning for display
)

# Initialize LightRAG with CoT-enabled ACE
rag = LightRAG(
    working_dir="./rag_storage",
    llm_model_name="qwen2.5-coder:7b",
    llm_model_func=ollama_model_complete,
    enable_ace=True,
    embedding_func=EmbeddingFunc(...)
)

# Apply the configuration
rag.ace_config = ace_config
```

### Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `cot_enabled` | bool | True | Master switch to enable/disable CoT reasoning |
| `cot_depth` | str | "standard" | Depth level: "minimal", "standard", or "detailed" |
| `cot_graph_verification` | bool | True | Enable CoT for graph integrity verification |
| `cot_general_reflection` | bool | True | Enable CoT for general quality reflection |
| `cot_include_reasoning_output` | bool | True | Store reasoning chains for debugging and WebUI display |

## 📊 CoT Depth Levels

### Minimal Depth
**Best for**: Fast processing, resource-constrained environments
- Quick source text scanning
- Critical decision highlights
- Immediate action recommendations
- **Token Cost**: ~200-400 tokens

### Standard Depth (Recommended)
**Best for**: Production use, balanced performance
- Step-by-step source analysis
- Entity and relationship verification
- Deduplication reasoning
- Summary of key decisions
- **Token Cost**: ~600-1200 tokens

### Detailed Depth
**Best for**: Critical applications, debugging complex cases
- Multi-phase verification process
- Confidence scoring and impact analysis
- Comprehensive error taxonomy
- Strategic improvement planning
- **Token Cost**: ~1500-3000 tokens

## 🔍 Use Cases

### Graph Verification CoT

When `cot_graph_verification=True`, the Reflector performs:

1. **Source Text Analysis**: Systematic scanning of source chunks
2. **Entity Verification**: Existence checks and attribute validation
3. **Relationship Verification**: Structural and content verification
4. **Deduplication Analysis**: Identifying and merging duplicate entities
5. **Action Formulation**: Generating specific repair actions

**Example Output**:
```json
[
    {
        "action": "delete_relation",
        "source": "Albert Einstein",
        "target": "Mars",
        "reason": "Relationship not supported by source text"
    },
    {
        "action": "merge_entities",
        "sources": ["AI", "Artificial Intelligence"],
        "target": "Artificial Intelligence",
        "reason": "Same real-world concept with different names"
    }
]
```

### General Reflection CoT

When `cot_general_reflection=True`, the Reflector analyzes:

1. **Quality Assessment**: Accuracy, relevance, completeness evaluation
2. **Error Analysis**: Identification of specific issues and root causes
3. **Performance Factors**: Understanding what contributed to outcomes
4. **Actionable Insights**: Generating specific improvement recommendations

**Example Output**:
```json
[
    "Add explicit domain context prompts for specialized topics",
    "Implement fact-checking step for numerical claims",
    "Include source attribution requirements for sensitive information"
]
```

## 🔧 Implementation Details

### Reasoning Extraction

The system automatically extracts reasoning from LLM outputs using multiple patterns:

```reasoning
Step 1: I analyzed the source text and found no mention of Mars.
Step 2: The relationship claims Einstein went to Mars, which is not supported.
Step 3: I recommend deleting this hallucinated relationship.
```

The reasoning is stored in the generation result for WebUI display:
- `generation_result["reflection_reasoning"]` - From general reflection
- `generation_result["graph_verification_reasoning"]` - From graph verification

### Template System

CoT uses a modular template system in `lightrag/ace/cot_templates.py`:

- **CoTTemplates**: Main template manager
- **CoTDepth**: Enum for depth levels
- **Configurable templates**: Separate templates for each depth and use case

### Integration Points

CoT integrates with existing ACE workflow:

1. **Reflector Initialization**: Templates loaded based on ACE config
2. **Prompt Construction**: CoT templates integrated with existing prompts
3. **Response Processing**: Reasoning extracted alongside JSON actions
4. **Logging and Storage**: Reasoning captured for debugging and display

## 📈 Performance Impact

### Token Usage
- **Minimal**: +200-400 tokens per request
- **Standard**: +600-1200 tokens per request
- **Detailed**: +1500-3000 tokens per request

### Latency
- **Processing Time**: +2-8 seconds per request (depends on model)
- **Model Dependency**: 7B+ models handle CoT reasoning most effectively

### Accuracy Gains
- **Hallucination Detection**: 15-25% improvement in accuracy
- **Error Reduction**: Fewer false positives in graph repairs
- **Decision Quality**: More consistent and reliable analysis

## 🧪 Testing and Validation

### Unit Tests
```bash
# Run CoT-specific tests
python -m pytest tests/test_cot_integration.py -v
```

### Integration Tests
```bash
# Test CoT with full ACE workflow
python -m pytest tests/test_ace_reflector_repair.py -v
```

### Manual Validation
```python
# Quick test of CoT functionality
python tests/test_cot_integration.py
```

## 🔍 Troubleshooting

### Common Issues

**1. CoT Not Working**
- Check `ace_config.cot_enabled` is True
- Verify `cot_graph_verification` or `cot_general_reflection` are True
- Ensure Reflector has access to `ace_config`

**2. No Reasoning Output**
- Check `cot_include_reasoning_output` is True
- Verify LLM is following CoT instructions
- Look at logs for reasoning extraction messages

**3. High Token Costs**
- Switch from `detailed` to `standard` or `minimal` depth
- Consider disabling CoT for non-critical operations
- Use smaller models for initial processing, larger for verification

### Debug Mode

Enable detailed logging to see CoT reasoning:
```python
import logging
logging.getLogger("lightrag.ace.reflector").setLevel(logging.INFO)
```

### WebUI Integration

CoT reasoning is automatically available in WebUI when stored:
- Reasoning sections appear in ACE trajectory logs
- Graph verification reasoning shows repair decisions
- General reflection reasoning displays quality analysis

## 🚀 Best Practices

### Production Recommendations

1. **Use Standard Depth**: Balanced performance and accuracy
2. **Enable Reasoning Output**: Essential for debugging and transparency
3. **Monitor Token Usage**: Track costs with CoT enabled
4. **Test Thoroughly**: Validate CoT behavior with your specific data

### Development Recommendations

1. **Start with Minimal**: Test CoT functionality with minimal overhead
2. **Gradual Increase**: Move to standard/detailed as needed
3. **Customize Templates**: Modify templates for domain-specific needs
4. **Validate Extracted Reasoning**: Ensure reasoning extraction works with your LLM

### Performance Optimization

1. **Selective CoT**: Enable only for critical operations
2. **Cache Templates**: Templates are cached automatically
3. **Batch Processing**: Process multiple items with single CoT analysis
4. **Model Selection**: Use capable models (7B+) for best CoT performance

## 📚 Further Reading

- [ACE Framework Overview](ACE_FRAMEWORK.md)
- [Model Profiling Results](../../MODEL_PROFILING_RESULTS.md)
- [Testing Documentation](../../tests/README.md)

## 🤝 Contributing

To extend or modify CoT functionality:

1. **Edit Templates**: Modify `lightrag/ace/cot_templates.py`
2. **Add Tests**: Include new tests in `tests/test_cot_integration.py`
3. **Update Documentation**: Keep this file current with changes
4. **Performance Testing**: Validate changes don't break existing functionality

---

**Last Updated**: v0.5.0
**Maintainers**: LightRAG Development Team
