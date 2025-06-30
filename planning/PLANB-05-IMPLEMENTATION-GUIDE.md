# PLANB-05 vLLM Installation - Complete Implementation Guide

**Version:** 1.0  
**Created:** June 30, 2025  
**Task:** Implement PLANB-05 vLLM Installation with scripts and validation procedures  
**Target:** Latest compatible vLLM (0.6.1+) replacing problematic 0.2.7 version  

## Executive Summary

This implementation guide provides complete scripts and procedures to implement PLANB-05 vLLM Installation, addressing the compatibility issues identified in the existing `/opt/citadel/scripts/vllm_installation.sh` which uses the problematic vLLM 0.2.7 version.

## Current State Analysis

### ❌ Issues with Existing Installation
- **Problematic vLLM Version**: Current script uses vLLM 0.2.7 (incompatible with Python 3.12 and PyTorch 2.4+)
- **Wrong Environment**: Uses separate `vllm-env` instead of Plan B's standardized `/opt/citadel/dev-env`
- **Missing HF Integration**: No Hugging Face token automation
- **User Mismatch**: Not aligned with agent0 user standardization

### ✅ Plan B Solutions
- **Latest vLLM**: Upgrade to vLLM 0.6.1+ (compatible with PyTorch 2.4+ and Python 3.12)
- **Standardized Environment**: Use `/opt/citadel/dev-env` as specified in Plan B
- **HF Token Integration**: Automated authentication setup
- **Agent0 Alignment**: All configurations use agent0 user

## Implementation Architecture

```mermaid
graph TD
    A[PLANB-05 Implementation] --> B[Environment Preparation]
    B --> C[System Dependencies Setup]
    C --> D[Choose Installation Method]
    
    D --> E[Quick Install<br/>15-30 minutes]
    D --> F[Detailed Install<br/>60-90 minutes]
    
    E --> G[Single Command<br/>Latest vLLM + Dependencies]
    F --> H[Step-by-Step<br/>Full Control + Debug]
    
    G --> I[HF Token Integration]
    H --> I
    
    I --> J[Flash Attention<br/>Optional Performance]
    J --> K[Service Scripts Creation]
    K --> L[Validation Testing]
    
    L --> M[Installation Tests]
    L --> N[Functionality Tests]
    L --> O[Performance Tests]
    
    M --> P[✅ PLANB-05 Complete]
    N --> P
    O --> P
    
    style A fill:#e3f2fd
    style E fill:#fff3e0
    style F fill:#fce4ec
    style I fill:#e1f5fe
    style P fill:#e8f5e8,stroke:#4caf50,stroke-width:3px
```

## Script Collection

### 1. Main Installation Script: `vllm_latest_installation.sh`

