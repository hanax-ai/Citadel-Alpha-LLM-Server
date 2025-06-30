# PLANB-04: Python 3.12 Environment Setup and Optimization

**Task:** Install and configure Python 3.12 with optimized virtual environment for AI workloads  
**Duration:** 30-45 minutes  
**Prerequisites:** PLANB-01, PLANB-02, and PLANB-03 completed, NVIDIA drivers installed  

## Overview

This task installs Python 3.12 with optimized configurations for AI/ML workloads, creates dedicated virtual environments, and installs PyTorch with CUDA 12.4+ support.

## Python 3.12 Features for AI Workloads

### Performance Improvements
- **30% faster than Python 3.11** for compute-intensive tasks
- **Improved memory management** for large model handling
- **Better threading performance** for concurrent model inference
- **Optimized bytecode** for AI library operations

### Key Features
- **Fine-grained error locations** for better debugging
- **Improved typing** for better code quality
- **Enhanced performance profiling** for optimization
- **Better asyncio support** for concurrent operations

## Installation Steps

### Step 1: Python 3.12 Installation

1. **Add Python 3.12 Repository**
   ```bash
   # Add deadsnakes PPA for latest Python versions
   sudo apt update
   sudo apt install -y software-properties-common
   sudo add-apt-repository ppa:deadsnakes/ppa -y
   sudo apt update
   
   # Verify repository addition
   apt-cache policy python3.12
   ```

2. **Install Python 3.12 with Development Tools**
   ```bash
   # Install Python 3.12 and development packages
   sudo apt install -y \
     python3.12 \
     python3.12-dev \
     python3.12-venv \
     python3.12-distutils \
     python3.12-tk \
     python3.12-gdbm \
     python3.12-dbg
   
   # Install pip for Python 3.12
   curl -sS https://bootstrap.pypa.io/get-pip.py | python3.12
   
   # Install additional build dependencies
   sudo apt install -y \
     python3.12-full \
     build-essential \
     libssl-dev \
     libffi-dev \
     libbz2-dev \
     libreadline-dev \
     libsqlite3-dev \
     libncursesw5-dev \
     xz-utils \
     tk-dev \
     libxml2-dev \
     libxmlsec1-dev \
     liblzma-dev
   ```

3. **Configure Python Alternatives**
   ```bash
   # Set up Python alternatives for easy switching
   sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100
   sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 90
   sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 100
   
   # Set up pip alternatives
   sudo update-alternatives --install /usr/bin/pip3 pip3 /usr/local/bin/pip3.12 100
   sudo update-alternatives --install /usr/bin/pip pip /usr/local/bin/pip3.12 100
   
   # Verify Python version
   python3 --version
   python --version
   pip --version
   ```

### Step 2: Virtual Environment Setup

1. **Create Citadel AI Virtual Environment**
   ```bash
   # Create the main virtual environment for Citadel AI
   cd /opt/citadel
   python3.12 -m venv citadel-env
   
   # Activate the environment
   source citadel-env/bin/activate
   
   # Upgrade pip and install base packages
   pip install --upgrade pip setuptools wheel
   
   # Verify environment
   which python
   python --version
   ```

