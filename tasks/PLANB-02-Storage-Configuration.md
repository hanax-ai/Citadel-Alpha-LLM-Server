# PLANB-02: Storage Configuration and Optimization

**Task:** Configure dedicated storage for models with symlinks and backup integration  
**Duration:** 30-45 minutes  
**Prerequisites:** PLANB-01 completed, storage devices recognized  

## Overview

This task configures the storage architecture for Citadel AI OS with dedicated model storage, symlink integration, and backup configuration as specified in the storage map.

## Storage Architecture

### Current Configuration
```
Device Map (Post Ubuntu Installation):
├── nvme0n1 (Primary NVMe - 4TB)
│   ├── nvme0n1p1 (1G vfat)     → /boot/efi
│   ├── nvme0n1p2 (2G ext4)     → /boot  
│   └── nvme0n1p3 (3.9T LVM)    → ubuntu-vg
│       ├── root-lv (200G)      → /
│       ├── home-lv (500G)      → /home
│       ├── opt-lv (1T)         → /opt
│       ├── var-lv (500G)       → /var
│       └── tmp-lv (100G)       → /tmp
├── nvme1n1 (3.6T ext4)         → /mnt/citadel-models
└── sda (7.3T ext4)             → /mnt/citadel-backup
```

### Target Directory Structure
```
/opt/citadel/                   # Main application directory
├── models/                     # Symlink → /mnt/citadel-models/active
├── vllm-env/                   # Python virtual environment
├── scripts/                    # Installation and management scripts
├── configs/                    # Configuration files
├── logs/                       # Application logs
└── tmp/                        # Temporary files

/mnt/citadel-models/            # Dedicated model storage (nvme1n1)
├── active/                     # Active models (symlinked from /opt/citadel/models)
├── archive/                    # Archived/backup models
├── downloads/                  # Temporary download staging
└── cache/                      # Model cache and temporary files

/mnt/citadel-backup/            # Backup storage (sda)
├── models/                     # Model backups
├── configs/                    # Configuration backups
├── system/                     # System backups
└── logs/                       # Log archives
```

## Storage Configuration Steps

### Step 1: Verify Current Storage State

```bash
# Check current storage configuration
echo "=== Current Storage State ==="
df -h
echo ""
lsblk
echo ""
sudo fdisk -l | grep -E "(nvme|sda)"
echo ""
mount | grep -E "(citadel|nvme|sda)"
```

### Step 2: Optimize Storage Mount Options

1. **Update /etc/fstab with Optimized Options**
   ```bash
   # Backup current fstab
   sudo cp /etc/fstab /etc/fstab.backup
   
   # Get actual UUIDs
   NVME1_UUID=$(sudo blkid /dev/nvme1n1 | grep -o 'UUID="[^"]*"' | cut -d'"' -f2)
   SDA_UUID=$(sudo blkid /dev/sda | grep -o 'UUID="[^"]*"' | cut -d'"' -f2)
   
   echo "NVME1 UUID: $NVME1_UUID"
   echo "SDA UUID: $SDA_UUID"
   
   # Create optimized fstab entries
   sudo tee -a /etc/fstab << EOF
   
   # Citadel AI OS Storage Configuration
   # Model Storage (NVMe) - Optimized for AI workloads
   UUID=$NVME1_UUID /mnt/citadel-models ext4 defaults,noatime,nodiratime,barrier=0,data=writeback 0 2
   
   # Backup Storage (HDD) - Optimized for reliability
   UUID=$SDA_UUID /mnt/citadel-backup ext4 defaults,noatime,barrier=1,data=ordered 0 2
   EOF
   ```

2. **Apply New Mount Options**
   ```bash
   # Unmount and remount with new options
   sudo umount /mnt/citadel-models /mnt/citadel-backup
   sudo mount -a
   
   # Verify new mount options
   mount | grep citadel
   ```

### Step 3: Create Directory Structure

1. **Model Storage Directory Structure**
   ```bash
   # Create model storage directories
   sudo mkdir -p /mnt/citadel-models/{active,archive,downloads,cache}
   sudo mkdir -p /mnt/citadel-models/active/{mixtral-8x7b,yi-34b,nous-hermes-2,openchat-3.5,phi-3-mini,deepcoder-14b,mimo-vl-7b}
   
   # Set proper ownership and permissions
   sudo chown -R agent0:agent0 /mnt/citadel-models
   sudo chmod -R 755 /mnt/citadel-models
   sudo chmod -R 775 /mnt/citadel-models/downloads
   sudo chmod -R 775 /mnt/citadel-models/cache
   ```

2. **Backup Storage Directory Structure**
   ```bash
   # Create backup storage directories
   sudo mkdir -p /mnt/citadel-backup/{models,configs,system,logs}
   sudo mkdir -p /mnt/citadel-backup/models/{daily,weekly,monthly}
   sudo mkdir -p /mnt/citadel-backup/system/{snapshots,archives}
   
   # Set proper ownership and permissions
   sudo chown -R agent0:agent0 /mnt/citadel-backup
   sudo chmod -R 755 /mnt/citadel-backup
   ```

