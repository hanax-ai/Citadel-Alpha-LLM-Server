#!/usr/bin/env python3
"""
Enhanced Monitoring Data Collector
Extends existing storage_monitor.py with comprehensive metrics collection
"""

import os
import sys
import time
import json
import requests
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from contextlib import contextmanager

# Add configs directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from storage_settings import StorageSettings, load_storage_settings
    from storage_monitor import StorageMonitor
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    print("Please ensure configs/storage_settings.py and scripts/storage_monitor.py exist.")
    sys.exit(1)

# Try to import optional monitoring packages
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import pynvml
    pynvml.nvmlInit()
    PYNVML_AVAILABLE = True
except (ImportError, Exception):
    PYNVML_AVAILABLE = False


@dataclass
class MetricsSnapshot:
    """Comprehensive metrics snapshot"""
    timestamp: str
    system: Optional[Dict[str, Any]]
    gpu: Optional[List[Dict[str, Any]]]
    storage: Optional[List[Dict[str, Any]]]
    models: Optional[List[Dict[str, Any]]]
    services: Optional[List[Dict[str, Any]]]
    alerts: List[Dict[str, Any]]


@dataclass
class AlertCondition:
    """Alert condition definition"""
    alert_type: str
    severity: str
    message: str
    threshold: float
    current_value: float
    timestamp: str


class DependencyChecker:
    """Check monitoring dependencies and provide fallbacks"""
    
    @staticmethod
    def check_monitoring_dependencies() -> Dict[str, bool]:
        """Check availability of monitoring dependencies"""
        return {
            "psutil": PSUTIL_AVAILABLE,
            "pynvml": PYNVML_AVAILABLE,
            "requests": True,  # Should be available
            "json": True       # Built-in
        }
    
    @staticmethod
    def install_missing_dependencies() -> bool:
        """Attempt to install missing dependencies"""
        missing_packages = []
        
        if not PSUTIL_AVAILABLE:
            missing_packages.append("psutil")
        
        if not PYNVML_AVAILABLE:
            missing_packages.append("pynvml")
        
        if missing_packages:
            try:
                import subprocess
                cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result.returncode == 0
            except Exception:
                return False
        
        return True


