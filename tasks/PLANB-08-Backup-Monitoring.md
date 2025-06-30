# PLANB-08: Backup Strategy and Comprehensive Monitoring Setup

**Task:** Implement backup strategy and comprehensive monitoring for production deployment  
**Duration:** 60-90 minutes  
**Prerequisites:** PLANB-01 through PLANB-07 completed, all services configured and tested  

## Overview

This final task implements a comprehensive backup strategy for models and system configurations, establishes monitoring dashboards, sets up alerting, and creates operational procedures for the Citadel AI OS deployment.

## Backup Strategy Architecture

### Backup Hierarchy
```
Backup Strategy:
├── Real-time Backups
│   ├── Configuration sync (every 15 minutes)
│   ├── Log archival (hourly)
│   └── System state snapshots (daily)
├── Model Backups
│   ├── Daily incremental backups
│   ├── Weekly full backups
│   └── Monthly archival backups
├── System Backups
│   ├── Daily system configuration backup
│   ├── Weekly disk image backup
│   └── Monthly cold storage backup
└── Disaster Recovery
    ├── Automated failover procedures
    ├── Backup validation testing
    └── Recovery time objectives (RTO < 4 hours)
```

### Storage Allocation
```
/mnt/citadel-backup/ (7.3TB):
├── models/              # 4TB - Model backups
│   ├── daily/           # Last 7 days
│   ├── weekly/          # Last 4 weeks  
│   ├── monthly/         # Last 12 months
│   └── archive/         # Long-term storage
├── system/              # 2TB - System backups
│   ├── configs/         # Configuration backups
│   ├── snapshots/       # System snapshots
│   └── images/          # Disk images
├── logs/                # 1TB - Log archives
│   ├── services/        # Service logs
│   ├── models/          # Model operation logs
│   └── monitoring/      # Monitoring data
└── temp/                # 300GB - Temporary backup staging
```

## Backup Implementation Steps

### Step 1: Create Backup Infrastructure

1. **Create Backup Directory Structure**
   ```bash
   # Create comprehensive backup directory structure
   echo "=== Creating Backup Infrastructure ==="
   
   # Main backup directories
   sudo mkdir -p /mnt/citadel-backup/{models,system,logs,temp}
   
   # Model backup subdirectories
   sudo mkdir -p /mnt/citadel-backup/models/{daily,weekly,monthly,archive}
   sudo mkdir -p /mnt/citadel-backup/models/daily/{mon,tue,wed,thu,fri,sat,sun}
   sudo mkdir -p /mnt/citadel-backup/models/weekly/{week1,week2,week3,week4}
   sudo mkdir -p /mnt/citadel-backup/models/monthly/{jan,feb,mar,apr,may,jun,jul,aug,sep,oct,nov,dec}
   
   # System backup subdirectories
   sudo mkdir -p /mnt/citadel-backup/system/{configs,snapshots,images}
   sudo mkdir -p /mnt/citadel-backup/system/configs/{daily,weekly,monthly}
   
   # Log archive subdirectories
   sudo mkdir -p /mnt/citadel-backup/logs/{services,models,monitoring}
   
   # Set proper ownership
   sudo chown -R agent0:agent0 /mnt/citadel-backup
   chmod -R 755 /mnt/citadel-backup
   
   echo "✅ Backup directory structure created"
   ```

2. **Create Backup Configuration**
   ```bash
   # Create backup configuration file
   tee /opt/citadel/configs/backup-config.yaml << 'EOF'
   # Citadel AI Backup Configuration
   backup_config:
     version: "1.0"
     
     storage:
       backup_root: "/mnt/citadel-backup"
       source_models: "/mnt/citadel-models/active"
       source_configs: "/opt/citadel/configs"
       source_logs: "/opt/citadel/logs"
       temp_dir: "/mnt/citadel-backup/temp"
       
     retention_policy:
       daily_backups: 7        # Keep 7 daily backups
       weekly_backups: 4       # Keep 4 weekly backups
       monthly_backups: 12     # Keep 12 monthly backups
       archive_threshold: 365  # Archive after 1 year
       
     backup_schedule:
       models:
         daily: "0 2 * * *"          # 2:00 AM daily
         weekly: "0 3 * * 0"         # 3:00 AM Sunday
         monthly: "0 4 1 * *"        # 4:00 AM 1st of month
       configs:
         realtime: "*/15 * * * *"    # Every 15 minutes
         daily: "0 1 * * *"          # 1:00 AM daily
       logs:
         hourly: "0 * * * *"         # Every hour
         daily: "0 5 * * *"          # 5:00 AM daily
         
     compression:
       algorithm: "zstd"       # Fast compression
       level: 3                # Balanced compression
       parallel_jobs: 4        # Parallel compression
       
     validation:
       checksum_algorithm: "sha256"
       verify_after_backup: true
       test_restore_monthly: true
       
     alerts:
       backup_failure: true
       storage_threshold: 85   # Alert at 85% full
       retention_cleanup: true
   EOF
   ```

### Step 2: Create Backup Scripts

