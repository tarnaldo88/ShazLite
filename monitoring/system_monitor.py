#!/usr/bin/env python3
"""
System monitoring and alerting for the Audio Fingerprinting System.

This module provides comprehensive system monitoring including resource usage,
application metrics, and automated alerting capabilities.

Requirements addressed:
- 2.4: Response time monitoring and alerting
- 4.2: Database performance monitoring
- 4.5: System resource monitoring
"""

import time
import psutil
import threading
import json
import logging
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class Alert:
    """Container for system alerts."""
    id: str
    timestamp: float
    severity: str  # 'info', 'warning', 'critical'
    component: str
    metric: str
    value: float
    threshold: float
    message: str
    resolved: bool = False
    resolved_timestamp: Optional[float] = None


@dataclass
class MetricThreshold:
    """Container for metric threshold configuration."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = 'greater'  # 'greater', 'less', 'equal'
    duration_seconds: float = 60  # How long threshold must be exceeded
    enabled: bool = True


@dataclass
class SystemMetrics:
    """Container for system metrics snapshot."""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: Optional[List[float]] = None


class SystemMonitor:
    """Main system monitoring class."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or self._default_config()
        self.metrics_history: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        self.thresholds: List[MetricThreshold] = self._load_thresholds()
        self.alert_handlers: List[Callable] = []
        
        self._monitoring = False
        self._monitor_thread = None
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _default_config(self) -> Dict[str, Any]:
        """Default monitoring configuration."""
        return {
            'monitoring_interval': 30,  # seconds
            'metrics_retention_hours': 24,
            'alert_cooldown_minutes': 15,
            'email_alerts': {
                'enabled': False,
                'smtp_server': 'localhost',
                'smtp_port': 587,
                'username': '',
                'password': '',
                'from_email': 'monitor@audiofingerprinting.local',
                'to_emails': []
            },
            'webhook_alerts': {
                'enabled': False,
                'url': '',
                'headers': {}
            }
        }
    
    def _load_thresholds(self) -> List[MetricThreshold]:
        """Load metric thresholds configuration."""
        return [
            # CPU thresholds
            MetricThreshold('cpu_percent', 70.0, 90.0, 'greater', 120),
            
            # Memory thresholds
            MetricThreshold('memory_percent', 80.0, 95.0, 'greater', 60),
            
            # Disk thresholds
            MetricThreshold('disk_percent', 85.0, 95.0, 'greater', 300),
            
            # Response time thresholds (will be added by application metrics)
            MetricThreshold('api_response_time_ms', 5000.0, 10000.0, 'greater', 60),
            MetricThreshold('fingerprint_processing_ms', 3000.0, 5000.0, 'greater', 30),
            MetricThreshold('database_query_ms', 1000.0, 3000.0, 'greater', 30),
        ]
    
    def start_monitoring(self):
        """Start system monitoring."""
        if self._monitoring:
            return
        
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
        self.logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """Stop system monitoring."""
        self._monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5.0)
        
        self.logger.info("System monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self._monitoring:
            try:
                # Collect system metrics
                metrics = self._collect_system_metrics()
                self.metrics_history.append(metrics)
                
                # Check thresholds and generate alerts
                self._check_thresholds(metrics)
                
                # Clean up old data
                self._cleanup_old_data()
                
                # Sleep until next monitoring cycle
                time.sleep(self.config['monitoring_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config['monitoring_interval'])
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics
        network = psutil.net_io_counters()
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix-like systems only)
        load_average = None
        try:
            load_average = list(psutil.getloadavg())
        except AttributeError:
            # Windows doesn't have load average
            pass
        
        return SystemMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_available_mb=memory.available / 1024 / 1024,
            disk_percent=disk.percent,
            disk_used_gb=disk.used / 1024 / 1024 / 1024,
            disk_free_gb=disk.free / 1024 / 1024 / 1024,
            network_bytes_sent=network.bytes_sent,
            network_bytes_recv=network.bytes_recv,
            process_count=process_count,
            load_average=load_average
        )
    
    def _check_thresholds(self, metrics: SystemMetrics):
        """Check metrics against thresholds and generate alerts."""
        current_time = time.time()
        
        for threshold in self.thresholds:
            if not threshold.enabled:
                continue
            
            # Get metric value
            metric_value = getattr(metrics, threshold.metric_name, None)
            if metric_value is None:
                continue
            
            # Check threshold
            threshold_exceeded = False
            if threshold.comparison == 'greater':
                threshold_exceeded = metric_value > threshold.critical_threshold
                severity = 'critical'
            elif threshold.comparison == 'less':
                threshold_exceeded = metric_value < threshold.critical_threshold
                severity = 'critical'
            
            # Check warning threshold
            if not threshold_exceeded:
                if threshold.comparison == 'greater':
                    threshold_exceeded = metric_value > threshold.warning_threshold
                elif threshold.comparison == 'less':
                    threshold_exceeded = metric_value < threshold.warning_threshold
                
                if threshold_exceeded:
                    severity = 'warning'
            
            if threshold_exceeded:
                # Check if we need to wait for duration
                if self._check_threshold_duration(threshold, metrics, current_time):
                    self._generate_alert(
                        component='system',
                        metric=threshold.metric_name,
                        value=metric_value,
                        threshold=threshold.critical_threshold if severity == 'critical' else threshold.warning_threshold,
                        severity=severity,
                        message=f"{threshold.metric_name} is {metric_value:.1f} (threshold: {threshold.warning_threshold:.1f})"
                    )
    
    def _check_threshold_duration(self, threshold: MetricThreshold, current_metrics: SystemMetrics, current_time: float) -> bool:
        """Check if threshold has been exceeded for the required duration."""
        if threshold.duration_seconds <= 0:
            return True
        
        # Look back through metrics history
        duration_start = current_time - threshold.duration_seconds
        relevant_metrics = [m for m in self.metrics_history if m.timestamp >= duration_start]
        
        if len(relevant_metrics) < 2:
            return False
        
        # Check if threshold was exceeded for the entire duration
        for metrics in relevant_metrics:
            metric_value = getattr(metrics, threshold.metric_name, None)
            if metric_value is None:
                return False
            
            if threshold.comparison == 'greater':
                if metric_value <= threshold.warning_threshold:
                    return False
            elif threshold.comparison == 'less':
                if metric_value >= threshold.warning_threshold:
                    return False
        
        return True
    
    def _generate_alert(self, component: str, metric: str, value: float, threshold: float, severity: str, message: str):
        """Generate and process an alert."""
        alert_id = f"{component}_{metric}_{int(time.time())}"
        
        # Check for recent similar alerts (cooldown)
        cooldown_seconds = self.config['alert_cooldown_minutes'] * 60
        recent_alerts = [
            a for a in self.alerts 
            if (a.component == component and 
                a.metric == metric and 
                a.timestamp > time.time() - cooldown_seconds and
                not a.resolved)
        ]
        
        if recent_alerts:
            return  # Skip duplicate alert
        
        alert = Alert(
            id=alert_id,
            timestamp=time.time(),
            severity=severity,
            component=component,
            metric=metric,
            value=value,
            threshold=threshold,
            message=message
        )
        
        self.alerts.append(alert)
        self.logger.warning(f"ALERT [{severity.upper()}]: {message}")
        
        # Process alert through handlers
        for handler in self.alert_handlers:
            try:
                handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")
    
    def _cleanup_old_data(self):
        """Clean up old metrics and resolved alerts."""
        current_time = time.time()
        retention_seconds = self.config['metrics_retention_hours'] * 3600
        
        # Clean up old metrics
        cutoff_time = current_time - retention_seconds
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        # Clean up old resolved alerts (keep for 7 days)
        alert_retention_seconds = 7 * 24 * 3600
        alert_cutoff_time = current_time - alert_retention_seconds
        self.alerts = [a for a in self.alerts if a.timestamp > alert_cutoff_time or not a.resolved]
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    def resolve_alert(self, alert_id: str):
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert.id == alert_id and not alert.resolved:
                alert.resolved = True
                alert.resolved_timestamp = time.time()
                self.logger.info(f"Alert resolved: {alert_id}")
                break
    
    def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get the most recent system metrics."""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary statistics for recent metrics."""
        if not self.metrics_history:
            return {}
        
        # Filter metrics for the specified time period
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        # Calculate statistics
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_percent for m in recent_metrics]
        
        return {
            'time_period_hours': hours,
            'sample_count': len(recent_metrics),
            'cpu_percent': {
                'current': cpu_values[-1],
                'average': sum(cpu_values) / len(cpu_values),
                'max': max(cpu_values),
                'min': min(cpu_values)
            },
            'memory_percent': {
                'current': memory_values[-1],
                'average': sum(memory_values) / len(memory_values),
                'max': max(memory_values),
                'min': min(memory_values)
            },
            'disk_percent': {
                'current': disk_values[-1],
                'average': sum(disk_values) / len(disk_values),
                'max': max(disk_values),
                'min': min(disk_values)
            }
        }
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts."""
        return [a for a in self.alerts if not a.resolved]
    
    def export_metrics(self, filename: str, hours: int = 24):
        """Export metrics to JSON file."""
        cutoff_time = time.time() - (hours * 3600)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        data = {
            'export_timestamp': time.time(),
            'time_period_hours': hours,
            'metrics_count': len(recent_metrics),
            'metrics': [
                {
                    'timestamp': m.timestamp,
                    'cpu_percent': m.cpu_percent,
                    'memory_percent': m.memory_percent,
                    'memory_used_mb': m.memory_used_mb,
                    'disk_percent': m.disk_percent,
                    'disk_used_gb': m.disk_used_gb,
                    'process_count': m.process_count,
                    'load_average': m.load_average
                }
                for m in recent_metrics
            ],
            'alerts': [
                {
                    'id': a.id,
                    'timestamp': a.timestamp,
                    'severity': a.severity,
                    'component': a.component,
                    'metric': a.metric,
                    'value': a.value,
                    'threshold': a.threshold,
                    'message': a.message,
                    'resolved': a.resolved,
                    'resolved_timestamp': a.resolved_timestamp
                }
                for a in self.alerts
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)


class ApplicationMetricsCollector:
    """Collector for application-specific metrics."""
    
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.app_metrics: Dict[str, List[float]] = {}
    
    def record_api_response_time(self, endpoint: str, response_time_ms: float):
        """Record API response time metric."""
        if 'api_response_times' not in self.app_metrics:
            self.app_metrics['api_response_times'] = []
        
        self.app_metrics['api_response_times'].append(response_time_ms)
        
        # Check against thresholds
        if response_time_ms > 10000:  # 10 second critical threshold
            self.monitor._generate_alert(
                component='api',
                metric='response_time',
                value=response_time_ms,
                threshold=10000,
                severity='critical',
                message=f"API response time {response_time_ms:.0f}ms exceeds 10s limit on {endpoint}"
            )
        elif response_time_ms > 5000:  # 5 second warning threshold
            self.monitor._generate_alert(
                component='api',
                metric='response_time',
                value=response_time_ms,
                threshold=5000,
                severity='warning',
                message=f"API response time {response_time_ms:.0f}ms exceeds 5s warning on {endpoint}"
            )
    
    def record_fingerprint_processing_time(self, processing_time_ms: float):
        """Record fingerprint processing time metric."""
        if 'fingerprint_processing_times' not in self.app_metrics:
            self.app_metrics['fingerprint_processing_times'] = []
        
        self.app_metrics['fingerprint_processing_times'].append(processing_time_ms)
        
        # Check against fingerprint processing requirements (5 seconds)
        if processing_time_ms > 5000:
            self.monitor._generate_alert(
                component='audio_engine',
                metric='processing_time',
                value=processing_time_ms,
                threshold=5000,
                severity='critical',
                message=f"Fingerprint processing time {processing_time_ms:.0f}ms exceeds 5s requirement"
            )
    
    def record_database_query_time(self, query_type: str, query_time_ms: float):
        """Record database query time metric."""
        metric_key = f'db_query_times_{query_type}'
        if metric_key not in self.app_metrics:
            self.app_metrics[metric_key] = []
        
        self.app_metrics[metric_key].append(query_time_ms)
        
        # Check against database query requirements (3 seconds)
        if query_time_ms > 3000:
            self.monitor._generate_alert(
                component='database',
                metric='query_time',
                value=query_time_ms,
                threshold=3000,
                severity='critical',
                message=f"Database query ({query_type}) time {query_time_ms:.0f}ms exceeds 3s requirement"
            )
    
    def get_application_summary(self) -> Dict[str, Any]:
        """Get summary of application metrics."""
        summary = {}
        
        for metric_name, values in self.app_metrics.items():
            if values:
                summary[metric_name] = {
                    'count': len(values),
                    'average': sum(values) / len(values),
                    'max': max(values),
                    'min': min(values),
                    'recent_average': sum(values[-10:]) / min(len(values), 10)  # Last 10 samples
                }
        
        return summary


def create_email_alert_handler(config: Dict[str, Any]) -> Callable[[Alert], None]:
    """Create an email alert handler."""
    def send_email_alert(alert: Alert):
        if not config.get('enabled', False):
            return
        
        try:
            msg = MimeMultipart()
            msg['From'] = config['from_email']
            msg['To'] = ', '.join(config['to_emails'])
            msg['Subject'] = f"[{alert.severity.upper()}] Audio Fingerprinting Alert: {alert.component}"
            
            body = f"""
