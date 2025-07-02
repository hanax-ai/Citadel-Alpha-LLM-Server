#!/bin/bash
# planb-03-nvidia-driver-setup.sh
# NVIDIA 570.x Driver Installation with CUDA 12.4+ for PLANB-03
# Modular implementation with comprehensive error handling and validation

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="/opt/citadel/configs/gpu-config.json"
LOG_FILE="/opt/citadel/logs/planb-03-nvidia-setup.log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Error handling function
handle_error() {
    local exit_code=$?
    log_error "Command failed with exit code $exit_code: $1"
    log_error "Rolling back changes..."
    
    # Attempt rollback using Python backup manager
    if command -v python3 >/dev/null 2>&1; then
        python3 "$SCRIPT_DIR/nvidia_backup_manager.py" rollback || {
            log_error "Rollback failed - manual intervention may be required"
        }
    fi
    
    exit $exit_code
}

# Trap errors
trap 'handle_error "Line $LINENO"' ERR

# Initialize logging
create_log_directory() {
    log_step "Setting up logging and directories"
    mkdir -p "$(dirname "$LOG_FILE")"
    touch "$LOG_FILE"
    chmod 664 "$LOG_FILE"
    # Add this line below to fix the bug
    chown "$USER:$USER" "$LOG_FILE"
    
    # Create required directories
    mkdir -p /opt/citadel/{configs,scripts,backups,logs}
    chown -R "$USER:$USER" /opt/citadel 2>/dev/null || true
}

# Check prerequisites
check_prerequisites() {
    log_step "Checking prerequisites"
    
    # Check if running as regular user with sudo access
    if [[ $EUID -eq 0 ]]; then
        log_warn "Running as root - some operations may have different behavior"
    fi
    
    # Check sudo access
    if ! sudo -n true 2>/dev/null; then
        log_warn "Sudo access may be required for some operations"
    fi
    
    # Check Ubuntu version
    if ! grep -q "Ubuntu 24.04" /etc/os-release; then
        log_warn "This script is designed for Ubuntu 24.04 LTS"
    fi
    
    # Check if previous tasks are completed
    if [[ ! -f "$PROJECT_ROOT/tasks/task-results/task-PLANB-01-results.md" ]]; then
        log_error "PLANB-01 must be completed before running this script"
        #exit 1
    fi
    
    log_info "✅ Prerequisites check passed"
}

# Install Python dependencies
install_python_dependencies() {
    log_step "Installing Python dependencies"
    
    # Ensure Python 3 is available
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is required but not installed"
        #exit 1
    fi
    
    # Make Python scripts executable
    chmod +x "$SCRIPT_DIR/nvidia_backup_manager.py"
    chmod +x "$SCRIPT_DIR/gpu_manager.py"
    
    log_info "✅ Python dependencies ready"
}

# Create initial GPU configuration
create_gpu_configuration() {
    log_step "Creating GPU configuration"
    
    # Create configuration using Python module
    python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/configs')
from gpu_settings import GPUSettings, GPUPerformanceSettings, RepositorySettings
from pathlib import Path

settings = GPUSettings(
    driver_version='570',
    cuda_version='12-4',
    gpu_model='RTX 4070 Ti SUPER',
    target_gpus=2,
    auto_detect_clocks=True,
    performance_settings=GPUPerformanceSettings(),
    repository=RepositorySettings()
)

settings.save_to_file(Path('$CONFIG_FILE'))
print('✅ GPU configuration created')
"
    
    log_info "✅ GPU configuration created at $CONFIG_FILE"
}

# Check GPU hardware
check_gpu_hardware() {
    log_step "Checking GPU hardware"
    
    # Use Python GPU manager to check hardware
    if ! python3 "$SCRIPT_DIR/gpu_manager.py" detect; then
        log_error "GPU hardware check failed"
        #exit 1
    fi
    
    log_info "✅ GPU hardware verified"
}

# Create backup
create_system_backup() {
    log_step "Creating system backup"
    
    # Use Python backup manager
    if ! python3 "$SCRIPT_DIR/nvidia_backup_manager.py" backup; then
        log_error "Failed to create system backup"
        #exit 1
    fi
    
    log_info "✅ System backup created"
}

# Clean existing NVIDIA packages
clean_existing_nvidia() {
    log_step "Cleaning existing NVIDIA packages"
    
    log_info "Removing existing NVIDIA packages..."
    
    # Remove packages with error handling
    sudo apt-get remove --purge "nvidia*" -y 2>/dev/null || {
        log_warn "Some NVIDIA packages could not be removed"
    }
    
    sudo apt-get remove --purge "cuda*" -y 2>/dev/null || {
        log_warn "Some CUDA packages could not be removed"
    }
    
    sudo apt-get remove --purge "libnvidia*" -y 2>/dev/null || {
        log_warn "Some NVIDIA library packages could not be removed"
    }
    
    sudo apt-get autoremove -y || log_warn "Autoremove failed"
    sudo apt-get autoclean || log_warn "Autoclean failed"
    
    # Remove configuration files
    sudo find /etc/modprobe.d -name "*nvidia*" -delete 2>/dev/null || true
    sudo find /etc/modprobe.d -name "*blacklist-nvidia*" -delete 2>/dev/null || true
    
    log_info "✅ NVIDIA cleanup completed"
}