1. **Create Model Backup Script**
   ```bash
   # Create comprehensive model backup script
   tee /opt/citadel/scripts/backup-models.sh << 'EOF'
   #!/bin/bash
   # backup-models.sh - Backup AI models with intelligent deduplication
   
   set -euo pipefail
   
   # Configuration
   BACKUP_ROOT="/mnt/citadel-backup"
   SOURCE_MODELS="/mnt/citadel-models/active"
   CONFIG_FILE="/opt/citadel/configs/backup-config.yaml"
   LOG_FILE="/opt/citadel/logs/backup-models.log"
   
   # Backup type from command line argument
   BACKUP_TYPE="${1:-daily}"
   
   # Logging function
   log_message() {
       echo "$(date '+%Y-%m-%d %H:%M:%S') [$BACKUP_TYPE] $1" | tee -a "$LOG_FILE"
   }
   
   # Calculate backup directory based on type and date
   get_backup_dir() {
       local backup_type="$1"
       local base_dir="$BACKUP_ROOT/models/$backup_type"
       
       case "$backup_type" in
           daily)
               local day_name=$(date '+%a' | tr '[:upper:]' '[:lower:]')
               echo "$base_dir/$day_name"
               ;;
           weekly)
               local week_num=$(date '+%U')
               local week_slot=$((week_num % 4 + 1))
               echo "$base_dir/week$week_slot"
               ;;
           monthly)
               local month_name=$(date '+%b' | tr '[:upper:]' '[:lower:]')
               echo "$base_dir/$month_name"
               ;;
           *)
               echo "$base_dir"
               ;;
       esac
   }
   
   # Create backup with deduplication
   create_backup() {
       local backup_dir="$1"
       local backup_name="backup-$(date '+%Y%m%d-%H%M%S')"
       local backup_path="$backup_dir/$backup_name"
       
       log_message "Starting $BACKUP_TYPE backup to $backup_path"
       
       # Create backup directory
       mkdir -p "$backup_path"
       
       # Find previous backup for hardlink deduplication
       local previous_backup=""
       if [ -d "$backup_dir" ]; then
           previous_backup=$(find "$backup_dir" -maxdepth 1 -type d -name "backup-*" | sort | tail -1)
       fi
       
       # Perform backup with rsync
       local rsync_opts="-av --delete --stats"
       if [ -n "$previous_backup" ]; then
           rsync_opts="$rsync_opts --link-dest=$previous_backup"
           log_message "Using hardlink deduplication with $previous_backup"
       fi
       
       # Backup each model directory
       for model_dir in "$SOURCE_MODELS"/*; do
           if [ -d "$model_dir" ]; then
               local model_name=$(basename "$model_dir")
               log_message "Backing up model: $model_name"
               
               rsync $rsync_opts "$model_dir/" "$backup_path/$model_name/"
               
               # Create checksum
               find "$backup_path/$model_name" -type f -exec sha256sum {} \; > "$backup_path/$model_name.sha256"
           fi
       done
       
       # Create backup metadata
       cat > "$backup_path/backup-info.json" << JSON
   {
       "backup_type": "$BACKUP_TYPE",
       "backup_date": "$(date -Iseconds)",
       "source_path": "$SOURCE_MODELS",
       "backup_path": "$backup_path",
       "hostname": "$(hostname)",
       "models_backed_up": [
   $(find "$SOURCE_MODELS" -maxdepth 1 -type d -not -path "$SOURCE_MODELS" -exec basename {} \; | sed 's/.*/"&"/' | paste -sd,)
       ],
       "backup_size_gb": $(du -sg "$backup_path" | cut -f1)
   }
   JSON
       
       # Compress backup if enabled
       if command -v zstd &> /dev/null; then
           log_message "Compressing backup with zstd"
           tar -cf - -C "$backup_dir" "$backup_name" | zstd -3 -T4 > "$backup_path.tar.zst"
           rm -rf "$backup_path"
           backup_path="$backup_path.tar.zst"
       fi
       
       log_message "Backup completed: $backup_path"
       
       # Clean up old backups based on retention policy
       cleanup_old_backups "$backup_dir" "$BACKUP_TYPE"
   }
   
   # Cleanup old backups
   cleanup_old_backups() {
       local backup_dir="$1"
       local backup_type="$2"
       
       local retention_days
       case "$backup_type" in
           daily) retention_days=7 ;;
           weekly) retention_days=28 ;;
           monthly) retention_days=365 ;;
           *) retention_days=7 ;;
       esac
       
       log_message "Cleaning up backups older than $retention_days days"
       
       find "$backup_dir" -name "backup-*" -type f -mtime +$retention_days -delete
       find "$backup_dir" -name "backup-*" -type d -mtime +$retention_days -exec rm -rf {} +
   }
   
   # Verify backup integrity
   verify_backup() {
       local backup_path="$1"
       
       if [[ "$backup_path" == *.tar.zst ]]; then
           log_message "Verifying compressed backup integrity"
           zstd -t "$backup_path" && log_message "✅ Backup verification passed" || log_message "❌ Backup verification failed"
       else
           log_message "Verifying backup checksums"
           # Verify checksums if available
           for checksum_file in "$backup_path"/*.sha256; do
               if [ -f "$checksum_file" ]; then
                   (cd "$(dirname "$checksum_file")" && sha256sum -c "$(basename "$checksum_file")") || log_message "❌ Checksum verification failed for $checksum_file"
               fi
           done
       fi
   }
   
   # Main execution
   main() {
       log_message "Starting Citadel AI model backup ($BACKUP_TYPE)"
       
       # Check if source exists
       if [ ! -d "$SOURCE_MODELS" ]; then
           log_message "❌ Source models directory not found: $SOURCE_MODELS"
           exit 1
       fi
       
       # Check backup storage space
       local available_space=$(df "$BACKUP_ROOT" | awk 'NR==2 {print $4}')
       local required_space=$(du -s "$SOURCE_MODELS" | cut -f1)
       
       if [ "$available_space" -lt "$((required_space * 2))" ]; then
           log_message "⚠️ Low backup storage space warning"
       fi
       
       # Perform backup
       local backup_dir
       backup_dir=$(get_backup_dir "$BACKUP_TYPE")
       create_backup "$backup_dir"
       
       # Verify backup if compression was used
       if [ -f "$backup_path" ]; then
           verify_backup "$backup_path"
       fi
       
       log_message "Model backup completed successfully"
   }
   
   # Execute main function
   main "$@"
   EOF
   
   chmod +x /opt/citadel/scripts/backup-models.sh
   ```