2. **Create Environment Management Script**
   ```bash
   # Create environment management script
   tee /opt/citadel/scripts/env-manager.sh << 'EOF'
   #!/bin/bash
   # env-manager.sh - Manage Python virtual environments
   
   CITADEL_ROOT="/opt/citadel"
   MAIN_ENV="$CITADEL_ROOT/citadel-env"
   VLLM_ENV="$CITADEL_ROOT/vllm-env"
   DEV_ENV="$CITADEL_ROOT/dev-env"
   
   show_usage() {
       echo "Usage: $0 [activate|deactivate|create|list|info] [env_name]"
       echo ""
       echo "Commands:"
       echo "  activate [env]   - Activate virtual environment (default: citadel-env)"
       echo "  deactivate       - Deactivate current environment"
       echo "  create [env]     - Create new virtual environment"
       echo "  list             - List all environments"
       echo "  info             - Show current environment info"
       echo ""
       echo "Available environments:"
       echo "  citadel-env      - Main application environment"
       echo "  vllm-env         - vLLM inference environment"
       echo "  dev-env          - Development and testing environment"
   }
   
   activate_env() {
       local env_name=${1:-"citadel-env"}
       local env_path="$CITADEL_ROOT/$env_name"
       
       if [ -d "$env_path" ]; then
           echo "Activating environment: $env_name"
           source "$env_path/bin/activate"
           echo "Active environment: $(basename $VIRTUAL_ENV)"
           echo "Python version: $(python --version)"
           echo "Pip version: $(pip --version)"
       else
           echo "Environment $env_name not found at $env_path"
           exit 1
       fi
   }
   
   create_env() {
       local env_name=${1:-"citadel-env"}
       local env_path="$CITADEL_ROOT/$env_name"
       
       if [ -d "$env_path" ]; then
           echo "Environment $env_name already exists"
           exit 1
       fi
       
       echo "Creating environment: $env_name"
       python3.12 -m venv "$env_path"
       source "$env_path/bin/activate"
       pip install --upgrade pip setuptools wheel
       echo "Environment $env_name created successfully"
   }
   
   list_envs() {
       echo "Available environments:"
       for env in citadel-env vllm-env dev-env; do
           if [ -d "$CITADEL_ROOT/$env" ]; then
               echo "  ✅ $env"
           else
               echo "  ❌ $env (not created)"
           fi
       done
   }
   
   show_info() {
       if [ -n "$VIRTUAL_ENV" ]; then
           echo "Active environment: $(basename $VIRTUAL_ENV)"
           echo "Environment path: $VIRTUAL_ENV"
           echo "Python version: $(python --version)"
           echo "Python path: $(which python)"
           echo "Pip version: $(pip --version)"
           echo "Installed packages: $(pip list --format=freeze | wc -l)"
       else
           echo "No virtual environment active"
           echo "System Python: $(python3 --version)"
       fi
   }
   
   case "$1" in
       activate)
           activate_env "$2"
           ;;
       deactivate)
           if [ -n "$VIRTUAL_ENV" ]; then
               deactivate
               echo "Environment deactivated"
           else
               echo "No active environment to deactivate"
           fi
           ;;
       create)
           create_env "$2"
           ;;
       list)
           list_envs
           ;;
       info)
           show_info
           ;;
       *)
           show_usage
           exit 1
           ;;
   esac
   EOF
   
   chmod +x /opt/citadel/scripts/env-manager.sh
   ```

3. **Create Additional Specialized Environments**
   ```bash
   # Create vLLM-specific environment
   /opt/citadel/scripts/env-manager.sh create vllm-env
   
   # Create development environment
   /opt/citadel/scripts/env-manager.sh create dev-env
   
   # List all environments
   /opt/citadel/scripts/env-manager.sh list
   ```

### Step 3: PyTorch Installation with CUDA Support

1. **Install PyTorch in Main Environment**
   ```bash
   # Activate main environment
   source /opt/citadel/citadel-env/bin/activate
   
   # Install PyTorch with CUDA 12.4 support
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   
   # Verify PyTorch installation
   python -c "import torch; print(f'PyTorch version: {torch.__version__}')"
   python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
   python -c "import torch; print(f'CUDA version: {torch.version.cuda}')"
   python -c "import torch; print(f'GPU count: {torch.cuda.device_count()}')"
   ```

2. **Install PyTorch in vLLM Environment**
   ```bash
   # Activate vLLM environment
   source /opt/citadel/vllm-env/bin/activate
   
   # Install PyTorch with CUDA support
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   
   # Install additional ML dependencies
   pip install \
     numpy \
     scipy \
     scikit-learn \
     pandas \
     matplotlib \
     seaborn \
     jupyter \
     notebook \
     ipython
   
   # Verify installation
   python -c "import torch; print('PyTorch with CUDA:', torch.cuda.is_available())"
   ```

### Step 4: Core AI/ML Dependencies Installation