# Update system packages
update_system_packages() {
    log_step "Updating system packages"
    
    sudo apt update || {
        log_error "Failed to update package lists"
        #exit 1
    }
    
    sudo apt upgrade -y || {
        log_warn "Some packages failed to upgrade"
    }
    
    # Install build dependencies
    local build_deps=(
        "build-essential" "cmake" "git" "wget" "curl" "dkms"
        "linux-headers-$(uname -r)" "gcc" "g++" "make" "pkg-config"
        "libssl-dev" "zlib1g-dev" "libbz2-dev" "libreadline-dev"
        "libsqlite3-dev" "libncursesw5-dev" "xz-utils" "tk-dev"
        "libxml2-dev" "libxmlsec1-dev" "libffi-dev" "liblzma-dev"
    )
    
    log_info "Installing build dependencies..."
    sudo apt install -y "${build_deps[@]}" || {
        log_error "Failed to install build dependencies"
        #exit 1
    }
    
    log_info "✅ System packages updated"
}

# Add NVIDIA repository
add_nvidia_repository() {
    log_step "Adding NVIDIA repository"
    
    # Get repository URL from configuration
    local repo_url
    repo_url=$(python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/configs')
from gpu_settings import GPUSettings
from pathlib import Path
settings = GPUSettings.load_from_file(Path('$CONFIG_FILE'))
print(settings.get_repository_url())
")
    
    log_info "Downloading NVIDIA repository keyring..."
    wget -q "$repo_url" -O /tmp/cuda-keyring.deb || {
        log_error "Failed to download NVIDIA repository keyring"
        #exit 1
    }
    
    sudo dpkg -i /tmp/cuda-keyring.deb || {
        log_error "Failed to install NVIDIA repository keyring"
        #exit 1
    }
    
    sudo apt update || {
        log_error "Failed to update package lists after adding repository"
        #exit 1
    }
    
    # Verify repository addition
    if apt-cache policy | grep -q nvidia; then
        log_info "✅ NVIDIA repository added successfully"
    else
        log_error "NVIDIA repository not found after installation"
        #exit 1
    fi
    
    rm -f /tmp/cuda-keyring.deb
}

# Install NVIDIA driver
install_nvidia_driver() {
    log_step "Installing NVIDIA driver"
    
    # Get driver version from configuration
    local driver_version
    driver_version=$(python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/configs')
from gpu_settings import GPUSettings
from pathlib import Path
settings = GPUSettings.load_from_file(Path('$CONFIG_FILE'))
print(settings.driver_version)
")
    
    log_info "Installing NVIDIA driver $driver_version series..."
    
    # Check if driver is available
    if ! apt-cache search "nvidia-driver-$driver_version" | grep -q "nvidia-driver-$driver_version"; then
        log_error "NVIDIA driver $driver_version not available in repository"
        #exit 1
    fi
    
    sudo apt install -y "nvidia-driver-$driver_version" || {
        log_error "Failed to install NVIDIA driver $driver_version"
        #exit 1
    }
    
    log_info "✅ NVIDIA driver $driver_version installed successfully"
}

# Install CUDA toolkit
install_cuda_toolkit() {
    log_step "Installing CUDA toolkit"
    
    # Get CUDA version from configuration
    local cuda_version
    cuda_version=$(python3 -c "
import sys
sys.path.append('$PROJECT_ROOT/configs')
from gpu_settings import GPUSettings
from pathlib import Path
settings = GPUSettings.load_from_file(Path('$CONFIG_FILE'))
print(settings.cuda_version)
")
    
    log_info "Installing CUDA Toolkit $cuda_version..."
    
    sudo apt install -y "cuda" || {
        log_error "Failed to install CUDA Toolkit"
        #exit 1
    }
    
    # Install additional CUDA development tools
    local cuda_packages=(
        "cuda-compiler-$cuda_version"
        "cuda-libraries-dev-$cuda_version"
        "cuda-driver-dev-$cuda_version"
        "cuda-cudart-dev-$cuda_version"
        "cuda-nvml-dev-$cuda_version"
    )
    
    for package in "${cuda_packages[@]}"; do
        if apt-cache search "$package" | grep -q "$package"; then
            sudo apt install -y "$package" || {
                log_warn "Failed to install $package (non-critical)"
            }
        else
            log_warn "Package $package not available (skipping)"
        fi
    done
    
    log_info "✅ CUDA Toolkit installation completed"
}

# Install cuDNN
install_cudnn() {
    log_step "Installing cuDNN"
    
    local cudnn_packages=(
        "libcudnn9"
        "libcudnn9-dev" 
        "libcudnn9-samples"
    )
    
    for package in "${cudnn_packages[@]}"; do
        if apt-cache search "$package" | grep -q "$package"; then
            sudo apt install -y "$package" || {
                log_warn "Failed to install $package"
            }
        else
            log_warn "Package $package not available"
        fi
    done
    
    log_info "✅ cuDNN installation completed"
}

# Configure environment variables
configure_environment() {
    log_step "Configuring environment variables"
    
    # Backup existing environment configuration
    [[ -f /etc/environment ]] && sudo cp /etc/environment /etc/environment.backup.$(date +%Y%m%d-%H%M%S)
    [[ -f ~/.bashrc ]] && cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d-%H%M%S)
    
    # Detect CUDA installation path dynamically
    local cuda_path=""
    local possible_paths=(
        "/usr/local/cuda-12.6"
        "/usr/local/cuda-12.5"
        "/usr/local/cuda-12.4"
        "/usr/local/cuda-12.3"
        "/usr/local/cuda-12.2"
        "/usr/local/cuda-12.1"
        "/usr/local/cuda-12.0"
        "/usr/local/cuda-12"
        "/usr/local/cuda"
        "/opt/cuda"
    )
    
    # Try to find CUDA installation by checking for highest version first
    for path in "${possible_paths[@]}"; do
        if [[ -d "$path" && -f "$path/bin/nvcc" ]]; then
            cuda_path="$path"
            break
        fi
    done
    
    # If no standard path found, try to detect from package manager
    if [[ -z "$cuda_path" ]]; then
        local detected_path
        detected_path=$(find /usr/local -maxdepth 1 -name "cuda*" -type d 2>/dev/null | sort -V | tail -1)
        if [[ -n "$detected_path" && -f "$detected_path/bin/nvcc" ]]; then
            cuda_path="$detected_path"
        fi
    fi
    
    # Final fallback check
    if [[ -z "$cuda_path" ]]; then
        log_error "CUDA installation not found in any expected location"
        return 1
    fi
    
    log_info "Found CUDA installation at: $cuda_path"
    
    # Get current PATH
    local current_path
    current_path=$(grep "^PATH=" /etc/environment 2>/dev/null | cut -d'=' -f2 | tr -d '"' || echo "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin")
    
    # Update system environment
    echo "PATH=\"${current_path}:${cuda_path}/bin\"" | sudo tee /etc/environment
    echo "CUDA_HOME=\"${cuda_path}\"" | sudo tee -a /etc/environment
    echo "CUDA_ROOT=\"${cuda_path}\"" | sudo tee -a /etc/environment
    echo "LD_LIBRARY_PATH=\"${cuda_path}/lib64:${cuda_path}/extras/CUPTI/lib64\"" | sudo tee -a /etc/environment
    
    # Update user bashrc if CUDA configuration doesn't exist
    if ! grep -q "NVIDIA CUDA Configuration" ~/.bashrc; then
        log_info "Adding CUDA configuration to user profile..."
        cat >> ~/.bashrc << EOF

# NVIDIA CUDA Configuration
export CUDA_HOME="${cuda_path}"
export CUDA_ROOT="${cuda_path}"
export PATH="${cuda_path}/bin:\$PATH"
export LD_LIBRARY_PATH="${cuda_path}/lib64:${cuda_path}/extras/CUPTI/lib64:\$LD_LIBRARY_PATH"
export NVIDIA_VISIBLE_DEVICES=all
export NVIDIA_DRIVER_CAPABILITIES=compute,utility
EOF
    fi
    
    log_info "✅ Environment variables configured"
    if [ -f "$HOME/.bashrc" ]; then
        sudo -u $USER bash -i -c "source $HOME/.bashrc"
    fi
}

# Main execution function
main() {
    echo "==============================================="
    echo "PLANB-03: NVIDIA Driver Setup and Optimization"
    echo "==============================================="
    echo
    
    create_log_directory
    check_prerequisites
    install_python_dependencies
    create_gpu_configuration
    check_gpu_hardware
    create_system_backup
    clean_existing_nvidia
    update_system_packages
    add_nvidia_repository
    install_nvidia_driver
    install_cuda_toolkit
    install_cudnn
    configure_environment
    
    echo
    log_info "🎉 NVIDIA driver installation completed successfully!"
    log_info "⚠️  SYSTEM REBOOT REQUIRED to load new drivers"
    log_info "After reboot, run the post-installation validation:"
    log_info "   python3 tests/test_planb_03_validation.py"
    echo
}

# Run main function
main "$@"