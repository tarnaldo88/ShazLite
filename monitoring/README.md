# Audio Fingerprinting System - Performance Monitoring

This directory contains comprehensive performance monitoring and optimization tools for the Audio Fingerprinting System.

## Overview

The monitoring system provides:

- **Real-time system monitoring** with alerting
- **Performance profiling** for audio processing and API endpoints
- **Database optimization** tools and query analysis
- **Web-based dashboard** for visualization
- **Automated alerting** via email and webhooks

## Components

### 1. System Monitor (`system_monitor.py`)

Monitors system resources and application performance in real-time.

**Features:**
- CPU, memory, disk usage monitoring
- Application-specific metrics (API response times, fingerprint processing)
- Configurable alerting thresholds
- Email and webhook notifications
- Metrics export and historical data

**Usage:**
```bash
# Interactive monitoring
python monitoring/system_monitor.py

# Daemon mode
python monitoring/system_monitor.py --daemon

# Export metrics
python monitoring/system_monitor.py --export metrics.json

# Show current status
python monitoring/system_monitor.py --status
```

**Configuration:**
Create a `monitor_config.json` file:
```json
{
  "monitoring_interval": 30,
  "metrics_retention_hours": 24,
  "alert_cooldown_minutes": 15,
  "email_alerts": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "monitor@yourcompany.com",
    "to_emails": ["admin@yourcompany.com"]
  }
}
```

### 2. Performance Profiler (`performance_profiler.py`)

Profiles application performance to identify bottlenecks.

**Features:**
- Audio processing performance analysis
- Database query profiling
- API endpoint response time measurement
- Memory usage tracking
- Performance recommendations

**Usage:**
```bash
# Profile audio processing
python monitoring/performance_profiler.py --mode audio --iterations 10

# Profile database operations
python monitoring/performance_profiler.py --mode database --iterations 5

# Profile API endpoints (requires running server)
python monitoring/performance_profiler.py --mode api --audio-file test.wav

# Full system profiling
python monitoring/performance_profiler.py --mode full --output profile_report.json
```

**Requirements Validation:**
The profiler automatically checks against system requirements:
- Fingerprint generation: ≤ 5 seconds
- Total processing time: ≤ 10 seconds  
- Database queries: ≤ 3 seconds

### 3. Database Optimizer (`database_optimizer.py`)

Analyzes and optimizes database performance.

**Features:**
- Query performance analysis using `pg_stat_statements`
- Index usage analysis and recommendations
- Table statistics and size monitoring
- Automated optimization suggestions
- Performance benchmarking

**Usage:**
```bash
# Analyze database performance
python monitoring/database_optimizer.py --analyze

# Generate optimization report
python monitoring/database_optimizer.py --report db_optimization.json

# Apply safe optimizations
python monitoring/database_optimizer.py --optimize --auto-apply
```

**Key Optimizations:**
- Critical fingerprint indexes for fast lookups
- Query plan analysis and suggestions
- Unused index identification
- Table statistics updates

### 4. Monitoring Dashboard (`monitoring_dashboard.py`)

Web-based dashboard for real-time monitoring visualization.

**Features:**
- Real-time metrics display
- Alert management interface
- Performance graphs and charts
- System health overview
- Mobile-responsive design

**Usage:**
```bash
# Start dashboard (requires Flask)
pip install flask
python monitoring/monitoring_dashboard.py

# Custom host/port
python monitoring/monitoring_dashboard.py --host 0.0.0.0 --port 8080
```

**Access:** http://localhost:5000

## Performance Requirements

The monitoring system validates against these requirements:

| Component | Metric | Requirement | Alert Threshold |
|-----------|--------|-------------|-----------------|
| Audio Engine | Fingerprint Generation | ≤ 5 seconds | 3s warning, 5s critical |
| API | Total Processing Time | ≤ 10 seconds | 5s warning, 10s critical |
| Database | Query Response Time | ≤ 3 seconds | 1s warning, 3s critical |
| System | CPU Usage | Normal operation | 70% warning, 90% critical |
| System | Memory Usage | Normal operation | 80% warning, 95% critical |
| System | Disk Usage | Normal operation | 85% warning, 95% critical |

## Installation

### Prerequisites

```bash
# Required packages
pip install psutil

# Optional packages for full functionality
pip install flask requests
```

### Database Setup

Enable `pg_stat_statements` for query analysis:

```sql
-- Add to postgresql.conf
shared_preload_libraries = 'pg_stat_statements'
pg_stat_statements.track = all

-- Restart PostgreSQL and run:
CREATE EXTENSION pg_stat_statements;
```

## Integration

### With FastAPI Application

Add performance monitoring to your FastAPI app:

```python
from monitoring.system_monitor import SystemMonitor, ApplicationMetricsCollector
from monitoring.performance_profiler import PerformanceProfiler

# Initialize monitoring
monitor = SystemMonitor()
app_metrics = ApplicationMetricsCollector(monitor)
profiler = PerformanceProfiler()

# Start monitoring
monitor.start_monitoring()
profiler.start_monitoring()

# In your API endpoints
@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    processing_time = (time.time() - start_time) * 1000
    app_metrics.record_api_response_time(
        request.url.path, 
        processing_time
    )
    
    return response
```

