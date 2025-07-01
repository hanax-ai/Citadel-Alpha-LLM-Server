# PLANB-03: NVIDIA 570.x Driver Installation and GPU Optimization

**Task:** Install NVIDIA 570.x drivers with CUDA 12.4+ support for optimal AI workload performance  
**Duration:** 45-60 minutes  
**Prerequisites:** PLANB-01 and PLANB-02 completed, GPU hardware installed  

## Overview

This task installs the latest NVIDIA 570.x series drivers with CUDA 12.4+ toolkit, optimized for dual GPU AI workloads on Ubuntu 24.04 LTS.

## Hardware Requirements

### Target GPU Configuration
- **Primary GPU**: NVIDIA RTX 4070 Ti SUPER (16GB VRAM)
- **Secondary GPU**: NVIDIA RTX 4070 Ti SUPER (16GB VRAM)
- **Total VRAM**: 32GB
- **Architecture**: Ada Lovelace (Compute Capability 8.9)
- **CUDA Cores**: 8,448 per GPU (16,896 total)

### Driver Specifications
- **Driver Version**: 570.x series (latest stable)
- **CUDA Version**: 12.4 or 12.5
- **cuDNN Version**: 9.x
- **Target Architecture**: x86_64

## Pre-Installation Steps

### Step 1: Create Configuration and Backup System

1. **Create GPU Configuration File**
   ```bash
   # Create GPU configuration directory
   sudo mkdir -p /opt/citadel/configs
   
   # Create GPU configuration file with dynamic detection
   sudo tee /opt/citadel/configs/gpu-config.json << 'EOF'
   {
     "driver_version": "570",
     "cuda_version": "12-4",
     "target_gpus": 2,
     "gpu_model": "RTX 4070 Ti SUPER",
     "auto_detect_clocks": true,
     "performance_settings": {
       "power_limit_percent": 95,
       "memory_clock_offset": 0,
       "graphics_clock_offset": 0,
       "compute_mode": "EXCLUSIVE_PROCESS"
     },
     "repository": {
       "ubuntu_version": "2404",
       "architecture": "x86_64"
     }
   }
   EOF
   ```

