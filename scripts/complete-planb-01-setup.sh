#!/bin/bash

# =============================================================================
# PLANB-01 Completion Script - Ubuntu Post-Installation Configuration
# =============================================================================
# Purpose: Complete remaining Ubuntu Server 24.04 setup tasks for LLM server
# Usage: sudo ./scripts/complete-planb-01-setup.sh
# Requirements: sudo privileges
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[INFO] $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root (use sudo)"
fi

log "Starting PLANB-01 post-installation configuration..."

# =============================================================================
# Step 1: System Update and Essential Packages
# =============================================================================
log "Step 1: Updating system and installing essential packages..."

apt update && apt upgrade -y

apt install -y \
    curl wget git vim htop tree \
    build-essential cmake \
    software-properties-common \
    apt-transport-https ca-certificates gnupg lsb-release \
    unzip zip p7zip-full \
    net-tools iotop iftop \
    tmux screen \
    python3-pip python3-venv \
    nodejs npm \
    speedtest-cli

log "Essential packages installed successfully"

# =============================================================================
# Step 2: Configure Hana-X Lab Host Mappings
# =============================================================================
log "Step 2: Configuring Hana-X Lab host mappings..."

# Reason: Check if host mappings already exist to avoid duplicates
if ! grep -q "HANA-X LAB" /etc/hosts; then
    cat >> /etc/hosts << 'EOF'

# ───── HANA-X LAB – STATIC HOST MAPPINGS ─────
192.168.10.50    hana-x-jr0          # Windows Admin Workstation (ThinkPad)
192.168.10.33    dev                 # AI Development Node
192.168.10.29    llm                 # LLM Foundation Model Node (current)
192.168.10.30    vectordb            # Vector Database + Embedding Server
192.168.10.31    orca                # Agent Simulation & Orchestration Node
192.168.10.34    qa                  # QA/Test Server
192.168.10.36    dev-ops             # CI/CD + Monitoring Node
192.168.10.35    db                  # PostgreSQL Database Server
192.168.10.19    agent0              # Agent Workstation (Desktop)
EOF
    log "Hana-X Lab host mappings configured"
else
    info "Host mappings already exist, skipping..."
fi

# =============================================================================
# Step 3: Configure Additional Storage
# =============================================================================
log "Step 3: Configuring additional storage..."

# Get current disk UUIDs using robust blkid output
NVME1_UUID=$(blkid -s UUID -o value /dev/nvme1n1 2>/dev/null || echo "")
SDA_UUID=$(blkid -s UUID -o value /dev/sda 2>/dev/null || echo "")

# Format drives if not already formatted
if [[ -z "$NVME1_UUID" ]]; then
    warn "WARNING: /dev/nvme1n1 will be formatted for model storage. This will DESTROY ALL DATA on the device!"
    echo -n "Are you sure you want to format /dev/nvme1n1? (yes/no): "
    read -r CONFIRM_NVME
    if [[ "$CONFIRM_NVME" == "yes" ]]; then
        log "Formatting nvme1n1 for model storage..."
        mkfs.ext4 /dev/nvme1n1 -L "citadel-models"
        NVME1_UUID=$(blkid -s UUID -o value /dev/nvme1n1)
    else
        error "User cancelled nvme1n1 formatting. Cannot continue without storage setup."
    fi
else
    info "nvme1n1 already formatted"
fi

if [[ -z "$SDA_UUID" ]]; then
    warn "WARNING: /dev/sda will be formatted for backup storage. This will DESTROY ALL DATA on the device!"
    echo -n "Are you sure you want to format /dev/sda? (yes/no): "
    read -r CONFIRM_SDA
    if [[ "$CONFIRM_SDA" == "yes" ]]; then
        log "Formatting sda for backup storage..."
        mkfs.ext4 /dev/sda -L "citadel-backup"
        SDA_UUID=$(blkid -s UUID -o value /dev/sda)
    else
        error "User cancelled sda formatting. Cannot continue without storage setup."
    fi
else
    info "sda already formatted"
fi

# Create mount directories
mkdir -p /mnt/citadel-models
mkdir -p /mnt/citadel-backup

# Update fstab if not already present
if ! grep -q "citadel-models" /etc/fstab; then
    cat >> /etc/fstab << EOF

# Citadel AI OS Storage Configuration
UUID=$NVME1_UUID /mnt/citadel-models ext4 defaults,noatime 0 2
UUID=$SDA_UUID /mnt/citadel-backup ext4 defaults,noatime 0 2
EOF
    log "Storage configuration added to fstab"
else
    info "Storage already configured in fstab"
fi

# Mount all filesystems
mount -a

# Verify mounts
if mountpoint -q /mnt/citadel-models && mountpoint -q /mnt/citadel-backup; then
    log "Storage mounted successfully"
else
    warn "Storage mounting may have issues - check manually"
fi

# Set proper ownership
chown agent0:agent0 /mnt/citadel-models
chown agent0:agent0 /mnt/citadel-backup

# =============================================================================
# Step 4: Expand LVM for Root Filesystem
# =============================================================================
log "Step 4: Expanding LVM volumes for better space utilization..."

# Get available space in volume group using machine-readable output
VG_FREE_BYTES=$(vgs --noheadings --units b -o vg_free ubuntu-vg 2>/dev/null | tr -d ' B' || echo "0")

