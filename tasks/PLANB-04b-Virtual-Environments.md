# PLANB-04b: Virtual Environments Setup Module

**Module:** Virtual Environment Creation and Management  
**Parent Task:** [PLANB-04-Python-Environment.md](PLANB-04-Python-Environment.md)  
**Duration:** 10-15 minutes  
**Prerequisites:** [PLANB-04a-Python-Installation.md](PLANB-04a-Python-Installation.md) completed

## Overview

This module creates and configures specialized virtual environments for different AI workloads with comprehensive management tools and error handling.

## Implementation Steps

### Step 1: Load Configuration and Validate Prerequisites

```bash
# Load configuration and validate prerequisites
CONFIG_FILE="/opt/citadel/configs/python-config.json"
ERROR_HANDLER="/opt/citadel/scripts/python-error-handler.sh"

validate_prerequisites() {
    echo "Validating prerequisites for virtual environment setup..."
    
    # Check Python 3.12 installation
    if ! python3.12 --version >/dev/null 2>&1; then
        echo "ERROR: Python 3.12 not found - run PLANB-04a first"
        return 1
    fi
    
    # Check pip installation
    if ! python3.12 -m pip --version >/dev/null 2>&1; then
        echo "ERROR: Pip for Python 3.12 not found"
        return 1
    fi
    
    # Check citadel directory
    if [ ! -d "/opt/citadel" ]; then
        echo "ERROR: /opt/citadel directory not found"
        return 1
    fi
    
    # Check configuration file
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "ERROR: Configuration file not found: $CONFIG_FILE"
        return 1
    fi
    
    echo "✅ Prerequisites validated"
    return 0
}

# Validate before proceeding
if ! validate_prerequisites; then
    echo "❌ Prerequisites validation failed"
    exit 1
fi
```

### Step 2: Create Environment Management Script

