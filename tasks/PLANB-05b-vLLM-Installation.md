# PLANB-05b: vLLM Core Installation

**Task:** Install latest vLLM version with configuration management  
**Duration:** 30-60 minutes  
**Prerequisites:** PLANB-05a-vLLM-Prerequisites.md completed  

## Overview

This document covers the core vLLM installation process using the configuration management system. Choose from two installation methods based on your needs and time constraints.

## Installation Methods

### Method 1: Quick Install (Recommended)
**Duration**: 15-30 minutes  
**Complexity**: Low  
**Best for**: Users who want a fast, proven installation with minimal steps  

#### Quick Installation Script

Use the configured quick installation script:

```bash
# Ensure environment is activated
source /opt/citadel/dev-env/bin/activate

# Run the quick installation script
./scripts/vllm_quick_install.sh
```

#### Manual Quick Install

If you prefer to run commands manually:

```bash
# Load configuration and activate environment
source /opt/citadel/dev-env/bin/activate

# Install vLLM with all dependencies using configuration
python -c "
from configs.vllm_settings import load_vllm_settings
install_settings, _, _ = load_vllm_settings()
print('Installing vLLM with configuration-based dependencies...')
"

# Install vLLM
pip install vllm

# Install core dependencies
pip install \
    transformers>=4.36.0 \
    tokenizers>=0.15.0 \
    accelerate>=0.25.0 \
    bitsandbytes>=0.41.0 \
    scipy>=1.11.0 \
    numpy>=1.24.0 \
    requests>=2.31.0 \
    aiohttp>=3.9.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    pydantic>=2.5.0 \
    huggingface-hub>=0.19.0

# Install monitoring and utilities
pip install \
    prometheus-client>=0.19.0 \
    psutil>=5.9.0 \
    GPUtil>=1.4.0 \
    py3nvml>=0.2.7 \
    rich>=13.7.0
```

### Method 2: Detailed Install with Error Handling
**Duration**: 45-60 minutes  
**Complexity**: High  
**Best for**: Users who need step-by-step control and comprehensive error handling  

#### Step 1: Install Core vLLM

```bash
# Activate environment
source /opt/citadel/dev-env/bin/activate

# Install vLLM with error handling
echo "Installing vLLM latest version..."
if pip install vllm; then
    echo "✅ vLLM installation successful"
    python -c "import vllm; print(f'vLLM version: {vllm.__version__}')"
else
    echo "❌ vLLM installation failed, trying alternative method..."
    # Alternative installation from source
    cd /tmp
    git clone --depth 1 https://github.com/vllm-project/vllm.git
    cd vllm
    pip install -e .
    cd /opt/citadel && rm -rf /tmp/vllm
fi
```

#### Step 2: Install Dependencies with Rollback

```bash
# Create rollback point
pip freeze > /tmp/pre_vllm_packages.txt

# Install dependencies with error handling
echo "Installing vLLM dependencies..."

# Core ML dependencies
if ! pip install \
    transformers>=4.36.0 \
    tokenizers>=0.15.0 \
    accelerate>=0.25.0 \
    scipy>=1.11.0 \
    numpy>=1.24.0; then
    echo "❌ Core ML dependencies failed, rolling back..."
    pip uninstall -y -r /tmp/pre_vllm_packages.txt
    exit 1
fi

# Web framework dependencies
if ! pip install \
    fastapi>=0.104.0 \
    uvicorn[standard]>=0.24.0 \
    pydantic>=2.5.0 \
    aiohttp>=3.9.0; then
    echo "❌ Web framework dependencies failed, rolling back..."
    pip uninstall -y -r /tmp/pre_vllm_packages.txt
    exit 1
fi

# Monitoring dependencies
pip install \
    prometheus-client>=0.19.0 \
    psutil>=5.9.0 \
    GPUtil>=1.4.0 \
    py3nvml>=0.2.7 \
    rich>=13.7.0

echo "✅ All dependencies installed successfully"
```

## Flash Attention Installation (Optional)

### Performance Enhancement

Flash Attention significantly improves performance for long sequences:

```bash
# Install flash-attn with error handling
echo "Installing Flash Attention (this may take 10-15 minutes)..."

# Method 1: Standard installation
if pip install flash-attn --no-build-isolation; then
    echo "✅ Flash Attention installed successfully"
    python -c "import flash_attn; print('Flash Attention working')" 2>/dev/null || echo "⚠️ Flash Attention import failed"
else
    echo "⚠️ Flash Attention installation failed (optional component)"
    echo "Continuing without Flash Attention..."
fi
```

## Configuration Integration

### Apply Configuration Settings

```bash
# Apply configuration-based environment setup
python -c "
from configs.vllm_settings import load_vllm_settings, get_environment_variables
import os

# Load settings
install_settings, model_settings, test_settings = load_vllm_settings()

# Set environment variables
env_vars = get_environment_variables(install_settings)
for key, value in env_vars.items():
    os.environ[key] = value
    print(f'Set {key}={value}')

print('✅ Configuration applied successfully')
"
```

### Hugging Face Integration