2. **Create Backup and Rollback Functions**
   ```bash
   # Create comprehensive backup and rollback script
   sudo tee /opt/citadel/scripts/nvidia-backup-rollback.sh << 'EOF'
   #!/bin/bash
   # nvidia-backup-rollback.sh - Backup and rollback NVIDIA configurations
   
   set -euo pipefail
   
   BACKUP_DIR="/opt/citadel/backups/nvidia-$(date +%Y%m%d-%H%M%S)"
   CONFIG_FILE="/opt/citadel/configs/gpu-config.json"
   
   # Error handling function
   handle_error() {
       echo "ERROR: $1" >&2
       echo "Rolling back changes..." >&2
       rollback_changes
       exit 1
   }
   
   # Create backup
   create_backup() {
       echo "Creating backup at $BACKUP_DIR"
       sudo mkdir -p "$BACKUP_DIR"
       
       # Backup package state
       dpkg -l | grep -E "(nvidia|cuda)" > "$BACKUP_DIR/packages.list" 2>/dev/null || echo "No NVIDIA packages found"
       
       # Backup configuration files
       [ -f /etc/X11/xorg.conf ] && sudo cp /etc/X11/xorg.conf "$BACKUP_DIR/" 2>/dev/null || true
       [ -d /etc/modprobe.d ] && sudo cp -r /etc/modprobe.d "$BACKUP_DIR/" 2>/dev/null || true
       [ -f /etc/environment ] && sudo cp /etc/environment "$BACKUP_DIR/" 2>/dev/null || true
       [ -f ~/.bashrc ] && cp ~/.bashrc "$BACKUP_DIR/bashrc.user" 2>/dev/null || true
       
       # Backup systemd services
       sudo systemctl list-unit-files | grep nvidia > "$BACKUP_DIR/services.list" 2>/dev/null || true
       
       echo "Backup completed: $BACKUP_DIR"
   }
   
   # Rollback changes
   rollback_changes() {
       if [ -z "${BACKUP_DIR:-}" ] || [ ! -d "$BACKUP_DIR" ]; then
           echo "No backup directory found for rollback"
           return 1
       fi
       
       echo "Rolling back from backup: $BACKUP_DIR"
       
       # Restore configuration files
       [ -f "$BACKUP_DIR/xorg.conf" ] && sudo cp "$BACKUP_DIR/xorg.conf" /etc/X11/ 2>/dev/null || true
       [ -d "$BACKUP_DIR/modprobe.d" ] && sudo cp -r "$BACKUP_DIR/modprobe.d/"* /etc/modprobe.d/ 2>/dev/null || true
       [ -f "$BACKUP_DIR/environment" ] && sudo cp "$BACKUP_DIR/environment" /etc/ 2>/dev/null || true
       [ -f "$BACKUP_DIR/bashrc.user" ] && cp "$BACKUP_DIR/bashrc.user" ~/.bashrc 2>/dev/null || true
       
       echo "Rollback completed. System may require reboot."
   }
   
   # Detect GPU specifications
   detect_gpu_specs() {
       if ! command -v nvidia-smi >/dev/null 2>&1; then
           echo "NVIDIA drivers not installed - using default values"
           return 0
       fi
       
       # Get GPU information
       GPU_COUNT=$(nvidia-smi -L | wc -l)
       GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)
       MAX_POWER=$(nvidia-smi --query-gpu=power.max_limit --format=csv,noheader,nounits | head -1 | sed 's/ W//')
       MAX_MEM_CLOCK=$(nvidia-smi --query-gpu=clocks.max.memory --format=csv,noheader,nounits | head -1 | sed 's/ MHz//')
       MAX_GR_CLOCK=$(nvidia-smi --query-gpu=clocks.max.graphics --format=csv,noheader,nounits | head -1 | sed 's/ MHz//')
       
       echo "Detected GPU specifications:"
       echo "  Count: $GPU_COUNT"
       echo "  Model: $GPU_NAME"
       echo "  Max Power: ${MAX_POWER}W"
       echo "  Max Memory Clock: ${MAX_MEM_CLOCK}MHz"
       echo "  Max Graphics Clock: ${MAX_GR_CLOCK}MHz"
       
       # Update configuration with detected values
       if [ -f "$CONFIG_FILE" ]; then
           python3 << PYEOF
   import json
   
   with open('$CONFIG_FILE', 'r') as f:
       config = json.load(f)
   
   config['detected_specs'] = {
       'gpu_count': $GPU_COUNT,
       'gpu_name': '$GPU_NAME',
       'max_power_watts': ${MAX_POWER:-320},
       'max_memory_clock_mhz': ${MAX_MEM_CLOCK:-9501},
       'max_graphics_clock_mhz': ${MAX_GR_CLOCK:-2610}
   }
   
   with open('$CONFIG_FILE', 'w') as f:
       json.dump(config, f, indent=2)
   PYEOF
       fi
   }
   
   case "${1:-}" in
       backup)
           create_backup
           ;;
       rollback)
           rollback_changes
           ;;
       detect)
           detect_gpu_specs
           ;;
       *)
           echo "Usage: $0 {backup|rollback|detect}"
           exit 1
           ;;
   esac
   EOF
   
   chmod +x /opt/citadel/scripts/nvidia-backup-rollback.sh
   ```

3. **Safe Driver Removal with Backup**
   ```bash
   # Create backup before removal
   /opt/citadel/scripts/nvidia-backup-rollback.sh backup || {
       echo "ERROR: Failed to create backup"
       exit 1
   }
   
   # Remove existing NVIDIA packages with error handling
   echo "Removing existing NVIDIA packages..."
   if ! sudo apt-get remove --purge "nvidia*" -y 2>/dev/null; then
       echo "WARNING: Some NVIDIA packages could not be removed"
   fi
   
   if ! sudo apt-get remove --purge "cuda*" -y 2>/dev/null; then
       echo "WARNING: Some CUDA packages could not be removed"
   fi
   
   if ! sudo apt-get remove --purge "libnvidia*" -y 2>/dev/null; then
       echo "WARNING: Some NVIDIA library packages could not be removed"
   fi
   
   sudo apt-get autoremove -y || echo "WARNING: Autoremove failed"
   sudo apt-get autoclean || echo "WARNING: Autoclean failed"
   
   # Remove NVIDIA configuration files safely
   [ -f /etc/X11/xorg.conf ] && sudo rm -f /etc/X11/xorg.conf
   sudo find /etc/modprobe.d -name "*nvidia*" -delete 2>/dev/null || true
   sudo find /etc/modprobe.d -name "*blacklist-nvidia*" -delete 2>/dev/null || true
   
   echo "✅ NVIDIA cleanup completed"
   ```

2. **Update System Packages**
   ```bash
   # Update package lists and system
   sudo apt update && sudo apt upgrade -y
   
   # Install required build dependencies
   sudo apt install -y \
     build-essential \
     cmake \
     git \
     wget \
     curl \
     dkms \
     linux-headers-$(uname -r) \
     gcc \
     g++ \
     make \
     pkg-config \
     libssl-dev \
     zlib1g-dev \
     libbz2-dev \
     libreadline-dev \
     libsqlite3-dev \
     libncursesw5-dev \
     xz-utils \
     tk-dev \
     libxml2-dev \
     libxmlsec1-dev \
     libffi-dev \
     liblzma-dev
   ```

