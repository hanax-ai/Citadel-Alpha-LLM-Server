#!/bin/bash
# planb-04a-python-installation.sh - Python 3.12 Installation Module

set -euo pipefail

CONFIG_FILE="/opt/citadel/configs/python-config.json"
ERROR_HANDLER="/opt/citadel/scripts/python-error-handler.sh"
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
    $ERROR_HANDLER rollback
    exit 1
}

# Step 1: Load Configuration and Create Backup
initialize_installation() {
    log "Initializing Python 3.12 installation..."
    
    # Validate configuration file exists
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Create backup before installation
    log "Creating backup before Python installation..."
    if ! $ERROR_HANDLER backup; then
        handle_error "Failed to create backup"
    fi
    
    log "✅ Initialization completed successfully"
}

# Step 2: Repository Setup with Error Handling
setup_repository() {
    log "Setting up Python 3.12 repository..."
    
    local ppa_repo=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['python']['repository'])")
    log "Adding Python repository: $ppa_repo"
    
    # Update package lists first
    if ! apt-get update; then
        handle_error "Failed to update package lists"
    fi
    
    # Install software-properties-common if not present
    if ! apt-get install -y --allow-unauthenticated software-properties-common ; then
        handle_error "Failed to install software-properties-common"
    fi
    
    # Add PPA repository
    if ! add-apt-repository "$ppa_repo" -y; then
        handle_error "Failed to add Python PPA repository"
    fi
    
    # Update package lists again
    if ! apt update -y; then
        handle_error "Failed to update package lists after PPA addition"
    fi
    
    # Verify Python 3.12 is available (either from deadsnakes or Ubuntu repos)
    if ! apt-cache policy python3.12 | head -1 | grep -q 'python3.12:'; then
        handle_error "Python 3.12 not available in repositories"
    else
        log "✅ Python 3.12 available from repositories"
    fi
    
    log "✅ Repository setup completed successfully"
}

# Step 3: Python 3.12 Installation with Validation
install_python312() {
    log "Installing Python 3.12 and related packages..."
    
    # Get package list from configuration
    local python_packages=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
packages = ' '.join(config['python']['packages'])
print(packages)
")
    
    local build_deps=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
deps = ' '.join(config['python']['build_dependencies'])
print(deps)
")
    
    log "Installing Python packages: $python_packages"
    if ! apt-get install -y --no-install-recommends $python_packages; then
        handle_error "Failed to install Python 3.12 packages"
    fi
    
    log "Installing build dependencies: $build_deps"
    if ! apt-get install -y --no-install-recommends $build_deps; then
        handle_error "Failed to install build dependencies"
    fi
    
    # Verify Python 3.12 installation
    if ! python3.12 --version; then
        handle_error "Python 3.12 installation verification failed"
    fi
    
    log "✅ Python 3.12 installation completed successfully"
}

# Step 4: Pip Installation with Error Handling
install_pip312() {
    log "Installing pip for Python 3.12..."
    
    # Download get-pip.py with error handling
    if ! curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py; then
        handle_error "Failed to download get-pip.py"
    fi
    
    # Install pip
    if ! python3.12 /tmp/get-pip.py; then
        handle_error "Failed to install pip for Python 3.12"
    fi
    
    # Cleanup
    rm -f /tmp/get-pip.py
    
    # Upgrade pip to latest version
    if ! python3.12 -m pip install --upgrade pip; then
        log "WARNING: Failed to upgrade pip (non-critical)"
    fi
    
    # Verify pip installation
    if ! python3.12 -m pip --version; then
        handle_error "Pip installation verification failed"
    fi
    
    log "✅ Pip installation completed successfully"
}

