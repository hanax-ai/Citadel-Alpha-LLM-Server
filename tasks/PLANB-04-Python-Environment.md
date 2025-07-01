# PLANB-04: Python 3.12 Environment Setup and Optimization

**Task:** Install and configure Python 3.12 with optimized virtual environment for AI workloads
**Duration:** 30-45 minutes
**Prerequisites:** PLANB-01, PLANB-02, and PLANB-03 completed, NVIDIA drivers installed

## Overview

This task installs Python 3.12 with optimized configurations for AI/ML workloads, creates dedicated virtual environments, and installs PyTorch with CUDA 12.4+ support. The implementation uses a modular, configuration-driven approach with comprehensive error handling and safety checks.

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

## Modular Implementation Structure

This task is implemented using a modular approach with the following components:

1. **Main Orchestration** (this file)
2. **Python Installation Module** ([`PLANB-04a-Python-Installation.md`](PLANB-04a-Python-Installation.md))
3. **Virtual Environment Module** ([`PLANB-04b-Virtual-Environments.md`](PLANB-04b-Virtual-Environments.md))
4. **Dependencies Module** ([`PLANB-04c-Dependencies-Optimization.md`](PLANB-04c-Dependencies-Optimization.md))
5. **Validation Module** ([`PLANB-04d-Validation-Testing.md`](PLANB-04d-Validation-Testing.md))

## Configuration System

### Step 1: Create Python Environment Configuration

```bash
# Create Python environment configuration
sudo tee /opt/citadel/configs/python-config.json << 'EOF'
{
  "python": {
    "version": "3.12",
    "repository": "ppa:deadsnakes/ppa",
    "packages": [
      "python3.12",
      "python3.12-dev",
      "python3.12-venv",
      "python3.12-distutils",
      "python3.12-tk",
      "python3.12-gdbm",
      "python3.12-dbg",
      "python3.12-full"
    ],
    "build_dependencies": [
      "build-essential",
      "libssl-dev",
      "libffi-dev",
      "libbz2-dev",
      "libreadline-dev",
      "libsqlite3-dev",
      "libncursesw5-dev",
      "xz-utils",
      "tk-dev",
      "libxml2-dev",
      "libxmlsec1-dev",
      "liblzma-dev"
    ]
  },
  "environments": {
    "citadel-env": {
      "purpose": "Main application environment",
      "pytorch_version": "latest",
      "cuda_support": true
    },
    "vllm-env": {
      "purpose": "vLLM inference environment",
      "pytorch_version": "latest",
      "cuda_support": true
    },
    "dev-env": {
      "purpose": "Development and testing environment",
      "pytorch_version": "latest",
      "cuda_support": false
    }
  },
  "optimization": {
    "memory": {
      "gc_threshold": [700, 10, 10],
      "malloc_arena_max": "4",
      "malloc_mmap_threshold": "131072"
    },
    "threading": {
      "max_threads": 16,
      "affinity": "granularity=fine,verbose,compact,1,0"
    },
    "cuda": {
      "launch_blocking": false,
      "cache_disable": false,
      "auto_boost": true,
      "alloc_conf": "max_split_size_mb:512",
      "tf32_override": true
    }
  },
  "paths": {
    "citadel_root": "/opt/citadel",
    "models_cache": "/mnt/citadel-models/cache",
    "transformers_cache": "/mnt/citadel-models/cache/transformers",
    "datasets_cache": "/mnt/citadel-models/cache/datasets"
  }
}
EOF
```

## Prerequisites Validation and Safety Checks

### Step 2: Create Prerequisites Validation Script

```bash
# Create comprehensive prerequisites validation script
sudo tee /opt/citadel/scripts/validate-prerequisites.sh << 'EOF'
#!/bin/bash
# validate-prerequisites.sh - Validate prerequisites for Python environment setup

set -euo pipefail

CONFIG_FILE="/opt/citadel/configs/python-config.json"
LOG_FILE="/opt/citadel/logs/python-setup.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "ERROR: $1"
    exit 1
}

# Check if configuration file exists
validate_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    
    if ! python3 -m json.tool "$CONFIG_FILE" >/dev/null 2>&1; then
        handle_error "Invalid JSON in configuration file: $CONFIG_FILE"
    fi
    
    log "✅ Configuration file validated"
}

# Check previous tasks completion
validate_previous_tasks() {
    log "Validating previous task completion..."
    
    # Check PLANB-01: Ubuntu installation
    if ! command -v lsb_release >/dev/null 2>&1; then
        handle_error "PLANB-01 not completed: Ubuntu system tools not found"
    fi
    
    if ! lsb_release -rs | grep -q "24.04"; then
        handle_error "PLANB-01 not completed: Ubuntu 24.04 not detected"
    fi
    
    # Check PLANB-02: Storage configuration
    if [ ! -d "/opt/citadel" ]; then
        handle_error "PLANB-02 not completed: /opt/citadel directory not found"
    fi
    
    if [ ! -d "/mnt/citadel-models" ]; then
        handle_error "PLANB-02 not completed: Model storage not mounted"
    fi
    
    # Check PLANB-03: NVIDIA drivers
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        handle_error "PLANB-03 not completed: NVIDIA drivers not installed"
    fi
    
    if ! nvidia-smi >/dev/null 2>&1; then
        handle_error "PLANB-03 not completed: NVIDIA drivers not working"
    fi
    
    log "✅ Previous tasks validation completed"
}

# Check system resources
validate_resources() {
    log "Validating system resources..."
    
    # Check available disk space (need at least 10GB)
    AVAILABLE_SPACE=$(df /opt/citadel | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=$((10 * 1024 * 1024)) # 10GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        handle_error "Insufficient disk space: need 10GB, have $(($AVAILABLE_SPACE / 1024 / 1024))GB"
    fi
    
    # Check available memory (need at least 4GB)
    AVAILABLE_MEMORY=$(free -m | awk 'NR==2{print $7}')
    REQUIRED_MEMORY=4096
    
    if [ "$AVAILABLE_MEMORY" -lt "$REQUIRED_MEMORY" ]; then
        handle_error "Insufficient memory: need 4GB, have ${AVAILABLE_MEMORY}MB available"
    fi
    
    # Check internet connectivity
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        handle_error "No internet connectivity - required for package downloads"
    fi
    
    log "✅ System resources validated"
}

# Check for conflicting installations
validate_conflicts() {
    log "Checking for potential conflicts..."
    
    # Check if Python 3.12 is already installed
    if command -v python3.12 >/dev/null 2>&1; then
        log "WARNING: Python 3.12 already installed - will verify compatibility"
    fi
    
    # Check for existing virtual environments
    if [ -d "/opt/citadel/citadel-env" ]; then
        log "WARNING: citadel-env already exists - will backup and recreate"
    fi
    
    log "✅ Conflict validation completed"
}

# Main validation function
main() {
    log "Starting prerequisites validation for PLANB-04"
    
    validate_config
    validate_previous_tasks
    validate_resources
    validate_conflicts
    
    log "✅ All prerequisites validated successfully"
    echo "Prerequisites validation completed - system ready for Python environment setup"
}

main "$@"
EOF

chmod +x /opt/citadel/scripts/validate-prerequisites.sh

# Run prerequisites validation
echo "Running prerequisites validation..."
if ! /opt/citadel/scripts/validate-prerequisites.sh; then
    echo "❌ Prerequisites validation failed"
    exit 1
fi
```