3. **Verify GPU Detection**
   ```bash
   # Check if GPUs are detected by the system
   lspci | grep -i nvidia
   lspci -vnn | grep -i nvidia
   
   # Check current GPU status
   sudo lshw -C display
   ```

### Step 2: Configure Repository and Install Driver with Error Handling

1. **Add NVIDIA Repository with Dynamic Detection**
   ```bash
   # Load configuration
   CONFIG_FILE="/opt/citadel/configs/gpu-config.json"
   if [ ! -f "$CONFIG_FILE" ]; then
       echo "ERROR: GPU configuration file not found"
       exit 1
   fi
   
   # Extract configuration values
   UBUNTU_VERSION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['repository']['ubuntu_version'])")
   ARCHITECTURE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['repository']['architecture'])")
   
   # Download and install repository keyring with error handling
   REPO_URL="https://developer.download.nvidia.com/compute/cuda/repos/ubuntu${UBUNTU_VERSION}/${ARCHITECTURE}/cuda-keyring_1.1-1_all.deb"
   
   echo "Adding NVIDIA repository for Ubuntu ${UBUNTU_VERSION} ${ARCHITECTURE}"
   if ! wget -q "$REPO_URL" -O /tmp/cuda-keyring.deb; then
       echo "ERROR: Failed to download NVIDIA repository keyring"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   if ! sudo dpkg -i /tmp/cuda-keyring.deb; then
       echo "ERROR: Failed to install NVIDIA repository keyring"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   if ! sudo apt update; then
       echo "ERROR: Failed to update package lists"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   # Verify repository addition
   if apt-cache policy | grep -q nvidia; then
       echo "✅ NVIDIA repository added successfully"
   else
       echo "ERROR: NVIDIA repository not found after installation"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   # Cleanup temporary file
   rm -f /tmp/cuda-keyring.deb
   ```

2. **Install NVIDIA Driver with Error Handling**
   ```bash
   # Get driver version from configuration
   DRIVER_VERSION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['driver_version'])")
   
   echo "Installing NVIDIA driver ${DRIVER_VERSION}.x series"
   
   # Check available drivers
   if ! apt-cache search "nvidia-driver-${DRIVER_VERSION}" | grep -q "nvidia-driver-${DRIVER_VERSION}"; then
       echo "ERROR: NVIDIA driver ${DRIVER_VERSION} not available in repository"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   # Install driver with error handling
   if ! sudo apt install -y "nvidia-driver-${DRIVER_VERSION}"; then
       echo "ERROR: Failed to install NVIDIA driver ${DRIVER_VERSION}"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   echo "✅ NVIDIA driver ${DRIVER_VERSION} installed successfully"
   ```

3. **Install CUDA Toolkit with Error Handling**
   ```bash
   # Get CUDA version from configuration
   CUDA_VERSION=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['cuda_version'])")
   
   echo "Installing CUDA Toolkit ${CUDA_VERSION}"
   
   # Check available CUDA toolkit
   if ! apt-cache search "cuda-toolkit-${CUDA_VERSION}" | grep -q "cuda-toolkit-${CUDA_VERSION}"; then
       echo "ERROR: CUDA Toolkit ${CUDA_VERSION} not available in repository"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   # Install CUDA Toolkit
   if ! sudo apt install -y "cuda-toolkit-${CUDA_VERSION}"; then
       echo "ERROR: Failed to install CUDA Toolkit ${CUDA_VERSION}"
       /opt/citadel/scripts/nvidia-backup-rollback.sh rollback
       exit 1
   fi
   
   # Install additional CUDA development tools with error handling
   CUDA_PACKAGES=(
       "cuda-compiler-${CUDA_VERSION}"
       "cuda-libraries-dev-${CUDA_VERSION}"
       "cuda-driver-dev-${CUDA_VERSION}"
       "cuda-cudart-dev-${CUDA_VERSION}"
       "cuda-nvml-dev-${CUDA_VERSION}"
   )
   
   for package in "${CUDA_PACKAGES[@]}"; do
       if apt-cache search "$package" | grep -q "$package"; then
           if ! sudo apt install -y "$package"; then
               echo "WARNING: Failed to install $package (non-critical)"
           fi
       else
           echo "WARNING: Package $package not available (skipping)"
       fi
   done
   
   echo "✅ CUDA Toolkit installation completed"
   ```