# Step 5: Configure Python Alternatives
configure_alternatives() {
    log "Configuring Python alternatives..."

    # Set up Python alternatives (after confirming python3.12 is installed)
    if ! update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100; then
        handle_error "Failed to configure python3 alternative"
    fi

    if ! update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 90; then
        log "WARNING: Failed to configure python3.10 alternative (non-critical)"
    fi

    if ! update-alternatives --install /usr/bin/python python /usr/bin/python3.12 100; then
        handle_error "Failed to configure python alternative"
    fi

    # Set up pip alternatives
    local pip312_path=$(command -v pip3.12 2>/dev/null || echo "/usr/local/bin/pip3.12")

    if [ -f "$pip312_path" ]; then
        if ! update-alternatives --install /usr/bin/pip3 pip3 "$pip312_path" 100; then
            log "WARNING: Failed to configure pip3 alternative (non-critical)"
        fi

        if ! update-alternatives --install /usr/bin/pip pip "$pip312_path" 100; then
            log "WARNING: Failed to configure pip alternative (non-critical)"
        fi
    fi

    # Verify alternatives configuration
    if ! python --version | grep -q '3.12'; then
        log "WARNING: Python alternative not pointing to 3.12"
    fi
    
    log "✅ Alternatives configuration completed successfully"
}

# Step 6: Comprehensive Installation Verification
verify_installation() {
    log "=== Python 3.12 Installation Verification ==="
    
    # Check Python version
    local python_version=$(python3.12 --version 2>&1)
    log "Python 3.12 version: $python_version"
    
    if ! echo "$python_version" | grep -q "Python 3.12"; then
        handle_error "Python 3.12 not properly installed"
    fi
    
    # Check alternative configuration
    local current_python=$(python --version 2>&1)
    log "Current python version: $current_python"
    
    if ! echo "$current_python" | grep -q "Python 3.12"; then
        log "WARNING: Python alternative not pointing to 3.12"
    fi
    
    # Check pip installation
    local pip_version=$(python3.12 -m pip --version 2>&1)
    log "Pip version: $pip_version"
    
    if ! echo "$pip_version" | grep -q "pip"; then
        handle_error "Pip not properly installed"
    fi
    
    # Test basic Python functionality
    if ! python3.12 -c "import sys; print('Python test passed'); sys.exit(0)"; then
        handle_error "Python 3.12 basic functionality test failed"
    fi
    
    # Test pip functionality
    if ! python3.12 -m pip list >/dev/null 2>&1; then
        handle_error "Pip functionality test failed"
    fi
    
    log "✅ Python 3.12 installation verification completed successfully"
}

# Step 7: Post-Installation Cleanup and Status
post_installation_cleanup() {
    log "=== Post-Installation Cleanup ==="
    
    # Clean package cache
    apt-get autoclean || true
    apt-get autoremove -y || true
    
    # Update package database only if updatedb is available
    if command -v updatedb >/dev/null 2>&1; then
        updatedb 2>/dev/null || true
    else
        log "updatedb not available - skipping database update"
    fi
    
    # Create status report
    local status_file="/opt/citadel/logs/python-installation-status.txt"
    cat > "$status_file" << EOF
Python 3.12 Installation Status Report
Generated: $(date)

Python Version: $(python3.12 --version 2>&1)
Python Path: $(which python3.12)
Pip Version: $(python3.12 -m pip --version 2>&1)
Pip Path: $(which pip3.12 2>/dev/null || echo "Not in PATH")

Alternatives Configuration:
$(update-alternatives --list python3 2>/dev/null || echo "No python3 alternatives")
$(update-alternatives --list python 2>/dev/null || echo "No python alternatives")

Installation Status: SUCCESS
EOF
    
    log "✅ Status report created: $status_file"
}

# Main execution function
main() {
    log "Starting PLANB-04a Python 3.12 Installation Module"
    
    # Create backup before starting
    if ! $ERROR_HANDLER backup; then
        handle_error "Failed to create backup"
    fi
    
    # Execute installation steps directly with error handling
    log "Step 1: Initialization"
    if ! initialize_installation; then
        handle_error "Initialization failed"
    fi
    
    log "Step 2: Repository Setup"
    if ! setup_repository; then
        handle_error "Repository setup failed"
    fi
    
    log "Step 3: Python Installation"
    if ! install_python312; then
        handle_error "Python installation failed"
    fi
    
    log "Step 4: Pip Installation"
    if ! install_pip312; then
        handle_error "Pip installation failed"
    fi
    
    log "Step 5: Alternatives Configuration"
    if ! configure_alternatives; then
        handle_error "Alternatives configuration failed"
    fi
    
    # Run verification and cleanup
    verify_installation
    post_installation_cleanup
    
    log ""
    log "🎉 Python 3.12 installation module completed successfully!"
    log "✅ Python 3.12 is ready for virtual environment setup"
    log ""
}

# Execute main function
main "$@"