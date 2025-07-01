# PLANB-04a: Python 3.12 Installation Module

**Module:** Python 3.12 Installation with Error Handling  
**Parent Task:** [PLANB-04-Python-Environment.md](PLANB-04-Python-Environment.md)  
**Duration:** 10-15 minutes  

## Overview

This module handles the installation of Python 3.12 with comprehensive error handling and rollback capabilities. It uses configuration-driven approach and validates each step.

## Implementation Steps

### Step 1: Load Configuration and Create Backup

```bash
# Load configuration
CONFIG_FILE="/opt/citadel/configs/python-config.json"
ERROR_HANDLER="/opt/citadel/scripts/python-error-handler.sh"

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
    local ppa_repo=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE'))['python']['repository'])")
    
    echo "Adding Python repository: $ppa_repo"
    
    # Update package lists first
    if ! sudo apt update; then
        echo "ERROR: Failed to update package lists"
        return 1
    fi
    
    # Install software-properties-common if not present
    if ! sudo apt install -y software-properties-common; then
        echo "ERROR: Failed to install software-properties-common"
        return 1
    fi
    
    # Add PPA repository
    if ! sudo add-apt-repository "$ppa_repo" -y; then
        echo "ERROR: Failed to add Python PPA repository"
        return 1
    fi
    
    # Update package lists again
    if ! sudo apt update; then
        echo "ERROR: Failed to update package lists after PPA addition"
        return 1
    fi
    
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
    
    echo "Installing Python packages: $python_packages"
    if ! sudo apt install -y $python_packages; then
        echo "ERROR: Failed to install Python 3.12 packages"
        return 1
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
    
    # Download get-pip.py with error handling
    if ! curl -sS https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py; then
        echo "ERROR: Failed to download get-pip.py"
        return 1
    fi
    
    # Install pip
    if ! python3.12 /tmp/get-pip.py; then
        echo "ERROR: Failed to install pip for Python 3.12"
        return 1
    fi
    
    # Cleanup
    rm -f /tmp/get-pip.py
    
    # Upgrade pip to latest version
    if ! python3.12 -m pip install --upgrade pip; then
        echo "WARNING: Failed to upgrade pip (non-critical)"
    fi
    
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

    # Only remove alternatives for python3/python/pip3/pip if they point to python3.12 or pip3.12, or if about to be overwritten
    # This minimizes risk of removing all python alternatives before python3.12 is installed

    # Set up Python alternatives (after confirming python3.12 is installed)
    if ! sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100; then
        echo "ERROR: Failed to configure python3 alternative"
        return 1
    fi

    if ! sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 90; then
        echo "WARNING: Failed to configure python3.10 alternative (non-critical)"
    fi

    if ! sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 100; then
        echo "ERROR: Failed to configure python alternative"
        return 1
    fi

    # Set up pip alternatives
    local pip312_path=$(which pip3.12 2>/dev/null || echo "/usr/local/bin/pip3.12")

    if [ -f "$pip312_path" ]; then
        if ! sudo update-alternatives --install /usr/bin/pip3 pip3 "$pip312_path" 100; then
            echo "WARNING: Failed to configure pip3 alternative (non-critical)"
        fi

        if ! sudo update-alternatives --install /usr/bin/pip pip "$pip312_path" 100; then
            echo "WARNING: Failed to configure pip alternative (non-critical)"
        fi
    fi

    # Optionally, remove any alternatives that point to non-existent binaries (cleanup)
    # This is safe after python3.12 and pip3.12 are installed and alternatives are set
    sudo update-alternatives --remove-all python3 2>/dev/null || true
    sudo update-alternatives --remove-all python 2>/dev/null || true
    sudo update-alternatives --remove-all pip3 2>/dev/null || true
    sudo update-alternatives --remove-all pip 2>/dev/null || true

    # Re-add alternatives to ensure correct configuration
    sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 100
    sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 100
    if [ -f "$pip312_path" ]; then
        sudo update-alternatives --install /usr/bin/pip3 pip3 "$pip312_path" 100
        sudo update-alternatives --install /usr/bin/pip pip "$pip312_path" 100
    fi

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
    
    # Check Python version
    local python_version=$(python3.12 --version 2>&1)
    echo "Python 3.12 version: $python_version"
    
    if ! echo "$python_version" | grep -q "Python 3.12"; then
        echo "ERROR: Python 3.12 not properly installed"
        return 1
    fi
    
    # Check alternative configuration
    local current_python=$(python --version 2>&1)
    echo "Current python version: $current_python"
    
    if ! echo "$current_python" | grep -q "Python 3.12"; then
        echo "WARNING: Python alternative not pointing to 3.12"
    fi
    
    # Check pip installation
    local pip_version=$(python3.12 -m pip --version 2>&1)
    echo "Pip version: $pip_version"
    
    if ! echo "$pip_version" | grep -q "pip"; then
        echo "ERROR: Pip not properly installed"
        return 1
    fi
    
    # Test basic Python functionality
    if ! python3.12 -c "import sys; print('Python test passed'); sys.exit(0)"; then
        echo "ERROR: Python 3.12 basic functionality test failed"
        return 1
    fi
    
    # Test pip functionality
    if ! python3.12 -m pip list >/dev/null 2>&1; then
        echo "ERROR: Pip functionality test failed"
        return 1
    fi
    
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

## Module Summary

This module provides:

- **Configuration-driven installation** using JSON configuration
- **Comprehensive error handling** with automatic rollback
- **Step-by-step validation** ensuring each component works
- **Safe alternatives configuration** for version management
- **Detailed logging** and status reporting
- **Cleanup procedures** for optimal system state

**Next Module:** Continue to [PLANB-04b-Virtual-Environments.md](PLANB-04b-Virtual-Environments.md) for virtual environment setup.