# Check if we have meaningful free space (more than 1GB = 1073741824 bytes)
if [[ "$VG_FREE_BYTES" =~ ^[0-9]+$ ]] && [[ "$VG_FREE_BYTES" -gt 1073741824 ]]; then
    # Extend root logical volume by 500GB if space available
    EXTEND_SIZE="500G"
    log "Extending root volume by $EXTEND_SIZE..."
    
    lvextend -L +$EXTEND_SIZE /dev/ubuntu-vg/ubuntu-lv 2>/dev/null || {
        warn "Could not extend by $EXTEND_SIZE, using all available space"
        lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv
    }
    
    # Resize filesystem
    resize2fs /dev/ubuntu-vg/ubuntu-lv
    log "Root filesystem expanded successfully"
else
    info "No free space available in volume group"
fi

# =============================================================================
# Step 5: System Optimization for AI Workloads
# =============================================================================
log "Step 5: Applying system optimizations for AI workloads..."

# Update GRUB for AI workloads
if ! grep -q "iommu=pt" /etc/default/grub; then
    sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="[^"]*/& iommu=pt intel_iommu=on/' /etc/default/grub
    update-grub
    log "GRUB updated for IOMMU support"
else
    info "GRUB already configured for AI workloads"
fi

# Configure systemd for large workloads
mkdir -p /etc/systemd/system.conf.d
cat > /etc/systemd/system.conf.d/citadel.conf << 'EOF'
[Manager]
DefaultLimitNOFILE=65536
DefaultLimitNPROC=32768
DefaultLimitMEMLOCK=infinity
EOF

log "Systemd configured for large workloads"

# =============================================================================
# Step 6: Security Configuration
# =============================================================================
log "Step 6: Configuring security settings..."

# Configure UFW firewall
ufw --force enable
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow from 192.168.10.0/24

log "Firewall configured for Hana-X Lab network"

# Configure SSH hardening
if ! grep -q "Citadel AI OS SSH Configuration" /etc/ssh/sshd_config; then
    cat >> /etc/ssh/sshd_config << 'EOF'

# Citadel AI OS SSH Configuration
PermitRootLogin no
PasswordAuthentication yes
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
EOF

    systemctl restart ssh
    log "SSH security hardening applied"
else
    info "SSH already configured"
fi

# =============================================================================
# Step 7: Performance Baseline and Validation
# =============================================================================
log "Step 7: Establishing performance baseline..."

# Create performance test script
cat > /tmp/performance_test.sh << 'EOF'
#!/bin/bash
echo "=== CITADEL AI OS - PERFORMANCE BASELINE ==="
echo "Date: $(date)"
echo ""
echo "=== System Information ==="
hostnamectl
echo ""
echo "=== CPU Information ==="
lscpu | grep -E "(Model name|CPU\(s\)|Thread|Socket)"
echo ""
echo "=== Memory Information ==="
free -h
echo ""
echo "=== Storage Information ==="
df -h
echo ""
echo "=== GPU Detection ==="
lspci | grep -i nvidia
echo ""
echo "=== Network Test ==="
ping -c 3 google.com
echo ""
echo "=== Disk I/O Test (Model Storage) ==="
# Check available space before creating test file (need >1GB)
AVAILABLE_KB=$(df --output=avail /mnt/citadel-models | tail -n1)
REQUIRED_KB=$((1024 * 1024))  # 1GB in KB

if [ "$AVAILABLE_KB" -gt "$REQUIRED_KB" ]; then
    echo "Creating 1GB test file for I/O benchmark..."
    dd if=/dev/zero of=/mnt/citadel-models/iotest bs=1G count=1 oflag=dsync 2>&1
    rm -f /mnt/citadel-models/iotest
else
    echo "ERROR: Insufficient disk space for I/O test (need 1GB, have $(($AVAILABLE_KB / 1024))MB)"
    echo "Skipping disk I/O test to prevent storage issues"
fi
echo ""
echo "=== Mount Verification ==="
mount | grep -E "(citadel|nvme|sda)"
EOF

chmod +x /tmp/performance_test.sh
/tmp/performance_test.sh > /var/log/citadel-baseline.log 2>&1

log "Performance baseline saved to /var/log/citadel-baseline.log"

# =============================================================================
# Step 8: Final Validation
# =============================================================================
log "Step 8: Performing final validation..."

VALIDATION_PASSED=true

# Check storage mounts
if ! mountpoint -q /mnt/citadel-models; then
    error "Model storage not mounted"
    VALIDATION_PASSED=false
fi

if ! mountpoint -q /mnt/citadel-backup; then
    error "Backup storage not mounted"
    VALIDATION_PASSED=false
fi

# Check user permissions
if ! sudo -u agent0 test -w /mnt/citadel-models; then
    error "agent0 cannot write to model storage"
    VALIDATION_PASSED=false
fi

# Check network connectivity
if ! ping -c 1 google.com >/dev/null 2>&1; then
    warn "Internet connectivity test failed"
fi

# Check GPU detection
if ! lspci | grep -qi nvidia; then
    warn "NVIDIA GPUs not detected"
fi

if $VALIDATION_PASSED; then
    log "All validation checks passed!"
else
    error "Some validation checks failed"
fi

# =============================================================================
# Completion Summary
# =============================================================================
log "PLANB-01 configuration completed successfully!"
info "=================================="
info "Next Steps:"
info "1. Reboot system to apply GRUB changes"
info "2. Install NVIDIA drivers (PLANB-03)"
info "3. Configure Python environment (PLANB-04)"
info "4. Install vLLM framework (PLANB-05)"
info "=================================="
info "Review performance baseline: cat /var/log/citadel-baseline.log"
info "Storage locations:"
info "  - Model storage: /mnt/citadel-models"
info "  - Backup storage: /mnt/citadel-backup"
info "=================================="

warn "IMPORTANT: Please reboot the system to apply all changes"
warn "sudo reboot"