# PLANB-04a: Python 3.12 Installation Module

**Module:** Python 3.12 Installation with Error Handling  
**Parent Task:** [PLANB-04-Python-Environment.md](PLANB-04-Python-Environment.md)  
**Duration:** 10-15 minutes  

## Overview

This module handles the installation of Python 3.12 with comprehensive error handling and rollback capabilities. It uses configuration-driven approach and validates each step.

## Implementation Steps

### Step 1: Prerequisites Validation and Configuration Load

```bash
# Prerequisites validation and configuration loading
validate_prerequisites() {
    echo "=== Prerequisites Validation ==="
    
    # Check for root/sudo privileges
    if [ "$EUID" -eq 0 ]; then
        echo "WARNING: Running as root. Consider using sudo for specific commands instead."
    elif ! sudo -n true 2>/dev/null; then
        echo "ERROR: This script requires sudo privileges"
        echo "Please run: sudo -v"
        return 1
    fi
    
    # Check internet connectivity
    echo "Checking internet connectivity..."
    if ! ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
        echo "ERROR: No internet connectivity - required for package downloads"
        return 1
    fi
    
    # Check available disk space (need at least 2GB)
    local available_space=$(df /usr | awk 'NR==2 {print $4}')
    local required_space=$((2 * 1024 * 1024)) # 2GB in KB
    
    if [ "$available_space" -lt "$required_space" ]; then
        echo "ERROR: Insufficient disk space. Need 2GB, have $(($available_space / 1024 / 1024))GB"
        return 1
    fi
    
    # Check if Python 3 is available for configuration parsing
    if ! command -v python3 >/dev/null 2>&1; then
        echo "ERROR: python3 is required for configuration parsing"
        return 1
    fi
    
    echo "✅ Prerequisites validation completed"
    return 0
}

# Load configuration
CONFIG_FILE="/opt/citadel/configs/python-config.json"
ERROR_HANDLER="/opt/citadel/scripts/python-error-handler.sh"

# Validate prerequisites before proceeding
if ! validate_prerequisites; then
    echo "❌ Prerequisites validation failed"
    exit 1
fi

# Create backup before installation
echo "Creating backup before Python installation..."
if ! $ERROR_HANDLER backup; then
    echo "❌ Failed to create backup"
    exit 1
fi

echo "✅ Backup created successfully"
```

### Step 2: Repository Setup with Error Handling

```bash
# Add Python 3.12 repository with error handling
setup_repository() {
    # Use load_env_config.py for safer configuration parsing
    local config_loader="/opt/citadel/scripts/load_env_config.py"
    
    if [ -f "$config_loader" ]; then
        # Use the configuration loader script
        eval "$(python3 "$config_loader" "$CONFIG_FILE" python.repository)"
        local ppa_repo="$PYTHON_REPOSITORY"
    else
        # Fallback to inline parsing with error handling
        local ppa_repo
        if ! ppa_repo=$(python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print(config['python']['repository'])
except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
    print('ppa:deadsnakes/ppa', file=sys.stderr)  # fallback
    exit(1)
" 2>/dev/null); then
            echo "WARNING: Failed to read repository from config, using default"
            ppa_repo="ppa:deadsnakes/ppa"
        fi
    fi
    
    echo "Adding Python repository: $ppa_repo"
    
    # Check if repository is already added
    if apt-cache policy python3.12 2>/dev/null | grep -q "deadsnakes"; then
        echo "✅ Python 3.12 repository already configured"
        return 0
    fi
    
    # Update package lists first
    echo "Updating package lists..."
    if ! sudo apt update; then
        echo "ERROR: Failed to update package lists"
        return 1
    fi
    
    # Install software-properties-common if not present
    echo "Ensuring software-properties-common is installed..."
    if ! dpkg -l | grep -q software-properties-common; then
        if ! sudo apt install -y software-properties-common; then
            echo "ERROR: Failed to install software-properties-common"
            return 1
        fi
    fi
    
    # Add PPA repository with verification
    echo "Adding PPA repository: $ppa_repo"
    if ! sudo add-apt-repository "$ppa_repo" -y; then
        echo "ERROR: Failed to add Python PPA repository"
        return 1
    fi
    
    # Update package lists again
    echo "Updating package lists after PPA addition..."
    if ! sudo apt update; then
        echo "ERROR: Failed to update package lists after PPA addition"
        return 1
    fi
    
    # Verify repository was added successfully
    echo "Verifying repository addition..."
    if ! apt-cache policy python3.12 2>/dev/null | grep -q "deadsnakes"; then
        echo "ERROR: Python 3.12 not available from deadsnakes repository"
        return 1
    fi
    
    echo "✅ Repository setup completed successfully"
    return 0
}

# Execute repository setup with error handling
if ! $ERROR_HANDLER execute "Repository Setup" "setup_repository" "apt-cache policy python3.12 | grep -q 'deadsnakes'"; then
    echo "❌ Repository setup failed"
    $ERROR_HANDLER rollback
    exit 1
fi
```

