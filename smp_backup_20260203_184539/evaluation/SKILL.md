# 🧪 Evaluation Skill

**Purpose**: Manages comprehensive evaluation framework for LightRAG, including benchmarking, metrics tracking, and performance analysis.

## 🎯 Mission
- Run RAGAS benchmarking and evaluation suites
- Track performance metrics over time
- Manage A/B testing for prompts and configurations
- Coordinate evaluation pipelines and reporting

## 🛠️ Tools & Scripts

### RAGAS Benchmarking
```bash
# Run comprehensive RAGAS evaluation
python3 scripts/run_ragas_evaluation.py

# Run specific test suite
python3 scripts/run_ragas_evaluation.py --suite answer_correctness
```

### Metrics Tracking
```bash
# Generate performance report
python3 scripts/metrics_report.py --period weekly

# Compare current vs baseline
python3 scripts/compare_performance.py --baseline main
```

### A/B Testing
```bash
# Start A/B test for new prompts
python3 scripts/ab_test_prompts.py --control current --candidate new_prompts

# Analyze A/B test results
python3 scripts/analyze_ab_test.py --test-id 123
```

### Langfuse Integration
```bash
# Export data to Langfuse for analysis
python3 scripts/langfuse_export.py --dataset evaluation_results

# Configure Langfuse tracking
python3 scripts/setup_langfuse.py
```

## 📋 Usage Examples

### Basic Evaluation
```bash
# Run full evaluation suite
/evaluation --full-suite

# Quick performance check
/evaluation --quick-check

# Benchmark against specific dataset
/evaluation --benchmark --dataset hotpotqa
```

### Metrics Management
```bash
# Track performance trends
/evaluation --track-metrics --period daily

# Generate comparison report
/evaluation --compare --commit-1 abc123 --commit-2 def456
```

## 🔗 Integration Points
- **CI/CD**: Automatic evaluation on code changes
- **Beads**: Track evaluation tasks and results
- **Graph Skill**: Evaluate graph-based performance
- **Testing Skill**: Coordinate test and evaluation pipelines

## 📊 Metrics Tracked
- RAGAS scores (faithfulness, answer relevance, context precision)
- End-to-end latency
- Resource utilization
- User satisfaction metrics

## 🎯 Key Files
- `evaluation/` - Evaluation datasets and results
- `scripts/run_ragas_evaluation.py` - Main evaluation script
- `evaluation/configs/` - Evaluation configurations
- `evaluation/results/` - Benchmark results and reports