4. **Install cuDNN with Error Handling**
   ```bash
   echo "Installing cuDNN 9.x"
   
   # Install cuDNN packages with error handling
   CUDNN_PACKAGES=(
       "libcudnn9"
       "libcudnn9-dev"
       "libcudnn9-samples"
   )
   
   for package in "${CUDNN_PACKAGES[@]}"; do
       if apt-cache search "$package" | grep -q "$package"; then
           if ! sudo apt install -y "$package"; then
               echo "WARNING: Failed to install $package"
           fi
       else
           echo "WARNING: Package $package not available"
       fi
   done
   
   echo "✅ cuDNN installation completed"
   ```

### Step 3: System Configuration with Error Handling

1. **Configure Environment Variables with Backup**
   ```bash
   # Backup existing environment configuration
   echo "Backing up environment configuration..."
   [ -f /etc/environment ] && sudo cp /etc/environment /etc/environment.backup.$(date +%Y%m%d-%H%M%S)
   [ -f ~/.bashrc ] && cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d-%H%M%S)
   
   # Detect CUDA installation path
   CUDA_PATH="/usr/local/cuda"
   if [ ! -d "$CUDA_PATH" ]; then
       # Try to find CUDA installation
       for path in /usr/local/cuda-* /usr/cuda /opt/cuda; do
           if [ -d "$path" ]; then
               CUDA_PATH="$path"
               echo "Found CUDA installation at: $CUDA_PATH"
               break
           fi
       done
   fi
   
   if [ ! -d "$CUDA_PATH" ]; then
       echo "WARNING: CUDA installation directory not found, using default path"
       CUDA_PATH="/usr/local/cuda"
   fi
   
   # Get current PATH to preserve existing entries
   CURRENT_PATH=$(grep "^PATH=" /etc/environment 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin")
   

   # Add CUDA to system PATH and library path without overwriting existing variables
   echo "Configuring system environment variables..."
   # Remove any existing PATH entry
   sudo sed -i '/^PATH=/d' /etc/environment
   # Append new PATH and CUDA variables
   echo "PATH=\"${CURRENT_PATH}:${CUDA_PATH}/bin\"" | sudo tee -a /etc/environment
   echo "CUDA_HOME=\"${CUDA_PATH}\"" | sudo tee -a /etc/environment
   echo "CUDA_ROOT=\"${CUDA_PATH}\"" | sudo tee -a /etc/environment
   echo "LD_LIBRARY_PATH=\"${CUDA_PATH}/lib64:${CUDA_PATH}/extras/CUPTI/lib64\"" | sudo tee -a /etc/environment
   
   # Check if CUDA configuration already exists in bashrc
   if ! grep -q "NVIDIA CUDA Configuration" ~/.bashrc; then
       echo "Adding CUDA configuration to user profile..."
       tee -a ~/.bashrc << EOF
   
   # NVIDIA CUDA Configuration
   export CUDA_HOME="${CUDA_PATH}"
   export CUDA_ROOT="${CUDA_PATH}"
   export PATH="${CUDA_PATH}/bin:\$PATH"
   export LD_LIBRARY_PATH="${CUDA_PATH}/lib64:${CUDA_PATH}/extras/CUPTI/lib64:\$LD_LIBRARY_PATH"
   export NVIDIA_VISIBLE_DEVICES=all
   export NVIDIA_DRIVER_CAPABILITIES=compute,utility
   EOF
   else
       echo "CUDA configuration already exists in bashrc"
   fi
   
   # Apply environment changes with error handling
   if source ~/.bashrc 2>/dev/null; then
       echo "✅ Environment variables configured successfully"
   else
       echo "WARNING: Could not source bashrc - changes will take effect on next login"
   fi
   
   # Verify CUDA environment setup
   if [ -f "${CUDA_PATH}/bin/nvcc" ]; then
       echo "✅ CUDA environment setup verified"
   else
       echo "WARNING: CUDA compiler not found at expected location"
   fi
   ```

