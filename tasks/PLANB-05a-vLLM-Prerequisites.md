# PLANB-05a: vLLM Installation Prerequisites

**Task:** Environment preparation and dependency setup for vLLM installation  
**Duration:** 30-45 minutes  
**Prerequisites:** PLANB-01 through PLANB-04 completed  

## Overview

This document covers the prerequisite steps required before installing vLLM, including environment preparation, system dependencies, and configuration setup.

## Environment Configuration

### Step 1: Configuration Setup

Before starting, ensure you have properly configured your environment variables:

1. **Copy Environment Template**
   ```bash
   # Copy the environment template
   cp .env.example .env
   
   # Edit with your actual values
   nano .env
   ```

2. **Required Configuration Variables**
   ```bash
   # Essential variables that must be set
   HF_TOKEN=hf_your_actual_token_here
   DEV_ENV_PATH=/opt/citadel/dev-env
   MODEL_STORAGE_PATH=/mnt/citadel-models
   MAX_JOBS=8
   TORCH_CUDA_ARCH_LIST=8.9
   ```

3. **Validate Configuration**
   ```bash
   # Test configuration loading
   python -c "
   from configs.vllm_settings import load_vllm_settings
   install_settings, model_settings, test_settings = load_vllm_settings()
   print('✅ Configuration loaded successfully')
   print(f'Environment: {install_settings.dev_env_path}')
   print(f'GPU Memory: {install_settings.gpu_memory_utilization}')
   "
   ```

### Step 2: Environment Verification

1. **Verify Current Installation State**
   ```bash
   # Activate development environment
   source /opt/citadel/dev-env/bin/activate
   
   # Check current Python and PyTorch versions
   echo "=== Current Environment State ==="
   python --version
   python -c "import torch; print(f'PyTorch: {torch.__version__}')"
   python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
   python -c "import torch; print(f'CUDA Version: {torch.version.cuda}')"
   pip list | grep -E "(torch|transformers|vllm)"
   ```

2. **Clean Previous vLLM Installation**
   ```bash
   # Remove any existing vLLM installation
   pip uninstall vllm -y
   pip uninstall vllm-flash-attn -y
   pip uninstall flash-attn -y
   
   # Clear pip cache
   pip cache purge
   
   # Verify clean state
   pip list | grep vllm || echo "vLLM successfully removed"
   ```

## System Dependencies Installation

### Step 1: Build Dependencies

1. **Install System Packages**
   ```bash
   # Install system packages required for vLLM compilation
   sudo apt update
   sudo apt install -y \
     build-essential \
     cmake \
     ninja-build \
     python3.12-dev \
     libopenmpi-dev \
     libaio-dev \
     libcurl4-openssl-dev \
     libssl-dev \
     libffi-dev \
     libnuma-dev \
     pkg-config
   
   # Install additional compilation tools
   sudo apt install -y \
     gcc-11 \
     g++-11 \
     libc6-dev \
     libc-dev-bin \
     linux-libc-dev
   ```

2. **Configure GCC Version**
   ```bash
   # Set GCC version for compilation
   sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100
   sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100
   
   # Verify GCC version
   gcc --version
   g++ --version
   ```

### Step 2: Compilation Environment Setup

1. **Configure Environment Variables**
   ```bash
   # Load configuration and set environment variables
   python -c "
   from configs.vllm_settings import load_vllm_settings, get_environment_variables
   install_settings, _, _ = load_vllm_settings()
   env_vars = get_environment_variables(install_settings)
   
   # Generate export commands
   for key, value in env_vars.items():
       print(f'export {key}=\"{value}\"')
   " > /tmp/vllm_env_setup.sh
   
   # Source the environment setup
   source /tmp/vllm_env_setup.sh
   
   # Verify environment variables
   echo "CC: $CC"
   echo "CXX: $CXX"
   echo "TORCH_CUDA_ARCH_LIST: $TORCH_CUDA_ARCH_LIST"
   echo "MAX_JOBS: $MAX_JOBS"
   ```

2. **Persist Environment Configuration**
   ```bash
   # Add to shell profile for persistence
   tee -a ~/.bashrc << 'EOF'
   
   # vLLM Compilation Environment (Auto-generated)
   # Load from configuration system
   if [ -f "/home/agent0/Citadel-Alpha-LLM-Server-1/.env" ]; then
       export $(grep -v '^#' /home/agent0/Citadel-Alpha-LLM-Server-1/.env | xargs)
   fi
   EOF
   
   source ~/.bashrc
   ```