```bash
# Create enhanced environment management script with error handling
create_env_manager() {
    local script_path="/opt/citadel/scripts/env-manager.sh"
    
    echo "Creating environment management script..."
    
    sudo tee "$script_path" << 'EOF'
#!/bin/bash
# env-manager.sh - Manage Python virtual environments with error handling

set -euo pipefail

CONFIG_FILE="/opt/citadel/configs/python-config.json"
CITADEL_ROOT="/opt/citadel"
LOG_FILE="/opt/citadel/logs/env-manager.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
handle_error() {
    log "ERROR: $1"
    exit 1
}

# Load environment configuration
load_env_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Extract environment names from config
    ENV_NAMES=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
envs = list(config['environments'].keys())
print(' '.join(envs))
" 2>/dev/null) || handle_error "Failed to parse environment configuration"
}

# Show usage
show_usage() {
    echo "Usage: $0 [activate|deactivate|create|list|info|delete] [env_name]"
    echo ""
    echo "Commands:"
    echo "  activate [env]   - Activate virtual environment (default: citadel-env)"
    echo "  deactivate       - Deactivate current environment"
    echo "  create [env]     - Create new virtual environment"
    echo "  list             - List all environments"
    echo "  info             - Show current environment info"
    echo "  delete [env]     - Delete virtual environment"
    echo ""
    echo "Available environments (from config):"
    
    load_env_config
    for env in $ENV_NAMES; do
        local purpose=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
print(config['environments']['$env']['purpose'])
" 2>/dev/null || echo "Unknown purpose")
        echo "  $env - $purpose"
    done
}

# Create virtual environment
create_env() {
    local env_name=${1:-"citadel-env"}
    local env_path="$CITADEL_ROOT/$env_name"
    
    log "Creating environment: $env_name"
    
    if [ -d "$env_path" ]; then
        log "WARNING: Environment $env_name already exists at $env_path"
        read -p "Delete and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Removing existing environment: $env_name"
            rm -rf "$env_path"
        else
            log "Skipping environment creation"
            return 0
        fi
    fi
    
    # Create virtual environment
    if ! python3.12 -m venv "$env_path"; then
        handle_error "Failed to create virtual environment: $env_name"
    fi
    
    # Activate and upgrade base packages
    source "$env_path/bin/activate"
    
    if ! pip install --upgrade pip setuptools wheel; then
        log "WARNING: Failed to upgrade base packages (non-critical)"
    fi
    
    log "✅ Environment $env_name created successfully"
}

# Activate environment
activate_env() {
    local env_name=${1:-"citadel-env"}
    local env_path="$CITADEL_ROOT/$env_name"
    
    if [ ! -d "$env_path" ]; then
        handle_error "Environment $env_name not found at $env_path"
    fi
    
    log "Activating environment: $env_name"
    source "$env_path/bin/activate"
    
    echo "Active environment: $(basename "$VIRTUAL_ENV")"
    echo "Python version: $(python --version)"
    echo "Pip version: $(pip --version)"
}

# List environments
list_envs() {
    echo "Available environments:"
    load_env_config
    
    for env in $ENV_NAMES; do
        local env_path="$CITADEL_ROOT/$env"
        if [ -d "$env_path" ]; then
            local python_version=$(source "$env_path/bin/activate" && python --version 2>/dev/null || echo "Unknown")
            echo "  ✅ $env ($python_version)"
        else
            echo "  ❌ $env (not created)"
        fi
    done
}

# Show environment info
show_info() {
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        echo "Active environment: $(basename "$VIRTUAL_ENV")"
        echo "Environment path: $VIRTUAL_ENV"
        echo "Python version: $(python --version)"
        echo "Python path: $(which python)"
        echo "Pip version: $(pip --version)"
        echo "Installed packages: $(pip list --format=freeze | wc -l)"
    else
        echo "No virtual environment active"
        echo "System Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    fi
}

# Delete environment
delete_env() {
    local env_name=${1:-""}
    
    if [ -z "$env_name" ]; then
        echo "ERROR: Environment name required for deletion"
        return 1
    fi
    
    local env_path="$CITADEL_ROOT/$env_name"
    
    if [ ! -d "$env_path" ]; then
        log "Environment $env_name not found at $env_path"
        return 1
    fi
    
    read -p "Delete environment $env_name? This cannot be undone (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Deleting environment: $env_name"
        rm -rf "$env_path"
        log "✅ Environment $env_name deleted"
    else
        log "Environment deletion cancelled"
    fi
}

# Main command processing
case "${1:-}" in
    activate)
        activate_env "$2"
        ;;
    deactivate)
        if [ -n "${VIRTUAL_ENV:-}" ]; then
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
    delete)
        delete_env "$2"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
EOF
    
    chmod +x "$script_path"
    echo "✅ Environment manager script created: $script_path"
    return 0
}

# Create the environment manager
if ! $ERROR_HANDLER execute "Environment Manager Creation" "create_env_manager" "[ -f /opt/citadel/scripts/env-manager.sh ]"; then
    echo "❌ Failed to create environment manager"
    exit 1
fi
```

### Step 3: Create Virtual Environments from Configuration

```bash
# Create all virtual environments defined in configuration
create_configured_environments() {
    echo "Creating virtual environments from configuration..."
    
    # Get environment names from configuration
    local env_names=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
envs = list(config['environments'].keys())
print(' '.join(envs))
")
    
    for env_name in $env_names; do
        echo "Creating environment: $env_name"
        
        # Get environment configuration
        local purpose=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
print(config['environments']['$env_name']['purpose'])
")
        
        echo "Purpose: $purpose"
        
        # Create environment using the manager
        if ! /opt/citadel/scripts/env-manager.sh create "$env_name"; then
            echo "ERROR: Failed to create environment: $env_name"
            return 1
        fi
        
        echo "✅ Environment $env_name created successfully"
    done
    
    return 0
}

# Execute environment creation with error handling
if ! $ERROR_HANDLER execute "Virtual Environments Creation" "create_configured_environments" "/opt/citadel/scripts/env-manager.sh list | grep -q '✅'"; then
    echo "❌ Failed to create virtual environments"
    $ERROR_HANDLER rollback
    exit 1
fi
```

