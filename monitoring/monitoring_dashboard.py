#!/usr/bin/env python3
"""
Web-based monitoring dashboard for the Audio Fingerprinting System.

This module provides a simple web interface for monitoring system performance,
viewing metrics, and managing alerts.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from flask import Flask, render_template_string, jsonify, request
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

from monitoring.system_monitor import SystemMonitor, ApplicationMetricsCollector
from monitoring.performance_profiler import PerformanceProfiler
from monitoring.database_optimizer import DatabaseOptimizer


class MonitoringDashboard:
    """Web-based monitoring dashboard."""
    
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.app_metrics = ApplicationMetricsCollector(monitor)
        self.profiler = PerformanceProfiler()
        self.db_optimizer = DatabaseOptimizer()
        
        if FLASK_AVAILABLE:
            self.app = Flask(__name__)
            self._setup_routes()
        else:
            self.app = None
    
    def _setup_routes(self):
        """Setup Flask routes for the dashboard."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template_string(DASHBOARD_HTML)
        
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current system metrics."""
            current_metrics = self.monitor.get_current_metrics()
            summary = self.monitor.get_metrics_summary(1)
            
            return jsonify({
                'current': {
                    'timestamp': current_metrics.timestamp if current_metrics else time.time(),
                    'cpu_percent': current_metrics.cpu_percent if current_metrics else 0,
                    'memory_percent': current_metrics.memory_percent if current_metrics else 0,
                    'disk_percent': current_metrics.disk_percent if current_metrics else 0,
                    'process_count': current_metrics.process_count if current_metrics else 0
                },
                'summary': summary
            })
        
        @self.app.route('/api/alerts')
        def get_alerts():
            """Get active alerts."""
            alerts = self.monitor.get_active_alerts()
            return jsonify([
                {
                    'id': alert.id,
                    'timestamp': alert.timestamp,
                    'severity': alert.severity,
                    'component': alert.component,
                    'metric': alert.metric,
                    'value': alert.value,
                    'threshold': alert.threshold,
                    'message': alert.message
                }
                for alert in alerts
            ])
        
        @self.app.route('/api/alerts/<alert_id>/resolve', methods=['POST'])
        def resolve_alert(alert_id):
            """Resolve an alert."""
            self.monitor.resolve_alert(alert_id)
            return jsonify({'status': 'resolved'})
        
        @self.app.route('/api/performance')
        def get_performance():
            """Get performance metrics."""
            app_summary = self.app_metrics.get_application_summary()
            profiler_summary = self.profiler.get_metrics_summary()
            
            return jsonify({
                'application_metrics': app_summary,
                'profiler_metrics': profiler_summary
            })
        
        @self.app.route('/api/database')
        def get_database_stats():
            """Get database statistics."""
            try:
                stats = self.db_optimizer.get_table_statistics()
                suggestions = self.db_optimizer.suggest_optimizations()
                
                return jsonify({
                    'table_statistics': stats,
                    'optimization_suggestions': suggestions[:10]  # Limit to top 10
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/health')
        def health_check():
            """Health check endpoint."""
            return jsonify({
                'status': 'healthy',
                'timestamp': time.time(),
                'monitoring_active': self.monitor._monitoring
            })
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the dashboard web server."""
        if not FLASK_AVAILABLE:
            print("Flask is not available. Install it with: pip install flask")
            return
        
        if not self.monitor._monitoring:
            self.monitor.start_monitoring()
        
        print(f"Starting monitoring dashboard at http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Fingerprinting System - Monitoring Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-title {
            font-size: 14px;
            color: #666;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .metric-unit {
            font-size: 14px;
            color: #666;
        }
        .progress-bar {
            width: 100%;
            height: 8px;
            background-color: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill {
            height: 100%;
            transition: width 0.3s ease;
        }
        .progress-normal { background-color: #4caf50; }
        .progress-warning { background-color: #ff9800; }
        .progress-critical { background-color: #f44336; }
        .alerts-section {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .alert {
            padding: 12px;
            margin: 8px 0;
            border-radius: 4px;
            border-left: 4px solid;
        }
        .alert-critical {
            background-color: #ffebee;
            border-left-color: #f44336;
        }
        .alert-warning {
            background-color: #fff3e0;
            border-left-color: #ff9800;
        }
        .alert-info {
            background-color: #e3f2fd;
            border-left-color: #2196f3;
        }
        .alert-header {
            font-weight: bold;
            margin-bottom: 4px;
        }
        .alert-message {
            font-size: 14px;
            color: #666;
        }
        .alert-time {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
        }
        .resolve-btn {
            background: #4caf50;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 4px;
        }
        .resolve-btn:hover {
            background: #45a049;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-healthy { background-color: #4caf50; }
        .status-warning { background-color: #ff9800; }
        .status-critical { background-color: #f44336; }
        .refresh-info {
            text-align: center;
            color: #666;
            font-size: 14px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Audio Fingerprinting System - Monitoring Dashboard</h1>
            <p>
                <span id="status-indicator" class="status-indicator status-healthy"></span>
                System Status: <span id="system-status">Healthy</span>
                | Last Updated: <span id="last-updated">--</span>
            </p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">CPU Usage</div>
                <div class="metric-value" id="cpu-value">--</div>
                <div class="metric-unit">%</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-normal" id="cpu-progress" style="width: 0%"></div>
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">Memory Usage</div>
                <div class="metric-value" id="memory-value">--</div>
                <div class="metric-unit">%</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-normal" id="memory-progress" style="width: 0%"></div>
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">Disk Usage</div>
                <div class="metric-value" id="disk-value">--</div>
                <div class="metric-unit">%</div>
                <div class="progress-bar">
                    <div class="progress-fill progress-normal" id="disk-progress" style="width: 0%"></div>
                </div>
            </div>

            <div class="metric-card">
                <div class="metric-title">Active Processes</div>
                <div class="metric-value" id="processes-value">--</div>
                <div class="metric-unit">processes</div>
            </div>
        </div>

        <div class="alerts-section">
            <h2>Active Alerts</h2>
            <div id="alerts-container">
                <p>Loading alerts...</p>
            </div>
        </div>

        <div class="refresh-info">
            Dashboard refreshes every 30 seconds
        </div>
    </div>

    <script>
        function updateMetrics() {
            fetch('/api/metrics')
                .then(response => response.json())
                .then(data => {
                    const current = data.current;
                    
                    // Update CPU
                    document.getElementById('cpu-value').textContent = current.cpu_percent.toFixed(1);
                    updateProgressBar('cpu-progress', current.cpu_percent);
                    
                    // Update Memory
                    document.getElementById('memory-value').textContent = current.memory_percent.toFixed(1);
                    updateProgressBar('memory-progress', current.memory_percent);
                    
                    // Update Disk
                    document.getElementById('disk-value').textContent = current.disk_percent.toFixed(1);
                    updateProgressBar('disk-progress', current.disk_percent);
                    
                    // Update Processes
                    document.getElementById('processes-value').textContent = current.process_count;
                    
                    // Update timestamp
                    document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
                })
                .catch(error => {
                    console.error('Error fetching metrics:', error);
                });
        }

        function updateProgressBar(elementId, value) {
            const element = document.getElementById(elementId);
            element.style.width = value + '%';
            
            // Update color based on value
            element.className = 'progress-fill';
            if (value > 90) {
                element.classList.add('progress-critical');
            } else if (value > 70) {
                element.classList.add('progress-warning');
            } else {
                element.classList.add('progress-normal');
            }
        }

        function updateAlerts() {
            fetch('/api/alerts')
                .then(response => response.json())
                .then(alerts => {
                    const container = document.getElementById('alerts-container');
                    
                    if (alerts.length === 0) {
                        container.innerHTML = '<p style="color: #4caf50;">No active alerts</p>';
                        updateSystemStatus('healthy');
                        return;
                    }
                    
                    // Determine overall system status
                    const hasCritical = alerts.some(alert => alert.severity === 'critical');
                    const hasWarning = alerts.some(alert => alert.severity === 'warning');
                    
                    if (hasCritical) {
                        updateSystemStatus('critical');
                    } else if (hasWarning) {
                        updateSystemStatus('warning');
                    } else {
                        updateSystemStatus('healthy');
                    }
                    
                    container.innerHTML = alerts.map(alert => `
                        <div class="alert alert-${alert.severity}">
                            <div class="alert-header">${alert.component.toUpperCase()}: ${alert.metric}</div>
                            <div class="alert-message">${alert.message}</div>
                            <div class="alert-time">
                                ${new Date(alert.timestamp * 1000).toLocaleString()}
                                <button class="resolve-btn" onclick="resolveAlert('${alert.id}')">Resolve</button>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error fetching alerts:', error);
                });
        }

        function updateSystemStatus(status) {
            const indicator = document.getElementById('status-indicator');
            const statusText = document.getElementById('system-status');
            
            indicator.className = 'status-indicator status-' + status;
            
            switch(status) {
                case 'critical':
                    statusText.textContent = 'Critical Issues';
                    break;
                case 'warning':
                    statusText.textContent = 'Warning';
                    break;
                default:
                    statusText.textContent = 'Healthy';
            }
        }

        function resolveAlert(alertId) {
            fetch(`/api/alerts/${alertId}/resolve`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'resolved') {
                    updateAlerts(); // Refresh alerts
                }
            })
            .catch(error => {
                console.error('Error resolving alert:', error);
            });
        }

        // Initial load
        updateMetrics();
        updateAlerts();

        // Refresh every 30 seconds
        setInterval(() => {
            updateMetrics();
            updateAlerts();
        }, 30000);
    </script>
</body>
</html>
"""


def main():
    """Main function for the monitoring dashboard."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring Dashboard for Audio Fingerprinting System')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if not FLASK_AVAILABLE:
        print("Flask is required for the web dashboard.")
        print("Install it with: pip install flask")
        print("\nAlternatively, you can use the command-line monitoring tools:")
        print("  python monitoring/system_monitor.py --status")
        print("  python monitoring/performance_profiler.py")
        print("  python monitoring/database_optimizer.py --analyze")
        return
    
    # Create and start monitor
    monitor = SystemMonitor()
    dashboard = MonitoringDashboard(monitor)
    
    try:
        dashboard.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
    finally:
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()