## Dependency Updates

### Step 1: Core Dependencies

1. **Update Package Management Tools**
   ```bash
   # Update core dependencies to latest compatible versions
   pip install --upgrade \
     pip \
     setuptools \
     wheel \
     packaging \
     ninja
   ```

2. **Update PyTorch**
   ```bash
   # Update PyTorch to latest stable version
   pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   
   # Verify PyTorch update
   python -c "import torch; print(f'Updated PyTorch: {torch.__version__}')"
   python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
   ```

## Hugging Face Authentication

### Step 1: Configure Authentication

1. **Set Up HF CLI**
   ```bash
   # Install Hugging Face Hub CLI
   pip install huggingface_hub[cli]>=0.19.0
   
   # Configure authentication using environment variable
   echo "${HF_TOKEN}" | huggingface-cli login --token
   
   # Verify authentication
   huggingface-cli whoami
   ```

2. **Set Cache Directories**
   ```bash
   # Create cache directories
   mkdir -p /mnt/citadel-models/cache
   mkdir -p /mnt/citadel-models/cache/transformers
   
   # Set permissions
   chmod 755 /mnt/citadel-models/cache
   chmod 755 /mnt/citadel-models/cache/transformers
   
   echo "✅ Hugging Face authentication and cache configured"
   ```

## Compatibility Verification

### vLLM Compatibility Matrix

```yaml
target_configuration:
  vllm_version: "0.6.1+"
  pytorch_version: "2.4+"
  cuda_version: "12.4+"
  python_version: "3.12"
  gpu_architecture: "Ada Lovelace (RTX 4070 Ti SUPER)"

compatibility_status:
  vllm_0.6.1:
    pytorch: ">=2.1.0,<2.8.0"
    python: ">=3.8,<=3.12"
    cuda: ">=11.8,<=12.5"
    transformers: ">=4.36.0"
    status: "✅ COMPATIBLE"
```

### Verification Commands

```bash
# Run compatibility check
python -c "
import sys
import torch

print('=== Compatibility Check ===')
print(f'Python: {sys.version}')
print(f'PyTorch: {torch.__version__}')
print(f'CUDA: {torch.version.cuda}')
print(f'GPU Available: {torch.cuda.is_available()}')

if torch.cuda.is_available():
    print(f'GPU Count: {torch.cuda.device_count()}')
    for i in range(torch.cuda.device_count()):
        print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')

# Check Python version compatibility
py_version = sys.version_info
if py_version.major == 3 and py_version.minor == 12:
    print('✅ Python version compatible')
else:
    print('⚠️ Python version may have issues')

# Check PyTorch version
torch_version = torch.__version__.split('.')
if int(torch_version[0]) >= 2 and int(torch_version[1]) >= 1:
    print('✅ PyTorch version compatible')
else:
    print('⚠️ PyTorch version may have issues')
"
```

## Pre-Installation Checklist

Before proceeding to installation, verify all prerequisites:

- [ ] ✅ Configuration files created and validated
- [ ] ✅ Environment variables properly set
- [ ] ✅ System dependencies installed
- [ ] ✅ GCC/G++ version configured
- [ ] ✅ PyTorch updated to latest compatible version
- [ ] ✅ Hugging Face authentication configured
- [ ] ✅ Cache directories created with proper permissions
- [ ] ✅ Compatibility verification passed

## Troubleshooting Prerequisites

### Common Issues

1. **Configuration Loading Fails**
   - Ensure `.env` file exists and contains required variables
   - Check file permissions on configuration files
   - Validate environment variable syntax

2. **GCC Version Issues**
   - Verify GCC-11 is installed: `gcc-11 --version`
   - Check alternatives: `update-alternatives --display gcc`
   - Ensure development packages are installed

3. **CUDA Not Available**
   - Verify NVIDIA drivers: `nvidia-smi`
   - Check CUDA installation: `nvcc --version`
   - Ensure PyTorch CUDA version matches system CUDA

4. **HF Authentication Fails**
   - Verify token format (starts with `hf_`)
   - Check token permissions on Hugging Face
   - Ensure network connectivity to huggingface.co

## Next Steps

Once all prerequisites are completed and verified, proceed to:
- **[PLANB-05b-vLLM-Installation.md](PLANB-05b-vLLM-Installation.md)** for core vLLM installation

---

**Status**: ✅ **Prerequisites Ready**  
**Estimated Time**: 30-45 minutes  
**Complexity**: Medium  
**Critical**: Proper configuration and dependency setup are essential for successful vLLM installation