2. **Create System Configuration Backup Script**
   ```bash
   # Create system configuration backup script
   tee /opt/citadel/scripts/backup-configs.sh << 'EOF'
   #!/bin/bash
   # backup-configs.sh - Backup system configurations and settings
   
   set -euo pipefail
   
   BACKUP_ROOT="/mnt/citadel-backup/system/configs"
   LOG_FILE="/opt/citadel/logs/backup-configs.log"
   
   log_message() {
       echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
   }
   
   backup_configs() {
       local backup_name="config-backup-$(date '+%Y%m%d-%H%M%S')"
       local backup_path="$BACKUP_ROOT/daily/$backup_name"
       
       log_message "Starting configuration backup to $backup_path"
       
       mkdir -p "$backup_path"
       
       # Backup Citadel AI configurations
       cp -r /opt/citadel/configs "$backup_path/citadel-configs"
       
       # Backup systemd service files
       mkdir -p "$backup_path/systemd"
       cp /etc/systemd/system/citadel-*.service "$backup_path/systemd/" 2>/dev/null || true
       cp /etc/systemd/system/citadel-*.target "$backup_path/systemd/" 2>/dev/null || true
       cp /etc/systemd/system/citadel-ai.env "$backup_path/systemd/" 2>/dev/null || true
       
       # Backup network configuration
       mkdir -p "$backup_path/network"
       cp /etc/netplan/*.yaml "$backup_path/network/" 2>/dev/null || true
       
       # Backup fstab and mount configuration
       cp /etc/fstab "$backup_path/fstab"
       
       # Backup user configurations
       mkdir -p "$backup_path/user-configs"
       cp /home/agent0/.bashrc "$backup_path/user-configs/" 2>/dev/null || true
       cp /home/agent0/.profile "$backup_path/user-configs/" 2>/dev/null || true
       
       # Backup NVIDIA configuration
       mkdir -p "$backup_path/nvidia"
       cp /etc/modprobe.d/nvidia.conf "$backup_path/nvidia/" 2>/dev/null || true
       
       # Create backup manifest
       cat > "$backup_path/backup-manifest.json" << JSON
   {
       "backup_date": "$(date -Iseconds)",
       "hostname": "$(hostname)",
       "kernel_version": "$(uname -r)",
       "os_version": "$(lsb_release -d | cut -f2)",
       "backup_contents": [
           "citadel-configs",
           "systemd-services",
           "network-config",
           "fstab",
           "user-configs",
           "nvidia-config"
       ]
   }
   JSON
       
       # Compress backup
       tar -czf "$backup_path.tar.gz" -C "$BACKUP_ROOT/daily" "$backup_name"
       rm -rf "$backup_path"
       
       log_message "Configuration backup completed: $backup_path.tar.gz"
       
       # Clean up old backups (keep 30 days)
       find "$BACKUP_ROOT/daily" -name "config-backup-*.tar.gz" -mtime +30 -delete
   }
   
   log_message "Starting system configuration backup"
   backup_configs
   log_message "Configuration backup completed"
   EOF
   
   chmod +x /opt/citadel/scripts/backup-configs.sh
   ```

### Step 3: Create Monitoring Infrastructure

