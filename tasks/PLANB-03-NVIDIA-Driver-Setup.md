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

### Step 1: System Preparation

1. **Remove Existing NVIDIA Drivers**
   ```bash
   # Remove any existing NVIDIA packages
   sudo apt remove --purge nvidia* -y
   sudo apt remove --purge cuda* -y
   sudo apt remove --purge libnvidia* -y
   sudo apt autoremove -y
   sudo apt autoclean
   
   # Remove NVIDIA configuration files
   sudo rm -rf /etc/X11/xorg.conf
   sudo rm -rf /etc/modprobe.d/nvidia*
   sudo rm -rf /etc/modprobe.d/blacklist-nvidia*
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

### Step 2: Configure Repository and Install Driver

1. **Add NVIDIA Repository**
   ```bash
   # Add NVIDIA package repository for Ubuntu 24.04
   wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/cuda-keyring_1.1-1_all.deb
   sudo dpkg -i cuda-keyring_1.1-1_all.deb
   sudo apt update
   
   # Verify repository addition
   apt-cache policy | grep -i nvidia
   ```

2. **Install NVIDIA Driver 570.x**
   ```bash
   # Search for available 570.x drivers
   apt-cache search nvidia-driver-570
   
   # Install the latest 570.x driver
   sudo apt install -y nvidia-driver-570
   
   # Alternative: Install specific version if needed
   # sudo apt install -y nvidia-driver-570-server
   ```

3. **Install CUDA Toolkit 12.4+**
   ```bash
   # Install CUDA Toolkit
   sudo apt install -y cuda-toolkit-12-4
   
   # Install additional CUDA development tools
   sudo apt install -y \
     cuda-compiler-12-4 \
     cuda-libraries-dev-12-4 \
     cuda-driver-dev-12-4 \
     cuda-cudart-dev-12-4 \
     cuda-nvml-dev-12-4
   ```

4. **Install cuDNN 9.x**
   ```bash
   # Install cuDNN runtime and development packages
   sudo apt install -y \
     libcudnn9 \
     libcudnn9-dev \
     libcudnn9-samples
   ```

### Step 3: System Configuration

1. **Configure Environment Variables**
   ```bash
   # Add CUDA to system PATH and library path
   sudo tee /etc/environment << 'EOF'
   PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/usr/local/cuda/bin"
   CUDA_HOME="/usr/local/cuda"
   CUDA_ROOT="/usr/local/cuda"
   LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64"
   EOF
   
   # Add CUDA paths to user profile
   tee -a ~/.bashrc << 'EOF'
   
   # NVIDIA CUDA Configuration
   export CUDA_HOME="/usr/local/cuda"
   export CUDA_ROOT="/usr/local/cuda"
   export PATH="/usr/local/cuda/bin:$PATH"
   export LD_LIBRARY_PATH="/usr/local/cuda/lib64:/usr/local/cuda/extras/CUPTI/lib64:$LD_LIBRARY_PATH"
   export NVIDIA_VISIBLE_DEVICES=all
   export NVIDIA_DRIVER_CAPABILITIES=compute,utility
   EOF
   
   # Apply environment changes
   source ~/.bashrc
   ```

2. **Configure GPU Persistence Mode**
   ```bash
   # Create systemd service for GPU persistence
   sudo tee /etc/systemd/system/nvidia-persistenced.service << 'EOF'
   [Unit]
   Description=NVIDIA Persistence Daemon
   After=syslog.target network.target
   
   [Service]
   Type=forking
   PIDFile=/var/run/nvidia-persistenced/nvidia-persistenced.pid
   Restart=always
   ExecStart=/usr/bin/nvidia-persistenced --verbose
   ExecStopPost=/bin/rm -rf /var/run/nvidia-persistenced
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable and start the service
   sudo systemctl enable nvidia-persistenced
   sudo systemctl start nvidia-persistenced
   ```

3. **Optimize GPU Performance**
   ```bash
   # Create GPU optimization script
   sudo tee /opt/citadel/scripts/gpu-optimize.sh << 'EOF'
   #!/bin/bash
   # gpu-optimize.sh - Optimize GPU settings for AI workloads
   
   echo "=== GPU Optimization for AI Workloads ==="
   
   # Set GPU performance mode
   sudo nvidia-smi -pm 1
   
   # Set maximum power limit (if supported)
   sudo nvidia-smi -pl 320  # Adjust based on your GPU specs
   
   # Set GPU application clocks to maximum
   sudo nvidia-smi -ac 9501,2610  # Memory,Graphics clocks for RTX 4070 Ti SUPER
   
   # Enable ECC if supported (usually not on consumer cards)
   # sudo nvidia-smi -e 1
   
   # Set compute mode to exclusive process
   sudo nvidia-smi -c 3
   
   # Display current status
   nvidia-smi
   
   echo "GPU optimization completed"
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

### Step 2: Performance Optimization

1. **Apply GPU Optimizations**
   ```bash
   # Run GPU optimization script
   /opt/citadel/scripts/gpu-optimize.sh
   
   # Verify optimization applied
   nvidia-smi -q | grep -E "(Power|Performance|Clocks)"
   ```

2. **Configure Automatic Optimization on Boot**
   ```bash
   # Create systemd service for GPU optimization
   sudo tee /etc/systemd/system/gpu-optimize.service << 'EOF'
   [Unit]
   Description=GPU Optimization for AI Workloads
   After=nvidia-persistenced.service
   Requires=nvidia-persistenced.service
   
   [Service]
   Type=oneshot
   ExecStart=/opt/citadel/scripts/gpu-optimize.sh
   RemainAfterExit=yes
   
   [Install]
   WantedBy=multi-user.target
   EOF
   
   # Enable the service
   sudo systemctl enable gpu-optimize.service
   sudo systemctl start gpu-optimize.service
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