### Step 3: Python 3.12 Installation with Validation

```bash
# Install Python 3.12 with comprehensive error handling
install_python312() {
    echo "Installing Python 3.12 and related packages..."
    
    # Get package lists from configuration with error handling
    local python_packages build_deps
    local config_loader="/opt/citadel/scripts/load_env_config.py"
    
    if [ -f "$config_loader" ]; then
        # Use configuration loader for safer parsing
        eval "$(python3 "$config_loader" "$CONFIG_FILE" python.packages)"
        eval "$(python3 "$config_loader" "$CONFIG_FILE" python.build_dependencies)"
        python_packages="$PYTHON_PACKAGES"
        build_deps="$PYTHON_BUILD_DEPENDENCIES"
    else
        # Fallback with error handling
        if ! python_packages=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print(' '.join(config['python']['packages']))
except Exception as e:
    print('python3.12 python3.12-dev python3.12-venv', file=sys.stderr)
    exit(1)
" 2>/dev/null); then
            echo "WARNING: Using default Python packages"
            python_packages="python3.12 python3.12-dev python3.12-venv python3.12-distutils"
        fi
        
        if ! build_deps=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print(' '.join(config['python']['build_dependencies']))
except Exception as e:
    print('build-essential libssl-dev libffi-dev', file=sys.stderr)
    exit(1)
" 2>/dev/null); then
            echo "WARNING: Using default build dependencies"
            build_deps="build-essential libssl-dev libffi-dev libbz2-dev libreadline-dev libsqlite3-dev"
        fi
    fi
    
    echo "Installing Python packages: $python_packages"
    if ! sudo apt install -y $python_packages; then
        echo "ERROR: Failed to install Python 3.12 packages"
        # Try installing core packages individually
        echo "Attempting to install core packages individually..."
        for pkg in python3.12 python3.12-dev python3.12-venv; do
            if ! sudo apt install -y "$pkg"; then
                echo "ERROR: Failed to install critical package: $pkg"
                return 1
            fi
        done
    fi
    
    echo "Installing build dependencies: $build_deps"
    if ! sudo apt install -y $build_deps; then
        echo "ERROR: Failed to install build dependencies"
        return 1
    fi
    
    return 0
}

# Execute Python installation with validation
if ! $ERROR_HANDLER execute "Python Installation" "install_python312" "python3.12 --version"; then
    echo "❌ Python 3.12 installation failed"
    $ERROR_HANDLER rollback
    exit 1
fi
```

### Step 4: Pip Installation with Error Handling