### Step 4: Create Environment Activation Script

```bash
# Create enhanced activation script with optimizations
create_activation_script() {
    local script_path="/opt/citadel/scripts/activate-citadel.sh"
    
    echo "Creating enhanced activation script..."
    
    # Get paths from configuration
    local citadel_root=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
print(config['paths']['citadel_root'])
")
    
    local models_cache=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
print(config['paths']['models_cache'])
")
    
    sudo tee "$script_path" << EOF
#!/bin/bash
# activate-citadel.sh - Activate Citadel AI environment with optimizations

CITADEL_ROOT="$citadel_root"
CITADEL_USER="\$(whoami)"
CONFIG_FILE="$CONFIG_FILE"

echo "🚀 Activating Citadel AI Environment for user: \$CITADEL_USER"
echo "🌐 Hana-X Lab Environment (db server - 192.168.10.35)"
echo "========================================================="

# Validate environment exists
if [ ! -f "\$CITADEL_ROOT/citadel-env/bin/activate" ]; then
    echo "❌ Virtual environment not found"
    echo "Run: /opt/citadel/scripts/env-manager.sh create citadel-env"
    exit 1
fi

# Activate virtual environment
source "\$CITADEL_ROOT/citadel-env/bin/activate"
echo "✅ Virtual environment activated"

# Load optimization configuration
if [ -f "\$CONFIG_FILE" ]; then
    # Apply memory optimizations
    export MALLOC_ARENA_MAX="\$(python3 -c 'import json; print(json.load(open("'"\$CONFIG_FILE"'"))["optimization"]["memory"]["malloc_arena_max"])' 2>/dev/null || echo '4')"
    
    # Apply threading optimizations  
    export OMP_NUM_THREADS="\$(python3 -c 'import json; print(min(json.load(open("'"\$CONFIG_FILE"'"))["optimization"]["threading"]["max_threads"], 16))' 2>/dev/null || echo '8')"
    export MKL_NUM_THREADS="\$OMP_NUM_THREADS"
    export NUMEXPR_NUM_THREADS="\$OMP_NUM_THREADS"
    
    # Apply CUDA optimizations
    export CUDA_LAUNCH_BLOCKING="\$(python3 -c 'import json; print("1" if json.load(open("'"\$CONFIG_FILE"'"))["optimization"]["cuda"]["launch_blocking"] else "0")' 2>/dev/null || echo '0')"
    export CUDA_CACHE_DISABLE="\$(python3 -c 'import json; print("1" if json.load(open("'"\$CONFIG_FILE"'"))["optimization"]["cuda"]["cache_disable"] else "0")' 2>/dev/null || echo '0')"
    
    echo "✅ Optimizations applied from configuration"
fi

# Set environment variables
export CITADEL_ROOT="\$CITADEL_ROOT"
export CITADEL_MODELS="\$CITADEL_ROOT/models"
export CITADEL_CONFIGS="\$CITADEL_ROOT/configs"
export CITADEL_LOGS="\$CITADEL_ROOT/logs"

# Set cache directories
export HF_HOME="$models_cache"
export TRANSFORMERS_CACHE="$models_cache/transformers"
export HF_DATASETS_CACHE="$models_cache/datasets"

# Display environment info
echo ""
echo "Environment Information:"
echo "  Python: \$(python --version 2>/dev/null || echo 'Not available')"
echo "  Virtual Env: \$(basename "\$VIRTUAL_ENV")"
echo "  Config File: \$CONFIG_FILE"
echo ""
echo "🎯 Citadel AI environment ready!"
EOF
    
    chmod +x "$script_path"
    echo "✅ Activation script created: $script_path"
    return 0
}

# Create activation script with error handling
if ! $ERROR_HANDLER execute "Activation Script Creation" "create_activation_script" "[ -f /opt/citadel/scripts/activate-citadel.sh ]"; then
    echo "❌ Failed to create activation script"
    exit 1
fi
```

