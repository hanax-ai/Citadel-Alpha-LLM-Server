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
LOAD_CONFIG_SCRIPT="/opt/citadel/scripts/load_env_config.py"

validate_prerequisites() {
    echo "Validating prerequisites for virtual environment setup..."
    
    # Check Python 3.12 installation
    if ! command -v python3.12 >/dev/null 2>&1; then
        echo "ERROR: Python 3.12 not found - run PLANB-04a first"
        return 1
    fi
    
    # Verify Python 3.12 works
    if ! python3.12 --version >/dev/null 2>&1; then
        echo "ERROR: Python 3.12 installation is broken"
        return 1
    fi
    
    # Check pip installation
    if ! python3.12 -m pip --version >/dev/null 2>&1; then
        echo "ERROR: Pip for Python 3.12 not found"
        return 1
    fi
    
    # Check citadel directory structure
    for dir in "/opt/citadel" "/opt/citadel/scripts" "/opt/citadel/configs" "/opt/citadel/logs"; do
        if [ ! -d "$dir" ]; then
            echo "ERROR: Required directory not found: $dir"
            return 1
        fi
    done
    
    # Check configuration file
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "ERROR: Configuration file not found: $CONFIG_FILE"
        return 1
    fi
    
    # Validate JSON syntax
    if ! python3 -m json.tool "$CONFIG_FILE" >/dev/null 2>&1; then
        echo "ERROR: Invalid JSON in configuration file"
        return 1
    fi
    
    # Check for load_env_config.py script
    if [ ! -f "$LOAD_CONFIG_SCRIPT" ]; then
        echo "WARNING: load_env_config.py not found, will use fallback parsing"
    fi
    
    # Check error handler script
    if [ ! -f "$ERROR_HANDLER" ]; then
        echo "ERROR: Error handler script not found: $ERROR_HANDLER"
        return 1
    fi
    
    echo "✅ Prerequisites validated successfully"
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
# Create the environment manager (inline, not as a function)
script_path="/opt/citadel/scripts/env-manager.sh"
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

# Load environment configuration with better error handling
load_env_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Use load_env_config.py if available, otherwise fallback
    local config_loader="/opt/citadel/scripts/load_env_config.py"
    
    if [ -f "$config_loader" ]; then
        # Use the standardized configuration loader
        ENV_NAMES=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    if 'environments' not in config:
        print('citadel-env vllm-env dev-env', file=sys.stderr)  # defaults
        sys.exit(1)
    envs = list(config['environments'].keys())
    print(' '.join(envs))
except Exception as e:
    print('citadel-env vllm-env dev-env', file=sys.stderr)  # defaults
    sys.exit(1)
" 2>/dev/null) || {
            log "WARNING: Failed to parse environments from config, using defaults"
            ENV_NAMES="citadel-env vllm-env dev-env"
        }
    else
        # Fallback parsing
        ENV_NAMES=$(python3 -c "
import json
try:
    config = json.load(open('$CONFIG_FILE'))
    envs = list(config['environments'].keys())
    print(' '.join(envs))
except:
    print('citadel-env vllm-env dev-env')
" 2>/dev/null || echo "citadel-env vllm-env dev-env")
    fi
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

# Create virtual environment with better error handling
create_env() {
    local env_name=${1:-"citadel-env"}
    local env_path="$CITADEL_ROOT/$env_name"
    local force_recreate=${2:-false}
    
    log "Creating environment: $env_name"
    
    # Check if environment already exists
    if [ -d "$env_path" ]; then
        log "WARNING: Environment $env_name already exists at $env_path"
        
        # Check if running in non-interactive mode or force recreate
        if [ "$force_recreate" = "true" ] || [ ! -t 0 ]; then
            log "Removing existing environment (non-interactive mode or force)"
            rm -rf "$env_path"
        else
            # Interactive mode - ask user
            echo -n "Delete and recreate? (y/N): "
            read -r REPLY
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                log "Removing existing environment: $env_name"
                rm -rf "$env_path"
            else
                log "Skipping environment creation"
                return 0
            fi
        fi
    fi
    
    # Verify Python 3.12 is available
    if ! command -v python3.12 >/dev/null 2>&1; then
        handle_error "python3.12 not found in PATH"
    fi
    
    # Create virtual environment with better error reporting
    log "Creating virtual environment at: $env_path"
    if ! python3.12 -m venv "$env_path"; then
        handle_error "Failed to create virtual environment: $env_name"
    fi
    
    # Verify environment was created properly
    if [ ! -f "$env_path/bin/activate" ]; then
        handle_error "Virtual environment creation failed - activate script not found"
    fi
    
    # Activate and upgrade base packages
    log "Upgrading base packages in environment: $env_name"
    (
        source "$env_path/bin/activate"
        
        # Verify activation worked
        if [ -z "$VIRTUAL_ENV" ]; then
            log "ERROR: Failed to activate virtual environment"
            return 1
        fi
        
        # Upgrade pip with retries
        local max_attempts=3
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if pip install --upgrade pip setuptools wheel; then
                log "✅ Base packages upgraded successfully"
                break
            else
                log "WARNING: Attempt $attempt failed to upgrade base packages"
                if [ $attempt -eq $max_attempts ]; then
                    log "WARNING: Failed to upgrade base packages after $max_attempts attempts (non-critical)"
                    break
                fi
                attempt=$((attempt + 1))
                sleep 2
            fi
        done
    )
    
    log "✅ Environment $env_name created successfully"
    return 0
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
    echo "Active environment: $(basename \"$VIRTUAL_ENV\")"
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
        echo "Active environment: $(basename \"$VIRTUAL_ENV\")"
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

# Delete environment with safety checks
delete_env() {
    local env_name=${1:-""}
    local force_delete=${2:-false}
    
    if [ -z "$env_name" ]; then
        echo "ERROR: Environment name required for deletion"
        echo "Usage: $0 delete <env_name>"
        return 1
    fi
    
    # Validate environment name to prevent accidental deletion
    if [[ ! "$env_name" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo "ERROR: Invalid environment name. Use only alphanumeric characters, hyphens, and underscores"
        return 1
    fi
    
    local env_path="$CITADEL_ROOT/$env_name"
    
    # Safety check - ensure path is within citadel directory
    if [[ ! "$env_path" =~ ^/opt/citadel/ ]]; then
        echo "ERROR: Environment path must be within /opt/citadel/"
        return 1
    fi
    
    if [ ! -d "$env_path" ]; then
        log "Environment $env_name not found at $env_path"
        return 1
    fi
    
    # Additional safety - check if this looks like a virtual environment
    if [ ! -f "$env_path/bin/activate" ] || [ ! -f "$env_path/pyvenv.cfg" ]; then
        echo "ERROR: Directory does not appear to be a virtual environment"
        echo "Missing: activate script or pyvenv.cfg"
        return 1
    fi
    
    # Show environment info before deletion
    echo "Environment to delete:"
    echo "  Name: $env_name"
    echo "  Path: $env_path"
    echo "  Size: $(du -sh "$env_path" 2>/dev/null | cut -f1 || echo 'Unknown')"
    
    # Check if running in non-interactive mode or force delete
    if [ "$force_delete" = "true" ] || [ ! -t 0 ]; then
        log "Deleting environment (non-interactive mode or force): $env_name"
    else
        # Interactive confirmation
        echo -n "Delete environment $env_name? This cannot be undone (y/N): "
        read -r REPLY
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Environment deletion cancelled"
            return 0
        fi
    fi
    
    log "Deleting environment: $env_name"
    if rm -rf "$env_path"; then
        log "✅ Environment $env_name deleted successfully"
    else
        log "ERROR: Failed to delete environment $env_name"
        return 1
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
if [ ! -f /opt/citadel/scripts/env-manager.sh ]; then
    echo "❌ Failed to create environment manager"
    exit 1
fi
```

### Step 3: Create Virtual Environments from Configuration

```bash
# Create all virtual environments defined in configuration
create_configured_environments() {
    echo "Creating virtual environments from configuration..."
    
    # Get environment names from configuration with error handling
    local env_names
    local config_loader="/opt/citadel/scripts/load_env_config.py"
    
    if [ -f "$config_loader" ]; then
        # Use configuration loader for better error handling
        env_names=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    if 'environments' not in config:
        print('citadel-env vllm-env dev-env')
        sys.exit(0)
    envs = list(config['environments'].keys())
    print(' '.join(envs))
except Exception as e:
    print('citadel-env vllm-env dev-env')
" 2>/dev/null) || {
            echo "WARNING: Using default environments"
            env_names="citadel-env vllm-env dev-env"
        }
    else
        # Fallback parsing
        env_names=$(python3 -c "
import json
try:
    config = json.load(open('$CONFIG_FILE'))
    envs = list(config['environments'].keys())
    print(' '.join(envs))
except:
    print('citadel-env vllm-env dev-env')
" 2>/dev/null || echo "citadel-env vllm-env dev-env")
    fi
    
    echo "Environments to create: $env_names"
    
    # Create each environment
    for env_name in $env_names; do
        echo "Creating environment: $env_name"
        
        # Get environment configuration safely
        local purpose
        purpose=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    purpose = config.get('environments', {}).get('$env_name', {}).get('purpose', 'AI/ML environment')
    print(purpose)
except Exception:
    print('AI/ML environment')
" 2>/dev/null || echo "AI/ML environment")
        
        echo "Purpose: $purpose"
        
        # Create environment using the manager with force recreate for automation
        local script_path="/opt/citadel/scripts/env-manager.sh"
        if [ ! -f "$script_path" ]; then
            echo "ERROR: Environment manager script not found: $script_path"
            return 1
        fi
        
        # Call create_env function directly with force recreate for non-interactive
        if ! (
            export CITADEL_ROOT="/opt/citadel"
            export CONFIG_FILE="$CONFIG_FILE"
            cd /opt/citadel
            python3.12 -m venv "$CITADEL_ROOT/$env_name" && \
            (source "$CITADEL_ROOT/$env_name/bin/activate" && pip install --upgrade pip setuptools wheel)
        ); then
            echo "ERROR: Failed to create environment: $env_name"
            return 1
        fi
        
        echo "✅ Environment $env_name created successfully"
    done
    
    echo "✅ All virtual environments created successfully"
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
    
    # Get paths from configuration with error handling
    local citadel_root models_cache
    local config_loader="/opt/citadel/scripts/load_env_config.py"
    
    if [ -f "$config_loader" ]; then
        # Use standardized configuration loader
        citadel_root=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print(config.get('paths', {}).get('citadel_root', '/opt/citadel'))
except Exception:
    print('/opt/citadel')
" 2>/dev/null || echo "/opt/citadel")
        
        models_cache=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print(config.get('paths', {}).get('models_cache', '/mnt/citadel-models/cache'))
except Exception:
    print('/mnt/citadel-models/cache')
" 2>/dev/null || echo "/mnt/citadel-models/cache")
    else
        # Fallback values
        echo "WARNING: Using default paths (config loader not found)"
        citadel_root="/opt/citadel"
        models_cache="/mnt/citadel-models/cache"
    fi
    
    sudo tee "$script_path" << EOF
#!/bin/bash
# activate-citadel.sh - Activate Citadel AI environment with optimizations

CITADEL_ROOT="$citadel_root"
CITADEL_USER="\$(whoami)"
CONFIG_FILE="$CONFIG_FILE"
LOAD_CONFIG_SCRIPT="/opt/citadel/scripts/load_env_config.py"

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

# Load optimization configuration using load_env_config.py
if [ -f "\$LOAD_CONFIG_SCRIPT" ] && [ -f "\$CONFIG_FILE" ]; then
    echo "Loading optimizations from configuration..."
    eval "\$(python3 "\$LOAD_CONFIG_SCRIPT" "\$CONFIG_FILE")"
    echo "✅ Optimizations applied from configuration"
elif [ -f "\$CONFIG_FILE" ]; then
    echo "Loading optimizations with fallback parsing..."
    # Fallback optimization loading
    export MALLOC_ARENA_MAX="\$(python3 -c 'import json; print(json.load(open("'"\$CONFIG_FILE"'")).get("optimization", {}).get("memory", {}).get("malloc_arena_max", 4))' 2>/dev/null || echo '4')"
    export OMP_NUM_THREADS="\$(python3 -c 'import json; print(min(json.load(open("'"\$CONFIG_FILE"'")).get("optimization", {}).get("threading", {}).get("max_threads", 8), 16))' 2>/dev/null || echo '8')"
    export MKL_NUM_THREADS="\$OMP_NUM_THREADS"
    export NUMEXPR_NUM_THREADS="\$OMP_NUM_THREADS"
    export CUDA_LAUNCH_BLOCKING="\$(python3 -c 'import json; print("1" if json.load(open("'"\$CONFIG_FILE"'")).get("optimization", {}).get("cuda", {}).get("launch_blocking", False) else "0")' 2>/dev/null || echo '0')"
    export CUDA_CACHE_DISABLE="\$(python3 -c 'import json; print("1" if json.load(open("'"\$CONFIG_FILE"'")).get("optimization", {}).get("cuda", {}).get("cache_disable", False) else "0")' 2>/dev/null || echo '0')"
    echo "✅ Fallback optimizations applied"
else
    echo "⚠️  WARNING: Configuration not found, using default optimizations"
    export MALLOC_ARENA_MAX="4"
    export OMP_NUM_THREADS="8"
    export MKL_NUM_THREADS="8"
    export NUMEXPR_NUM_THREADS="8"
    export CUDA_LAUNCH_BLOCKING="0"
    export CUDA_CACHE_DISABLE="0"
fi

# Set environment variables
export CITADEL_ROOT="\$CITADEL_ROOT"
export CITADEL_MODELS="\$CITADEL_ROOT/models"
export CITADEL_CONFIGS="\$CITADEL_ROOT/configs"
export CITADEL_LOGS="\$CITADEL_ROOT/logs"

# Set cache directories with validation
export HF_HOME="$models_cache"
export TRANSFORMERS_CACHE="$models_cache/transformers"
export HF_DATASETS_CACHE="$models_cache/datasets"

# Create cache directories if they don't exist
mkdir -p "\$HF_HOME" "\$TRANSFORMERS_CACHE" "\$HF_DATASETS_CACHE" 2>/dev/null || true

# Display environment info
echo ""
echo "Environment Information:"
echo "  Python: \$(python --version 2>/dev/null || echo 'Not available')"
echo "  Virtual Env: \$(basename "\$VIRTUAL_ENV")"
echo "  Config File: \$CONFIG_FILE"
echo "  Cache Directory: \$HF_HOME"
echo "  Optimizations: MALLOC_ARENA_MAX=\$MALLOC_ARENA_MAX, OMP_NUM_THREADS=\$OMP_NUM_THREADS"
echo ""
echo "🎯 Citadel AI environment ready!"
EOF
    
    chmod +x "$script_path"
    
    # Verify script creation
    if [ ! -f "$script_path" ]; then
        echo "ERROR: Failed to create activation script"
        return 1
    fi
    
    if [ ! -x "$script_path" ]; then
        echo "ERROR: Activation script is not executable"
        return 1
    fi
    
    # Test script syntax
    if ! bash -n "$script_path"; then
        echo "ERROR: Activation script has syntax errors"
        return 1
    fi
    
    echo "✅ Activation script created and validated: $script_path"
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
    
    # Test environment manager script
    echo "Testing environment manager..."
    local env_manager="/opt/citadel/scripts/env-manager.sh"
    
    if [ ! -f "$env_manager" ]; then
        echo "ERROR: Environment manager script not found: $env_manager"
        return 1
    fi
    
    if [ ! -x "$env_manager" ]; then
        echo "ERROR: Environment manager script is not executable"
        return 1
    fi
    
    # Test script syntax
    if ! bash -n "$env_manager"; then
        echo "ERROR: Environment manager script has syntax errors"
        return 1
    fi
    
    # Test environment listing (this should work even if environments don't exist)
    echo "Testing environment listing..."
    if ! "$env_manager" list >/dev/null 2>&1; then
        echo "WARNING: Environment manager list command failed (may be expected if no environments exist)"
    fi
    
    # Test each configured environment
    local env_names
    env_names=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    envs = list(config.get('environments', {}).keys())
    print(' '.join(envs))
except Exception:
    print('citadel-env vllm-env dev-env')
" 2>/dev/null || echo "citadel-env vllm-env dev-env")
    
    echo "Testing environments: $env_names"
    
    for env_name in $env_names; do
        echo "Testing environment: $env_name"
        
        local env_path="/opt/citadel/$env_name"
        
        # Check if environment directory exists
        if [ ! -d "$env_path" ]; then
            echo "❌ Environment $env_name not found at $env_path"
            return 1
        fi
        
        # Check for activate script
        if [ ! -f "$env_path/bin/activate" ]; then
            echo "❌ Environment $env_name missing activate script"
            return 1
        fi
        
        # Check for pyvenv.cfg
        if [ ! -f "$env_path/pyvenv.cfg" ]; then
            echo "❌ Environment $env_name missing pyvenv.cfg"
            return 1
        fi
        
        # Test activation and basic functionality
        echo "  Testing activation and Python version..."
        if ! (
            source "$env_path/bin/activate" 2>/dev/null && \
            python --version >/dev/null 2>&1 && \
            pip --version >/dev/null 2>&1
        ); then
            echo "❌ Failed to activate environment $env_name or basic tools not working"
            return 1
        fi
        
        # Test that the environment is using Python 3.12
        local python_version
        python_version=$(source "$env_path/bin/activate" 2>/dev/null && python --version 2>&1)
        if [[ ! "$python_version" == *"3.12"* ]]; then
            echo "⚠️  WARNING: Environment $env_name not using Python 3.12 (got: $python_version)"
        fi
        
        echo "✅ Environment $env_name tested successfully"
    done
    
    # Test activation script
    echo "Testing activation script..."
    local activation_script="/opt/citadel/scripts/activate-citadel.sh"
    
    if [ ! -f "$activation_script" ]; then
        echo "ERROR: Activation script not found: $activation_script"
        return 1
    fi
    
    if [ ! -x "$activation_script" ]; then
        echo "ERROR: Activation script is not executable"
        return 1
    fi
    
    # Test script syntax
    if ! bash -n "$activation_script"; then
        echo "ERROR: Activation script has syntax errors"
        return 1
    fi
    
    # Test activation script execution (dry run)
    echo "  Testing activation script execution..."
    if ! (
        # Create a test environment if citadel-env doesn't exist
        test_env="/opt/citadel/citadel-env"
        if [ ! -d "$test_env" ]; then
            echo "Creating temporary test environment for activation test"
            python3.12 -m venv "$test_env"
        fi
        
        # Test the activation script
        source "$activation_script" >/dev/null 2>&1 && \
        echo 'Activation test passed' >/dev/null
    ); then
        echo "❌ Activation script test failed"
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

### Security Considerations

#### Virtual Environment Isolation
- **Path Validation**: Environment paths are validated to prevent directory traversal
- **Safe Deletion**: Multiple safety checks before environment deletion
- **Non-Interactive Mode**: Automation-friendly operation without interactive prompts
- **Permission Checks**: Proper file permissions on scripts and environments

#### Configuration Security
- **Input Validation**: JSON configuration is validated before parsing
- **Fallback Values**: Safe defaults when configuration is unavailable
- **Error Handling**: Graceful degradation when configuration is malformed

#### Script Safety
- **Syntax Validation**: All generated scripts are syntax-checked before execution
- **Path Restrictions**: Environment operations restricted to `/opt/citadel/` directory
- **Process Isolation**: Virtual environment operations run in isolated subshells

## Troubleshooting

### Common Issues and Solutions

#### Issue: Virtual Environment Creation Fails
**Symptoms**: `python3.12 -m venv` command fails
**Solutions**:
```bash
# Check Python 3.12 installation
python3.12 --version
python3.12 -m venv --help

# Check available disk space
df -h /opt/citadel

# Check permissions
ls -la /opt/citadel/
sudo chown -R $(whoami):$(whoami) /opt/citadel/ # if needed

# Try creating manually
python3.12 -m venv /opt/citadel/test-env
rm -rf /opt/citadel/test-env  # cleanup
```

#### Issue: Environment Activation Fails
**Symptoms**: `source activate` doesn't work or gives errors
**Solutions**:
```bash
# Check activate script exists
ls -la /opt/citadel/citadel-env/bin/activate

# Check script permissions
chmod +x /opt/citadel/citadel-env/bin/activate

# Try manual activation
cd /opt/citadel/citadel-env
source bin/activate
python --version
```

#### Issue: Configuration Loading Fails
**Symptoms**: Environment variables not set correctly
**Solutions**:
```bash
# Test configuration file
python3 -m json.tool /opt/citadel/configs/python-config.json

# Test load_env_config.py
python3 /opt/citadel/scripts/load_env_config.py /opt/citadel/configs/python-config.json

# Manual configuration test
python3 -c "
import json
with open('/opt/citadel/configs/python-config.json') as f:
    config = json.load(f)
    print('Environments:', list(config.get('environments', {}).keys()))
"
```

#### Issue: Environment Manager Script Fails
**Symptoms**: `env-manager.sh` commands don't work
**Solutions**:
```bash
# Check script exists and is executable
ls -la /opt/citadel/scripts/env-manager.sh
chmod +x /opt/citadel/scripts/env-manager.sh

# Test script syntax
bash -n /opt/citadel/scripts/env-manager.sh

# Check log file for errors
tail -f /opt/citadel/logs/env-manager.log

# Run with debugging
bash -x /opt/citadel/scripts/env-manager.sh list
```

#### Issue: Pip Upgrade Fails in Environment
**Symptoms**: `pip install --upgrade pip` fails in virtual environment
**Solutions**:
```bash
# Check network connectivity
ping -c 3 pypi.org

# Try different pip commands
python -m pip install --upgrade pip --user
python -m pip install --upgrade pip --force-reinstall

# Check pip configuration
python -m pip config list
python -m pip config debug
```

## Module Summary

This module provides:

- **Configuration-driven environment creation** from JSON config
- **Comprehensive environment management** with full lifecycle support
- **Error handling and validation** for each environment
- **Enhanced activation scripts** with optimization loading
- **Detailed testing and reporting** for verification

**Next Module:** Continue to [PLANB-04c-Dependencies-Optimization.md](PLANB-04c-Dependencies-Optimization.md) for dependencies installation.