```bash
#!/bin/bash
# PLANB-05: Latest vLLM Installation with Compatibility Resolution
# Version: 1.0
# Target: vLLM 0.6.1+ with PyTorch 2.4+ and Python 3.12

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CITADEL_ROOT="/opt/citadel"
DEV_ENV_PATH="/opt/citadel/dev-env"
HF_TOKEN="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"
USER_NAME="agent0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites for PLANB-05..."
    
    # Check if running as correct user
    if [ "$USER" != "$USER_NAME" ]; then
        error_exit "This script must be run as user '$USER_NAME', current user is '$USER'"
    fi
    
    # Check if dev-env exists
    if [ ! -d "$DEV_ENV_PATH" ]; then
        error_exit "Development environment not found at $DEV_ENV_PATH. Please complete PLANB-04 first."
    fi
    
    # Check Python version
    source "$DEV_ENV_PATH/bin/activate"
    python_version=$(python --version 2>&1 | cut -d' ' -f2)
    if [[ ! "$python_version" =~ ^3\.12 ]]; then
        error_exit "Python 3.12 required, found: $python_version"
    fi
    
    # Check PyTorch version
    pytorch_version=$(python -c "import torch; print(torch.__version__)" 2>/dev/null || echo "none")
    if [[ "$pytorch_version" == "none" ]]; then
        error_exit "PyTorch not found. Please complete PLANB-04 first."
    fi
    
    log_success "Prerequisites check passed"
    log_info "Python version: $python_version"
    log_info "PyTorch version: $pytorch_version"
}

# Clean previous installation
clean_previous_installation() {
    log_info "Cleaning previous vLLM installation..."
    
    source "$DEV_ENV_PATH/bin/activate"
    
    # Remove any existing vLLM installation
    pip uninstall vllm -y 2>/dev/null || true
    pip uninstall vllm-flash-attn -y 2>/dev/null || true
    pip uninstall flash-attn -y 2>/dev/null || true
    
    # Clear pip cache
    pip cache purge
    
    log_success "Previous installation cleaned"
}

# Update system dependencies
update_system_dependencies() {
    log_info "Installing system dependencies..."
    
    # Update package list
    sudo apt update
    
    # Install build dependencies
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
        pkg-config \
        gcc-11 \
        g++-11 \
        libc6-dev \
        libc-dev-bin \
        linux-libc-dev
    
    # Set GCC version for compilation
    sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100 || true
    sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100 || true
    
    log_success "System dependencies installed"
}

# Configure compilation environment
configure_compilation_environment() {
    log_info "Configuring compilation environment..."
    
    # Set compilation environment variables
    export CC=gcc-11
    export CXX=g++-11
    export CUDA_HOME=/usr/local/cuda
    export NVCC_PREPEND_FLAGS='-ccbin /usr/bin/gcc-11'
    export TORCH_CUDA_ARCH_LIST="8.9"  # For RTX 4070 Ti SUPER
    export MAX_JOBS=8  # Limit parallel compilation to prevent OOM
    
    # Add to shell profile for persistence
    tee -a ~/.bashrc << 'EOF'

# vLLM Compilation Environment
export CC=gcc-11
export CXX=g++-11
export NVCC_PREPEND_FLAGS='-ccbin /usr/bin/gcc-11'
export TORCH_CUDA_ARCH_LIST="8.9"
export MAX_JOBS=8
EOF
    
    source ~/.bashrc
    
    log_success "Compilation environment configured"
}

# Quick installation method
quick_install() {
    log_info "Starting quick vLLM installation..."
    
    source "$DEV_ENV_PATH/bin/activate"
    
    # Single command installation with all dependencies
    pip install vllm && \
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
        huggingface-hub>=0.19.0 && \
    pip install \
        prometheus-client>=0.19.0 \
        psutil>=5.9.0 \
        GPUtil>=1.4.0 \
        py3nvml>=0.2.7
    
    log_success "Quick installation completed"
}

# Detailed installation method
detailed_install() {
    log_info "Starting detailed vLLM installation..."
    
    source "$DEV_ENV_PATH/bin/activate"
    
    # Install latest vLLM version
    log_info "Installing vLLM latest version..."
    pip install vllm
    
    # Install core dependencies
    log_info "Installing core dependencies..."
    pip install \
        transformers>=4.36.0 \
        tokenizers>=0.15.0 \
        sentencepiece>=0.1.99 \
        numpy>=1.24.0 \
        requests>=2.31.0 \
        aiohttp>=3.9.0 \
        pydantic>=2.5.0 \
        pydantic-core>=2.14.0 \
        typing-extensions>=4.8.0
    
    # Install additional ML dependencies
    log_info "Installing ML dependencies..."
    pip install \
        accelerate>=0.25.0 \
        scipy>=1.11.0 \
        scikit-learn>=1.3.0 \
        datasets>=2.14.0 \
        evaluate>=0.4.0 \
        safetensors>=0.4.0
    
    # Install web framework dependencies
    log_info "Installing web framework dependencies..."
    pip install \
        fastapi>=0.104.0 \
        uvicorn[standard]>=0.24.0 \
        python-multipart>=0.0.6 \
        httpx>=0.25.0 \
        aiofiles>=23.2.1 \
        jinja2>=3.1.2
    
    # Install monitoring and utilities
    log_info "Installing monitoring and utilities..."
    pip install \
        psutil>=5.9.0 \
        GPUtil>=1.4.0 \
        py3nvml>=0.2.7 \
        nvidia-ml-py3>=7.352.0 \
        rich>=13.7.0 \
        typer>=0.9.0 \
        tqdm>=4.66.0
    
    log_success "Detailed installation completed"
}

# Install Flash Attention (optional)
install_flash_attention() {
    log_info "Installing Flash Attention for performance optimization..."
    
    source "$DEV_ENV_PATH/bin/activate"
    
    # Install flash-attn (this may take 10-15 minutes to compile)
    pip install flash-attn --no-build-isolation || {
        log_warning "Flash Attention installation failed (optional component)"
        return 0
    }
    
    log_success "Flash Attention installed successfully"
}

# Configure Hugging Face authentication
configure_huggingface() {
    log_info "Configuring Hugging Face authentication..."
    
    source "$DEV_ENV_PATH/bin/activate"
    
    # Install Hugging Face Hub CLI
    pip install huggingface_hub[cli]>=0.19.0
    
    # Configure authentication with token
    echo "$HF_TOKEN" | huggingface-cli login --token
    
    # Set environment variables
    export HF_TOKEN="$HF_TOKEN"
    export HUGGINGFACE_HUB_TOKEN="$HF_TOKEN"
    export HF_HOME="/mnt/citadel-models/cache"
    export TRANSFORMERS_CACHE="/mnt/citadel-models/cache/transformers"
    
    # Add to environment file
    tee -a ~/.bashrc << EOF

# Hugging Face Configuration
export HF_TOKEN=$HF_TOKEN
export HUGGINGFACE_HUB_TOKEN=$HF_TOKEN
export HF_HOME=/mnt/citadel-models/cache
export TRANSFORMERS_CACHE=/mnt/citadel-models/cache/transformers
EOF
    
    # Verify authentication
    huggingface-cli whoami
    
    log_success "Hugging Face authentication configured"
}

# Verify installation
verify_installation() {
    log_info "Verifying vLLM installation..."
    
    source "$DEV_ENV_PATH/bin/activate"
    
    # Check vLLM version and core functionality
    python -c "
import vllm
import torch
import transformers
import fastapi

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
print('🎉 All core components verified!')
"
    
    log_success "Installation verification completed"
}

# Main execution
main() {
    log_info "Starting PLANB-05 vLLM Installation"
    log_info "================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Clean previous installation
    clean_previous_installation
    
    # Update system dependencies
    update_system_dependencies
    
    # Configure compilation environment
    configure_compilation_environment
    
    # Choose installation method
    echo ""
    log_info "Choose installation method:"
    echo "1. Quick Install (15-30 minutes, recommended)"
    echo "2. Detailed Install (60-90 minutes, step-by-step)"
    read -p "Enter choice [1-2]: " choice
    
    case $choice in
        1)
            log_info "Selected: Quick Install"
            quick_install
            ;;
        2)
            log_info "Selected: Detailed Install"
            detailed_install
            ;;
        *)
            log_warning "Invalid choice, defaulting to Quick Install"
            quick_install
            ;;
    esac
    
    # Configure Hugging Face
    configure_huggingface
    
    # Ask about Flash Attention
    echo ""
    read -p "Install Flash Attention for performance? (y/N): " flash_choice
    case $flash_choice in
        [Yy]*)
            install_flash_attention
            ;;
        *)
            log_info "Skipping Flash Attention installation"
            ;;
    esac
    
    # Verify installation
    verify_installation
    
    log_success "PLANB-05 vLLM Installation completed successfully!"
    log_info "Next step: Proceed to PLANB-06-Storage-Symlinks.md"
}

# Execute main function
main "$@"
```