## Validation Steps

### Step 5: Comprehensive Environment Testing

```bash
# Test all virtual environments
test_environments() {
    echo "=== Virtual Environment Testing ==="
    
    # Test environment manager
    echo "Testing environment manager..."
    if ! /opt/citadel/scripts/env-manager.sh list; then
        echo "ERROR: Environment manager test failed"
        return 1
    fi
    
    # Test each environment
    local env_names=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
envs = list(config['environments'].keys())
print(' '.join(envs))
")
    
    for env_name in $env_names; do
        echo "Testing environment: $env_name"
        
        local env_path="/opt/citadel/$env_name"
        if [ ! -d "$env_path" ]; then
            echo "ERROR: Environment $env_name not found"
            return 1
        fi
        
        # Test activation
        if ! (source "$env_path/bin/activate" && python --version); then
            echo "ERROR: Failed to activate environment $env_name"
            return 1
        fi
        
        echo "✅ Environment $env_name tested successfully"
    done
    
    # Test activation script
    echo "Testing activation script..."
    if ! bash /opt/citadel/scripts/activate-citadel.sh -c "echo 'Activation test passed'"; then
        echo "ERROR: Activation script test failed"
        return 1
    fi
    
    echo "✅ All virtual environment tests passed"
    return 0
}

# Execute comprehensive testing
if ! test_environments; then
    echo "❌ Virtual environment testing failed"
    $ERROR_HANDLER rollback
    exit 1
fi
```

### Step 6: Create Status Report

```bash
# Generate virtual environments status report
generate_status_report() {
    local status_file="/opt/citadel/logs/virtual-environments-status.txt"
    
    cat > "$status_file" << EOF
Virtual Environments Setup Status Report
Generated: $(date)

Configuration File: $CONFIG_FILE
Environment Manager: /opt/citadel/scripts/env-manager.sh
Activation Script: /opt/citadel/scripts/activate-citadel.sh

Created Environments:
$(/opt/citadel/scripts/env-manager.sh list)

Environment Details:
EOF
    
    # Add details for each environment
    local env_names=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
envs = list(config['environments'].keys())
print(' '.join(envs))
")
    
    for env_name in $env_names; do
        local env_path="/opt/citadel/$env_name"
        if [ -d "$env_path" ]; then
            echo "" >> "$status_file"
            echo "$env_name:" >> "$status_file"
            echo "  Path: $env_path" >> "$status_file"
            echo "  Python: $(source "$env_path/bin/activate" && python --version 2>&1)" >> "$status_file"
            echo "  Packages: $(source "$env_path/bin/activate" && pip list --format=freeze | wc -l)" >> "$status_file"
        fi
    done
    
    echo "" >> "$status_file"
    echo "Setup Status: SUCCESS" >> "$status_file"
    
    echo "✅ Status report created: $status_file"
    return 0
}

# Generate status report
generate_status_report

echo ""
echo "🎉 Virtual Environments module completed successfully!"
echo "✅ All environments created and tested"
echo "📋 Use: /opt/citadel/scripts/env-manager.sh list"
echo ""
```

## Module Summary

This module provides:

- **Configuration-driven environment creation** from JSON config
- **Comprehensive environment management** with full lifecycle support
- **Error handling and validation** for each environment
- **Enhanced activation scripts** with optimization loading
- **Detailed testing and reporting** for verification

**Next Module:** Continue to [PLANB-04c-Dependencies-Optimization.md](PLANB-04c-Dependencies-Optimization.md) for dependencies installation.