## Error Handling and Rollback System

### Step 3: Create Error Handling Framework

```bash
# Create error handling and rollback framework
sudo tee /opt/citadel/scripts/python-error-handler.sh << 'EOF'
#!/bin/bash
# python-error-handler.sh - Error handling and rollback for Python setup

set -euo pipefail

BACKUP_DIR="/opt/citadel/backups/python-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/opt/citadel/logs/python-setup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup
create_backup() {
    log "Creating backup at $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing Python installations
    if command -v python3 >/dev/null 2>&1; then
        python3 --version > "$BACKUP_DIR/python_version.txt" 2>&1 || true
    fi
    
    # Backup existing virtual environments
    if [ -d "/opt/citadel" ]; then
        find /opt/citadel -name "*-env" -type d > "$BACKUP_DIR/existing_envs.txt" 2>/dev/null || true
    fi
    
    # Backup package lists
    dpkg -l | grep python > "$BACKUP_DIR/python_packages.txt" 2>/dev/null || true
    
    # Backup environment variables
    env | grep -E "(PYTHON|PATH)" > "$BACKUP_DIR/environment.txt" 2>/dev/null || true
    
    log "✅ Backup created: $BACKUP_DIR"
}

# Rollback function
rollback_changes() {
    if [ -z "${BACKUP_DIR:-}" ] || [ ! -d "$BACKUP_DIR" ]; then
        log "ERROR: No backup directory found for rollback"
        return 1
    fi
    
    log "Rolling back changes from backup: $BACKUP_DIR"
    
    # Remove failed virtual environments
    for env in citadel-env vllm-env dev-env; do
        if [ -d "/opt/citadel/$env" ]; then
            log "Removing failed environment: $env"
            rm -rf "/opt/citadel/$env" || true
        fi
    done
    
    # Remove Python alternatives if they were added
    if update-alternatives --list python3 2>/dev/null | grep -q "python3.12"; then
        log "Removing Python alternatives"
        sudo update-alternatives --remove python3 /usr/bin/python3.12 2>/dev/null || true
        sudo update-alternatives --remove python /usr/bin/python3.12 2>/dev/null || true
    fi
    
    log "✅ Rollback completed"
}

# Validate step completion
validate_step() {
    local step_name="$1"
    local validation_command="$2"
    
    log "Validating step: $step_name"
    
    if eval "$validation_command"; then
        log "✅ Step validated: $step_name"
        return 0
    else
        log "❌ Step validation failed: $step_name"
        return 1
    fi
}

# Execute step with error handling
execute_step() {
    local step_name="$1"
    local step_command="$2"
    local validation_command="$3"
    
    log "Executing step: $step_name"
    
    if eval "$step_command"; then
        if validate_step "$step_name" "$validation_command"; then
            log "✅ Step completed successfully: $step_name"
            return 0
        else
            log "❌ Step validation failed: $step_name"
            return 1
        fi
    else
        log "❌ Step execution failed: $step_name"
        return 1
    fi
}

case "${1:-}" in
    backup)
        create_backup
        ;;
    rollback)
        rollback_changes
        ;;
    validate)
        validate_step "$2" "$3"
        ;;
    execute)
        execute_step "$2" "$3" "$4"
        ;;
    *)
        echo "Usage: $0 {backup|rollback|validate|execute}"
        echo "  backup                    - Create system backup"
        echo "  rollback                  - Rollback changes"
        echo "  validate <name> <cmd>     - Validate step completion"
        echo "  execute <name> <cmd> <val> - Execute step with validation"
        exit 1
        ;;
esac
EOF

chmod +x /opt/citadel/scripts/python-error-handler.sh
```

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