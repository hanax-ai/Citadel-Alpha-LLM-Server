#!/bin/bash
# planb-04b-virtual-environments.sh - Virtual Environments Setup Module

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

# Step 1: Load Configuration and Validate Prerequisites
validate_prerequisites() {
    log "Validating prerequisites for virtual environment setup..."
    
    # Check Python 3.12 installation
    if ! python3.12 --version >/dev/null 2>&1; then
        handle_error "Python 3.12 not found - run PLANB-04a first"
    fi
    
    # Check pip installation
    if ! python3.12 -m pip --version >/dev/null 2>&1; then
        handle_error "Pip for Python 3.12 not found"
    fi
    
    # Check citadel directory
    if [ ! -d "/opt/citadel" ]; then
        handle_error "/opt/citadel directory not found"
    fi
    
    # Check configuration file
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    
    log "✅ Prerequisites validated"
}

# Step 2: Create Environment Management Script
create_env_manager() {
    local script_path="/opt/citadel/scripts/env-manager.sh"
    
    log "Creating environment management script..."
    
    tee "$script_path" <<EOF
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
    log "✅ Environment manager script created: $script_path"
    
    if [ ! -f /opt/citadel/scripts/env-manager.sh ]; then
        handle_error "Failed to create environment manager"
    fi
}

# Step 3: Create Virtual Environments from Configuration
create_configured_environments() {
    log "Creating virtual environments from configuration..."
    
    # Get environment names from configuration
    local env_names=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
envs = list(config['environments'].keys())
print(' '.join(envs))
")
    
    for env_name in $env_names; do
        log "Creating environment: $env_name"
        
        # Get environment configuration
        local purpose=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
print(config['environments']['$env_name']['purpose'])
")
        
        log "Purpose: $purpose"
        
        # Create environment using the manager
        if ! /opt/citadel/scripts/env-manager.sh create "$env_name"; then
            handle_error "Failed to create environment: $env_name"
        fi
        
        log "✅ Environment $env_name created successfully"
    done
}

# Step 4: Create Enhanced Activation Script
create_activation_script() {
    local script_path="/opt/citadel/scripts/activate-citadel.sh"
    
    log "Creating enhanced activation script..."
    
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
    log "✅ Activation script created: $script_path"
}

# Step 5: Comprehensive Environment Testing
test_environments() {
    log "=== Virtual Environment Testing ==="
    
    # Test environment manager
    log "Testing environment manager..."
    if ! /opt/citadel/scripts/env-manager.sh list; then
        handle_error "Environment manager test failed"
    fi
    
    # Test each environment
    local env_names=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
envs = list(config['environments'].keys())
print(' '.join(envs))
")
    
    for env_name in $env_names; do
        log "Testing environment: $env_name"
        
        local env_path="/opt/citadel/$env_name"
        if [ ! -d "$env_path" ]; then
            handle_error "Environment $env_name not found"
        fi
        
        # Test activation
        if ! (source "$env_path/bin/activate" && python --version); then
            handle_error "Failed to activate environment $env_name"
        fi
        
        log "✅ Environment $env_name tested successfully"
    done
    
    # Test activation script
    log "Testing activation script..."
    if ! ( source /opt/citadel/scripts/activate-citadel.sh && echo 'Activation test passed' ); then
        handle_error "Activation script test failed"
    fi
    
    log "✅ All virtual environment tests passed"
}

# Step 6: Generate Status Report
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
    
    log "✅ Status report created: $status_file"
}

# Main execution function
main() {
    log "Starting PLANB-04b Virtual Environments Setup Module"
    
    # Execute steps with error handling
    if ! $ERROR_HANDLER execute "Prerequisites Validation" "validate_prerequisites" "python3.12 --version >/dev/null 2>&1"; then
        handle_error "Prerequisites validation failed"
    fi
    
    if ! $ERROR_HANDLER execute "Environment Manager Creation" "create_env_manager" "[ -f /opt/citadel/scripts/env-manager.sh ]"; then
        handle_error "Environment manager creation failed"
    fi
    
    if ! $ERROR_HANDLER execute "Virtual Environments Creation" "create_configured_environments" "/opt/citadel/scripts/env-manager.sh list | grep -q '✅'"; then
        handle_error "Virtual environments creation failed"
    fi
    
    if ! $ERROR_HANDLER execute "Activation Script Creation" "create_activation_script" "[ -f /opt/citadel/scripts/activate-citadel.sh ]"; then
        handle_error "Activation script creation failed"
    fi
    
    # Run testing and reporting
    test_environments
    generate_status_report
    
    log ""
    log "🎉 Virtual Environments module completed successfully!"
    log "✅ All environments created and tested"
    log "📋 Use: /opt/citadel/scripts/env-manager.sh list"
    log ""
}

# Execute main function
main "$@"