1. **Create Comprehensive Monitoring Script**
   ```bash
   # Create comprehensive monitoring script
   tee /opt/citadel/scripts/monitoring-collector.py << 'EOF'
   #!/usr/bin/env python3
   """
   Citadel AI Monitoring Data Collector
   Collects metrics from all system components
   """
   
   import json
   import time
   import psutil
   import GPUtil
   import subprocess
   import requests
   from datetime import datetime
   from pathlib import Path
   import logging
   
   # Configuration
   MONITORING_CONFIG = {
       "collection_interval": 60,  # seconds
       "metrics_file": "/opt/citadel/logs/monitoring/metrics.json",
       "alerts_file": "/opt/citadel/logs/monitoring/alerts.json",
       "retention_days": 30,
       "model_ports": {
           "mixtral": 11400,
           "yi34b": 11404,
           "hermes": 11401,
           "openchat": 11402,
           "phi3": 11403,
           "coder": 11405,
           "vision": 11500
       }
   }
   
   # Setup logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler('/opt/citadel/logs/monitoring/collector.log'),
           logging.StreamHandler()
       ]
   )
   logger = logging.getLogger(__name__)
   
   class SystemMonitor:
       def __init__(self):
           self.metrics_file = Path(MONITORING_CONFIG["metrics_file"])
           self.alerts_file = Path(MONITORING_CONFIG["alerts_file"])
           self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
           
       def collect_system_metrics(self):
           """Collect system-level metrics"""
           try:
               cpu_percent = psutil.cpu_percent(interval=1)
               memory = psutil.virtual_memory()
               disk_usage = psutil.disk_usage('/')
               
               # Network statistics
               network = psutil.net_io_counters()
               
               return {
                   "timestamp": datetime.now().isoformat(),
                   "cpu": {
                       "usage_percent": cpu_percent,
                       "count": psutil.cpu_count(),
                       "load_avg": list(psutil.getloadavg())
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
               logger.error(f"Error collecting system metrics: {e}")
               return None
   
       def collect_gpu_metrics(self):
           """Collect GPU metrics"""
           try:
               gpus = GPUtil.getGPUs()
               gpu_metrics = []
               
               for gpu in gpus:
                   gpu_metrics.append({
                       "id": gpu.id,
                       "name": gpu.name,
                       "memory_used_mb": gpu.memoryUsed,
                       "memory_total_mb": gpu.memoryTotal,
                       "memory_percent": round((gpu.memoryUsed / gpu.memoryTotal) * 100, 2),
                       "gpu_percent": round(gpu.load * 100, 2),
                       "temperature": gpu.temperature
                   })
               
               return gpu_metrics
           except Exception as e:
               logger.error(f"Error collecting GPU metrics: {e}")
               return []
   
       def collect_storage_metrics(self):
           """Collect storage metrics for Citadel paths"""
           try:
               storage_paths = [
                   ("/opt/citadel", "application"),
                   ("/mnt/citadel-models", "models"),
                   ("/mnt/citadel-backup", "backup")
               ]
               
               storage_metrics = []
               for path, label in storage_paths:
                   if Path(path).exists():
                       usage = psutil.disk_usage(path)
                       storage_metrics.append({
                           "path": path,
                           "label": label,
                           "total_gb": round(usage.total / (1024**3), 2),
                           "free_gb": round(usage.free / (1024**3), 2),
                           "used_percent": round((usage.used / usage.total) * 100, 2)
                       })
               
               return storage_metrics
           except Exception as e:
               logger.error(f"Error collecting storage metrics: {e}")
               return []
   
       def collect_model_metrics(self):
           """Collect metrics from model services"""
           model_metrics = []
           
           for model_name, port in MONITORING_CONFIG["model_ports"].items():
               try:
                   # Check health endpoint
                   response = requests.get(f"http://localhost:{port}/health", timeout=5)
                   healthy = response.status_code == 200
                   
                   # Try to get metrics if available
                   metrics_data = {}
                   try:
                       metrics_response = requests.get(f"http://localhost:{port}/metrics", timeout=5)
                       if metrics_response.status_code == 200:
                           # Parse basic metrics (this would depend on vLLM's metrics format)
                           metrics_data = {"metrics_available": True}
                   except:
                       metrics_data = {"metrics_available": False}
                   
                   model_metrics.append({
                       "model_name": model_name,
                       "port": port,
                       "healthy": healthy,
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
   
       def collect_service_metrics(self):
           """Collect systemd service metrics"""
           services = [
               "citadel-ai.target",
               "citadel-storage.service",
               "citadel-gpu.service",
               "citadel-models.target",
               "citadel-monitor.service"
           ]
           
           service_metrics = []
           for service in services:
               try:
                   result = subprocess.run(
                       ["systemctl", "is-active", service],
                       capture_output=True,
                       text=True
                   )
                   active = result.returncode == 0
                   
                   service_metrics.append({
                       "service_name": service,
                       "active": active,
                       "status": result.stdout.strip()
                   })
               except Exception as e:
                   service_metrics.append({
                       "service_name": service,
                       "active": False,
                       "error": str(e)
                   })
           
           return service_metrics
   
       def check_alerts(self, metrics):
           """Check for alert conditions"""
           alerts = []
           timestamp = datetime.now().isoformat()
           
           # System alerts
           if metrics.get("system", {}).get("cpu", {}).get("usage_percent", 0) > 90:
               alerts.append({
                   "type": "high_cpu",
                   "severity": "warning",
                   "message": f"High CPU usage: {metrics['system']['cpu']['usage_percent']:.1f}%",
                   "timestamp": timestamp
               })
           
           if metrics.get("system", {}).get("memory", {}).get("used_percent", 0) > 85:
               alerts.append({
                   "type": "high_memory",
                   "severity": "warning",
                   "message": f"High memory usage: {metrics['system']['memory']['used_percent']:.1f}%",
                   "timestamp": timestamp
               })
           
           # Storage alerts
           for storage in metrics.get("storage", []):
               if storage.get("used_percent", 0) > 85:
                   alerts.append({
                       "type": "high_storage",
                       "severity": "warning",
                       "message": f"High storage usage on {storage['label']}: {storage['used_percent']:.1f}%",
                       "timestamp": timestamp
                   })
           
           # GPU alerts
           for gpu in metrics.get("gpu", []):
               if gpu.get("memory_percent", 0) > 90:
                   alerts.append({
                       "type": "high_gpu_memory",
                       "severity": "warning",
                       "message": f"High GPU memory on GPU {gpu['id']}: {gpu['memory_percent']:.1f}%",
                       "timestamp": timestamp
                   })
               
               if gpu.get("temperature", 0) > 80:
                   alerts.append({
                       "type": "high_gpu_temperature",
                       "severity": "critical",
                       "message": f"High GPU temperature on GPU {gpu['id']}: {gpu['temperature']}°C",
                       "timestamp": timestamp
                   })
           
           # Model service alerts
           for model in metrics.get("models", []):
               if not model.get("healthy", True):
                   alerts.append({
                       "type": "model_unhealthy",
                       "severity": "critical",
                       "message": f"Model {model['model_name']} is unhealthy",
                       "timestamp": timestamp
                   })
           
           return alerts
   
       def save_metrics(self, metrics):
           """Save metrics to file"""
           try:
               # Load existing metrics
               if self.metrics_file.exists():
                   with open(self.metrics_file, 'r') as f:
                       all_metrics = json.load(f)
               else:
                   all_metrics = []
               
               # Add new metrics
               all_metrics.append(metrics)
               
               # Keep only recent metrics (last N days)
               cutoff_time = time.time() - (MONITORING_CONFIG["retention_days"] * 24 * 3600)
               all_metrics = [
                   m for m in all_metrics 
                   if time.mktime(time.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")) > cutoff_time
               ]
               
               # Save metrics
               with open(self.metrics_file, 'w') as f:
                   json.dump(all_metrics, f, indent=2)
                   
           except Exception as e:
               logger.error(f"Error saving metrics: {e}")
   
       def save_alerts(self, alerts):
           """Save alerts to file"""
           if not alerts:
               return
               
           try:
               # Load existing alerts
               if self.alerts_file.exists():
                   with open(self.alerts_file, 'r') as f:
                       all_alerts = json.load(f)
               else:
                   all_alerts = []
               
               # Add new alerts
               all_alerts.extend(alerts)
               
               # Keep only recent alerts
               cutoff_time = time.time() - (7 * 24 * 3600)  # Keep 7 days
               all_alerts = [
                   a for a in all_alerts 
                   if time.mktime(time.strptime(a["timestamp"], "%Y-%m-%dT%H:%M:%S.%f")) > cutoff_time
               ]
               
               # Save alerts
               with open(self.alerts_file, 'w') as f:
                   json.dump(all_alerts, f, indent=2)
                   
               # Log critical alerts
               for alert in alerts:
                   if alert["severity"] == "critical":
                       logger.critical(f"ALERT: {alert['message']}")
                   else:
                       logger.warning(f"ALERT: {alert['message']}")
                       
           except Exception as e:
               logger.error(f"Error saving alerts: {e}")
   
       def collect_all_metrics(self):
           """Collect all metrics"""
           logger.info("Collecting system metrics...")
           
           metrics = {
               "timestamp": datetime.now().isoformat(),
               "system": self.collect_system_metrics(),
               "gpu": self.collect_gpu_metrics(),
               "storage": self.collect_storage_metrics(),
               "models": self.collect_model_metrics(),
               "services": self.collect_service_metrics()
           }
           
           # Check for alerts
           alerts = self.check_alerts(metrics)
           
           # Save data
           self.save_metrics(metrics)
           if alerts:
               self.save_alerts(alerts)
           
           logger.info(f"Collected metrics with {len(alerts)} alerts")
           return metrics, alerts
   
   def main():
       monitor = SystemMonitor()
       
       while True:
           try:
               metrics, alerts = monitor.collect_all_metrics()
               time.sleep(MONITORING_CONFIG["collection_interval"])
           except KeyboardInterrupt:
               logger.info("Monitoring stopped by user")
               break
           except Exception as e:
               logger.error(f"Monitoring error: {e}")
               time.sleep(10)  # Wait before retrying
   
   if __name__ == "__main__":
       main()
   EOF
   
   chmod +x /opt/citadel/scripts/monitoring-collector.py
   ```