class SystemMetricsCollector:
    """Focused system metrics collection"""
    
    def __init__(self, settings: StorageSettings):
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.SystemMetrics")
    
    def collect_metrics(self) -> Optional[Dict[str, Any]]:
        """Collect system-level metrics"""
        if not PSUTIL_AVAILABLE:
            self.logger.warning("psutil not available, skipping system metrics")
            return None
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            load_avg = list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # Memory metrics
            memory = psutil.virtual_memory()
            
            # Disk metrics
            disk_usage = psutil.disk_usage('/')
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": cpu_count,
                    "load_avg": load_avg
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "used_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk_usage.total / (1024**3), 2),
                    "free_gb": round(disk_usage.free / (1024**3), 2),
                    "used_percent": round((disk_usage.used / disk_usage.total) * 100, 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            return None


class GPUMetricsCollector:
    """Focused GPU metrics collection"""
    
    def __init__(self, settings: StorageSettings):
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.GPUMetrics")
    
    def collect_metrics(self) -> List[Dict[str, Any]]:
        """Collect GPU metrics"""
        if not PYNVML_AVAILABLE:
            self.logger.warning("pynvml not available, skipping GPU metrics")
            return []
        
        try:
            gpu_metrics = []
            device_count = pynvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                
                # GPU info
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # Memory info
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                
                # Utilization
                utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                
                # Temperature
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                gpu_metrics.append({
                    "id": i,
                    "name": name,
                    "memory_used_mb": memory_info.used // (1024 * 1024),
                    "memory_total_mb": memory_info.total // (1024 * 1024),
                    "memory_percent": round((memory_info.used / memory_info.total) * 100, 2),
                    "gpu_percent": utilization.gpu,
                    "memory_util_percent": utilization.memory,
                    "temperature": temperature
                })
            
            return gpu_metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting GPU metrics: {e}")
            return []


class ModelServiceCollector:
    """Focused model service metrics collection"""
    
    def __init__(self, settings: StorageSettings):
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.ModelService")
    
    def collect_metrics(self) -> List[Dict[str, Any]]:
        """Collect metrics from model services"""
        model_metrics = []
        
        for model_name, port in self.settings.monitoring.model_ports.items():
            try:
                # Check health endpoint
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                healthy = response.status_code == 200
                
                # Try to get additional metrics
                metrics_data = {"metrics_available": False}
                try:
                    metrics_response = requests.get(f"http://localhost:{port}/metrics", timeout=5)
                    if metrics_response.status_code == 200:
                        metrics_data = {"metrics_available": True}
                        # Could parse Prometheus-style metrics here
                except:
                    pass
                
                model_metrics.append({
                    "model_name": model_name,
                    "port": port,
                    "healthy": healthy,
                    "response_time_ms": response.elapsed.total_seconds() * 1000,
                    "timestamp": datetime.now().isoformat(),
                    **metrics_data
                })
                
            except Exception as e:
                model_metrics.append({
                    "model_name": model_name,
                    "port": port,
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
        
        return model_metrics


class AlertManager:
    """Focused alert management"""
    
    def __init__(self, settings: StorageSettings):
        self.settings = settings
        self.logger = logging.getLogger(f"{__name__}.AlertManager")
    
    def check_alerts(self, metrics: MetricsSnapshot) -> List[AlertCondition]:
        """Check for alert conditions"""
        alerts = []
        timestamp = datetime.now().isoformat()
        
        # System alerts
        if metrics.system:
            cpu_usage = metrics.system.get("cpu", {}).get("usage_percent", 0)
            if cpu_usage > (self.settings.monitoring.cpu_usage_warning * 100):
                alerts.append(AlertCondition(
                    alert_type="high_cpu",
                    severity="warning" if cpu_usage < 90 else "critical",
                    message=f"High CPU usage: {cpu_usage:.1f}%",
                    threshold=self.settings.monitoring.cpu_usage_warning * 100,
                    current_value=cpu_usage,
                    timestamp=timestamp
                ))
            
            memory_usage = metrics.system.get("memory", {}).get("used_percent", 0)
            if memory_usage > (self.settings.monitoring.memory_usage_warning * 100):
                alerts.append(AlertCondition(
                    alert_type="high_memory",
                    severity="warning" if memory_usage < 95 else "critical",
                    message=f"High memory usage: {memory_usage:.1f}%",
                    threshold=self.settings.monitoring.memory_usage_warning * 100,
                    current_value=memory_usage,
                    timestamp=timestamp
                ))
        
        # GPU alerts
        if metrics.gpu:
            for gpu in metrics.gpu:
                gpu_memory = gpu.get("memory_percent", 0)
                if gpu_memory > (self.settings.monitoring.gpu_memory_warning * 100):
                    alerts.append(AlertCondition(
                        alert_type="high_gpu_memory",
                        severity="warning" if gpu_memory < 95 else "critical",
                        message=f"High GPU memory on GPU {gpu['id']}: {gpu_memory:.1f}%",
                        threshold=self.settings.monitoring.gpu_memory_warning * 100,
                        current_value=gpu_memory,
                        timestamp=timestamp
                    ))
                
                temperature = gpu.get("temperature", 0)
                if temperature > self.settings.monitoring.gpu_temperature_critical:
                    alerts.append(AlertCondition(
                        alert_type="high_gpu_temperature",
                        severity="critical",
                        message=f"High GPU temperature on GPU {gpu['id']}: {temperature}°C",
                        threshold=self.settings.monitoring.gpu_temperature_critical,
                        current_value=temperature,
                        timestamp=timestamp
                    ))
        
        # Model service alerts
        if metrics.models:
            for model in metrics.models:
                if not model.get("healthy", True):
                    alerts.append(AlertCondition(
                        alert_type="model_unhealthy",
                        severity="critical",
                        message=f"Model {model['model_name']} is unhealthy",
                        threshold=1.0,  # Should be healthy
                        current_value=0.0,  # Is unhealthy
                        timestamp=timestamp
                    ))
        
        return alerts


class EnhancedMonitoringCollector(StorageMonitor):
    """Enhanced monitoring collector extending existing storage monitor"""
    
    def __init__(self, settings: Optional[StorageSettings] = None):
        """Initialize enhanced monitoring collector"""
        super().__init__(settings)
        
        # Initialize specialized collectors
        self.system_collector = SystemMetricsCollector(self.settings)
        self.gpu_collector = GPUMetricsCollector(self.settings) 
        self.model_collector = ModelServiceCollector(self.settings)
        self.alert_manager = AlertManager(self.settings)
        
        # Check dependencies
        self.dependency_checker = DependencyChecker()
        deps = self.dependency_checker.check_monitoring_dependencies()
        
        missing_deps = [dep for dep, available in deps.items() if not available]
        if missing_deps:
            self.logger.warning(f"Missing monitoring dependencies: {missing_deps}")
            # Attempt to install
            if self.dependency_checker.install_missing_dependencies():
                self.logger.info("Successfully installed missing dependencies")
            else:
                self.logger.error("Failed to install missing dependencies")
    
    @contextmanager
    def monitoring_transaction(self, operation_name: str):
        """Context manager for monitoring operations with error handling"""
        start_time = time.time()
        try:
            self.logger.info(f"Starting monitoring operation: {operation_name}")
            yield
            duration = time.time() - start_time
            self.logger.info(f"Completed monitoring operation: {operation_name} in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Monitoring operation failed: {operation_name} after {duration:.2f}s - {e}")
            raise
    
    def collect_comprehensive_metrics(self) -> MetricsSnapshot:
        """Collect comprehensive metrics from all sources"""
        
        with self.monitoring_transaction("comprehensive_metrics_collection"):
            # Collect from all specialized collectors
            system_metrics = self.system_collector.collect_metrics()
            gpu_metrics = self.gpu_collector.collect_metrics()
            storage_metrics = self.collect_storage_metrics()  # From parent StorageMonitor
            model_metrics = self.model_collector.collect_metrics()
            service_metrics = self.collect_service_metrics()
            
            # Create comprehensive snapshot
            snapshot = MetricsSnapshot(
                timestamp=datetime.now().isoformat(),
                system=system_metrics,
                gpu=gpu_metrics,
                storage=storage_metrics,
                models=model_metrics,
                services=service_metrics,
                alerts=[]
            )
            
            # Check for alert conditions
            alerts = self.alert_manager.check_alerts(snapshot)
            snapshot.alerts = [asdict(alert) for alert in alerts]
            
            return snapshot
    
    def export_to_dev_ops_server(self, metrics: MetricsSnapshot) -> bool:
        """Export metrics to dev-ops server"""
        if not self.settings.monitoring.enable_remote_monitoring:
            return True
        
        try:
            dev_ops_url = f"http://{self.settings.monitoring.dev_ops_server}:{self.settings.monitoring.prometheus_port}"
            
            # Convert metrics to Prometheus format (simplified)
            # In practice, you'd use prometheus_client library
            metrics_data = {
                "citadel_metrics": asdict(metrics),
                "timestamp": metrics.timestamp,
                "source": "citadel-ai-192.168.10.35"
            }
            
            # Send to remote monitoring (placeholder)
            # Real implementation would use Prometheus remote_write API
            response = requests.post(
                f"{dev_ops_url}/api/v1/import",
                json=metrics_data,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Failed to export metrics to dev-ops server: {e}")
            return False
    
    def save_metrics_locally(self, metrics: MetricsSnapshot) -> None:
        """Save metrics to local storage"""
        try:
            metrics_file = Path(self.settings.paths.app_logs) / "monitoring" / "metrics.json"
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Load existing metrics
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    all_metrics = json.load(f)
            else:
                all_metrics = []
            
            # Add new metrics
            all_metrics.append(asdict(metrics))
            
            # Keep only recent metrics
            cutoff_time = time.time() - (self.settings.monitoring.metrics_retention_days * 24 * 3600)
            all_metrics = [
                m for m in all_metrics 
                if datetime.fromisoformat(m["timestamp"]).timestamp() > cutoff_time
            ]
            
            # Save metrics
            with open(metrics_file, 'w') as f:
                json.dump(all_metrics, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving metrics locally: {e}")


def main():
    """Enhanced main entry point with single model testing support"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Monitoring Collector")
    parser.add_argument("--interval", type=int, default=60, 
                       help="Collection interval in seconds")
    parser.add_argument("--model", help="Monitor specific model only (for testing)")
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode with single collection")
    parser.add_argument("--export-only", action="store_true",
                       help="Export existing metrics to dev-ops server")
    
    args = parser.parse_args()
    
    try:
        collector = EnhancedMonitoringCollector()
        
        if args.export_only:
            # Export existing metrics to dev-ops server
            metrics_file = Path(collector.settings.paths.app_logs) / "monitoring" / "metrics.json"
            if metrics_file.exists():
                with open(metrics_file, 'r') as f:
                    all_metrics = json.load(f)
                
                if all_metrics:
                    latest_metrics = MetricsSnapshot(**all_metrics[-1])
                    success = collector.export_to_dev_ops_server(latest_metrics)
                    print("✅ Metrics exported successfully" if success else "❌ Export failed")
                else:
                    print("⚠️ No metrics to export")
            else:
                print("❌ No metrics file found")
            return
        
        if args.test_mode:
            # Single collection for testing
            print("=== Test Mode: Single Metrics Collection ===")
            metrics = collector.collect_comprehensive_metrics()
            
            print(f"📊 Collected metrics at {metrics.timestamp}")
            print(f"System metrics: {'✅' if metrics.system else '❌'}")
            print(f"GPU metrics: {'✅' if metrics.gpu else '❌'}")
            print(f"Storage metrics: {'✅' if metrics.storage else '❌'}")
            print(f"Model metrics: {'✅' if metrics.models else '❌'}")
            print(f"Alerts: {len(metrics.alerts)}")
            
            # Save locally
            collector.save_metrics_locally(metrics)
            
            # Export to dev-ops server
            export_success = collector.export_to_dev_ops_server(metrics)
            print(f"Export to dev-ops server: {'✅' if export_success else '❌'}")
            
            return
        
        # Continuous monitoring
        print(f"=== Starting Enhanced Monitoring (interval: {args.interval}s) ===")
        print(f"Dev-ops server: {collector.settings.monitoring.dev_ops_server}")
        print(f"Model monitoring: {len(collector.settings.monitoring.model_ports)} models")
        
        while True:
            try:
                metrics = collector.collect_comprehensive_metrics()
                
                # Save locally
                collector.save_metrics_locally(metrics)
                
                # Export to dev-ops server
                collector.export_to_dev_ops_server(metrics)
                
                # Log summary
                alert_count = len(metrics.alerts)
                if alert_count > 0:
                    collector.logger.warning(f"Collected metrics with {alert_count} alerts")
                else:
                    collector.logger.info("Collected metrics - all systems normal")
                
                time.sleep(args.interval)
                
            except KeyboardInterrupt:
                print("\n⏹️ Monitoring stopped by user")
                break
            except Exception as e:
                collector.logger.error(f"Monitoring error: {e}")
                time.sleep(10)  # Wait before retrying
                
    except Exception as e:
        print(f"❌ Enhanced monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()