```bash
# Install pip for Python 3.12
install_pip312() {
    echo "Installing pip for Python 3.12..."
    
    # Check if pip is already installed with Python 3.12
    if python3.12 -m pip --version >/dev/null 2>&1; then
        echo "✅ Pip already installed with Python 3.12"
        # Still upgrade to latest version
        if ! python3.12 -m pip install --upgrade pip; then
            echo "WARNING: Failed to upgrade pip (non-critical)"
        fi
        return 0
    fi
    
    # Create temporary directory for download
    local temp_dir=$(mktemp -d)
    local get_pip_path="$temp_dir/get-pip.py"
    
    echo "Downloading get-pip.py to $get_pip_path..."
    
    # Download get-pip.py with retries and verification
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        echo "Download attempt $attempt of $max_attempts..."
        
        if curl -fsSL --retry 3 --retry-delay 2 \
               -o "$get_pip_path" \
               https://bootstrap.pypa.io/get-pip.py; then
            
            # Verify download
            if [ -f "$get_pip_path" ] && [ -s "$get_pip_path" ]; then
                echo "✅ get-pip.py downloaded successfully"
                break
            else
                echo "ERROR: Downloaded file is empty or invalid"
            fi
        else
            echo "ERROR: Failed to download get-pip.py (attempt $attempt)"
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            echo "ERROR: Failed to download get-pip.py after $max_attempts attempts"
            rm -rf "$temp_dir"
            return 1
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    # Install pip with verification
    echo "Installing pip for Python 3.12..."
    if ! python3.12 "$get_pip_path" --user; then
        echo "WARNING: User installation failed, trying system-wide..."
        if ! sudo python3.12 "$get_pip_path"; then
            echo "ERROR: Failed to install pip for Python 3.12"
            rm -rf "$temp_dir"
            return 1
        fi
    fi
    
    # Cleanup
    rm -rf "$temp_dir"
    
    # Verify pip installation
    if ! python3.12 -m pip --version >/dev/null 2>&1; then
        echo "ERROR: Pip installation verification failed"
        return 1
    fi
    
    # Upgrade pip to latest version
    echo "Upgrading pip to latest version..."
    if ! python3.12 -m pip install --upgrade pip; then
        echo "WARNING: Failed to upgrade pip (non-critical)"
    fi
    
    echo "✅ Pip installation completed successfully"
    return 0
}

# Execute pip installation with validation
if ! $ERROR_HANDLER execute "Pip Installation" "install_pip312" "python3.12 -m pip --version"; then
    echo "❌ Pip installation failed"
    $ERROR_HANDLER rollback
    exit 1
fi
```

### Step 5: Configure Python Alternatives

```bash

# Configure Python alternatives with error handling
configure_alternatives() {
    echo "Configuring Python alternatives..."

    # CRITICAL: Verify python3.12 is installed before configuring alternatives
    if ! command -v python3.12 >/dev/null 2>&1; then
        echo "ERROR: python3.12 not found, cannot configure alternatives"
        return 1
    fi

    # Find pip3.12 path with better detection
    local pip312_path
    if command -v pip3.12 >/dev/null 2>&1; then
        pip312_path=$(command -v pip3.12)
    elif [ -f "/usr/local/bin/pip3.12" ]; then
        pip312_path="/usr/local/bin/pip3.12"
    elif [ -f "$HOME/.local/bin/pip3.12" ]; then
        pip312_path="$HOME/.local/bin/pip3.12"
    else
        echo "WARNING: pip3.12 not found, skipping pip alternatives"
        pip312_path=""
    fi

    # Set up Python alternatives with validation
    echo "Setting up python3 alternative..."
    if ! sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100; then
        echo "ERROR: Failed to configure python3 alternative"
        return 1
    fi

    # Add python3.10 alternative only if it exists
    if command -v python3.10 >/dev/null 2>&1; then
        echo "Adding python3.10 alternative..."
        if ! sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 90; then
            echo "WARNING: Failed to configure python3.10 alternative (non-critical)"
        fi
    fi

    # Set up python alternative (symlink to python3)
    echo "Setting up python alternative..."
    if ! sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 100; then
        echo "ERROR: Failed to configure python alternative"
        return 1
    fi

    # Set up pip alternatives only if pip3.12 exists
    if [ -n "$pip312_path" ] && [ -f "$pip312_path" ]; then
        echo "Setting up pip alternatives..."
        
        if ! sudo update-alternatives --install /usr/bin/pip3 pip3 "$pip312_path" 100; then
            echo "WARNING: Failed to configure pip3 alternative (non-critical)"
        fi

        if ! sudo update-alternatives --install /usr/bin/pip pip "$pip312_path" 100; then
            echo "WARNING: Failed to configure pip alternative (non-critical)"
        fi
    fi

    # Verify alternatives are working
    echo "Verifying alternatives configuration..."
    if ! python3 --version | grep -q "3.12"; then
        echo "ERROR: python3 alternative not pointing to Python 3.12"
        return 1
    fi
    
    if ! python --version | grep -q "3.12"; then
        echo "ERROR: python alternative not pointing to Python 3.12"
        return 1
    fi

    echo "✅ Alternatives configured successfully"
    return 0
}

# Execute alternatives configuration with validation
if ! $ERROR_HANDLER execute "Alternatives Configuration" "configure_alternatives" "python --version | grep -q '3.12'"; then
    echo "❌ Alternatives configuration failed"
    $ERROR_HANDLER rollback
    exit 1
fi
```