2. **Configure GPU Persistence Mode with Error Handling**
   ```bash
   # Check if nvidia-persistenced binary exists
   if [ ! -f "/usr/bin/nvidia-persistenced" ]; then
       echo "WARNING: nvidia-persistenced not found - may not be available with this driver version"
       echo "Attempting to locate nvidia-persistenced..."
       PERSISTENCED_PATH=$(which nvidia-persistenced 2>/dev/null || find /usr -name "nvidia-persistenced" 2>/dev/null | head -1)
       
       if [ -n "$PERSISTENCED_PATH" ]; then
           echo "Found nvidia-persistenced at: $PERSISTENCED_PATH"
       else
           echo "WARNING: nvidia-persistenced not found - skipping persistence configuration"
           echo "GPU persistence will need to be enabled manually if required"
           exit 0
       fi
   else
       PERSISTENCED_PATH="/usr/bin/nvidia-persistenced"
   fi
   
   # Create systemd service for GPU persistence
   echo "Creating NVIDIA persistence daemon service..."
   sudo tee /etc/systemd/system/nvidia-persistenced.service << EOF
   [Unit]
   Description=NVIDIA Persistence Daemon
   After=syslog.target network.target
   
   [Service]
   Type=forking
   PIDFile=/var/run/nvidia-persistenced/nvidia-persistenced.pid
   Restart=always
   ExecStart=${PERSISTENCED_PATH} --verbose
   ExecStopPost=/bin/rm -rf /var/run/nvidia-persistenced
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Reload systemd and enable the service
   if ! sudo systemctl daemon-reload; then
       echo "ERROR: Failed to reload systemd daemon"
       exit 1
   fi
   
   if ! sudo systemctl enable nvidia-persistenced; then
       echo "ERROR: Failed to enable nvidia-persistenced service"
       exit 1
   fi
   
   if ! sudo systemctl start nvidia-persistenced; then
       echo "WARNING: Failed to start nvidia-persistenced service"
       echo "Service will start on next boot"
   else
       echo "✅ NVIDIA persistence daemon configured and started"
   fi
   
   # Verify service status
   if sudo systemctl is-active nvidia-persistenced >/dev/null 2>&1; then
       echo "✅ NVIDIA persistence daemon is running"
   else
       echo "WARNING: NVIDIA persistence daemon is not running"
   fi
   ```

3. **Optimize GPU Performance with Dynamic Configuration**
   ```bash
   # Create GPU optimization script with dynamic settings
   sudo tee /opt/citadel/scripts/gpu-optimize.sh << 'EOF'
   #!/bin/bash
   # gpu-optimize.sh - Optimize GPU settings for AI workloads with dynamic detection
   
   set -euo pipefail
   
   CONFIG_FILE="/opt/citadel/configs/gpu-config.json"
   
   # Error handling
   handle_error() {
       echo "ERROR: $1" >&2
       echo "GPU optimization failed" >&2
       exit 1
   }
   
   # Check if NVIDIA drivers are loaded
   if ! command -v nvidia-smi >/dev/null 2>&1; then
       handle_error "nvidia-smi not found - drivers may not be installed"
   fi
   
   if ! nvidia-smi >/dev/null 2>&1; then
       handle_error "nvidia-smi failed - drivers may not be loaded properly"
   fi
   
   echo "=== GPU Optimization for AI Workloads ==="
   
   # Load configuration if available
   if [ -f "$CONFIG_FILE" ]; then
       echo "Loading GPU configuration from $CONFIG_FILE"
       
       # Get configuration values
       AUTO_DETECT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('auto_detect_clocks', True))" 2>/dev/null || echo "true")
       POWER_LIMIT_PERCENT=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['performance_settings']['power_limit_percent'])" 2>/dev/null || echo "95")
       COMPUTE_MODE=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['performance_settings']['compute_mode'])" 2>/dev/null || echo "EXCLUSIVE_PROCESS")
       
       # Get detected specs if available
       if python3 -c "import json; 'detected_specs' in json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
           MAX_POWER=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['detected_specs']['max_power_watts'])" 2>/dev/null || echo "320")
           MAX_MEM_CLOCK=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['detected_specs']['max_memory_clock_mhz'])" 2>/dev/null || echo "9501")
           MAX_GR_CLOCK=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['detected_specs']['max_graphics_clock_mhz'])" 2>/dev/null || echo "2610")
       else
           # Detect current maximum values
           echo "Detecting GPU specifications..."
           MAX_POWER=$(nvidia-smi --query-gpu=power.max_limit --format=csv,noheader,nounits | head -1 | sed 's/ W//' || echo "320")
           MAX_MEM_CLOCK=$(nvidia-smi --query-gpu=clocks.max.memory --format=csv,noheader,nounits | head -1 | sed 's/ MHz//' || echo "9501")
           MAX_GR_CLOCK=$(nvidia-smi --query-gpu=clocks.max.graphics --format=csv,noheader,nounits | head -1 | sed 's/ MHz//' || echo "2610")
       fi
   else
       echo "No configuration file found, using default values"
       AUTO_DETECT="true"
       POWER_LIMIT_PERCENT="95"
       COMPUTE_MODE="EXCLUSIVE_PROCESS"
       MAX_POWER="320"
       MAX_MEM_CLOCK="9501"
       MAX_GR_CLOCK="2610"
   fi
   
   echo "GPU Optimization Settings:"
   echo "  Auto-detect clocks: $AUTO_DETECT"
   echo "  Power limit: ${POWER_LIMIT_PERCENT}% of ${MAX_POWER}W"
   echo "  Memory clock: ${MAX_MEM_CLOCK}MHz"
   echo "  Graphics clock: ${MAX_GR_CLOCK}MHz"
   echo "  Compute mode: $COMPUTE_MODE"
   echo ""
   
   # Set GPU performance mode
   echo "Setting performance mode..."
   if ! nvidia-smi -pm 1 >/dev/null 2>&1; then
       echo "WARNING: Could not enable persistence mode"
   fi
   
   # Calculate and set power limit for all GPUs
   POWER_LIMIT=$(( MAX_POWER * POWER_LIMIT_PERCENT / 100 ))
   GPU_COUNT=$(nvidia-smi -L | wc -l)
   echo "Setting power limit to ${POWER_LIMIT}W on all GPUs..."
   for idx in $(seq 0 $((GPU_COUNT-1))); do
       if ! nvidia-smi -i "$idx" -pl "$POWER_LIMIT" >/dev/null 2>&1; then
           echo "WARNING: Could not set power limit to ${POWER_LIMIT}W on GPU $idx"
       fi
   done

   # Set GPU application clocks for all GPUs
   if [ "$AUTO_DETECT" = "true" ]; then
       echo "Setting application clocks to ${MAX_MEM_CLOCK},${MAX_GR_CLOCK} on all GPUs..."
       for idx in $(seq 0 $((GPU_COUNT-1))); do
           if ! nvidia-smi -i "$idx" -ac "${MAX_MEM_CLOCK},${MAX_GR_CLOCK}" >/dev/null 2>&1; then
               echo "WARNING: Could not set application clocks on GPU $idx"
           fi
       done
   fi
   
   # Set compute mode
   case "$COMPUTE_MODE" in
       "DEFAULT")
           COMPUTE_MODE_NUM=0
           ;;
       "EXCLUSIVE_THREAD")
           COMPUTE_MODE_NUM=1
           ;;
       "PROHIBITED")
           COMPUTE_MODE_NUM=2
           ;;
       "EXCLUSIVE_PROCESS")
           COMPUTE_MODE_NUM=3
           ;;
       *)
           COMPUTE_MODE_NUM=3
           ;;
   esac
   
   echo "Setting compute mode to $COMPUTE_MODE..."
   if ! nvidia-smi -c "$COMPUTE_MODE_NUM" >/dev/null 2>&1; then
       echo "WARNING: Could not set compute mode"
   fi
   
   # Display current status
   echo ""
   echo "=== Current GPU Status ==="
   nvidia-smi
   
   echo ""
   echo "✅ GPU optimization completed"
   EOF
   
   chmod +x /opt/citadel/scripts/gpu-optimize.sh
   ```