Alert Details:
- Component: {alert.component}
- Metric: {alert.metric}
- Value: {alert.value:.2f}
- Threshold: {alert.threshold:.2f}
- Severity: {alert.severity}
- Message: {alert.message}
- Time: {datetime.fromtimestamp(alert.timestamp)}

Alert ID: {alert.id}
            """
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            if config.get('username') and config.get('password'):
                server.starttls()
                server.login(config['username'], config['password'])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
    
    return send_email_alert


def create_webhook_alert_handler(config: Dict[str, Any]) -> Callable[[Alert], None]:
    """Create a webhook alert handler."""
    def send_webhook_alert(alert: Alert):
        if not config.get('enabled', False):
            return
        
        try:
            import requests
            
            payload = {
                'alert_id': alert.id,
                'timestamp': alert.timestamp,
                'severity': alert.severity,
                'component': alert.component,
                'metric': alert.metric,
                'value': alert.value,
                'threshold': alert.threshold,
                'message': alert.message
            }
            
            headers = config.get('headers', {})
            headers['Content-Type'] = 'application/json'
            
            response = requests.post(
                config['url'],
                json=payload,
                headers=headers,
                timeout=10
            )
            
            response.raise_for_status()
            
        except Exception as e:
            logging.error(f"Failed to send webhook alert: {e}")
    
    return send_webhook_alert


def main():
    """Main function for system monitoring."""
    import argparse
    
    parser = argparse.ArgumentParser(description='System Monitor for Audio Fingerprinting')
    parser.add_argument('--config', help='Configuration file path')
    parser.add_argument('--daemon', action='store_true', help='Run as daemon')
    parser.add_argument('--export', help='Export metrics to file')
    parser.add_argument('--status', action='store_true', help='Show current status')
    
    args = parser.parse_args()
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    # Create monitor
    monitor = SystemMonitor(config)
    
    # Setup alert handlers
    if config.get('email_alerts', {}).get('enabled'):
        email_handler = create_email_alert_handler(config['email_alerts'])
        monitor.add_alert_handler(email_handler)
    
    if config.get('webhook_alerts', {}).get('enabled'):
        webhook_handler = create_webhook_alert_handler(config['webhook_alerts'])
        monitor.add_alert_handler(webhook_handler)
    
    if args.status:
        # Show current status
        monitor.start_monitoring()
        time.sleep(5)  # Collect some metrics
        
        current_metrics = monitor.get_current_metrics()
        if current_metrics:
            print("Current System Status:")
            print(f"  CPU: {current_metrics.cpu_percent:.1f}%")
            print(f"  Memory: {current_metrics.memory_percent:.1f}% ({current_metrics.memory_used_mb:.0f}MB used)")
            print(f"  Disk: {current_metrics.disk_percent:.1f}% ({current_metrics.disk_used_gb:.1f}GB used)")
            print(f"  Processes: {current_metrics.process_count}")
        
        active_alerts = monitor.get_active_alerts()
        if active_alerts:
            print(f"\nActive Alerts ({len(active_alerts)}):")
            for alert in active_alerts:
                print(f"  [{alert.severity.upper()}] {alert.component}: {alert.message}")
        else:
            print("\nNo active alerts")
        
        monitor.stop_monitoring()
    
    elif args.export:
        # Export metrics
        monitor.start_monitoring()
        time.sleep(2)  # Brief monitoring to get some data
        monitor.export_metrics(args.export)
        print(f"Metrics exported to: {args.export}")
        monitor.stop_monitoring()
    
    elif args.daemon:
        # Run as daemon
        print("Starting system monitoring daemon...")
        monitor.start_monitoring()
        
        try:
            while True:
                time.sleep(60)
                
                # Print periodic status
                summary = monitor.get_metrics_summary(1)
                if summary:
                    print(f"[{datetime.now()}] CPU: {summary['cpu_percent']['current']:.1f}%, "
                          f"Memory: {summary['memory_percent']['current']:.1f}%, "
                          f"Alerts: {len(monitor.get_active_alerts())}")
        
        except KeyboardInterrupt:
            print("\nShutting down monitor...")
            monitor.stop_monitoring()
    
    else:
        # Interactive mode
        monitor.start_monitoring()
        
        print("System monitor started. Press Ctrl+C to stop.")
        print("Commands: status, alerts, export <file>, quit")
        
        try:
            while True:
                command = input("> ").strip().lower()
                
                if command == "quit":
                    break
                elif command == "status":
                    summary = monitor.get_metrics_summary(1)
                    print(json.dumps(summary, indent=2))
                elif command == "alerts":
                    alerts = monitor.get_active_alerts()
                    for alert in alerts:
                        print(f"[{alert.severity.upper()}] {alert.component}: {alert.message}")
                elif command.startswith("export "):
                    filename = command.split(" ", 1)[1]
                    monitor.export_metrics(filename)
                    print(f"Exported to {filename}")
        
        except KeyboardInterrupt:
            pass
        
        finally:
            monitor.stop_monitoring()


if __name__ == "__main__":
    main()