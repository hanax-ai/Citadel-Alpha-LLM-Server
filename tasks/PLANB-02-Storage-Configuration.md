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

### Step 1: Install Required Tools and Verify Storage State

```bash
# Install required tools
echo "=== Installing Required Tools ==="
sudo apt update
sudo apt install -y sysstat smartmontools tree rsync || {
    echo "ERROR: Failed to install required packages"
    exit 1
}

# Verify tools are available
command -v iostat >/dev/null 2>&1 || { echo "ERROR: iostat not found"; exit 1; }
command -v smartctl >/dev/null 2>&1 || { echo "ERROR: smartctl not found"; exit 1; }
command -v tree >/dev/null 2>&1 || { echo "ERROR: tree not found"; exit 1; }
command -v rsync >/dev/null 2>&1 || { echo "ERROR: rsync not found"; exit 1; }

echo "✅ All required tools installed successfully"
echo ""

# Detect available storage devices
echo "=== Storage Device Detection ==="
NVME_MODEL_DEVICE=""
BACKUP_DEVICE=""

# Find secondary NVMe device (not the boot device or LVM physical volume)
PRIMARY_UUIDS=$(awk '/\/mnt\/citadel-models|\/mnt\/citadel-backup|\/ / {print $1}' /etc/fstab | grep -o 'UUID=[^ ]*' | cut -d'=' -f2)
for device in /dev/nvme*n1; do
    if [ -b "$device" ]; then
        # Check if any partition of this device is mounted as / or /boot or is a PV for LVM root
        skip_device=false
        for part in $(ls ${device}p* 2>/dev/null); do
            if mount | grep -q "$part"; then
                skip_device=true
                break
            fi
            # Check if partition UUID matches any primary UUID in fstab
            part_uuid=$(blkid -s UUID -o value "$part" 2>/dev/null)
            if echo "$PRIMARY_UUIDS" | grep -qw "$part_uuid"; then
                skip_device=true
                break
            fi
        done
        if ! $skip_device; then
            NVME_MODEL_DEVICE="$device"
            break
        fi
    fi
done

# Find backup HDD/SSD device
for device in /dev/sd*; do
    if [ -b "$device" ] && [[ "$device" =~ /dev/sd[a-z]$ ]]; then
        if ! mount | grep -q "$device"; then
            BACKUP_DEVICE="$device"
            break
        fi
    fi
done

# Validate device detection
if [ -z "$NVME_MODEL_DEVICE" ]; then
    echo "ERROR: Could not detect secondary NVMe device for model storage"
    echo "Available devices:"
    lsblk
    exit 1
fi

if [ -z "$BACKUP_DEVICE" ]; then
    echo "ERROR: Could not detect backup storage device"
    echo "Available devices:"
    lsblk
    exit 1
fi

echo "✅ Detected model storage device: $NVME_MODEL_DEVICE"
echo "✅ Detected backup storage device: $BACKUP_DEVICE"
echo ""

# Check current storage configuration
echo "=== Current Storage State ==="
df -h
echo ""
lsblk
echo ""
sudo fdisk -l | grep -E "(nvme|sd[a-z])"
echo ""
mount | grep -E "(citadel|nvme|sd[a-z])"
```

### Step 2: Optimize Storage Mount Options