4. **Create GPU Monitoring Script**
   ```bash
   # Create comprehensive GPU monitoring script
   sudo tee /opt/citadel/scripts/gpu-monitor.sh << 'EOF'
   #!/bin/bash
   # gpu-monitor.sh - Monitor GPU status and performance
   
   echo "=== GPU Status Report $(date) ==="
   echo ""
   
   echo "GPU Information:"
   nvidia-smi -L
   echo ""
   
   echo "Driver Information:"
   nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits
   echo ""
   
   echo "GPU Utilization:"
   nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits
   echo ""
   
   echo "Memory Usage:"
   nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader,nounits
   echo ""
   
   echo "GPU Clocks:"
   nvidia-smi --query-gpu=clocks.gr,clocks.mem,clocks.max.gr,clocks.max.mem --format=csv,noheader,nounits
   echo ""
   
   echo "Process Information:"
   nvidia-smi pmon -c 1
   echo ""
   
   echo "Detailed Status:"
   nvidia-smi
   EOF
   
   chmod +x /opt/citadel/scripts/gpu-monitor.sh
   ```

## Post-Installation Configuration

### Step 1: Reboot and Verification

1. **Reboot System**
   ```bash
   # Reboot to load new drivers
   sudo reboot
   ```

2. **Verify Driver Installation**
   ```bash
   # Check NVIDIA driver version
   nvidia-smi
   
   # Verify CUDA installation
   nvcc --version
   
   # Check CUDA device information
   /usr/local/cuda/extras/demo_suite/deviceQuery
   
   # Verify cuDNN installation
   /usr/local/cuda/extras/demo_suite/bandwidthTest
   ```

### Step 2: Performance Optimization with Error Handling

1. **Apply GPU Optimizations with Validation**
   ```bash
   # Update detected GPU specifications first
   echo "Updating GPU specifications..."
   if ! /opt/citadel/scripts/nvidia-backup-rollback.sh detect; then
       echo "WARNING: Could not detect GPU specifications, using defaults"
   fi
   
   # Run GPU optimization script with error handling
   echo "Applying GPU optimizations..."
   if ! /opt/citadel/scripts/gpu-optimize.sh; then
       echo "ERROR: GPU optimization failed"
       echo "System may still be functional, but performance may not be optimal"
   else
       echo "✅ GPU optimization completed successfully"
   fi
   
   # Verify optimization applied
   echo "Verifying optimization settings..."
   if nvidia-smi -q | grep -E "(Power|Performance|Clocks)" >/dev/null; then
       echo "✅ GPU optimization verified"
   else
       echo "WARNING: Could not verify GPU optimization settings"
   fi
   ```

