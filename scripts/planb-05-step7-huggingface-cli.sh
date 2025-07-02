#!/bin/bash
# PLANB-05 Step 7: Install Hugging Face CLI and Configure Authentication
# Secure, configuration-driven implementation following Citadel AI OS conventions

set -euo pipefail

# Script metadata
SCRIPT_NAME="PLANB-05-Step7-HuggingFace-CLI"
SCRIPT_VERSION="1.0.0"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Logging functions
log_info() {
    echo "[INFO] [$TIMESTAMP] $1" | tee -a "/var/log/citadel-installation.log"
}

log_error() {
    echo "[ERROR] [$TIMESTAMP] $1" | tee -a "/var/log/citadel-installation.log" >&2
}

log_success() {
    echo "[SUCCESS] [$TIMESTAMP] $1" | tee -a "/var/log/citadel-installation.log"
}

# Configuration validation
validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        log_error ".env file not found. Please copy .env.example to .env and configure it."
        exit 1
    fi
    
    # Source environment variables
    set -a
    source .env
    set +a
    
    # Validate required variables
    if [[ -z "${HF_TOKEN:-}" ]]; then
        log_error "HF_TOKEN not set in .env file"
        exit 1
    fi
    
    if [[ "${HF_TOKEN}" == "hf_your_token_here" ]]; then
        log_error "HF_TOKEN still contains placeholder value. Please set your actual token."
        exit 1
    fi
    
    # Validate token format
    if [[ ! "${HF_TOKEN}" =~ ^hf_[A-Za-z0-9]{20,}$ ]]; then
        log_error "HF_TOKEN format appears invalid. Should start with 'hf_' and be at least 23 characters."
        exit 1
    fi
    
    log_success "Environment configuration validated"
}

# Virtual environment validation
validate_virtual_environment() {
    log_info "Validating Python virtual environment..."
    
    local venv_path="${DEV_ENV_PATH:-/opt/citadel/dev-env}"
    
    if [[ ! -d "$venv_path" ]]; then
        log_error "Virtual environment not found at: $venv_path"
        log_error "Please complete PLANB-04 Python Environment setup first"
        exit 1
    fi
    
    if [[ ! -f "$venv_path/bin/activate" ]]; then
        log_error "Virtual environment activation script not found"
        exit 1
    fi
    
    log_success "Virtual environment validated: $venv_path"
}

# Create cache directories
create_cache_directories() {
    log_info "Creating Hugging Face cache directories..."
    
    local hf_home="${HF_HOME:-/mnt/citadel-models/cache}"
    local transformers_cache="${TRANSFORMERS_CACHE:-/mnt/citadel-models/cache/transformers}"
    
    # Create directories with proper permissions
    sudo mkdir -p "$hf_home" "$transformers_cache"
    sudo chown -R "$(whoami):$(whoami)" "$hf_home"
    sudo chmod -R 755 "$hf_home"
    
    log_success "Cache directories created: $hf_home, $transformers_cache"
}

# Install Hugging Face CLI
install_huggingface_cli() {
    log_info "Installing Hugging Face Hub CLI..."
    
    local venv_path="${DEV_ENV_PATH:-/opt/citadel/dev-env}"
    
    # Activate virtual environment
    source "$venv_path/bin/activate"
    
    # Upgrade pip first
    pip install --upgrade pip
    
    # Install huggingface_hub with CLI support
    pip install "huggingface_hub[cli]>=0.19.0"
    
    # Verify installation
    if ! command -v huggingface-cli &> /dev/null; then
        log_error "huggingface-cli command not found after installation"
        exit 1
    fi
    
    local hf_version=$(huggingface-cli --version 2>/dev/null || echo "unknown")
    log_success "Hugging Face CLI installed successfully: $hf_version"
}

# Configure authentication
configure_authentication() {
    log_info "Configuring Hugging Face authentication..."
    
    local venv_path="${DEV_ENV_PATH:-/opt/citadel/dev-env}"
    
    # Activate virtual environment
    source "$venv_path/bin/activate"
    
    # Use Python helper for secure authentication
    python3 scripts/huggingface_auth.py
    
    log_success "Hugging Face authentication configured"
}

# Verify authentication
verify_authentication() {
    log_info "Verifying Hugging Face authentication..."
    
    local venv_path="${DEV_ENV_PATH:-/opt/citadel/dev-env}"
    
    # Activate virtual environment
    source "$venv_path/bin/activate"
    
    # Test authentication
    if huggingface-cli whoami &> /dev/null; then
        local username=$(huggingface-cli whoami 2>/dev/null)
        log_success "Authentication verified for user: $username"
    else
        log_error "Authentication verification failed"
        exit 1
    fi
}

# Create environment configuration script
create_environment_script() {
    log_info "Creating environment configuration script..."
    
    local script_path="/opt/citadel/scripts/setup-hf-env.sh"
    
    # Create directory if it doesn't exist
    sudo mkdir -p "/opt/citadel/scripts"
    
    # Create environment setup script
    sudo tee "$script_path" > /dev/null << 'EOF'
#!/bin/bash
# Hugging Face Environment Setup
# Source this script to configure HF environment variables

# Load environment variables from .env
if [[ -f ".env" ]]; then
    set -a
    source .env
    set +a
fi

# Export Hugging Face variables
export HF_TOKEN="${HF_TOKEN}"
export HF_HOME="${HF_HOME:-/mnt/citadel-models/cache}"
export HUGGINGFACE_HUB_TOKEN="${HUGGINGFACE_HUB_TOKEN:-$HF_TOKEN}"
export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-/mnt/citadel-models/cache/transformers}"

echo "✅ Hugging Face environment configured"
echo "HF_HOME: $HF_HOME"
echo "TRANSFORMERS_CACHE: $TRANSFORMERS_CACHE"
EOF

    sudo chmod +x "$script_path"
    sudo chown "$(whoami):$(whoami)" "$script_path"
    
    log_success "Environment script created: $script_path"
}

# Main execution
main() {
    log_info "Starting $SCRIPT_NAME v$SCRIPT_VERSION"
    
    # Validation steps
    validate_environment
    validate_virtual_environment
    
    # Installation steps
    create_cache_directories
    install_huggingface_cli
    configure_authentication
    verify_authentication
    create_environment_script
    
    log_success "$SCRIPT_NAME completed successfully"
    echo ""
    echo "✅ Hugging Face CLI installation and configuration complete!"
    echo ""
    echo "Usage:"
    echo "  - Source environment: source /opt/citadel/scripts/setup-hf-env.sh"
    echo "  - Check authentication: huggingface-cli whoami"
    echo "  - Download models: huggingface-cli download model-name"
    echo ""
    echo "Next: Proceed to vLLM configuration and testing"
}

# Error handling
trap 'log_error "Script failed at line $LINENO"' ERR

# Execute main function
main "$@"