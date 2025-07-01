#!/bin/bash
# planb-02-storage-configuration.sh - PLANB-02 Storage Configuration Implementation
# 
# Purpose: Configure dedicated storage for models with symlinks and backup integration
# Author: Citadel AI OS Plan B
# Date: 2025-01-07

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/opt/citadel/logs/planb-02-setup.log"

# Storage devices (detected from current mounts)
NVME_MODEL_DEVICE="/dev/nvme1n1"
BACKUP_DEVICE="/dev/sda"

# Ensure log directory exists
sudo mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "=== PLANB-02 Storage Configuration Started ==="

# Step 1: Install Required Tools and Verify Storage State
log "Step 1: Installing required tools and verifying storage state"

log "Installing required packages..."
sudo apt update
sudo apt install -y sysstat smartmontools tree rsync || {
    log "ERROR: Failed to install required packages"
    exit 1
}

# Verify tools are available
for tool in iostat smartctl tree rsync; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        log "ERROR: $tool not found after installation"
        exit 1
    fi
done

log "✅ All required tools installed successfully"

# Verify current storage configuration
log "Current storage state:"
df -h | grep -E "(citadel|nvme|sda|Filesystem)" | tee -a "$LOG_FILE"
lsblk | tee -a "$LOG_FILE"

# Step 2: Optimize Storage Mount Options
log "Step 2: Optimizing storage mount options"

# Backup current fstab
sudo cp /etc/fstab /etc/fstab.backup-planb02

# Get actual UUIDs
NVME1_UUID=$(sudo blkid "$NVME_MODEL_DEVICE" | grep -o 'UUID="[^"]*"' | cut -d'"' -f2)
SDA_UUID=$(sudo blkid "$BACKUP_DEVICE" | grep -o 'UUID="[^"]*"' | cut -d'"' -f2)

# Validate UUIDs were found
if [ -z "$NVME1_UUID" ]; then
    log "ERROR: Could not get UUID for $NVME_MODEL_DEVICE"
    exit 1
fi

if [ -z "$SDA_UUID" ]; then
    log "ERROR: Could not get UUID for $BACKUP_DEVICE"
    exit 1
fi

log "✅ Model storage UUID: $NVME1_UUID"
log "✅ Backup storage UUID: $SDA_UUID"

# Remove existing citadel entries from fstab to avoid duplicates
sudo sed -i '/citadel/d' /etc/fstab

# Create optimized fstab entries
sudo tee -a /etc/fstab << EOF

# Citadel AI OS Storage Configuration
# Model Storage (NVMe) - Optimized for AI workloads
UUID=$NVME1_UUID /mnt/citadel-models ext4 defaults,noatime,nodiratime,barrier=0,data=writeback 0 2

# Backup Storage (HDD) - Optimized for reliability
UUID=$SDA_UUID /mnt/citadel-backup ext4 defaults,noatime,barrier=1,data=ordered 0 2
EOF

log "✅ Updated fstab with optimized mount options"

# Apply new mount options
log "Applying new mount options..."
sudo umount /mnt/citadel-models 2>/dev/null || echo "Model storage not currently mounted"
sudo umount /mnt/citadel-backup 2>/dev/null || echo "Backup storage not currently mounted"

# Test mount configuration
sudo mount -a || {
    log "ERROR: Mount configuration failed"
    sudo findmnt --verify
    exit 1
}

# Verify new mount options
if mount | grep citadel; then
    log "✅ Storage mounted successfully with optimized options"
else
    log "ERROR: Failed to mount storage with new options"
    exit 1
fi

# Step 3: Create Directory Structure
log "Step 3: Creating directory structure"

# Model storage directory structure
log "Creating model storage directories..."
sudo mkdir -p /mnt/citadel-models/{active,archive,downloads,cache}
sudo mkdir -p /mnt/citadel-models/active/{mixtral-8x7b,yi-34b,nous-hermes-2,openchat-3.5,phi-3-mini,deepcoder-14b,mimo-vl-7b}

# Set proper ownership and permissions for model storage
sudo chown -R agent0:agent0 /mnt/citadel-models
sudo chmod -R 755 /mnt/citadel-models
sudo chmod -R 775 /mnt/citadel-models/downloads
sudo chmod -R 775 /mnt/citadel-models/cache

log "✅ Model storage directory structure created"

# Backup storage directory structure
log "Creating backup storage directories..."
sudo mkdir -p /mnt/citadel-backup/{models,configs,system,logs}
sudo mkdir -p /mnt/citadel-backup/models/{daily,weekly,monthly}
sudo mkdir -p /mnt/citadel-backup/system/{snapshots,archives}

# Set proper ownership and permissions for backup storage
sudo chown -R agent0:agent0 /mnt/citadel-backup
sudo chmod -R 755 /mnt/citadel-backup

log "✅ Backup storage directory structure created"

# Main application directory structure
log "Creating main application directory structure..."
sudo mkdir -p /opt/citadel/{scripts,configs,logs,tmp}

# Set proper ownership
sudo chown -R agent0:agent0 /opt/citadel
sudo chmod -R 755 /opt/citadel
sudo chmod -R 775 /opt/citadel/tmp
sudo chmod -R 775 /opt/citadel/logs

log "✅ Main application directory structure created"

# Step 4: Create Symlink Integration
log "Step 4: Creating symlink integration"

# Create the main models symlink
cd /opt/citadel
ln -sf /mnt/citadel-models/active models

# Create convenience symlinks for individual models
mkdir -p model-links

# Create symlinks for each model
for model in mixtral-8x7b yi-34b nous-hermes-2 openchat-3.5 phi-3-mini deepcoder-14b mimo-vl-7b; do
    ln -sf /mnt/citadel-models/active/$model model-links/$model
