# LightRAG A/B Testing Framework

A comprehensive, production-grade A/B testing framework for LightRAG with real-time monitoring, statistical analysis, load testing, and canary deployment support.

## 🚀 Quick Start

### Basic A/B Test

```python
from ab_testing.comprehensive_framework import create_openviking_experiment, ExperimentEngine

# Create experiment configuration
config = create_openviking_experiment(
    openviking_url="http://localhost:8000",
    smp_url="http://localhost:9621"
)

# Start experiment
engine = ExperimentEngine(config)
await engine.start_experiment()

# Execute test requests
result = await engine.execute_request(
    request_data={"text": "React performance optimization"},
    user_id="user_123",
    session_id="session_456"
)

# Get final results
final_report = await engine.end_experiment()
```

### Real-time Monitoring

```python
from ab_testing.realtime_monitoring import create_monitoring_system

# Create monitoring system
monitor, server, terminal_monitor = create_monitoring_system()

# Start monitoring server (runs in background)
await server.start()

# Register experiment
monitor.register_experiment("openviking_vs_smp", {
    "name": "OpenViking vs SMP Comparison",
    "variants": ["openviking", "smp"]
})

# Monitor in terminal
terminal_monitor.start_monitoring()
```

### Load Testing

```python
from ab_testing.load_testing_canary import LoadTestRunner, LoadTestConfig

# Configure load test
config = LoadTestConfig(
    concurrent_users=50,
    requests_per_second=100,
    duration_seconds=300,
    endpoints=["http://localhost:8000/embeddings"]
)

# Run load test
runner = LoadTestRunner(config)
results = await runner.run_load_test("performance_test")
```

## 📋 Features

### Core Framework
- **Experiment Management**: Complete experiment lifecycle control
- **Traffic Splitting**: Hash-based, random, and round-robin distribution
- **Variant Configuration**: Flexible endpoint and variant management
- **Metrics Collection**: Real-time performance data tracking
- **Statistical Analysis**: T-tests, Mann-Whitney, bootstrap methods

### Real-time Monitoring
- **WebSocket Dashboard**: Live updates via web interface
- **Alert System**: Configurable thresholds and notifications
- **Terminal Monitor**: Rich CLI dashboard for local monitoring
- **Metrics Buffering**: Efficient data storage and retrieval
- **Multi-experiment Support**: Monitor multiple experiments simultaneously

### Advanced Analytics
- **Statistical Significance**: Multiple test methods with power analysis
- **Effect Size Calculation**: Cohen's d, Hedges' g, Cliff's delta
- **Confidence Intervals**: Bootstrap and parametric methods
- **Automated Decision Making**: AI-powered winner determination
- **Result Export**: JSON, CSV, and markdown report generation

### Load Testing & Canary
- **High-performance Testing**: Asynchronous load generation
- **Gradual Rollout**: Automated canary deployment
- **Safety Checks**: Configurable thresholds for rollback
- **Performance Monitoring**: Real-time metrics during deployment
- **Deployment Orchestration**: Complete pipeline automation

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Experiment    │    │   Traffic        │    │   Metrics       │
│   Manager       │───▶│   Splitter       │───▶│   Collector     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Statistical   │    │   Real-time       │    │   Dashboard     │
│   Analyzer      │    │   Monitor         │    │   UI            │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Load Testing  │    │   Canary         │    │   Alert         │
│   Engine        │    │   Deployer       │    │   System        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📊 Dashboard Features

### Web Dashboard
- **Real-time Charts**: Live response time and success rate visualization
- **Experiment Management**: Create, start, stop, and monitor experiments
- **Performance Metrics**: Detailed statistics and comparisons
- **Alert Management**: View and respond to system alerts
- **Historical Data**: Time-series analysis and trends

### Terminal Dashboard
- **Rich Interface**: Colorful terminal UI with live updates
- **Performance Overview**: At-a-glance experiment statistics
- **Resource Monitoring**: System health and capacity metrics
- **Quick Actions**: Fast experiment control commands

## 🔧 Configuration

### Experiment Configuration