```bash
# Configure HF authentication using settings
python -c "
from configs.vllm_settings import load_vllm_settings
import os
import subprocess

install_settings, _, _ = load_vllm_settings()

# Set HF environment variables
os.environ['HF_TOKEN'] = install_settings.hf_token
os.environ['HF_HOME'] = install_settings.hf_cache_dir
os.environ['TRANSFORMERS_CACHE'] = install_settings.transformers_cache

# Login to HF
result = subprocess.run(['huggingface-cli', 'login', '--token', install_settings.hf_token], 
                       input='', capture_output=True, text=True)
if result.returncode == 0:
    print('✅ Hugging Face authentication successful')
else:
    print('❌ Hugging Face authentication failed')
    print(result.stderr)
"
```

## Installation Verification

### Basic Verification

Run the comprehensive validation suite:

```bash
# Run installation validation
python tests/validation/test_vllm_installation.py
```

### Manual Verification

```bash
# Manual verification steps
echo "=== vLLM Installation Verification ==="

# Check vLLM version and core functionality
python -c "
import vllm
import torch
import transformers
import fastapi
from configs.vllm_settings import load_vllm_settings

# Load configuration
install_settings, model_settings, test_settings = load_vllm_settings()

print('=== Installation Summary ===')
print(f'✅ vLLM version: {vllm.__version__}')
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ Transformers: {transformers.__version__}')
print(f'✅ FastAPI: {fastapi.__version__}')
print(f'✅ CUDA available: {torch.cuda.is_available()}')
print(f'✅ GPU count: {torch.cuda.device_count()}')

if torch.cuda.is_available():
    for i in range(torch.cuda.device_count()):
        print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')

print(f'✅ Configuration loaded: {install_settings.dev_env_path}')
print(f'✅ Test model: {test_settings.test_model}')
print('🎉 All core components verified!')
"
```

## Error Handling and Rollback

### Common Installation Errors

1. **CUDA Compilation Errors**
   ```bash
   # Check CUDA setup
   nvcc --version
   echo $CUDA_HOME
   echo $TORCH_CUDA_ARCH_LIST
   
   # Reinstall with specific CUDA version if needed
   pip uninstall torch torchvision torchaudio -y
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   ```

2. **Memory Issues During Compilation**
   ```bash
   # Reduce parallel jobs
   export MAX_JOBS=4
   pip install vllm --no-cache-dir
   ```

3. **Dependency Conflicts**
   ```bash
   # Create fresh environment
   python -m venv /tmp/vllm_test_env
   source /tmp/vllm_test_env/bin/activate
   pip install vllm
   # Test in isolation, then copy working packages
   ```

### Rollback Procedures

```bash
# Complete rollback to pre-installation state
pip freeze > /tmp/current_packages.txt
pip uninstall -y -r /tmp/current_packages.txt
pip install -r /tmp/pre_vllm_packages.txt

# Verify rollback
python -c "
try:
    import vllm
    print('❌ Rollback failed - vLLM still installed')
except ImportError:
    print('✅ Rollback successful - vLLM removed')
"
```

## Performance Optimization

### GPU Memory Configuration

```bash
# Set optimal GPU memory utilization
python -c "
from configs.vllm_settings import load_vllm_settings
install_settings, _, _ = load_vllm_settings()

print(f'GPU Memory Utilization: {install_settings.gpu_memory_utilization}')
print(f'Tensor Parallel Size: {install_settings.tensor_parallel_size}')
print(f'CUDA Architecture: {install_settings.cuda_arch}')
"
```

### Compilation Optimization

```bash
# Verify compilation settings
echo "=== Compilation Configuration ==="
echo "CC: $CC"
echo "CXX: $CXX"
echo "NVCC_PREPEND_FLAGS: $NVCC_PREPEND_FLAGS"
echo "TORCH_CUDA_ARCH_LIST: $TORCH_CUDA_ARCH_LIST"
echo "MAX_JOBS: $MAX_JOBS"
```

## Post-Installation Tasks

### Update Existing Scripts

Update existing scripts to use the new configuration system:

```bash
# Update vllm_quick_install.sh to use configuration
# Update start_vllm_server.py to use configuration
# Update test_vllm_client.py to use configuration
```

### Create Service Scripts

Reference the updated scripts in the [`/scripts/`](../scripts/) directory:
- [`scripts/start_vllm_server.py`](../scripts/start_vllm_server.py) - Server startup
- [`scripts/test_vllm_client.py`](../scripts/test_vllm_client.py) - Client testing
- [`scripts/vllm_quick_install.sh`](../scripts/vllm_quick_install.sh) - Quick installation

## Installation Summary

After successful installation, you should have:

- ✅ **vLLM**: Latest compatible version (0.6.1+)
- ✅ **Dependencies**: All required packages with proper versions
- ✅ **Configuration**: Centralized configuration management
- ✅ **Authentication**: Hugging Face integration
- ✅ **Optimization**: GPU and compilation optimizations
- ✅ **Validation**: Comprehensive test suite

## Next Steps

Once installation is complete, proceed to:
- **[PLANB-05c-vLLM-Validation.md](PLANB-05c-vLLM-Validation.md)** for comprehensive testing
- **[PLANB-05d-vLLM-Troubleshooting.md](PLANB-05d-vLLM-Troubleshooting.md)** if issues arise

---

**Status**: ✅ **Installation Ready**  
**Estimated Time**: 30-60 minutes  
**Complexity**: Medium to High  
**Critical**: Proper error handling and configuration integration are essential