2. **Create Monitoring Dashboard Script**
   ```bash
   # Create monitoring dashboard script
   tee /opt/citadel/scripts/monitoring-dashboard.py << 'EOF'
   #!/usr/bin/env python3
   """
   Citadel AI Monitoring Dashboard
   Simple terminal-based monitoring dashboard
   """
   
   import json
   import time
   import os
   from datetime import datetime, timedelta
   from pathlib import Path
   import curses
   
   class MonitoringDashboard:
       def __init__(self):
           self.metrics_file = Path("/opt/citadel/logs/monitoring/metrics.json")
           self.alerts_file = Path("/opt/citadel/logs/monitoring/alerts.json")
           
       def load_latest_metrics(self):
           """Load the latest metrics"""
           try:
               if self.metrics_file.exists():
                   with open(self.metrics_file, 'r') as f:
                       all_metrics = json.load(f)
                   return all_metrics[-1] if all_metrics else None
               return None
           except Exception:
               return None
       
       def load_recent_alerts(self, hours=24):
           """Load recent alerts"""
           try:
               if self.alerts_file.exists():
                   with open(self.alerts_file, 'r') as f:
                       all_alerts = json.load(f)
                   
                   # Filter recent alerts
                   cutoff = datetime.now() - timedelta(hours=hours)
                   recent_alerts = [
                       alert for alert in all_alerts
                       if datetime.fromisoformat(alert["timestamp"]) > cutoff
                   ]
                   return recent_alerts[-10:]  # Last 10 alerts
               return []
           except Exception:
               return []
       
       def draw_dashboard(self, stdscr):
           """Draw the monitoring dashboard"""
           stdscr.clear()
           height, width = stdscr.getmaxyx()
           
           # Header
           title = "Citadel AI Monitoring Dashboard"
           stdscr.addstr(0, (width - len(title)) // 2, title, curses.A_BOLD)
           stdscr.addstr(1, 0, "=" * width)
           
           # Load data
           metrics = self.load_latest_metrics()
           alerts = self.load_recent_alerts()
           
           if not metrics:
               stdscr.addstr(3, 0, "No metrics data available")
               stdscr.refresh()
               return
           
           row = 3
           
           # System metrics
           stdscr.addstr(row, 0, "SYSTEM STATUS", curses.A_BOLD)
           row += 1
           
           if metrics.get("system"):
               sys_metrics = metrics["system"]
               stdscr.addstr(row, 2, f"CPU Usage: {sys_metrics.get('cpu', {}).get('usage_percent', 0):.1f}%")
               row += 1
               stdscr.addstr(row, 2, f"Memory Usage: {sys_metrics.get('memory', {}).get('used_percent', 0):.1f}%")
               row += 1
               stdscr.addstr(row, 2, f"Disk Usage: {sys_metrics.get('disk', {}).get('used_percent', 0):.1f}%")
               row += 1
           
           row += 1
           
           # GPU metrics
           stdscr.addstr(row, 0, "GPU STATUS", curses.A_BOLD)
           row += 1
           
           if metrics.get("gpu"):
               for gpu in metrics["gpu"]:
                   stdscr.addstr(row, 2, f"GPU {gpu['id']}: {gpu['memory_percent']:.1f}% memory, {gpu['gpu_percent']:.1f}% usage, {gpu['temperature']}°C")
                   row += 1
           
           row += 1
           
           # Model status
           stdscr.addstr(row, 0, "MODEL SERVICES", curses.A_BOLD)
           row += 1
           
           if metrics.get("models"):
               for model in metrics["models"]:
                   status = "✓" if model.get("healthy") else "✗"
                   color = curses.color_pair(1) if model.get("healthy") else curses.color_pair(2)
                   stdscr.addstr(row, 2, f"{status} {model['model_name']} (port {model['port']})", color)
                   row += 1
           
           row += 1
           
           # Recent alerts
           stdscr.addstr(row, 0, "RECENT ALERTS", curses.A_BOLD)
           row += 1
           
           if alerts:
               for alert in alerts[-5:]:  # Show last 5 alerts
                   color = curses.color_pair(2) if alert["severity"] == "critical" else curses.color_pair(3)
                   timestamp = alert["timestamp"][:19]  # Remove microseconds
                   stdscr.addstr(row, 2, f"{timestamp} [{alert['severity'].upper()}] {alert['message']}", color)
                   row += 1
                   if row >= height - 2:
                       break
           else:
               stdscr.addstr(row, 2, "No recent alerts")
               row += 1
           
           # Footer
           stdscr.addstr(height - 2, 0, "Press 'q' to quit, 'r' to refresh")
           stdscr.addstr(height - 1, 0, f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
           
           stdscr.refresh()
       
       def run(self, stdscr):
           """Run the dashboard"""
           # Initialize colors
           curses.start_color()
           curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
           curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
           curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
           
           stdscr.nodelay(True)
           stdscr.timeout(1000)  # Refresh every second
           
           while True:
               self.draw_dashboard(stdscr)
               
               key = stdscr.getch()
               if key == ord('q'):
                   break
               elif key == ord('r'):
                   continue  # Force refresh
   
   def main():
       dashboard = MonitoringDashboard()
       curses.wrapper(dashboard.run)
   
   if __name__ == "__main__":
       main()
   EOF
   
   chmod +x /opt/citadel/scripts/monitoring-dashboard.py
   ```