2. **Configure Automatic Optimization on Boot with Error Handling**
   ```bash
   # Check if GPU optimization script exists
   if [ ! -f "/opt/citadel/scripts/gpu-optimize.sh" ]; then
       echo "ERROR: GPU optimization script not found"
       exit 1
   fi
   
   # Check if nvidia-persistenced service exists
   AFTER_SERVICE=""
   REQUIRES_SERVICE=""
   if sudo systemctl list-unit-files | grep -q "nvidia-persistenced.service"; then
       AFTER_SERVICE="After=nvidia-persistenced.service"
       REQUIRES_SERVICE="Requires=nvidia-persistenced.service"
       echo "NVIDIA persistence service detected - adding dependency"
   else
       echo "NVIDIA persistence service not available - creating independent service"
   fi
   
   # Create systemd service for GPU optimization
   echo "Creating GPU optimization service..."
   sudo tee /etc/systemd/system/gpu-optimize.service << EOF
   [Unit]
   Description=GPU Optimization for AI Workloads
   ${AFTER_SERVICE}
   ${REQUIRES_SERVICE}
   
   [Service]
   Type=oneshot
   ExecStart=/opt/citadel/scripts/gpu-optimize.sh
   RemainAfterExit=yes
   StandardOutput=journal
   StandardError=journal
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Reload systemd and enable the service
   if ! sudo systemctl daemon-reload; then
       echo "ERROR: Failed to reload systemd daemon"
       exit 1
   fi
   
   if ! sudo systemctl enable gpu-optimize.service; then
       echo "ERROR: Failed to enable gpu-optimize service"
       exit 1
   fi
   
   # Test the service
   echo "Testing GPU optimization service..."
   if sudo systemctl start gpu-optimize.service; then
       echo "✅ GPU optimization service started successfully"
       
       # Check service status
       if sudo systemctl is-active gpu-optimize.service >/dev/null 2>&1; then
           echo "✅ GPU optimization service is active"
       else
           echo "WARNING: GPU optimization service started but is not active"
           sudo systemctl status gpu-optimize.service
       fi
   else
       echo "ERROR: Failed to start gpu-optimize service"
       sudo systemctl status gpu-optimize.service
       exit 1
   fi
   ```

### Step 3: Advanced Configuration

1. **Configure GPU Topology**
   ```bash
   # Check GPU topology
   nvidia-smi topo -m
   
   # Create topology optimization script
   sudo tee /opt/citadel/scripts/gpu-topology.sh << 'EOF'
   #!/bin/bash
   # gpu-topology.sh - Display and optimize GPU topology
   
   echo "=== GPU Topology Information ==="
   nvidia-smi topo -m
   echo ""
   
   echo "=== PCIe Information ==="
   lspci | grep -i nvidia
   echo ""
   
   echo "=== NUMA Topology ==="
   numactl --hardware | grep -A 20 "available:"
   EOF
   
   chmod +x /opt/citadel/scripts/gpu-topology.sh
   ```

2. **Configure Multi-GPU Settings**
   ```bash
   # Create multi-GPU configuration
   sudo tee /etc/modprobe.d/nvidia.conf << 'EOF'
   # NVIDIA driver configuration for multi-GPU setup
   options nvidia NVreg_DeviceFileUID=0 NVreg_DeviceFileGID=44 NVreg_DeviceFileMode=0660
   options nvidia NVreg_ModifyDeviceFiles=1
   options nvidia NVreg_EnableGpuFirmware=1
   
   # Performance optimizations
   options nvidia NVreg_UsePageAttributeTable=1
   options nvidia NVreg_EnableMSI=1
   options nvidia NVreg_TCEBypassMode=1
   EOF
   
   # Update initramfs
   sudo update-initramfs -u
   ```

## Validation Steps

### Step 1: Driver Verification
```bash
# Comprehensive driver verification
echo "=== NVIDIA Driver Verification ==="

# Check driver version
nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits
echo "Expected: 570.x series"
echo ""

# Check CUDA version
nvcc --version | grep "release"
echo "Expected: CUDA 12.4 or higher"
echo ""

# Verify GPU detection
nvidia-smi -L
echo "Expected: 2 GPUs detected"
```