## Validation Steps

### Step 6: Comprehensive Installation Verification

```bash
# Verify Python 3.12 installation
verify_installation() {
    echo "=== Python 3.12 Installation Verification ==="
    
    # Check Python 3.12 installation
    echo "Checking Python 3.12 installation..."
    if ! command -v python3.12 >/dev/null 2>&1; then
        echo "ERROR: python3.12 command not found"
        return 1
    fi
    
    local python_version=$(python3.12 --version 2>&1)
    echo "Python 3.12 version: $python_version"
    
    if ! echo "$python_version" | grep -q "Python 3.12"; then
        echo "ERROR: Python 3.12 not properly installed"
        return 1
    fi
    
    # Check alternative configuration
    echo "Checking alternatives configuration..."
    if command -v python >/dev/null 2>&1; then
        local current_python=$(python --version 2>&1)
        echo "Current python version: $current_python"
        
        if ! echo "$current_python" | grep -q "Python 3.12"; then
            echo "WARNING: Python alternative not pointing to 3.12"
            echo "This may cause issues. Run: sudo update-alternatives --config python"
        fi
    fi
    
    if command -v python3 >/dev/null 2>&1; then
        local current_python3=$(python3 --version 2>&1)
        echo "Current python3 version: $current_python3"
        
        if ! echo "$current_python3" | grep -q "Python 3.12"; then
            echo "WARNING: Python3 alternative not pointing to 3.12"
        fi
    fi
    
    # Check pip installation and functionality
    echo "Checking pip installation..."
    if ! python3.12 -m pip --version >/dev/null 2>&1; then
        echo "ERROR: Pip not properly installed for Python 3.12"
        return 1
    fi
    
    local pip_version=$(python3.12 -m pip --version 2>&1)
    echo "Pip version: $pip_version"
    
    if ! echo "$pip_version" | grep -q "pip"; then
        echo "ERROR: Pip version output invalid"
        return 1
    fi
    
    # Test basic Python functionality
    echo "Testing basic Python functionality..."
    if ! python3.12 -c "
import sys
import os
import json
print('Python 3.12 basic functionality test passed')
print(f'Python executable: {sys.executable}')
print(f'Python version: {sys.version_info}')
print(f'Platform: {sys.platform}')
sys.exit(0)
"; then
        echo "ERROR: Python 3.12 basic functionality test failed"
        return 1
    fi
    
    # Test pip functionality
    echo "Testing pip functionality..."
    if ! python3.12 -m pip list --format=freeze >/dev/null 2>&1; then
        echo "ERROR: Pip functionality test failed"
        return 1
    fi
    
    # Test module imports
    echo "Testing critical module imports..."
    if ! python3.12 -c "
import sys, os, json, urllib.request, ssl, sqlite3
print('Critical modules import successfully')
"; then
        echo "ERROR: Critical module import test failed"
        return 1
    fi
    
    # Check Python paths and environment
    echo "Python environment information:"
    python3.12 -c "
import sys
print(f'  Executable: {sys.executable}')
print(f'  Version: {sys.version}')
print(f'  Path: {sys.path[:3]}...')  # Show first 3 paths
print(f'  Prefix: {sys.prefix}')
print(f'  Base prefix: {sys.base_prefix}')
"
    
    echo "✅ Python 3.12 installation verification completed successfully"
    return 0
}

# Run verification
if ! verify_installation; then
    echo "❌ Installation verification failed"
    $ERROR_HANDLER rollback
    exit 1
fi
```