1. **Update /etc/fstab with Optimized Options**
   ```bash
   # Backup current fstab
   sudo cp /etc/fstab /etc/fstab.backup
   
   # Get actual UUIDs using detected devices
   NVME1_UUID=$(sudo blkid "$NVME_MODEL_DEVICE" | grep -o 'UUID="[^"]*"' | cut -d'"' -f2)
   SDA_UUID=$(sudo blkid "$BACKUP_DEVICE" | grep -o 'UUID="[^"]*"' | cut -d'"' -f2)
   
   # Validate UUIDs were found
   if [ -z "$NVME1_UUID" ]; then
       echo "ERROR: Could not get UUID for $NVME_MODEL_DEVICE"
       exit 1
   fi
   
   if [ -z "$SDA_UUID" ]; then
       echo "ERROR: Could not get UUID for $BACKUP_DEVICE"
       exit 1
   fi
   
   echo "✅ Model storage UUID: $NVME1_UUID"
   echo "✅ Backup storage UUID: $SDA_UUID"
   
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
   # Unmount and remount with new options (with error handling)
   sudo umount /mnt/citadel-models 2>/dev/null || echo "Model storage not currently mounted"
   sudo umount /mnt/citadel-backup 2>/dev/null || echo "Backup storage not currently mounted"
   
   # Test mount configuration
   sudo mount -a || {
       echo "ERROR: Mount configuration failed"
       echo "Checking fstab syntax..."
       sudo findmnt --verify
       exit 1
   }
   
   # Verify new mount options
   if mount | grep citadel; then
       echo "✅ Storage mounted successfully with optimized options"
   else
       echo "ERROR: Failed to mount storage with new options"
       exit 1
   fi
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
   
   # Configure I/O scheduler for NVMe (using detected device)
   NVME_BLOCK_DEVICE=$(basename "$NVME_MODEL_DEVICE")
   if [ -f "/sys/block/$NVME_BLOCK_DEVICE/queue/scheduler" ]; then
       echo 'none' | sudo tee "/sys/block/$NVME_BLOCK_DEVICE/queue/scheduler" || {
           echo "WARNING: Could not set I/O scheduler for $NVME_BLOCK_DEVICE"
       }
   else
       echo "WARNING: Scheduler file not found for $NVME_BLOCK_DEVICE"
   fi
   
   # Make I/O scheduler persistent
   sudo tee /etc/udev/rules.d/60-ssd-scheduler.rules << 'EOF'
   # Set I/O scheduler for NVMe drives
   ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
   EOF
   ```

2. **HDD Optimization**
   ```bash
   # Configure I/O scheduler for HDD (using detected device)
   BACKUP_BLOCK_DEVICE=$(basename "$BACKUP_DEVICE")
   if [ -f "/sys/block/$BACKUP_BLOCK_DEVICE/queue/scheduler" ]; then
       echo 'mq-deadline' | sudo tee "/sys/block/$BACKUP_BLOCK_DEVICE/queue/scheduler" || {
           echo "WARNING: Could not set I/O scheduler for $BACKUP_BLOCK_DEVICE"
       }
   else
       echo "WARNING: Scheduler file not found for $BACKUP_BLOCK_DEVICE"
   fi
   
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
   # Configure ext4 optimization for model storage (using correct partition device)
   MODEL_PARTITION_DEVICE=$(findmnt -nro SOURCE --target /mnt/citadel-models)
   if [ -z "$MODEL_PARTITION_DEVICE" ]; then
       echo "ERROR: Could not determine partition device for /mnt/citadel-models"
   else
       if sudo tune2fs -o journal_data_writeback "$MODEL_PARTITION_DEVICE"; then
           echo "✅ Configured writeback journaling for model storage ($MODEL_PARTITION_DEVICE)"
       else
           echo "WARNING: Could not configure writeback journaling on $MODEL_PARTITION_DEVICE"
       fi
   
       if sudo tune2fs -O ^has_journal "$MODEL_PARTITION_DEVICE"; then
           echo "✅ Disabled journaling for maximum performance ($MODEL_PARTITION_DEVICE)"
       else
           echo "WARNING: Could not disable journaling on $MODEL_PARTITION_DEVICE"
       fi
   fi
   
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
   # Create cron jobs for automated backups (prevent duplicates)
   BACKUP_CRON="0 2 * * * /opt/citadel/scripts/backup-config.sh >> /opt/citadel/logs/backup.log 2>&1"
   VERIFY_CRON="0 3 * * 0 /opt/citadel/scripts/verify-models.sh >> /opt/citadel/logs/verify.log 2>&1"
   
   # Check if cron jobs already exist
   if ! crontab -l 2>/dev/null | grep -q "backup-config.sh"; then
       (crontab -l 2>/dev/null; echo "$BACKUP_CRON") | crontab -
       echo "✅ Added daily backup cron job"
   else
       echo "Daily backup cron job already exists"
   fi
   
   if ! crontab -l 2>/dev/null | grep -q "verify-models.sh"; then
       (crontab -l 2>/dev/null; echo "$VERIFY_CRON") | crontab -
       echo "✅ Added weekly model verification cron job"
   else
       echo "Weekly verification cron job already exists"
   fi
   
   # Display current cron jobs
   echo "Current cron jobs:"
   crontab -l 2>/dev/null | grep -E "(backup-config|verify-models)" || echo "No Citadel cron jobs found"
   ```

### Step 7: Create Model Verification Script

