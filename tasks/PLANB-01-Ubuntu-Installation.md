# PLANB-01: Fresh Ubuntu Server 24.04 Installation

**Task:** Install Ubuntu Server 24.04 LTS with optimal configuration for AI workloads  
**Duration:** 45-60 minutes  
**Prerequisites:** Installation media (USB), target hardware available  

## Overview

This task covers the complete fresh installation of Ubuntu Server 24.04 LTS with specific configurations optimized for the Citadel AI OS environment.

## Hardware Requirements

### Minimum Specifications
- **CPU**: Intel Xeon or AMD EPYC (16+ cores)
- **RAM**: 128GB DDR4/DDR5
- **GPU**: 2x NVIDIA RTX 4070 Ti SUPER (32GB VRAM total)
- **Storage**: 
  - Primary NVMe: 4TB (OS and applications)
  - Secondary NVMe: 4TB (Model storage)
  - Backup HDD: 8TB (General backup and storage)
- **Network**: 10Gbps+ connection

### Target Storage Layout
```
├── nvme0n1 (Primary NVMe - 4TB)
│   ├── nvme0n1p1 (1GB)     → /boot/efi (EFI System)
│   ├── nvme0n1p2 (2GB)     → /boot (Boot partition)
│   └── nvme0n1p3 (3.9TB)   → LVM Physical Volume
│       └── ubuntu-vg
│           ├── root-lv (200GB)   → / (Root filesystem)
│           ├── home-lv (500GB)   → /home (User data)
│           ├── opt-lv (1TB)      → /opt (Applications)
│           ├── var-lv (500GB)    → /var (Variable data)
│           └── tmp-lv (100GB)    → /tmp (Temporary files)
├── nvme1n1 (Secondary NVMe - 4TB) → /mnt/citadel-models (Model storage)
└── sda (Backup HDD - 8TB)         → /mnt/citadel-backup (Backup storage)
```

## Installation Steps

### Step 1: Prepare Installation Media

1. **Download Ubuntu Server 24.04 LTS**
   ```bash
   # Download the latest Ubuntu Server 24.04 LTS ISO
   wget https://releases.ubuntu.com/24.04/ubuntu-24.04-live-server-amd64.iso
   
   # Verify checksum
   wget https://releases.ubuntu.com/24.04/SHA256SUMS
   sha256sum -c SHA256SUMS --ignore-missing
   ```

2. **Create Bootable USB**
   ```bash
   # Using dd (Linux/macOS)
   sudo dd if=ubuntu-24.04-live-server-amd64.iso of=/dev/sdX bs=4M status=progress oflag=sync
   
   # Or use Rufus on Windows
   # Or use balenaEtcher for cross-platform GUI
   ```

### Step 2: BIOS/UEFI Configuration

1. **Boot Settings**
   - Enable UEFI mode (disable Legacy BIOS)
   - Enable Secure Boot (recommended)
   - Set boot priority: USB → NVMe

2. **Hardware Settings**
   - Enable Virtualization (VT-x/AMD-V)
   - Enable IOMMU (for GPU passthrough capabilities)
   - Set CPU performance mode to "Performance"
   - Enable XMP/DOCP for RAM (if available)

### Step 3: Ubuntu Installation Process

1. **Boot from USB**
   - Select "Try or Install Ubuntu Server"
   - Choose language: English

2. **Network Configuration**
   - Configure primary network interface (eno1)
   - Set static IP for Hana-X Lab:
     ```
     IP: 192.168.10.35/24
     Gateway: 192.168.10.1
     DNS: 8.8.8.8, 1.1.1.1
     Hostname: db
     ```

3. **Storage Configuration**
   - **Important**: Choose "Custom storage layout"
   - Configure as per the target storage layout above
   - **Primary NVMe (nvme0n1)**:
     ```
     /dev/nvme0n1p1: 1GB, EFI System Partition
     /dev/nvme0n1p2: 2GB, ext4, mount=/boot
     /dev/nvme0n1p3: Remaining space, LVM PV
     ```
   - **LVM Configuration**:
     ```
     Volume Group: ubuntu-vg
     Logical Volumes:
     - root-lv: 200GB → / (ext4)
     - home-lv: 500GB → /home (ext4)
     - opt-lv: 1TB → /opt (ext4)
     - var-lv: 500GB → /var (ext4)
     - tmp-lv: 100GB → /tmp (ext4)
     ```

4. **User Configuration**
   - **User**: agent0
   - **Server name**: db
   - **Username**: agent0
   - **Password**: [Use strong password]
   - **Enable SSH**: Yes
   - **Full Name**: Citadel AI Agent0