```python
from ab_testing.comprehensive_framework import ExperimentConfig, ExperimentVariant
from ab_testing.comprehensive_framework import VariantType

variants = [
    ExperimentVariant(
        name="openviking",
        type=VariantType.TREATMENT,
        traffic_percentage=50.0,
        endpoint="http://localhost:8000/embeddings",
        headers={"Content-Type": "application/json"},
        config={"model": "qwen2.5-coder:1.5b"}
    ),
    ExperimentVariant(
        name="smp",
        type=VariantType.CONTROL,
        traffic_percentage=50.0,
        endpoint="http://localhost:9621/embeddings",
        headers={"Content-Type": "application/json"}
    )
]

config = ExperimentConfig(
    name="openviking_vs_smp",
    description="Compare OpenViking vs SMP embedding performance",
    variants=variants,
    sample_size=1000,
    confidence_level=0.95,
    min_effect_size=0.05,
    duration_hours=24,
    auto_rollout_enabled=False
)
```

### Monitoring Configuration

```python
from ab_testing.realtime_monitoring import RealTimeMonitor

monitor = RealTimeMonitor(buffer_size=1000)

# Configure alert thresholds
monitor.alert_thresholds = {
    "error_rate": 0.1,  # 10% error rate
    "response_time_p95": 5000,  # 5 seconds
    "success_rate_min": 0.9,  # 90% minimum success rate
    "sample_size_min": 100,  # Minimum samples for reliability
}
```

### Load Testing Configuration

```python
from ab_testing.load_testing_canary import LoadTestConfig

load_test_config = LoadTestConfig(
    concurrent_users=100,
    requests_per_second=50,
    duration_seconds=300,
    ramp_up_time=30,
    endpoints=["http://localhost:8000/embeddings"],
    timeout=30.0,
    retry_attempts=3
)
```

## 📈 Statistical Analysis

### Supported Tests
- **Independent Samples T-Test**: For normally distributed data
- **Mann-Whitney U Test**: Non-parametric alternative
- **Z-Test**: Large sample approximation
- **Bootstrap Test**: Resampling-based inference

### Effect Size Measures
- **Cohen's d**: Standardized mean difference
- **Hedges' g**: Small sample bias correction
- **Cliff's delta**: Non-parametric effect size

### Power Analysis
- **Statistical Power**: Probability of detecting true effects
- **Sample Size Calculation**: Required samples for desired power
- **Effect Size Estimation**: Practical significance assessment

## 🚦 Canary Deployment

### Stages
1. **Preparation**: Health checks and system validation
2. **Initial Traffic**: Small percentage (5%) to treatment
3. **Gradual Increase**: Slowly ramp up traffic percentage
4. **Monitoring**: Extended observation period
5. **Decision**: Promote or rollback based on metrics

### Safety Features
- **Automatic Rollback**: Fail-safe error handling
- **Threshold Monitoring**: Configurable success criteria
- **Gradual Progression**: Controlled traffic increase
- **Health Checks**: Continuous endpoint validation

## 🔌 Integration Examples

### OpenViking vs SMP Comparison

```python
from ab_testing.comprehensive_framework import create_openviking_experiment
from ab_testing.realtime_monitoring import create_monitoring_system
from ab_testing.load_testing_canary import DeploymentOrchestrator

# Complete integration
config = create_openviking_experiment()
engine = ExperimentEngine(config)

# Monitoring integration
monitor, server, _ = create_monitoring_system()
monitor.register_experiment("openviking_vs_smp", config.dict())

# Load testing before deployment
orchestrator = DeploymentOrchestrator()
deployment_results = await orchestrator.run_full_deployment_test(
    load_test_config=create_lightrag_load_test_config(),
    canary_config=create_lightrag_canary_config(),
    endpoints={
        "control": "http://localhost:9621/embeddings",
        "treatment": "http://localhost:8000/embeddings"
    }
)
```

### Custom Metrics Collection

```python
from ab_testing.comprehensive_framework import ExperimentMetrics

# Custom metrics handling
async def custom_request_handler(experiment_engine, user_id, request_data):
    # Execute request through experiment
    result = await experiment_engine.execute_request(
        request_data=request_data,
        user_id=user_id
    )

    # Add custom metrics
    custom_metrics = ExperimentMetrics(
        response_time_ms=result.metrics.response_time_ms,
        status_code=result.metrics.status_code,
        success=result.metrics.success,
        custom_metrics={
            "token_efficiency": calculate_token_efficiency(result.response_data),
            "semantic_similarity": calculate_similarity(result.response_data)
        }
    )

    experiment_engine.metrics_collector.record_metric(
        result.variant,
        result.request_id,
        custom_metrics
    )

    return result
```

## 📊 Results and Reports

### Automated Reports
- **Summary Statistics**: Key performance indicators
- **Statistical Tests**: Multiple analysis methods
- **Visualizations**: Charts and graphs
- **Recommendations**: AI-powered insights