1. **Install Core AI Libraries**
   ```bash
   # Activate main environment
   source /opt/citadel/citadel-env/bin/activate
   
   # Install core AI/ML libraries
   pip install \
     transformers>=4.36.0 \
     tokenizers>=0.15.0 \
     accelerate>=0.25.0 \
     datasets>=2.14.0 \
     evaluate>=0.4.0 \
     huggingface-hub>=0.19.0 \
     safetensors>=0.4.0
   
   # Install additional ML utilities
   pip install \
     numpy>=1.24.0 \
     scipy>=1.11.0 \
     scikit-learn>=1.3.0 \
     pandas>=2.0.0 \
     matplotlib>=3.7.0 \
     seaborn>=0.12.0 \
     plotly>=5.15.0
   
   # Install development and debugging tools
   pip install \
     ipython \
     jupyter \
     notebook \
     jupyterlab \
     pytest \
     black \
     flake8 \
     mypy \
     pre-commit
   ```

2. **Install Web Framework Dependencies**
   ```bash
   # Install FastAPI and related packages
   pip install \
     fastapi>=0.104.0 \
     uvicorn>=0.24.0 \
     pydantic>=2.5.0 \
     aiohttp>=3.9.0 \
     requests>=2.31.0 \
     httpx>=0.25.0
   
   # Install additional web utilities
   pip install \
     python-multipart \
     python-jose[cryptography] \
     passlib[bcrypt] \
     python-dotenv \
     jinja2 \
     aiofiles
   ```

3. **Install Monitoring and System Dependencies**
   ```bash
   # Install monitoring libraries
   pip install \
     prometheus-client>=0.19.0 \
     psutil>=5.9.0 \
     GPUtil>=1.4.0 \
     py3nvml>=0.2.7 \
     nvidia-ml-py3>=7.352.0
   
   # Install system utilities
   pip install \
     rich \
     typer \
     click \
     tqdm \
     colorama \
     tabulate \
     pyyaml \
     toml \
     configparser
   ```

### Step 5: Python Optimization Configuration

1. **Configure Python Performance Settings**
   ```bash
   # Create Python optimization configuration
   tee /opt/citadel/configs/python-optimization.py << 'EOF'
   """
   Python optimization configuration for AI workloads
   """
   import os
   import sys
   import gc
   import threading
   
   # Memory optimization
   def optimize_memory():
       """Optimize Python memory usage for AI workloads"""
       # Enable garbage collection optimization
       gc.set_threshold(700, 10, 10)
       
       # Set memory allocation strategy
       os.environ['MALLOC_ARENA_MAX'] = '4'
       os.environ['MALLOC_MMAP_THRESHOLD_'] = '131072'
       os.environ['MALLOC_TRIM_THRESHOLD_'] = '131072'
       os.environ['MALLOC_TOP_PAD_'] = '131072'
       os.environ['MALLOC_MMAP_MAX_'] = '65536'
   
   # Threading optimization
   def optimize_threading():
       """Optimize threading for multi-GPU workloads"""
       # Set optimal thread count
       num_cores = os.cpu_count()
       os.environ['OMP_NUM_THREADS'] = str(min(num_cores, 16))
       os.environ['MKL_NUM_THREADS'] = str(min(num_cores, 16))
       os.environ['NUMEXPR_NUM_THREADS'] = str(min(num_cores, 16))
       
       # Configure thread affinity
       os.environ['KMP_AFFINITY'] = 'granularity=fine,verbose,compact,1,0'
   
   # CUDA optimization
   def optimize_cuda():
       """Optimize CUDA settings for PyTorch"""
       # Enable CUDA memory optimization
       os.environ['CUDA_LAUNCH_BLOCKING'] = '0'
       os.environ['CUDA_CACHE_DISABLE'] = '0'
       os.environ['CUDA_AUTO_BOOST'] = '1'
       
       # Set memory management
       os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
       
       # Enable tensor core usage
       os.environ['NVIDIA_TF32_OVERRIDE'] = '1'
   
   # Hugging Face configuration
   def configure_huggingface():
       """Configure Hugging Face authentication and cache"""
       # Set authentication token
       os.environ['HF_TOKEN'] = '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'
       os.environ['HUGGINGFACE_HUB_TOKEN'] = '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'
       
       # Set cache directories
       os.environ['HF_HOME'] = '/mnt/citadel-models/cache'
       os.environ['TRANSFORMERS_CACHE'] = '/mnt/citadel-models/cache/transformers'
       os.environ['HF_DATASETS_CACHE'] = '/mnt/citadel-models/cache/datasets'
       
       print("Hugging Face authentication and cache configured")
   
   # Apply all optimizations
   def apply_optimizations():
       """Apply all Python optimizations"""
       optimize_memory()
       optimize_threading()
       optimize_cuda()
       configure_huggingface()
       print("Python optimizations applied")
   
   if __name__ == "__main__":
       apply_optimizations()
   EOF
   ```