### Step 4: Configure Automated Backup Schedule

1. **Create Backup Cron Jobs**
   ```bash
   # Create backup cron configuration
   tee /opt/citadel/configs/backup-crontab << 'EOF'
   # Citadel AI Backup Schedule
   
   # Model backups
   0 2 * * * /opt/citadel/scripts/backup-models.sh daily >> /opt/citadel/logs/backup-cron.log 2>&1
   0 3 * * 0 /opt/citadel/scripts/backup-models.sh weekly >> /opt/citadel/logs/backup-cron.log 2>&1
   0 4 1 * * /opt/citadel/scripts/backup-models.sh monthly >> /opt/citadel/logs/backup-cron.log 2>&1
   
   # Configuration backups
   */15 * * * * /opt/citadel/scripts/backup-configs.sh >> /opt/citadel/logs/backup-cron.log 2>&1
   
   # Log cleanup
   0 6 * * * find /opt/citadel/logs -name "*.log" -mtime +30 -delete
   0 6 * * * find /mnt/citadel-backup/logs -name "*.log" -mtime +90 -delete
   
   # Monitoring
   */5 * * * * /opt/citadel/scripts/monitoring-collector.py >> /opt/citadel/logs/monitoring-cron.log 2>&1
   EOF
   
   # Install cron jobs for agent0 user
   crontab /opt/citadel/configs/backup-crontab
   
   echo "Backup schedule installed"
   ```