### Step 2: CUDA Functionality Test
```bash
# Test CUDA functionality
echo "=== CUDA Functionality Test ==="

# Run CUDA device query
/usr/local/cuda/extras/demo_suite/deviceQuery | grep -E "(CUDA|Device|Memory)"

# Run bandwidth test
/usr/local/cuda/extras/demo_suite/bandwidthTest | grep -E "(Bandwidth|PASSED|FAILED)"

# Test cuDNN samples (if available)
if [ -d "/usr/src/cudnn_samples_v9" ]; then
    cd /usr/src/cudnn_samples_v9/mnistCUDNN
    sudo make clean && sudo make
    ./mnistCUDNN
fi
```

### Step 3: Performance Verification
```bash
# Verify GPU performance settings
echo "=== GPU Performance Verification ==="

# Check power management
nvidia-smi --query-gpu=persistence_mode,power.management --format=csv,noheader

# Check performance state
nvidia-smi --query-gpu=pstate --format=csv,noheader

# Check compute mode
nvidia-smi --query-gpu=compute_mode --format=csv,noheader

# Run quick performance test
python3 << 'EOF'
import subprocess
import time

print("Testing GPU compute performance...")
start_time = time.time()

# Simple matrix multiplication test
result = subprocess.run([
    'python3', '-c', 
    '''
import torch
if torch.cuda.is_available():
    device = torch.cuda.current_device()
    print(f"GPU {device}: {torch.cuda.get_device_name(device)}")
    a = torch.randn(1000, 1000).cuda()
    b = torch.randn(1000, 1000).cuda()
    c = torch.matmul(a, b)
    print("Matrix multiplication test: PASSED")
else:
    print("CUDA not available")
    '''
], capture_output=True, text=True)

print(result.stdout)
print(f"Test completed in {time.time() - start_time:.2f} seconds")
EOF
```

### Step 4: Multi-GPU Test
```bash
# Test multi-GPU functionality
echo "=== Multi-GPU Functionality Test ==="

python3 << 'EOF'
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")
print(f"Number of GPUs: {torch.cuda.device_count()}")

if torch.cuda.device_count() >= 2:
    for i in range(torch.cuda.device_count()):
        print(f"GPU {i}: {torch.cuda.get_device_name(i)}")
        print(f"  Memory: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.1f} GB")
    print("Multi-GPU test: PASSED")
else:
    print("Multi-GPU test: FAILED - Less than 2 GPUs detected")
EOF
```

## Troubleshooting

### Issue: Driver Installation Fails
**Symptoms**: Package conflicts, dependency issues
**Solutions**:
- Clean reinstall: `sudo apt purge nvidia* && sudo apt autoremove`
- Check kernel headers: `sudo apt install linux-headers-$(uname -r)`
- Disable Secure Boot temporarily if needed

### Issue: CUDA Not Detected
**Symptoms**: `nvcc: command not found`, CUDA libraries missing
**Solutions**:
- Verify PATH: `echo $PATH | grep cuda`
- Reinstall CUDA: `sudo apt install --reinstall cuda-toolkit-12-4`
- Source environment: `source ~/.bashrc`

### Issue: GPU Performance Issues
**Symptoms**: Low GPU utilization, thermal throttling
**Solutions**:
- Check power limits: `nvidia-smi -q | grep Power`
- Verify cooling: `nvidia-smi --query-gpu=temperature.gpu --format=csv`
- Apply optimizations: `/opt/citadel/scripts/gpu-optimize.sh`

### Issue: Multi-GPU Problems
**Symptoms**: Only one GPU detected, topology issues
**Solutions**:
- Check PCIe slots: `lspci | grep -i nvidia`
- Verify power supply adequacy
- Check BIOS settings for multi-GPU support

## Configuration Summary

### Installed Components
- ✅ **NVIDIA Driver**: 570.x series
- ✅ **CUDA Toolkit**: 12.4+
- ✅ **cuDNN**: 9.x
- ✅ **Performance Optimization**: Applied
- ✅ **Multi-GPU Support**: Configured
- ✅ **Monitoring Tools**: Installed

### Performance Settings
- **Persistence Mode**: Enabled
- **Performance State**: P0 (Maximum)
- **Compute Mode**: Exclusive Process
- **Power Management**: Maximum Performance
- **Memory/Graphics Clocks**: Maximum stable

### Service Configuration
- **nvidia-persistenced**: Enabled and running
- **gpu-optimize**: Runs on boot
- **Monitoring**: Available via scripts

## Next Steps

Continue to **[PLANB-04-Python-Environment.md](PLANB-04-Python-Environment.md)** for Python 3.12 environment setup with virtual environment configuration.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 45-60 minutes  
**Complexity**: High  
**Prerequisites**: Ubuntu 24.04 installed, GPU hardware present, system rebooted after installation