5. **Package Selection**
   - Install OpenSSH server
   - Skip snap packages (we'll install manually)

### Step 4: Post-Installation Configuration

1. **First Boot and Network Setup**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y
   
   # Install essential packages
   sudo apt install -y \
     curl wget git vim htop tree \
     build-essential cmake \
     software-properties-common \
     apt-transport-https ca-certificates gnupg lsb-release \
     unzip zip p7zip-full \
     net-tools iotop iftop \
     tmux screen
   
   # Configure Hana-X Lab host mappings
   sudo tee -a /etc/hosts << 'EOF'

# ───── HANA-X LAB – STATIC HOST MAPPINGS ─────
192.168.10.50    hana-x-jr0          # Windows Admin Workstation (ThinkPad)
192.168.10.33    dev                 # AI Development Node
192.168.10.29    llm                 # LLM Foundation Model Node
192.168.10.30    vectordb            # Vector Database + Embedding Server
192.168.10.31    orca                # Agent Simulation & Orchestration Node
192.168.10.34    qa                  # QA/Test Server
192.168.10.36    dev-ops             # CI/CD + Monitoring Node
192.168.10.35    db                  # PostgreSQL Database Server (current node)
192.168.10.19    agent0              # Agent Workstation (Desktop)
EOF
   ```

2. **Configure Additional Storage**
   ```bash
   # Format secondary NVMe for model storage
   sudo mkfs.ext4 /dev/nvme1n1
   sudo mkdir -p /mnt/citadel-models
   
   # Format backup HDD
   sudo mkfs.ext4 /dev/sda
   sudo mkdir -p /mnt/citadel-backup
   
   # Get UUIDs for fstab
   sudo blkid /dev/nvme1n1
   sudo blkid /dev/sda
   ```

3. **Update /etc/fstab**
   ```bash
   # Add to /etc/fstab (replace UUIDs with actual values)
   sudo tee -a /etc/fstab << 'EOF'
   
   # Citadel AI OS Storage Configuration
   UUID=nvme1n1-uuid /mnt/citadel-models ext4 defaults,noatime 0 2
   UUID=sda-uuid /mnt/citadel-backup ext4 defaults,noatime 0 2
   EOF
   
   # Test mount
   sudo mount -a
   sudo df -h
   ```

4. **Configure System Optimization**
   ```bash
   # Update GRUB for AI workloads
   sudo tee -a /etc/default/grub << 'EOF'
   GRUB_CMDLINE_LINUX_DEFAULT="quiet splash iommu=pt intel_iommu=on"
   EOF
   
   sudo update-grub
   
   # Configure systemd for large workloads
   sudo tee /etc/systemd/system.conf.d/citadel.conf << 'EOF'
   [Manager]
   DefaultLimitNOFILE=65536
   DefaultLimitNPROC=32768
   DefaultLimitMEMLOCK=infinity
   EOF
   ```

5. **Security Configuration**
   ```bash
   # Configure firewall for Hana-X Lab network
   sudo ufw enable
   sudo ufw default deny incoming
   sudo ufw default allow outgoing
   sudo ufw allow ssh
   sudo ufw allow from 192.168.10.0/24
   
   # Configure SSH hardening
   sudo tee -a /etc/ssh/sshd_config << 'EOF'
   
   # Citadel AI OS SSH Configuration
   PermitRootLogin no
   PasswordAuthentication yes
   PubkeyAuthentication yes
   MaxAuthTries 3
   ClientAliveInterval 300
   ClientAliveCountMax 2
   EOF
   
   sudo systemctl restart ssh
   ```

## Validation Steps

### Step 1: System Health Check
```bash
# System information
hostnamectl
uname -a
lsb_release -a

# Memory and CPU
free -h
lscpu | grep -E "(Model name|CPU\(s\)|Thread|Socket)"

# Storage verification
df -h
lsblk
sudo fdisk -l
```

### Step 2: Network Verification
```bash
# Network connectivity
ping -c 4 google.com
curl -I https://github.com

# Network configuration
ip addr show
ip route show
cat /etc/netplan/*.yaml
```

### Step 3: Storage Mount Verification
```bash
# Verify all mounts
mount | grep -E "(citadel|nvme|sda)"
sudo findmnt -D

# Test write permissions
sudo touch /mnt/citadel-models/test.txt
sudo touch /mnt/citadel-backup/test.txt
sudo rm /mnt/citadel-models/test.txt /mnt/citadel-backup/test.txt
```

### Step 4: Performance Baseline
```bash
# Disk I/O test
sudo dd if=/dev/zero of=/mnt/citadel-models/test bs=1G count=1 oflag=dsync
sudo rm /mnt/citadel-models/test

# Network speed test (if available)
sudo apt install -y speedtest-cli
speedtest-cli
```

## Troubleshooting

### Issue: Boot Problems
**Symptoms**: System doesn't boot, GRUB errors
**Solutions**:
- Check UEFI vs Legacy BIOS settings
- Verify Secure Boot compatibility
- Boot from rescue media and repair GRUB

### Issue: Storage Not Mounting
**Symptoms**: /mnt directories empty, mount errors
**Solutions**:
- Check device paths: `sudo fdisk -l`
- Verify UUIDs: `sudo blkid`
- Check fstab syntax: `sudo mount -a`

### Issue: Network Configuration
**Symptoms**: No internet access, DNS issues
**Solutions**:
- Check netplan configuration: `/etc/netplan/`
- Test DNS: `nslookup google.com`
- Reset network: `sudo netplan apply`

## Post-Installation Checklist

- [ ] System boots successfully
- [ ] All storage devices mounted
- [ ] Network connectivity established
- [ ] SSH access working
- [ ] User permissions configured
- [ ] System optimization applied
- [ ] Security hardening completed
- [ ] Performance baseline established

## Next Steps

Continue to **[PLANB-02-Storage-Configuration.md](PLANB-02-Storage-Configuration.md)** for detailed storage optimization and model directory setup.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 45-60 minutes  
**Complexity**: Medium  
**Prerequisites**: Hardware available, installation media prepared