### Export Formats
- **JSON**: Machine-readable detailed results
- **CSV**: Spreadsheet-compatible data
- **Markdown**: Human-readable reports
- **PDF**: Formatted executive summaries

## 🛠️ Installation

### Dependencies

```bash
pip install -r ab_testing/requirements.txt
```

Key dependencies:
- `fastapi>=0.128.0` - Web server and API
- `httpx>=0.28.1` - Async HTTP client
- `pandas>=2.0.0` - Data manipulation
- `numpy>=1.24.0` - Numerical computing
- `scipy>=1.10.0` - Statistical functions
- `websockets>=11.0` - Real-time communication
- `rich>=13.0.0` - Terminal UI
- `uvicorn>=0.20.0` - ASGI server

### Optional Dependencies

```bash
# For advanced statistical analysis
pip install scikit-learn>=1.3.0

# For enhanced visualizations
pip install plotly>=5.14.0
pip install seaborn>=0.12.0
```

## 🧪 Testing

### Unit Tests
```bash
python -m pytest tests/test_ab_framework.py -v
```

### Integration Tests
```bash
python -m pytest tests/test_integration.py -v
```

### Load Testing Validation
```bash
python tests/test_load_testing.py --validate
```

## 📚 API Reference

### ExperimentEngine
```python
class ExperimentEngine:
    async def start_experiment(self) -> bool
    async def execute_request(self, request_data, user_id, session_id="") -> Dict
    async def end_experiment(self) -> Dict
    def get_experiment_status(self) -> Dict
```

### RealTimeMonitor
```python
class RealTimeMonitor:
    def register_experiment(self, experiment_id, experiment_config)
    def add_metrics(self, experiment_id, variant_name, metrics_data)
    def get_experiment_summary(self, experiment_id) -> Dict
    def get_dashboard_data(self) -> Dict
```

### StatisticalAnalyzer
```python
class StatisticalAnalyzer:
    def analyze_experiment(self, control_data, treatment_data, test_type) -> StatisticalTestResult
    def interpret_effect_size(self, effect_size, test_type) -> str
    def calculate_required_sample_size(self, effect_size, desired_power) -> int
```

## 🔍 Monitoring and Alerting

### Alert Types
- **Error Rate**: High failure percentage
- **Response Time**: Slow performance detection
- **Sample Size**: Insufficient data warning
- **Statistical Power**: Low power alerts

### Notification Channels
- **WebSocket**: Real-time dashboard updates
- **Terminal**: CLI notifications
- **File Logging**: Persistent alert storage

## 🚀 Production Deployment

### Environment Setup
```bash
# Set environment variables
export AB_TESTING_LOG_LEVEL=INFO
export AB_TESTING_METRICS_RETENTION_HOURS=168
export AB_TESTING_DASHBOARD_PORT=8080
export AB_TESTING_MAX_CONCURRENT_EXPERIMENTS=10
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ab_testing/ ./ab_testing/
EXPOSE 8080

CMD ["python", "-m", "ab_testing.advanced_dashboard"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ab-testing-dashboard
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ab-testing
  template:
    metadata:
      labels:
        app: ab-testing
    spec:
      containers:
      - name: dashboard
        image: ab-testing:latest
        ports:
        - containerPort: 8080
        env:
        - name: AB_TESTING_DASHBOARD_PORT
          value: "8080"
```

## 🤝 Contributing

### Development Setup
```bash
git clone https://github.com/your-org/LightRAG.git
cd LightRAG/ab_testing
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Code Style
- Follow PEP 8 conventions
- Use type hints throughout
- Document all public methods
- Add unit tests for new features

### Testing Guidelines
- Maintain 90%+ test coverage
- Include integration tests for workflows
- Performance test load generation
- Statistical validation of analysis methods

## 📄 License

This A/B testing framework is licensed under the same terms as the LightRAG project.

## 🆘 Support

### Troubleshooting
- Check logs for error messages
- Verify endpoint connectivity
- Validate configuration parameters
- Monitor system resources

### Common Issues
1. **WebSocket Connection Failed**: Check firewall and port settings
2. **Statistical Power Low**: Increase sample size or effect size
3. **Load Test Timeout**: Adjust timeout and retry settings
4. **Canary Rollback**: Review threshold configurations

### Performance Tips
- Use connection pooling for HTTP requests
- Implement metrics buffering for high-throughput scenarios
- Configure appropriate sample sizes for statistical validity
- Monitor memory usage during long-running experiments

---

**Built with ❤️ for the LightRAG community**