3. **Main Application Directory Structure**
   ```bash
   # Create main application directory
   sudo mkdir -p /opt/citadel/{scripts,configs,logs,tmp}
   
   # Set proper ownership
   sudo chown -R agent0:agent0 /opt/citadel
   sudo chmod -R 755 /opt/citadel
   sudo chmod -R 775 /opt/citadel/tmp
   sudo chmod -R 775 /opt/citadel/logs
   ```

### Step 4: Create Symlink Integration

1. **Create Primary Model Symlink**
   ```bash
   # Create the main models symlink
   cd /opt/citadel
   ln -sf /mnt/citadel-models/active models
   
   # Verify symlink
   ls -la /opt/citadel/models
   ls -la /opt/citadel/models/
   ```

2. **Create Individual Model Symlinks**
   ```bash
   # Create convenience symlinks for individual models
   cd /opt/citadel
   mkdir -p model-links
   
   # Create symlinks for each model
   for model in mixtral-8x7b yi-34b nous-hermes-2 openchat-3.5 phi-3-mini deepcoder-14b mimo-vl-7b; do
       ln -sf /mnt/citadel-models/active/$model model-links/$model
   done
   
   # Verify model symlinks
   ls -la /opt/citadel/model-links/
   ```

### Step 5: Configure Storage Optimization

1. **NVMe SSD Optimization**
   ```bash
   # Enable TRIM for SSD longevity
   sudo systemctl enable fstrim.timer
   sudo systemctl start fstrim.timer
   
   # Configure I/O scheduler for NVMe
   echo 'none' | sudo tee /sys/block/nvme1n1/queue/scheduler
   
   # Make I/O scheduler persistent
   sudo tee /etc/udev/rules.d/60-ssd-scheduler.rules << 'EOF'
   # Set I/O scheduler for NVMe drives
   ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
   EOF
   ```

2. **HDD Optimization**
   ```bash
   # Configure I/O scheduler for HDD
   echo 'mq-deadline' | sudo tee /sys/block/sda/queue/scheduler
   
   # Add HDD scheduler rule
   sudo tee -a /etc/udev/rules.d/60-ssd-scheduler.rules << 'EOF'
   # Set I/O scheduler for SATA drives
   ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/scheduler}="mq-deadline"
   EOF
   
   # Reload udev rules
   sudo udevadm control --reload-rules
   ```

3. **File System Optimization**
   ```bash
   # Configure ext4 optimization for model storage
   sudo tune2fs -o journal_data_writeback /dev/nvme1n1
   sudo tune2fs -O ^has_journal /dev/nvme1n1
   
   # Note: This removes journaling for maximum performance
   # Only safe for non-critical data that can be regenerated
   ```

### Step 6: Configure Backup Integration

1. **Create Backup Scripts**
   ```bash
   # Create backup configuration script
   sudo tee /opt/citadel/scripts/backup-config.sh << 'EOF'
   #!/bin/bash
   # backup-config.sh - Configure automatic backups
   
   BACKUP_ROOT="/mnt/citadel-backup"
   SOURCE_MODELS="/mnt/citadel-models/active"
   SOURCE_CONFIGS="/opt/citadel/configs"
   
   # Create backup structure
   mkdir -p "$BACKUP_ROOT/models/$(date +%Y/%m)"
   mkdir -p "$BACKUP_ROOT/configs/$(date +%Y/%m)"
   
   # Backup active models (incremental)
   rsync -av --link-dest="$BACKUP_ROOT/models/latest" \
         "$SOURCE_MODELS/" \
         "$BACKUP_ROOT/models/$(date +%Y/%m/%d)/"
   
   # Update latest symlink
   ln -sfn "$BACKUP_ROOT/models/$(date +%Y/%m/%d)" "$BACKUP_ROOT/models/latest"
   
   # Backup configurations
   tar -czf "$BACKUP_ROOT/configs/$(date +%Y/%m)/configs-$(date +%Y%m%d-%H%M).tar.gz" \
       -C /opt/citadel configs/
   
   echo "Backup completed: $(date)"
   EOF
   
   chmod +x /opt/citadel/scripts/backup-config.sh
   ```

2. **Configure Automated Backups**
   ```bash
   # Create cron job for daily backups
   (crontab -l 2>/dev/null; echo "0 2 * * * /opt/citadel/scripts/backup-config.sh >> /opt/citadel/logs/backup.log 2>&1") | crontab -
   
   # Create weekly model verification
   (crontab -l 2>/dev/null; echo "0 3 * * 0 /opt/citadel/scripts/verify-models.sh >> /opt/citadel/logs/verify.log 2>&1") | crontab -
   ```