2. **Create Environment Activation Script**
   ```bash
   # Create enhanced activation script
   tee /opt/citadel/scripts/activate-citadel.sh << 'EOF'
   #!/bin/bash
   # activate-citadel.sh - Activate Citadel AI environment with optimizations
   
   CITADEL_ROOT="/opt/citadel"
   CITADEL_USER="agent0"
   
   echo "🚀 Activating Citadel AI Environment for user: $CITADEL_USER"
   echo "🌐 Hana-X Lab Environment (db server - 192.168.10.35)"
   echo "========================================================="
   
   # Activate virtual environment
   if [ -f "$CITADEL_ROOT/citadel-env/bin/activate" ]; then
       source "$CITADEL_ROOT/citadel-env/bin/activate"
       echo "✅ Virtual environment activated"
   else
       echo "❌ Virtual environment not found"
       exit 1
   fi
   
   # Apply Python optimizations
   if [ -f "$CITADEL_ROOT/configs/python-optimization.py" ]; then
       python "$CITADEL_ROOT/configs/python-optimization.py"
       echo "✅ Python optimizations applied"
   fi
   
   # Set Hugging Face authentication
   export HF_TOKEN="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"
   export HUGGINGFACE_HUB_TOKEN="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"
   export HF_HOME="/mnt/citadel-models/cache"
   export TRANSFORMERS_CACHE="/mnt/citadel-models/cache/transformers"
   
   # Set additional environment variables
   export CITADEL_ROOT="/opt/citadel"
   export CITADEL_MODELS="/opt/citadel/models"
   export CITADEL_CONFIGS="/opt/citadel/configs"
   export CITADEL_LOGS="/opt/citadel/logs"
   
   # Display environment info
   echo ""
   echo "Environment Information:"
   echo "  Python: $(python --version)"
   echo "  Virtual Env: $(basename $VIRTUAL_ENV)"
   echo "  PyTorch: $(python -c 'import torch; print(torch.__version__)' 2>/dev/null || echo 'Not installed')"
   echo "  CUDA Available: $(python -c 'import torch; print(torch.cuda.is_available())' 2>/dev/null || echo 'Unknown')"
   echo "  GPU Count: $(python -c 'import torch; print(torch.cuda.device_count())' 2>/dev/null || echo 'Unknown')"
   echo ""
   echo "🎯 Citadel AI environment ready!"
   EOF
   
   chmod +x /opt/citadel/scripts/activate-citadel.sh
   ```

## Validation Steps

### Step 1: Python Installation Verification
```bash
# Verify Python 3.12 installation
echo "=== Python Installation Verification ==="
python3.12 --version
python3 --version
python --version

# Check pip installation
pip --version
pip3 --version

# Verify alternative configuration
update-alternatives --list python3
update-alternatives --list pip
```

### Step 2: Virtual Environment Testing
```bash
# Test environment management
echo "=== Virtual Environment Testing ==="
/opt/citadel/scripts/env-manager.sh list
/opt/citadel/scripts/env-manager.sh info

# Test environment switching
source /opt/citadel/citadel-env/bin/activate
echo "Active environment: $(basename $VIRTUAL_ENV)"
which python
python --version

# Test vLLM environment
source /opt/citadel/vllm-env/bin/activate
echo "vLLM environment: $(basename $VIRTUAL_ENV)"
python --version
```