1. **Create Model Verification Script**
   ```bash
   sudo tee /opt/citadel/scripts/verify-models.sh << 'EOF'
   #!/bin/bash
   # verify-models.sh - Verify model integrity and storage health
   
   set -euo pipefail
   
   MODELS_DIR="/mnt/citadel-models/active"
   LOG_FILE="/opt/citadel/logs/verify.log"
   
   # Ensure log directory exists
   mkdir -p "$(dirname "$LOG_FILE")"
   
   echo "=== Model Verification Report $(date) ===" | tee -a "$LOG_FILE"
   
   # Check model directory accessibility
   if [ ! -d "$MODELS_DIR" ]; then
       echo "ERROR: Models directory not accessible: $MODELS_DIR" | tee -a "$LOG_FILE"
       exit 1
   fi
   
   # Check available space
   AVAILABLE_SPACE=$(df "$MODELS_DIR" | awk 'NR==2 {print $4}')
   SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024))
   
   echo "Available space: ${SPACE_GB}GB" | tee -a "$LOG_FILE"
   
   if [ "$SPACE_GB" -lt 100 ]; then
       echo "WARNING: Low disk space on model storage" | tee -a "$LOG_FILE"
   fi
   
   # Check model directories
   MODEL_COUNT=0
   for model_dir in "$MODELS_DIR"/*; do
       if [ -d "$model_dir" ]; then
           MODEL_NAME=$(basename "$model_dir")
           MODEL_SIZE=$(du -sh "$model_dir" 2>/dev/null | cut -f1 || echo "Unknown")
           echo "Model: $MODEL_NAME - Size: $MODEL_SIZE" | tee -a "$LOG_FILE"
           ((MODEL_COUNT++))
       fi
   done
   
   echo "Total models found: $MODEL_COUNT" | tee -a "$LOG_FILE"
   
   # Check storage health (if smartctl available)
   if command -v smartctl >/dev/null 2>&1; then
       NVME_DEVICE=$(df "$MODELS_DIR" | awk 'NR==2 {print $1}' | sed 's/p[0-9]*$//')
       if [ -b "$NVME_DEVICE" ]; then
           echo "Storage health check for $NVME_DEVICE:" | tee -a "$LOG_FILE"
           sudo smartctl -H "$NVME_DEVICE" 2>/dev/null | grep -E "(SMART|Health)" | tee -a "$LOG_FILE" || echo "Health check unavailable" | tee -a "$LOG_FILE"
       fi
   fi
   
   echo "Verification completed: $(date)" | tee -a "$LOG_FILE"
   echo "======================================" | tee -a "$LOG_FILE"
   EOF
   
   chmod +x /opt/citadel/scripts/verify-models.sh
   
   # Test the verification script
   echo "Testing model verification script..."
   /opt/citadel/scripts/verify-models.sh
   ```

### Step 8: Performance Monitoring Setup

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
   if command -v iostat >/dev/null 2>&1; then
       iostat -x 1 1 | grep -E "($(basename "$NVME_MODEL_DEVICE")|$(basename "$BACKUP_DEVICE")|Device)" || echo "I/O statistics unavailable"
   else
       echo "iostat not available"
   fi
   echo ""
   
   echo "Storage Temperature (if available):"
   if command -v smartctl >/dev/null 2>&1; then
       sudo smartctl -A "$NVME_MODEL_DEVICE" | grep -i temperature || echo "Temperature monitoring not available"
   else
       echo "smartctl not available"
   fi
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
if command -v tree >/dev/null 2>&1; then
    tree /opt/citadel -L 2 || echo "Could not display /opt/citadel structure"
    tree /mnt/citadel-models -L 2 || echo "Could not display /mnt/citadel-models structure"
    tree /mnt/citadel-backup -L 2 || echo "Could not display /mnt/citadel-backup structure"
else
    echo "tree command not available, using ls -la instead:"
    ls -la /opt/citadel/ || echo "Could not list /opt/citadel"
    ls -la /mnt/citadel-models/ || echo "Could not list /mnt/citadel-models"
    ls -la /mnt/citadel-backup/ || echo "Could not list /mnt/citadel-backup"
fi
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
- Verify filesystem integrity: `sudo fsck $NVME_MODEL_DEVICE` (use detected device)
- Check fstab syntax: `sudo mount -a`
- Validate fstab: `sudo findmnt --verify`

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