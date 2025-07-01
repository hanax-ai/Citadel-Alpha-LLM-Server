# PLANB-08b: Monitoring Infrastructure Setup

**Task:** Implement comprehensive monitoring system for Citadel AI services  
**Duration:** 30-45 minutes  
**Prerequisites:** PLANB-08a completed, backup infrastructure configured  

## Overview

This task implements the monitoring infrastructure for the Citadel AI OS deployment, providing real-time metrics collection, alerting, and dashboard capabilities. All web/UI frontends will be hosted on the dev-ops server at **192.168.10.36**.

## Monitoring Architecture

### Monitoring Components
```
Monitoring Infrastructure:
├── Local Data Collection (192.168.10.35)
│   ├── System Metrics Collector
│   ├── GPU Metrics Collector  
│   ├── Model Service Metrics
│   ├── Storage Health Monitor
│   └── Service Status Monitor
├── Remote Dashboards (192.168.10.36)
│   ├── Prometheus Server
│   ├── Grafana Dashboards
│   ├── Alert Manager
│   └── Web Interface
└── Integration Layer
    ├── Metrics Export to Dev-Ops Server
    ├── Alert Routing
    └── Dashboard Data Source
```

### Data Flow
```
Citadel AI Server (192.168.10.35) → Dev-Ops Server (192.168.10.36)
├── Metrics Collection → Prometheus Remote Write
├── Log Aggregation → Centralized Logging
├── Alert Generation → Alert Manager
└── Health Status → Dashboard Updates
```

## Implementation Steps

### Step 1: Configure Monitoring Settings

Extend the existing [`storage_settings.py`](configs/storage_settings.py) to include monitoring configuration following the project's pydantic pattern.

### Step 2: Create Monitoring Dependencies Validation

1. **Create Dependencies Check Script**
   ```bash
   # Create monitoring dependencies validation
   tee /opt/citadel/scripts/validate_monitoring_deps.py << 'EOF'
   #!/usr/bin/env python3
   """
   Validate monitoring dependencies before setup
   """
   
   import subprocess
   import sys
   from pathlib import Path
   from typing import List, Tuple
   
   # Required Python packages for monitoring
   REQUIRED_PACKAGES = [
       "psutil",
       "requests", 
       "pynvml",  # For GPU monitoring
       "prometheus-client",  # For metrics export
   ]
   
   def check_python_packages() -> List[Tuple[str, bool, str]]:
       """Check if required Python packages are available"""
       results = []
       
       for package in REQUIRED_PACKAGES:
           try:
               __import__(package.replace("-", "_"))
               results.append((package, True, "Available"))
           except ImportError:
               results.append((package, False, "Missing"))
       
       return results
   
   def install_missing_packages(missing_packages: List[str]) -> bool:
       """Install missing packages"""
       if not missing_packages:
           return True
       
       try:
           cmd = [sys.executable, "-m", "pip", "install"] + missing_packages
           result = subprocess.run(cmd, capture_output=True, text=True)
           return result.returncode == 0
       except Exception:
           return False
   
   def main():
       print("=== Monitoring Dependencies Validation ===")
       
       # Check Python packages
       package_results = check_python_packages()
       missing_packages = [pkg for pkg, available, _ in package_results if not available]
       
       print("\nPython Package Status:")
       for package, available, status in package_results:
           status_icon = "✅" if available else "❌"
           print(f"  {status_icon} {package}: {status}")
       
       # Install missing packages
       if missing_packages:
           print(f"\nInstalling missing packages: {missing_packages}")
           if install_missing_packages(missing_packages):
               print("✅ All missing packages installed successfully")
           else:
               print("❌ Failed to install some packages")
               return False
       
       print("\n✅ All monitoring dependencies validated")
       return True
   
   if __name__ == "__main__":
       success = main()
       sys.exit(0 if success else 1)
   EOF
   
   chmod +x /opt/citadel/scripts/validate_monitoring_deps.py
   ```

### Step 3: Create Monitoring Infrastructure

The monitoring system will follow the existing project patterns by extending the current [`storage_monitor.py`](scripts/storage_monitor.py) and integrating with the [`storage_settings.py`](configs/storage_settings.py) configuration.

### Step 4: Configure Remote Monitoring Integration

1. **Create Remote Monitoring Configuration**
   ```bash
   # Create monitoring integration for dev-ops server
   tee /opt/citadel/configs/monitoring-integration.yaml << 'EOF'
   # Monitoring Integration Configuration
   # Connects local monitoring to dev-ops server at 192.168.10.36
   
   remote_monitoring:
     enabled: true
     dev_ops_server: "192.168.10.36"
     
     prometheus:
       remote_write_url: "http://192.168.10.36:9090/api/v1/write"
       scrape_interval: "15s"
       evaluation_interval: "15s"
       
     grafana:
       dashboard_url: "http://192.168.10.36:3000"
       datasource: "prometheus"
       
     alerting:
       alert_manager_url: "http://192.168.10.36:9093"
       webhook_url: "http://192.168.10.36:9093/api/v1/alerts"
   
   local_collection:
     metrics_port: 8000
     health_check_port: 8001
     log_level: "INFO"
     collection_interval: 60
     
     endpoints:
       system_metrics: "/metrics/system"
       gpu_metrics: "/metrics/gpu"
       model_metrics: "/metrics/models"
       storage_metrics: "/metrics/storage"
       service_metrics: "/metrics/services"
   
   model_monitoring:
     ports:
       mixtral: 11400
       hermes: 11401
       openchat: 11402
       phi3: 11403
       yi34b: 11404
       coder: 11405
       vision: 11500
     
     health_endpoints:
       - "/health"
       - "/v1/models"
       - "/metrics"
   EOF
   ```

