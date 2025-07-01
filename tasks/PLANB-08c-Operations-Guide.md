# PLANB-08c: Operations Guide and Procedures

**Task:** Establish operational procedures and maintenance guidelines  
**Duration:** 15-30 minutes  
**Prerequisites:** PLANB-08a and PLANB-08b completed, backup and monitoring configured  

## Overview

This task establishes comprehensive operational procedures for managing the Citadel AI OS deployment, including daily operations, troubleshooting guides, and emergency procedures.

## Daily Operations

### Service Management

```bash
# Check system status
citadel health

# View recent logs
citadel logs monitor

# Restart specific service
citadel restart mixtral

# Check individual model status
systemctl status citadel-phi3.service
```

### Monitoring

```bash
# View monitoring dashboard (local)
/opt/citadel/scripts/monitoring_dashboard.py

# Check alerts
cat /opt/citadel/logs/monitoring/alerts.json | jq '.[-5:]'

# View metrics summary
cat /opt/citadel/logs/monitoring/metrics.json | jq '.[-1]'

# Access remote dashboards (dev-ops server)
# Navigate to: http://192.168.10.36:3000
```

### Backup Operations

```bash
# Manual backup
/opt/citadel/scripts/backup_models.py --type daily --model phi3
/opt/citadel/scripts/backup_configs.py

# Validate backups
/opt/citadel/scripts/backup_manager.py verify /mnt/citadel-backup/models/daily/

# View backup status
ls -la /mnt/citadel-backup/models/daily/
df -h /mnt/citadel-backup
```

### Storage Management

```bash
# Check storage health
/opt/citadel/scripts/storage_manager.py verify-symlinks

# Monitor storage usage
df -h | grep citadel

# Verify model integrity
/opt/citadel/scripts/storage_manager.py verify-prereq
```

## Troubleshooting Guide

### Service Issues

1. **Service Won't Start**
   ```bash
   # Check service status
   systemctl status citadel-mixtral.service
   
   # View service logs
   journalctl -u citadel-mixtral.service -f
   
   # Check resource usage
   htop
   nvidia-smi
   
   # Restart service
   citadel restart mixtral
   ```

2. **Model Loading Failures**
   ```bash
   # Check model paths
   ls -la /opt/citadel/models/
   
   # Verify symlinks
   /opt/citadel/scripts/storage_manager.py verify-symlinks
   
   # Check GPU availability
   nvidia-smi
   
   # Review model logs
   journalctl -u citadel-mixtral.service --since "10 minutes ago"
   ```

3. **Port Conflicts**
   ```bash
   # Check port usage
   netstat -tlnp | grep :1140
   
   # Kill conflicting processes
   pkill -f "vllm.entrypoints.openai.api_server"
   
   # Restart service
   systemctl restart citadel-mixtral.service
   ```

### Storage Issues

1. **Storage Full**
   ```bash
   # Check storage usage
   df -h | grep citadel
   
   # Clean old logs
   find /opt/citadel/logs -name "*.log" -mtime +7 -delete
   
   # Clean old backups
   /opt/citadel/scripts/backup_manager.py cleanup 30
   
   # Check for large temporary files
   find /tmp -size +1G -user agent0
   ```

2. **Broken Symlinks**
   ```bash
   # Verify symlinks
   /opt/citadel/scripts/storage_manager.py verify-symlinks
   
   # Repair broken symlinks
   /opt/citadel/scripts/storage_manager.py repair-symlinks
   
   # Manual symlink recreation
   sudo rm /opt/citadel/models
   sudo ln -sf /mnt/citadel-models/active /opt/citadel/models
   ```

3. **Mount Point Issues**
   ```bash
   # Check mount points
   mount | grep citadel
   mountpoint /mnt/citadel-models
   
   # Remount if needed
   sudo umount /mnt/citadel-models
   sudo mount /mnt/citadel-models
   
   # Check /etc/fstab
   grep citadel /etc/fstab
   ```

### Performance Issues