### Step 7: Performance Monitoring Setup

1. **Create Storage Monitoring Script**
   ```bash
   sudo tee /opt/citadel/scripts/storage-monitor.sh << 'EOF'
   #!/bin/bash
   # storage-monitor.sh - Monitor storage performance and usage
   
   echo "=== Storage Status Report $(date) ==="
   echo ""
   
   echo "Storage Usage:"
   df -h | grep -E "(citadel|nvme|sda|Filesystem)"
   echo ""
   
   echo "Mount Status:"
   mount | grep citadel
   echo ""
   
   echo "I/O Statistics:"
   iostat -x 1 1 | grep -E "(nvme1n1|sda|Device)"
   echo ""
   
   echo "Storage Temperature (if available):"
   sudo smartctl -A /dev/nvme1n1 | grep -i temperature || echo "Temperature monitoring not available"
   echo ""
   
   echo "Recent I/O Errors:"
   dmesg | tail -20 | grep -i "error\|fail" || echo "No recent I/O errors"
   EOF
   
   chmod +x /opt/citadel/scripts/storage-monitor.sh
   ```

## Validation Steps

### Step 1: Storage Configuration Verification
```bash
# Verify all mounts are active
echo "=== Mount Verification ==="
df -h | grep citadel
echo ""

# Check mount options
mount | grep citadel | grep -E "(noatime|writeback|ordered)"
echo ""

# Verify directory structure
echo "=== Directory Structure ==="
tree /opt/citadel -L 2
tree /mnt/citadel-models -L 2
tree /mnt/citadel-backup -L 2
```

### Step 2: Symlink Verification
```bash
# Test symlink functionality
echo "=== Symlink Testing ==="
ls -la /opt/citadel/models
echo ""

# Test write access through symlinks
touch /opt/citadel/models/test-write.txt
ls -la /mnt/citadel-models/active/test-write.txt
rm /opt/citadel/models/test-write.txt
echo "Symlink write test: PASSED"
```

### Step 3: Performance Testing
```bash
# Test model storage performance
echo "=== Performance Testing ==="
echo "Testing model storage write performance..."
dd if=/dev/zero of=/mnt/citadel-models/cache/test-write bs=1G count=1 oflag=direct
rm /mnt/citadel-models/cache/test-write

echo "Testing backup storage write performance..."
dd if=/dev/zero of=/mnt/citadel-backup/test-write bs=1G count=1 oflag=direct
rm /mnt/citadel-backup/test-write
```

### Step 4: Backup System Testing
```bash
# Test backup functionality
echo "=== Backup System Test ==="
echo "test content" > /opt/citadel/configs/test-config.txt
/opt/citadel/scripts/backup-config.sh
ls -la /mnt/citadel-backup/configs/*/
rm /opt/citadel/configs/test-config.txt
```

## Troubleshooting

### Issue: Mount Failures
**Symptoms**: Storage not mounting, permission errors
**Solutions**:
- Check UUID consistency: `sudo blkid`
- Verify filesystem integrity: `sudo fsck /dev/nvme1n1`
- Check fstab syntax: `sudo mount -a`

### Issue: Symlink Problems
**Symptoms**: Broken symlinks, permission denied
**Solutions**:
- Verify target directory exists: `ls -la /mnt/citadel-models/active`
- Check ownership: `ls -la /opt/citadel/`
- Recreate symlinks: `ln -sf /mnt/citadel-models/active /opt/citadel/models`

### Issue: Performance Issues
**Symptoms**: Slow I/O, high latency
**Solutions**:
- Check I/O scheduler: `cat /sys/block/nvme1n1/queue/scheduler`
- Monitor I/O stats: `iostat -x 1`
- Verify mount options: `mount | grep citadel`

## Configuration Summary

### Optimizations Applied
- ✅ **NVMe Optimization**: No I/O scheduler, writeback journaling
- ✅ **HDD Optimization**: Deadline scheduler, ordered journaling  
- ✅ **Mount Options**: noatime, nodiratime for performance
- ✅ **TRIM Support**: Enabled for SSD longevity
- ✅ **Symlink Integration**: Seamless model access
- ✅ **Backup Strategy**: Automated daily backups
- ✅ **Monitoring**: Performance and health monitoring

### Storage Capacity Allocation
- **Model Storage**: 3.6TB (dedicated NVMe)
- **Backup Storage**: 7.3TB (dedicated HDD)
- **Application Storage**: 1TB (from LVM on primary NVMe)
- **System Storage**: 200GB root + 500GB var (from LVM)

## Next Steps

Continue to **[PLANB-03-NVIDIA-Driver-Setup.md](PLANB-03-NVIDIA-Driver-Setup.md)** for NVIDIA 570.x driver installation and GPU optimization.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 30-45 minutes  
**Complexity**: Medium  
**Prerequisites**: Ubuntu 24.04 installed, storage devices recognized