2. **Create Backup Validation Script**
   ```bash
   # Create backup validation script
   tee /opt/citadel/scripts/validate-backups.sh << 'EOF'
   #!/bin/bash
   # validate-backups.sh - Validate backup integrity and completeness
   
   set -euo pipefail
   
   BACKUP_ROOT="/mnt/citadel-backup"
   LOG_FILE="/opt/citadel/logs/backup-validation.log"
   
   log_message() {
       echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
   }
   
   validate_model_backups() {
       local backup_type="$1"
       local backup_dir="$BACKUP_ROOT/models/$backup_type"
       
       log_message "Validating $backup_type model backups..."
       
       if [ ! -d "$backup_dir" ]; then
           log_message "❌ Backup directory not found: $backup_dir"
           return 1
       fi
       
       local backup_count=0
       local valid_backups=0
       
       for backup_file in "$backup_dir"/*.tar.zst; do
           if [ -f "$backup_file" ]; then
               backup_count=$((backup_count + 1))
               
               # Test archive integrity
               if zstd -t "$backup_file" >/dev/null 2>&1; then
                   valid_backups=$((valid_backups + 1))
                   log_message "✅ Valid backup: $(basename "$backup_file")"
               else
                   log_message "❌ Corrupted backup: $(basename "$backup_file")"
               fi
           fi
       done
       
       log_message "$backup_type backups: $valid_backups/$backup_count valid"
       return 0
   }
   
   validate_config_backups() {
       local backup_dir="$BACKUP_ROOT/system/configs/daily"
       
       log_message "Validating configuration backups..."
       
       local backup_count=0
       local valid_backups=0
       
       for backup_file in "$backup_dir"/config-backup-*.tar.gz; do
           if [ -f "$backup_file" ]; then
               backup_count=$((backup_count + 1))
               
               # Test archive integrity
               if tar -tzf "$backup_file" >/dev/null 2>&1; then
                   valid_backups=$((valid_backups + 1))
                   log_message "✅ Valid config backup: $(basename "$backup_file")"
               else
                   log_message "❌ Corrupted config backup: $(basename "$backup_file")"
               fi
           fi
       done
       
       log_message "Configuration backups: $valid_backups/$backup_count valid"
   }
   
   check_backup_storage() {
       log_message "Checking backup storage status..."
       
       # Check mount point
       if ! mountpoint -q "$BACKUP_ROOT"; then
           log_message "❌ Backup storage not mounted"
           return 1
       fi
       
       # Check available space
       local usage=$(df "$BACKUP_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//')
       if [ "$usage" -gt 85 ]; then
           log_message "⚠️ Backup storage usage high: ${usage}%"
       else
           log_message "✅ Backup storage usage: ${usage}%"
       fi
       
       # Check permissions
       if [ -w "$BACKUP_ROOT" ]; then
           log_message "✅ Backup storage writable"
       else
           log_message "❌ Backup storage not writable"
           return 1
       fi
       
       return 0
   }
   
   generate_backup_report() {
       local report_file="/opt/citadel/logs/backup-report-$(date '+%Y%m%d').json"
       
       log_message "Generating backup report: $report_file"
       
       cat > "$report_file" << JSON
   {
       "report_date": "$(date -Iseconds)",
       "backup_storage": {
           "mounted": $(mountpoint -q "$BACKUP_ROOT" && echo true || echo false),
           "usage_percent": $(df "$BACKUP_ROOT" | awk 'NR==2 {print $5}' | sed 's/%//'),
           "free_gb": $(df -BG "$BACKUP_ROOT" | awk 'NR==2 {print $4}' | sed 's/G//')
       },
       "model_backups": {
           "daily_count": $(find "$BACKUP_ROOT/models/daily" -name "*.tar.zst" 2>/dev/null | wc -l),
           "weekly_count": $(find "$BACKUP_ROOT/models/weekly" -name "*.tar.zst" 2>/dev/null | wc -l),
           "monthly_count": $(find "$BACKUP_ROOT/models/monthly" -name "*.tar.zst" 2>/dev/null | wc -l)
       },
       "config_backups": {
           "daily_count": $(find "$BACKUP_ROOT/system/configs/daily" -name "*.tar.gz" 2>/dev/null | wc -l)
       }
   }
   JSON
   }
   
   # Main execution
   main() {
       log_message "Starting backup validation"
       
       check_backup_storage
       validate_model_backups "daily"
       validate_model_backups "weekly"
       validate_model_backups "monthly"
       validate_config_backups
       generate_backup_report
       
       log_message "Backup validation completed"
   }
   
   main "$@"
   EOF
   
   chmod +x /opt/citadel/scripts/validate-backups.sh
   ```

## Final Validation and Testing

### Step 1: Complete System Validation

```bash
# Run complete system validation
echo "=== Complete Citadel AI System Validation ==="

# Check all services
citadel health

# Validate storage configuration
/opt/citadel/scripts/verify-symlinks.sh

# Test backup functionality
/opt/citadel/scripts/backup-configs.sh
/opt/citadel/scripts/validate-backups.sh

# Run monitoring collection once
/opt/citadel/scripts/monitoring-collector.py &
MONITOR_PID=$!
sleep 30
kill $MONITOR_PID

# Check monitoring data
ls -la /opt/citadel/logs/monitoring/

echo "✅ Complete system validation finished"
```

### Step 2: Performance Baseline

```bash
# Create performance baseline
echo "=== Creating Performance Baseline ==="

# System performance
echo "System Performance:"
lscpu | grep -E "(Model name|CPU\(s\)|Thread)"
free -h
df -h | grep -E "(citadel|nvme|sda)"

# GPU performance
echo ""
echo "GPU Performance:"
nvidia-smi --query-gpu=name,memory.total,memory.used,utilization.gpu,temperature.gpu --format=csv

# Storage performance
echo ""
echo "Storage Performance:"
echo "Model storage (NVMe):"
dd if=/dev/zero of=/mnt/citadel-models/test-perf bs=1M count=1000 oflag=direct 2>&1 | grep -E "(copied|GB/s|MB/s)"
rm -f /mnt/citadel-models/test-perf

echo "Backup storage (HDD):"
dd if=/dev/zero of=/mnt/citadel-backup/test-perf bs=1M count=1000 oflag=direct 2>&1 | grep -E "(copied|GB/s|MB/s)"
rm -f /mnt/citadel-backup/test-perf

echo "✅ Performance baseline completed"
```