done

# Verify symlinks
log "Verifying symlinks:"
ls -la /opt/citadel/models | tee -a "$LOG_FILE"
ls -la /opt/citadel/model-links/ | tee -a "$LOG_FILE"

log "✅ Symlink integration completed"

# Step 5: Configure Storage Optimization
log "Step 5: Configuring storage optimization"

# Enable TRIM for SSD longevity
log "Enabling TRIM for SSD longevity..."
sudo systemctl enable fstrim.timer
sudo systemctl start fstrim.timer

# Configure I/O scheduler for NVMe
NVME_BLOCK_DEVICE=$(basename "$NVME_MODEL_DEVICE")
if [ -f "/sys/block/$NVME_BLOCK_DEVICE/queue/scheduler" ]; then
    echo 'none' | sudo tee "/sys/block/$NVME_BLOCK_DEVICE/queue/scheduler" >/dev/null || {
        log "WARNING: Could not set I/O scheduler for $NVME_BLOCK_DEVICE"
    }
    log "✅ Set I/O scheduler for NVMe to 'none'"
else
    log "WARNING: Scheduler file not found for $NVME_BLOCK_DEVICE"
fi

# Configure I/O scheduler for HDD
BACKUP_BLOCK_DEVICE=$(basename "$BACKUP_DEVICE")
if [ -f "/sys/block/$BACKUP_BLOCK_DEVICE/queue/scheduler" ]; then
    echo 'mq-deadline' | sudo tee "/sys/block/$BACKUP_BLOCK_DEVICE/queue/scheduler" >/dev/null || {
        log "WARNING: Could not set I/O scheduler for $BACKUP_BLOCK_DEVICE"
    }
    log "✅ Set I/O scheduler for HDD to 'mq-deadline'"
else
    log "WARNING: Scheduler file not found for $BACKUP_BLOCK_DEVICE"
fi

# Make I/O scheduler persistent
log "Making I/O scheduler settings persistent..."
sudo tee /etc/udev/rules.d/60-ssd-scheduler.rules << 'EOF' >/dev/null
# Set I/O scheduler for NVMe drives
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"

# Set I/O scheduler for SATA drives
ACTION=="add|change", KERNEL=="sd[a-z]", ATTR{queue/scheduler}="mq-deadline"
EOF

# Reload udev rules
sudo udevadm control --reload-rules

log "✅ I/O scheduler optimization completed"

# File system optimization for model storage
log "Configuring ext4 optimization for model storage..."
MODEL_PARTITION_DEVICE=$(findmnt -nro SOURCE --target /mnt/citadel-models)
if [ -z "$MODEL_PARTITION_DEVICE" ]; then
    log "ERROR: Could not determine partition device for /mnt/citadel-models"
else
    if sudo tune2fs -o journal_data_writeback "$MODEL_PARTITION_DEVICE" 2>/dev/null; then
        log "✅ Configured writeback journaling for model storage ($MODEL_PARTITION_DEVICE)"
    else
        log "WARNING: Could not configure writeback journaling on $MODEL_PARTITION_DEVICE"
    fi
fi

log "✅ Storage optimization completed"

# Step 6: Configure Backup Integration
log "Step 6: Configuring backup integration"

# Create backup configuration script
log "Creating backup configuration script..."
cat > /opt/citadel/scripts/backup-config.sh << 'EOF'
#!/bin/bash
# backup-config.sh - Configure automatic backups

set -euo pipefail

BACKUP_ROOT="/mnt/citadel-backup"
SOURCE_MODELS="/mnt/citadel-models/active"
SOURCE_CONFIGS="/opt/citadel/configs"

# Create backup structure
mkdir -p "$BACKUP_ROOT/models/$(date +%Y/%m)"
mkdir -p "$BACKUP_ROOT/configs/$(date +%Y/%m)"

# Backup active models (incremental)
if [ -d "$SOURCE_MODELS" ] && [ "$(ls -A "$SOURCE_MODELS" 2>/dev/null)" ]; then
    rsync -av --link-dest="$BACKUP_ROOT/models/latest" \
          "$SOURCE_MODELS/" \
          "$BACKUP_ROOT/models/$(date +%Y/%m/%d)/"
    
    # Update latest symlink
    ln -sfn "$BACKUP_ROOT/models/$(date +%Y/%m/%d)" "$BACKUP_ROOT/models/latest"
    echo "Models backup completed: $(date)"
else
    echo "No models found to backup: $(date)"
fi

# Backup configurations
if [ -d "$SOURCE_CONFIGS" ] && [ "$(ls -A "$SOURCE_CONFIGS" 2>/dev/null)" ]; then
    tar -czf "$BACKUP_ROOT/configs/$(date +%Y/%m)/configs-$(date +%Y%m%d-%H%M).tar.gz" \
        -C /opt/citadel configs/
    echo "Configs backup completed: $(date)"
else
    echo "No configs found to backup: $(date)"
fi

echo "Backup completed: $(date)"
EOF

chmod +x /opt/citadel/scripts/backup-config.sh

log "✅ Backup configuration script created"

# Configure automated backups
log "Configuring automated backups..."
BACKUP_CRON="0 2 * * * /opt/citadel/scripts/backup-config.sh >> /opt/citadel/logs/backup.log 2>&1"

# Check if cron job already exists
if ! crontab -l 2>/dev/null | grep -q "backup-config.sh"; then
    (crontab -l 2>/dev/null; echo "$BACKUP_CRON") | crontab -
    log "✅ Added daily backup cron job"
else
    log "Daily backup cron job already exists"
fi

log "✅ Backup integration completed"

log "=== PLANB-02 Storage Configuration Completed Successfully ==="
log "All storage optimization, directory structure, symlinks, and backup integration configured"