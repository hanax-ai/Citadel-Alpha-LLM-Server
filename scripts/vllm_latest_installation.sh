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