## Error Recovery

### Step 7: Post-Installation Cleanup and Status

```bash
# Post-installation cleanup and status report
post_installation_cleanup() {
    echo "=== Post-Installation Cleanup ==="
    
    # Clean package cache
    sudo apt autoclean || true
    sudo apt autoremove -y || true
    
    # Update package database
    sudo updatedb 2>/dev/null || true
    
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
    
    echo "✅ Status report created: $status_file"
    return 0
}

# Execute cleanup
post_installation_cleanup

echo ""
echo "🎉 Python 3.12 installation module completed successfully!"
echo "✅ Python 3.12 is ready for virtual environment setup"
echo ""
```

## Security Considerations

### Safe Installation Practices

1. **Repository Verification**: Always verify repository sources before adding
2. **Package Integrity**: Use official deadsnakes PPA for Python installations
3. **Privilege Management**: Use sudo only when necessary, avoid running as root
4. **Download Security**: Verify downloads using checksums when possible
5. **System Backup**: Always create backups before system modifications

### Post-Installation Security

```bash
# Verify Python installation integrity
python3.12 -c "import hashlib, sys; print(f'Python executable: {sys.executable}')"

# Check for any suspicious modules
python3.12 -c "import sys; print('\\n'.join(sys.path))"

# Ensure pip uses HTTPS
python3.12 -m pip config set global.trusted-host ""
python3.12 -m pip config list
```

## Troubleshooting

### Common Issues and Solutions

#### Issue: Repository Addition Fails
**Symptoms**: `add-apt-repository` command fails
**Solutions**:
```bash
# Check internet connectivity
ping -c 3 8.8.8.8

# Manually add repository
echo "deb http://ppa.launchpad.net/deadsnakes/ppa/ubuntu $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/deadsnakes-ppa.list
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776
sudo apt update
```

#### Issue: Python 3.12 Package Not Found
**Symptoms**: `E: Unable to locate package python3.12`
**Solutions**:
```bash
# Verify repository
apt-cache policy python3.12

# Check Ubuntu version compatibility
lsb_release -a

# Manually update package lists
sudo apt update && sudo apt upgrade
```

#### Issue: Alternatives Configuration Fails
**Symptoms**: `update-alternatives` commands fail
**Solutions**:
```bash
# Check existing alternatives
sudo update-alternatives --display python3
sudo update-alternatives --display python

# Remove broken alternatives
sudo update-alternatives --remove-all python3
sudo update-alternatives --remove-all python

# Reconfigure manually
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100
```

#### Issue: Pip Installation Fails
**Symptoms**: get-pip.py download or installation fails
**Solutions**:
```bash
# Alternative pip installation
sudo apt install python3.12-pip

# Or use ensurepip
python3.12 -m ensurepip --default-pip

# Manual pip installation
wget https://bootstrap.pypa.io/get-pip.py
python3.12 get-pip.py --user
```

## Module Summary

This module provides:

- **Configuration-driven installation** using JSON configuration
- **Comprehensive error handling** with automatic rollback
- **Step-by-step validation** ensuring each component works
- **Safe alternatives configuration** for version management
- **Detailed logging** and status reporting
- **Cleanup procedures** for optimal system state

**Next Module:** Continue to [PLANB-04b-Virtual-Environments.md](PLANB-04b-Virtual-Environments.md) for virtual environment setup.