1. **High Resource Usage**
   ```bash
   # Monitor system resources
   htop
   iotop
   nvidia-smi
   
   # Check GPU memory
   nvidia-smi --query-gpu=memory.used,memory.total --format=csv
   
   # Review monitoring alerts
   cat /opt/citadel/logs/monitoring/alerts.json | jq '.[] | select(.severity=="critical")'
   
   # Restart resource-heavy services
   citadel restart models
   ```

2. **Slow Model Responses**
   ```bash
   # Test model endpoints
   curl -X POST http://localhost:11403/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "phi3", "messages": [{"role": "user", "content": "test"}]}'
   
   # Check model logs for errors
   journalctl -u citadel-phi3.service --since "5 minutes ago"
   
   # Monitor GPU utilization
   watch -n 1 nvidia-smi
   ```

### Network Issues

1. **Service Connectivity**
   ```bash
   # Test local endpoints
   curl http://localhost:11400/health
   curl http://localhost:11403/health
   
   # Check network configuration
   ip addr show
   netstat -tuln | grep :114
   
   # Test dev-ops server connectivity
   ping 192.168.10.36
   curl http://192.168.10.36:9090/-/healthy
   ```

2. **Monitoring Integration**
   ```bash
   # Test metrics export
   curl http://localhost:8000/metrics/system
   
   # Check remote monitoring
   curl http://192.168.10.36:9090/api/v1/query?query=up
   
   # Verify Grafana dashboards
   curl http://192.168.10.36:3000/api/health
   ```

## Emergency Procedures

### Complete System Restart

```bash
# Emergency stop all services
citadel-rollback emergency

# Wait for complete shutdown
sleep 30

# Verify all processes stopped
ps aux | grep vllm
ps aux | grep citadel

# Start infrastructure services
citadel start storage
citadel start gpu

# Start model services gradually
citadel start phi3
sleep 30
citadel start mixtral
sleep 30
citadel start models

# Verify system health
citadel health
```

### Storage Recovery

```bash
# Check storage integrity
sudo fsck /dev/nvme1n1p1
sudo fsck /dev/sda1

# Emergency remount
sudo umount /mnt/citadel-models /mnt/citadel-backup
sudo mount /mnt/citadel-models
sudo mount /mnt/citadel-backup

# Repair symlinks
/opt/citadel/scripts/storage_manager.py repair-symlinks

# Verify model accessibility
ls -la /opt/citadel/models/
```

### Model Recovery from Backup

```bash
# Stop affected model services
citadel stop models

# Identify latest backup
ls -lt /mnt/citadel-backup/models/daily/

# Restore from backup (example for mixtral)
cd /mnt/citadel-backup/models/daily
latest_backup=$(ls -t *mixtral* | head -1)

# Extract to staging area
mkdir -p /mnt/citadel-models/staging/recovery
tar -I zstd -xf "$latest_backup" -C /mnt/citadel-models/staging/recovery/

# Verify backup integrity
/opt/citadel/scripts/backup_manager.py verify "/mnt/citadel-models/staging/recovery"

# Replace active model (if verified)
mv /mnt/citadel-models/active/Mixtral-8x7B-Instruct-v0.1 /mnt/citadel-models/staging/backup-$(date +%Y%m%d)
mv /mnt/citadel-models/staging/recovery/Mixtral-8x7B-Instruct-v0.1 /mnt/citadel-models/active/

# Restart model services
citadel start models
```

### Monitoring Recovery

```bash
# Restart local monitoring
systemctl restart citadel-monitor.service

# Test local metrics collection
curl http://localhost:8000/metrics/system

# Reconnect to dev-ops server
# Check network connectivity
ping 192.168.10.36

# Restart metrics export
systemctl restart prometheus-node-exporter
systemctl restart citadel-metrics-exporter

# Verify dashboard connectivity
curl http://192.168.10.36:3000/api/health
```

## Maintenance Procedures

### Weekly Maintenance