### Step 5: Create Monitoring Service Integration

The monitoring services will be integrated into the existing systemd service structure from PLANB-07, following the same patterns for consistency.

## Validation Steps

### Step 1: Dependencies Verification

```bash
# Validate monitoring dependencies
echo "=== Monitoring Dependencies Verification ==="

# Check Python packages
/opt/citadel/scripts/validate_monitoring_deps.py

# Verify network connectivity to dev-ops server
ping -c 3 192.168.10.36 && echo "✅ Dev-ops server reachable" || echo "❌ Dev-ops server unreachable"

# Check local ports availability
netstat -tuln | grep -E ":(8000|8001)" && echo "⚠️ Monitoring ports in use" || echo "✅ Monitoring ports available"

echo "Dependencies verification completed"
```

### Step 2: Monitoring Infrastructure Testing

```bash
# Test monitoring infrastructure
echo "=== Monitoring Infrastructure Testing ==="

# Test local metrics collection
curl -s http://localhost:8000/metrics/system > /dev/null && echo "✅ System metrics accessible" || echo "❌ System metrics failed"

# Test remote integration (if dev-ops server configured)
curl -s "http://192.168.10.36:9090/-/healthy" > /dev/null && echo "✅ Prometheus connection OK" || echo "⚠️ Prometheus not accessible"

# Test model service monitoring
for port in 11400 11401 11402 11403 11404 11405 11500; do
    if curl -s "http://localhost:${port}/health" > /dev/null 2>&1; then
        echo "✅ Model service on port ${port} monitored"
    fi
done

echo "Monitoring infrastructure testing completed"
```

### Step 3: Gradual Monitoring Rollout

```bash
# Gradual monitoring rollout testing
echo "=== Gradual Monitoring Rollout ==="

# Test with single model first (phi3 - lightweight)
echo "Testing monitoring with Phi-3 model..."
if systemctl is-active --quiet citadel-phi3.service; then
    # Monitor for 60 seconds
    timeout 60 /opt/citadel/scripts/monitoring_collector.py --model phi3 --test-mode
    echo "✅ Single model monitoring test completed"
else
    echo "⚠️ Phi-3 service not running, skipping single model test"
fi

# Test metrics export
echo "Testing metrics export to dev-ops server..."
curl -X POST "http://192.168.10.36:9090/api/v1/write" \
    -H "Content-Type: application/x-protobuf" \
    --data-binary "@/opt/citadel/logs/monitoring/test-metrics.pb" \
    > /dev/null 2>&1 && echo "✅ Metrics export test passed" || echo "⚠️ Metrics export test failed"

echo "Gradual rollout testing completed"
```

## Integration Points

### Existing Project Integration

- **Configuration**: Extends [`StorageMonitoringSettings`](configs/storage_settings.py:200) in `storage_settings.py`
- **Base Monitoring**: Builds upon existing [`storage_monitor.py`](scripts/storage_monitor.py)
- **Service Management**: Integrates with systemd services from PLANB-07
- **Testing Framework**: Uses [`tests/storage/`](tests/storage/) patterns for monitoring tests
- **Logging**: Follows established logging patterns from [`storage_manager.py`](scripts/storage_manager.py)

### Error Handling Strategy

Following the project's error handling patterns from [`storage_manager.py`](scripts/storage_manager.py:90):

```python
# Monitoring operations will use transaction-based error handling
@contextmanager
def monitoring_transaction(operation_name: str):
    """Context manager for monitoring operations with rollback"""
    rollback_actions = []
    try:
        logger.info(f"Starting monitoring operation: {operation_name}")
        yield rollback_actions
        logger.info(f"Completed monitoring operation: {operation_name}")
    except Exception as e:
        logger.error(f"Monitoring operation failed: {operation_name} - {e}")
        # Execute rollback actions
        for action in reversed(rollback_actions):
            try:
                action()
            except Exception as rollback_error:
                logger.error(f"Monitoring rollback failed: {rollback_error}")
        raise
```

## Configuration Summary

### Monitoring Features
- ✅ **Multi-dimensional Metrics**: System, GPU, storage, and service monitoring
- ✅ **Remote Integration**: Seamless connection to dev-ops server (192.168.10.36)
- ✅ **Real-time Alerts**: Threshold-based alerting with severity levels
- ✅ **Service Discovery**: Automatic model service detection and monitoring
- ✅ **Error Recovery**: Comprehensive error handling with rollback capabilities

### Dev-Ops Server Integration
- **Prometheus**: Remote metrics storage and querying
- **Grafana**: Dashboard hosting and visualization
- **Alert Manager**: Centralized alerting and notification
- **Web Interface**: Unified monitoring interface

## Next Steps

Continue to **[PLANB-08c-Operations-Guide.md](PLANB-08c-Operations-Guide.md)** for operational procedures and documentation.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 30-45 minutes  
**Complexity**: Medium  
**Prerequisites**: Backup strategy implemented, network connectivity to dev-ops server  
**Integration**: Extends existing monitoring with comprehensive remote integration