### 2. Quick Installation Script: `vllm_quick_install.sh`

```bash
#!/bin/bash
# PLANB-05: Quick vLLM Installation (15-30 minutes)

set -euo pipefail

DEV_ENV_PATH="/opt/citadel/dev-env"
HF_TOKEN="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"

echo "🚀 PLANB-05 Quick vLLM Installation"
echo "=================================="

# Activate environment and install vLLM with all dependencies
source "$DEV_ENV_PATH/bin/activate" && \
pip install vllm && \
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
    huggingface-hub>=0.19.0 && \
pip install \
    prometheus-client>=0.19.0 \
    psutil>=5.9.0 \
    GPUtil>=1.4.0 \
    py3nvml>=0.2.7

# Configure HF authentication
echo "$HF_TOKEN" | huggingface-cli login --token

# Verify installation
echo "=== Installation Verification ==="
python -c "import vllm; print(f'✅ vLLM version: {vllm.__version__}')"
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'✅ Transformers: {transformers.__version__}')"
python -c "import torch; print(f'✅ CUDA available: {torch.cuda.is_available()}')"
echo "🎉 Quick installation completed successfully!"
```

### 3. Installation Test Script: `test_vllm_installation.py`

```python
#!/usr/bin/env python3
"""
PLANB-05: vLLM Installation Test Suite
Comprehensive testing and validation of vLLM installation
"""

import os
import sys
import time
import torch
from rich.console import Console
from rich.progress import Progress

console = Console()

def test_vllm_import():
    """Test vLLM import and basic functionality"""
    try:
        import vllm
        console.print(f"✅ vLLM imported successfully: {vllm.__version__}")
        
        # Check version compatibility
        version_parts = vllm.__version__.split('.')
        major, minor = int(version_parts[0]), int(version_parts[1])
        
        if major == 0 and minor >= 6:
            console.print("✅ vLLM version is compatible (0.6.x+)")
        elif major >= 1:
            console.print("✅ vLLM version is compatible (1.x+)")
        else:
            console.print(f"⚠️ vLLM version may have compatibility issues: {vllm.__version__}")
            
        return True
    except ImportError as e:
        console.print(f"❌ vLLM import failed: {e}")
        return False

def test_cuda_availability():
    """Test CUDA availability"""
    if torch.cuda.is_available():
        console.print(f"✅ CUDA available: {torch.version.cuda}")
        console.print(f"✅ GPU count: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            console.print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
        return True
    else:
        console.print("❌ CUDA not available")
        return False

def test_dependencies():
    """Test key dependencies"""
    dependencies = [
        ('transformers', '4.36.0'),
        ('tokenizers', '0.15.0'),
        ('fastapi', '0.104.0'),
        ('uvicorn', '0.24.0'),
        ('pydantic', '2.5.0'),
        ('huggingface_hub', '0.19.0')
    ]
    
    passed = 0
    for package, min_version in dependencies:
        try:
            module = __import__(package)
            version = getattr(module, '__version__', 'unknown')
            console.print(f"✅ {package}: {version}")
            passed += 1
        except ImportError:
            console.print(f"❌ {package}: not installed")
    
    console.print(f"Dependencies: {passed}/{len(dependencies)} passed")
    return passed == len(dependencies)

def test_vllm_engine():
    """Test vLLM engine initialization with a small model"""
    try:
        from vllm import LLM, SamplingParams
        
        console.print("🧪 Testing vLLM engine with small model...")
        
        # Use a small model for testing
        model_name = "facebook/opt-125m"
        
        # Initialize LLM
        llm = LLM(
            model=model_name,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.3,
            download_dir="/tmp/vllm_test_cache"
        )
        
        # Test generation
        prompts = ["Hello, how are you?"]
        sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=50)
        
        outputs = llm.generate(prompts, sampling_params)
        
        for output in outputs:
            prompt = output.prompt
            generated_text = output.outputs[0].text
            console.print(f"✅ Test generation successful:")
            console.print(f"  Prompt: {prompt}")
            console.print(f"  Generated: {generated_text}")
        
        return True
        
    except Exception as e:
        console.print(f"❌ vLLM engine test failed: {e}")
        return False

def test_huggingface_auth():
    """Test Hugging Face authentication"""
    try:
        from huggingface_hub import whoami
        
        user_info = whoami()
        console.print(f"✅ HF Authentication: {user_info['name']}")
        return True
    except Exception as e:
        console.print(f"❌ HF Authentication failed: {e}")
        return False

def test_performance():
    """Basic performance test"""
    try:
        import time
        from vllm import LLM, SamplingParams
        
        console.print("🏃 Running performance test...")
        
        llm = LLM(
            model="facebook/opt-125m",
            tensor_parallel_size=1,
            gpu_memory_utilization=0.3
        )
        
        # Performance test
        prompts = ["Hello world!"] * 10
        sampling_params = SamplingParams(max_tokens=20)
        
        start_time = time.time()
        outputs = llm.generate(prompts, sampling_params)
        end_time = time.time()
        
        total_time = end_time - start_time
        throughput = len(prompts) / total_time
        
        console.print(f"✅ Performance test completed:")
        console.print(f"   Requests: {len(prompts)}")
        console.print(f"   Total time: {total_time:.2f}s")
        console.print(f"   Throughput: {throughput:.2f} requests/second")
        
        return True
        
    except Exception as e:
        console.print(f"❌ Performance test failed: {e}")
        return False

def main():
    console.print("🚀 PLANB-05 vLLM Installation Test Suite")
    console.print("=" * 50)
    
    tests = [
        ("vLLM Import", test_vllm_import),
        ("CUDA Availability", test_cuda_availability),
        ("Dependencies", test_dependencies),
        ("Hugging Face Auth", test_huggingface_auth),
        ("vLLM Engine", test_vllm_engine),
        ("Performance", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        console.print(f"\n📋 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    console.print(f"\n📊 Test Results Summary:")
    console.print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        console.print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    console.print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        console.print("🎉 All tests passed! vLLM is ready for use.")
        return 0
    else:
        console.print("⚠️ Some tests failed. Check installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 4. vLLM Server Script: `start_vllm_server.py`

```python
#!/usr/bin/env python3
"""
PLANB-05: vLLM Server Startup Script
Simple vLLM server for testing and development
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

def start_vllm_server(model_path, port=8000, host="0.0.0.0"):
    """Start vLLM OpenAI-compatible API server"""
    
    if not Path(model_path).exists():
        print(f"❌ Model path not found: {model_path}")
        return False
    
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_path,
        "--host", host,
        "--port", str(port),
        "--tensor-parallel-size", "1",
        "--gpu-memory-utilization", "0.7",
        "--trust-remote-code"
    ]
    
    print(f"🚀 Starting vLLM server...")
    print(f"   Model: {model_path}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(cmd)
        print(f"✅ Server started with PID: {process.pid}")
        print(f"🌐 API will be available at: http://{host}:{port}")
        print("📚 API docs at: http://localhost:8000/docs")
        
        # Wait for process
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        process.terminate()
    except Exception as e:
        print(f"❌ Server failed: {e}")
        return False
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Start vLLM server")
    parser.add_argument("model_path", help="Path to model directory")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    
    args = parser.parse_args()
    
    return start_vllm_server(args.model_path, args.port, args.host)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
```

### 5. Client Test Script: `test_vllm_client.py`

```python
#!/usr/bin/env python3
"""
PLANB-05: vLLM Client Test Script
Test vLLM server with OpenAI-compatible client
"""

import requests
import json
import time
import argparse
from rich.console import Console

console = Console()

def test_server_health(base_url):
    """Test server health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            console.print("✅ Server health check: PASSED")
            return True
        else:
            console.print(f"❌ Server health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        console.print(f"❌ Server health check failed: {e}")
        return False

def test_completion(base_url, model_name="test"):
    """Test completion endpoint"""
    try:
        url = f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Hello! Please respond with a short greeting."}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        console.print("🧪 Testing completion endpoint...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            console.print(f"✅ Completion test: PASSED ({response_time:.2f}s)")
            console.print(f"   Response: {content}")
            return True
        else:
            console.print(f"❌ Completion test failed: HTTP {response.status_code}")
            console.print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        console.print(f"❌ Completion test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test vLLM server")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--model", default="test", help="Model name")
    
    args = parser.parse_args()
    
    console.print("🧪 vLLM Server Test")
    console.print("=" * 30)
    
    tests = [
        ("Health Check", lambda: test_server_health(args.url)),
        ("Completion", lambda: test_completion(args.url, args.model))
    ]
    
    passed = 0
    for test_name, test_func in tests:
        console.print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
    
    console.print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
```

## Implementation Execution Plan

### Phase 1: Prepare Implementation Environment
1. **Create Scripts Directory**
   ```bash
   mkdir -p /opt/citadel/scripts/planb-05
   ```

2. **Copy Scripts from this Guide**
   - Copy all scripts from this document to `/opt/citadel/scripts/planb-05/`
   - Make all shell scripts executable: `chmod +x *.sh`
   - Make all Python scripts executable: `chmod +x *.py`

### Phase 2: Execute Installation
1. **Run Main Installation Script**
   ```bash
   cd /opt/citadel/scripts/planb-05
   ./vllm_latest_installation.sh
   ```

2. **Or Use Quick Install**
   ```bash
   ./vllm_quick_install.sh
   ```

### Phase 3: Validation and Testing
1. **Run Installation Tests**
   ```bash
   python test_vllm_installation.py
   ```

2. **Test Server Functionality**
   ```bash
   # Start server (in background)
   python start_vllm_server.py facebook/opt-125m &
   
   # Test client
   python test_vllm_client.py
   ```

## Troubleshooting Guide

### Common Issues and Solutions

#### Issue: vLLM Version Compatibility
**Symptoms**: Import errors, version conflicts
**Solution**: 
- Verify using latest vLLM (0.6.1+): `pip show vllm`
- Check PyTorch version: `python -c "import torch; print(torch.__version__)"`
- Reinstall if version is wrong: `pip install --upgrade vllm`

#### Issue: CUDA Not Available
**Symptoms**: `torch.cuda.is_available()` returns False
**Solution**:
- Check NVIDIA drivers: `nvidia-smi`
- Verify CUDA installation: `nvcc --version`
- Reinstall PyTorch with CUDA: `pip install torch --index-url https://download.pytorch.org/whl/cu124`

#### Issue: Compilation Failures
**Symptoms**: Build errors during installation
**Solution**:
- Install build dependencies: `sudo apt install build-essential cmake ninja-build`
- Set compilation environment variables (included in main script)
- Use pre-compiled wheels when available

#### Issue: Memory Errors
**Symptoms**: OOM during installation or testing
**Solution**:
- Reduce `MAX_JOBS` environment variable
- Use lower `gpu_memory_utilization` (0.3-0.5)
- Close other applications during installation

## Success Criteria

### ✅ Installation Success Indicators
- [ ] vLLM version 0.6.1+ installed successfully
- [ ] All dependency tests pass
- [ ] CUDA availability confirmed
- [ ] HF authentication working
- [ ] Small model inference test passes
- [ ] Performance benchmark completes

### ✅ Integration Success Indicators
- [ ] Uses `/opt/citadel/dev-env` environment (not separate vllm-env)
- [ ] HF token automatically configured
- [ ] Agent0 user ownership maintained
- [ ] Compatible with existing Plan B structure

## Next Steps

After successful completion of PLANB-05:

1. **Proceed to PLANB-06**: Storage Symlinks configuration
2. **Update Service Scripts**: Integrate with systemd services
3. **Model Installation**: Download and configure models
4. **Performance Optimization**: Fine-tune GPU and memory settings

---

## Implementation Summary

This comprehensive guide provides:
- ✅ **Complete Script Collection**: All necessary scripts for PLANB-05 implementation
- ✅ **Two Installation Methods**: Quick (15-30 min) and Detailed (60-90 min) options
- ✅ **Comprehensive Testing**: Multi-layer validation and verification
- ✅ **Troubleshooting Guide**: Solutions for common issues
- ✅ **Integration Ready**: Aligned with Plan B architecture and standards

**Status**: 🎯 **Ready for Implementation**
**Next Action**: Execute the scripts in the specified sequence and validate results