```bash
# Weekly maintenance checklist
echo "=== Weekly Maintenance $(date) ==="

# Update system packages
sudo apt update && sudo apt upgrade -y

# Check disk usage
df -h | grep -E "(citadel|nvme|sda)"

# Validate all backups
/opt/citadel/scripts/backup_manager.py validate-all

# Check service health
citadel health

# Review monitoring alerts
grep -E "(critical|warning)" /opt/citadel/logs/monitoring/alerts.json

# Clean old logs
find /opt/citadel/logs -name "*.log" -mtime +7 -delete

# Verify GPU health
nvidia-smi --query-gpu=temperature.gpu,power.draw,memory.used --format=csv

echo "Weekly maintenance completed"
```

### Monthly Maintenance

```bash
# Monthly maintenance checklist
echo "=== Monthly Maintenance $(date) ==="

# Archive old backups
/opt/citadel/scripts/backup_manager.py archive --older-than 30

# Performance baseline check
/opt/citadel/scripts/performance_baseline.py

# Review and rotate logs
logrotate -f /etc/logrotate.d/citadel-ai

# Check storage health (SMART)
sudo smartctl -a /dev/nvme1n1
sudo smartctl -a /dev/sda

# Update monitoring dashboards
curl -X POST http://192.168.10.36:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @/opt/citadel/monitoring/dashboards/citadel-overview.json

# Generate monthly report
/opt/citadel/scripts/generate_monthly_report.py

echo "Monthly maintenance completed"
```

## Configuration Summary

### Operational Tools
- **citadel**: Main service management command
- **citadel-deploy**: Incremental deployment management
- **citadel-rollback**: Emergency rollback and backup system
- **storage_manager.py**: Storage and symlink management
- **backup_manager.py**: Backup operations and validation
- **monitoring tools**: Local and remote monitoring integration

### Key Directories
- `/opt/citadel/`: Application root
- `/opt/citadel/logs/`: System and service logs
- `/mnt/citadel-models/`: Model storage
- `/mnt/citadel-backup/`: Backup storage
- `/opt/citadel/configs/`: Configuration files
- `/opt/citadel/scripts/`: Management scripts

### Important Files
- `/opt/citadel/configs/storage_settings.py`: Main configuration
- `/opt/citadel/logs/monitoring/metrics.json`: Current metrics
- `/opt/citadel/logs/monitoring/alerts.json`: System alerts
- `/mnt/citadel-backup/backup_metadata.json`: Backup information

### Network Endpoints
- **Local Models**: `http://192.168.10.35:11400-11405`, `11500`
- **Local Monitoring**: `http://192.168.10.35:8000-8001`
- **Remote Dashboards**: `http://192.168.10.36:3000` (Grafana)
- **Remote Metrics**: `http://192.168.10.36:9090` (Prometheus)
- **Remote Alerts**: `http://192.168.10.36:9093` (AlertManager)

## Final Status

🎉 **Citadel AI OS Plan B Implementation Complete!**

### Implemented Components
- ✅ **Modular Task Structure**: Split into focused, manageable components
- ✅ **Backup Strategy**: Comprehensive automated backup with validation
- ✅ **Monitoring Infrastructure**: Local collection with remote dashboard integration
- ✅ **Operational Procedures**: Complete troubleshooting and maintenance guides
- ✅ **Error Handling**: Comprehensive error recovery and rollback capabilities
- ✅ **Integration**: Seamless integration with existing project patterns

### Production Ready Features
- **Automated Operations**: Cron-based scheduling and monitoring
- **Disaster Recovery**: Documented procedures with <4 hour RTO
- **Remote Management**: Centralized dashboards on dev-ops server (192.168.10.36)
- **Gradual Deployment**: Safe rollout with single model testing
- **Comprehensive Validation**: Multi-layer testing and verification

---

**Task Status**: ✅ **Ready for Production**  
**Estimated Time**: 15-30 minutes  
**Complexity**: Low  
**Prerequisites**: Backup and monitoring infrastructure completed  
**Integration**: Complete operational framework following project standards