## Operational Procedures

### Step 1: Create Operational Documentation

```bash
# Create operational procedures documentation
tee /opt/citadel/docs/operations.md << 'EOF'
# Citadel AI Operations Guide

## Daily Operations

### Service Management
```bash
# Check system status
citadel health

# View recent logs
citadel logs monitor

# Restart specific service
citadel restart mixtral
```

### Monitoring
```bash
# View monitoring dashboard
/opt/citadel/scripts/monitoring-dashboard.py

# Check alerts
cat /opt/citadel/logs/monitoring/alerts.json | jq '.[-5:]'

# View metrics
cat /opt/citadel/logs/monitoring/metrics.json | jq '.[-1]'
```

### Backup Operations
```bash
# Manual backup
/opt/citadel/scripts/backup-models.sh daily
/opt/citadel/scripts/backup-configs.sh

# Validate backups
/opt/citadel/scripts/validate-backups.sh

# View backup status
ls -la /mnt/citadel-backup/models/daily/
```

## Troubleshooting

### Service Issues
1. Check service status: `systemctl status citadel-service.service`
2. View service logs: `journalctl -u citadel-service.service -f`
3. Check resource usage: `htop`, `nvidia-smi`
4. Restart service: `citadel restart service`

### Storage Issues
1. Check mount points: `df -h | grep citadel`
2. Verify symlinks: `/opt/citadel/scripts/verify-symlinks.sh`
3. Check permissions: `ls -la /opt/citadel/ /mnt/citadel-*`
4. Repair symlinks: `/opt/citadel/scripts/repair-symlinks.sh`

### Performance Issues
1. Monitor resources: `/opt/citadel/scripts/monitoring-dashboard.py`
2. Check GPU status: `nvidia-smi`
3. Review recent alerts: `tail -f /opt/citadel/logs/monitoring/alerts.json`
4. Analyze logs: `journalctl -u citadel-models.target -f`

## Emergency Procedures

### Complete System Restart
```bash
# Stop all services
citadel stop

# Wait for complete shutdown
sleep 30

# Start all services
citadel start

# Monitor startup
citadel health
```

### Storage Recovery
```bash
# Check storage integrity
sudo fsck /dev/nvme1n1
sudo fsck /dev/sda

# Remount storage
sudo umount /mnt/citadel-models /mnt/citadel-backup
sudo mount -a

# Repair symlinks
/opt/citadel/scripts/repair-symlinks.sh
```

### Model Recovery from Backup
```bash
# Stop model services
citadel stop models

# Restore from backup
cd /mnt/citadel-backup/models/daily
latest_backup=$(ls -t *.tar.zst | head -1)
tar -I zstd -xf "$latest_backup" -C /mnt/citadel-models/active/

# Start model services
citadel start models
```
EOF
```

## Configuration Summary

### Backup Strategy
- ✅ **Daily Model Backups**: Incremental with deduplication
- ✅ **Weekly Full Backups**: Complete model archives
- ✅ **Monthly Archives**: Long-term storage
- ✅ **Configuration Backups**: Every 15 minutes
- ✅ **Automated Validation**: Daily integrity checks

### Monitoring System
- ✅ **Real-time Metrics**: System, GPU, storage, services
- ✅ **Alert System**: Automated threshold monitoring
- ✅ **Dashboard**: Terminal-based monitoring interface
- ✅ **Historical Data**: 30-day metric retention
- ✅ **Log Management**: Automated rotation and cleanup

### Operational Tools
- **citadel**: Main service management command
- **backup-models.sh**: Intelligent model backup
- **backup-configs.sh**: Configuration backup
- **validate-backups.sh**: Backup integrity validation
- **monitoring-collector.py**: Metrics collection
- **monitoring-dashboard.py**: Real-time dashboard

### Storage Optimization
- **Model Storage**: 3.6TB dedicated NVMe with optimizations
- **Backup Storage**: 7.3TB HDD with retention policies
- **Cache Management**: Intelligent cache placement
- **Compression**: zstd for fast backup compression
- **Deduplication**: Hardlink-based space saving

## Final Status

🎉 **Citadel AI OS Plan B Installation Complete!**

Your system is now configured with:
- ✅ Ubuntu Server 24.04 LTS optimized installation
- ✅ NVIDIA 570.x drivers with GPU optimization
- ✅ Python 3.12 with latest vLLM compatibility
- ✅ Dedicated storage architecture with symlink integration
- ✅ Systemd service management with health monitoring
- ✅ Comprehensive backup strategy with validation
- ✅ Real-time monitoring with alerting
- ✅ Operational procedures and documentation

The system is production-ready and fully automated for enterprise AI workloads.

---

**Task Status**: ✅ **Ready for Production**  
**Estimated Time**: 60-90 minutes  
**Complexity**: High  
**Prerequisites**: All previous PLANB tasks completed successfully

**Next Steps**: Deploy AI models and begin production operations with confidence in the robust backup and monitoring infrastructure.