### With Audio Processing

```python
from monitoring.performance_profiler import AudioProcessingProfiler

profiler = PerformanceProfiler()
audio_profiler = AudioProcessingProfiler(profiler)

# Profile fingerprint generation
result = audio_profiler.profile_fingerprint_generation(
    audio_data, sample_rate, channels
)
```

### With Database Operations

```python
from monitoring.performance_profiler import DatabaseProfiler

db_profiler = DatabaseProfiler(profiler)

# Profile database queries
result = db_profiler.profile_fingerprint_search(
    fingerprints, min_matches=5
)
```

## Alerting

### Email Alerts

Configure SMTP settings in the monitor configuration:

```json
{
  "email_alerts": {
    "enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "username": "your-email@gmail.com",
    "password": "your-app-password",
    "from_email": "monitor@yourcompany.com",
    "to_emails": ["admin@yourcompany.com", "ops@yourcompany.com"]
  }
}
```

### Webhook Alerts

Send alerts to external systems (Slack, PagerDuty, etc.):

```json
{
  "webhook_alerts": {
    "enabled": true,
    "url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

### Custom Alert Handlers

```python
def custom_alert_handler(alert):
    if alert.severity == 'critical':
        # Send to PagerDuty
        send_to_pagerduty(alert)
    elif alert.component == 'database':
        # Log to database monitoring system
        log_to_db_monitor(alert)

monitor.add_alert_handler(custom_alert_handler)
```

## Deployment

### Production Monitoring

1. **System Monitor as Service**
   ```bash
   # Create systemd service
   sudo cp monitoring/audio-fingerprinting-monitor.service /etc/systemd/system/
   sudo systemctl enable audio-fingerprinting-monitor
   sudo systemctl start audio-fingerprinting-monitor
   ```

2. **Dashboard as Service**
   ```bash
   # Run dashboard with gunicorn
   pip install gunicorn
   gunicorn -w 2 -b 0.0.0.0:5000 monitoring.monitoring_dashboard:app
   ```

3. **Automated Reports**
   ```bash
   # Add to crontab for daily reports
   0 6 * * * /path/to/python monitoring/database_optimizer.py --report /var/log/db_report_$(date +\%Y\%m\%d).json
   ```

### Docker Integration

Add monitoring to your Docker Compose:

```yaml
services:
  monitor:
    build: .
    command: python monitoring/system_monitor.py --daemon
    volumes:
      - ./logs:/app/logs
      - ./monitoring/config.json:/app/config.json
    depends_on:
      - api
      - database

  dashboard:
    build: .
    command: python monitoring/monitoring_dashboard.py --host 0.0.0.0
    ports:
      - "5000:5000"
    depends_on:
      - monitor
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Ensure proper permissions for log files
   chmod 755 logs/
   chmod 644 logs/*.log
   ```

2. **Database Connection Issues**
   ```bash
   # Test database connectivity
   python -c "from monitoring.database_optimizer import DatabaseOptimizer; DatabaseOptimizer().get_table_statistics()"
   ```

3. **High Memory Usage**
   ```bash
   # Reduce metrics retention
   # In config: "metrics_retention_hours": 6
   ```

4. **Missing Dependencies**
   ```bash
   # Install all optional dependencies
   pip install psutil flask requests
   ```

### Performance Tuning

1. **Reduce Monitoring Overhead**
   - Increase monitoring interval: `"monitoring_interval": 60`
   - Reduce metrics retention: `"metrics_retention_hours": 12`

2. **Optimize Database Monitoring**
   - Enable `pg_stat_statements` properly
   - Ensure database user has necessary permissions
   - Run `ANALYZE` regularly for accurate statistics

3. **Scale Monitoring**
   - Use separate monitoring database
   - Implement metrics aggregation
   - Use external monitoring systems (Prometheus, Grafana)

## Best Practices

1. **Monitoring Strategy**
   - Monitor key business metrics (identification success rate)
   - Set up cascading alerts (warning → critical)
   - Use appropriate alert cooldowns to avoid spam

2. **Performance Optimization**
   - Profile regularly during development
   - Monitor production performance continuously
   - Optimize based on actual usage patterns

3. **Alerting**
   - Test alert delivery regularly
   - Document alert response procedures
   - Use different channels for different severities

4. **Data Retention**
   - Keep detailed metrics for recent periods
   - Aggregate older data for long-term trends
   - Regular cleanup of old alerts and metrics

## Integration with External Systems

### Prometheus Integration

```python
# Export metrics to Prometheus format
from prometheus_client import Counter, Histogram, Gauge

api_requests = Counter('api_requests_total', 'Total API requests')
response_time = Histogram('api_response_time_seconds', 'API response time')
system_cpu = Gauge('system_cpu_percent', 'CPU usage percentage')
```

### Grafana Dashboards

Create Grafana dashboards for:
- System resource utilization
- API performance metrics
- Database query performance
- Alert status and trends

### Log Aggregation

Integrate with ELK stack or similar:
- Forward application logs to Elasticsearch
- Create Kibana dashboards for log analysis
- Set up log-based alerting rules