### Step 3: PyTorch and CUDA Verification
```bash
# Comprehensive PyTorch testing
echo "=== PyTorch and CUDA Verification ==="
source /opt/citadel/citadel-env/bin/activate

python << 'EOF'
import torch
import sys

print(f"Python version: {sys.version}")
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"cuDNN version: {torch.backends.cudnn.version()}")
    print(f"Number of GPUs: {torch.cuda.device_count()}")
    
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        print(f"GPU {i}: {props.name}")
        print(f"  Memory: {props.total_memory / 1024**3:.1f} GB")
        print(f"  Compute Capability: {props.major}.{props.minor}")
    
    # Test tensor operations
    print("\nTesting tensor operations...")
    device = torch.device("cuda:0")
    x = torch.randn(1000, 1000, device=device)
    y = torch.randn(1000, 1000, device=device)
    z = torch.matmul(x, y)
    print("Matrix multiplication test: PASSED")
    
    # Test memory allocation
    print(f"GPU memory allocated: {torch.cuda.memory_allocated(0) / 1024**2:.1f} MB")
    print(f"GPU memory reserved: {torch.cuda.memory_reserved(0) / 1024**2:.1f} MB")
    
else:
    print("CUDA not available - check installation")
EOF
```

### Step 4: Performance Benchmarking
```bash
# Run performance benchmark
echo "=== Performance Benchmarking ==="
source /opt/citadel/citadel-env/bin/activate

python << 'EOF'
import torch
import time
import numpy as np

def benchmark_gpu_performance():
    if not torch.cuda.is_available():
        print("CUDA not available for benchmarking")
        return
    
    device = torch.device("cuda:0")
    print(f"Benchmarking on: {torch.cuda.get_device_name(0)}")
    
    # Warm up
    for _ in range(10):
        x = torch.randn(1000, 1000, device=device)
        y = torch.randn(1000, 1000, device=device)
        z = torch.matmul(x, y)
    
    # Benchmark matrix multiplication
    sizes = [1000, 2000, 4000]
    for size in sizes:
        times = []
        for _ in range(10):
            x = torch.randn(size, size, device=device)
            y = torch.randn(size, size, device=device)
            
            torch.cuda.synchronize()
            start_time = time.time()
            z = torch.matmul(x, y)
            torch.cuda.synchronize()
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        avg_time = np.mean(times)
        print(f"Matrix size {size}x{size}: {avg_time:.4f}s avg")
    
    print("Performance benchmark completed")

benchmark_gpu_performance()
EOF
```

## Troubleshooting

### Issue: Python 3.12 Installation Fails
**Symptoms**: Package not found, dependency conflicts
**Solutions**:
- Update repository: `sudo apt update`
- Check PPA: `sudo add-apt-repository ppa:deadsnakes/ppa -y`
- Install manually from source if needed

### Issue: Virtual Environment Problems
**Symptoms**: Environment creation fails, activation issues
**Solutions**:
- Check Python installation: `python3.12 -m venv --help`
- Verify permissions: `ls -la /opt/citadel/`
- Recreate environment: `rm -rf /opt/citadel/citadel-env && python3.12 -m venv /opt/citadel/citadel-env`

### Issue: PyTorch CUDA Not Working
**Symptoms**: `torch.cuda.is_available()` returns False
**Solutions**:
- Verify NVIDIA drivers: `nvidia-smi`
- Check CUDA installation: `nvcc --version`
- Reinstall PyTorch: `pip install torch --index-url https://download.pytorch.org/whl/cu124 --force-reinstall`

### Issue: Memory or Performance Issues
**Symptoms**: Out of memory errors, slow performance
**Solutions**:
- Apply optimizations: `python /opt/citadel/configs/python-optimization.py`
- Check GPU memory: `nvidia-smi`
- Adjust batch sizes in applications

## Configuration Summary

### Python Setup
- ✅ **Python Version**: 3.12 (latest)
- ✅ **Virtual Environments**: Multiple specialized environments
- ✅ **PyTorch**: Latest with CUDA 12.4 support
- ✅ **Core Libraries**: Transformers, FastAPI, monitoring tools
- ✅ **Optimization**: Memory and threading optimization applied

### Environment Structure
- **citadel-env**: Main application environment
- **vllm-env**: vLLM inference environment  
- **dev-env**: Development and testing environment

### Performance Optimizations
- Memory allocation tuning
- Threading optimization for multi-GPU
- CUDA memory management
- Tensor Core utilization enabled

## Next Steps

Continue to **[PLANB-05-vLLM-Installation.md](PLANB-05-vLLM-Installation.md)** for the latest vLLM installation with proper PyTorch compatibility.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 30-45 minutes  
**Complexity**: Medium  
**Prerequisites**: Ubuntu 24.04, NVIDIA drivers installed, storage configured