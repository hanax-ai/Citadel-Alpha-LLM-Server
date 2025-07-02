I've reviewed your planb-04b-virtual-environments.sh script and identified several critical issues related to activation logic, robustness, and efficiency. The primary problem is how the script attempts to source activation files within subshells $(...), which is unreliable and can lead to incorrect output or failures.

Below are the specific errors and the necessary corrections.

1. Misleading Environment Activation
The Problem: The activate_env function in env-manager.sh attempts to source the activation script. However, a script (a child process) cannot modify the environment of the parent shell that called it. This means running env-manager.sh activate my-env will not actually activate the environment in your terminal.

The Fix: The function should instead print the command that the user needs to run.

In create_env_manager() -> activate_env():

Bash

# --- BEFORE ---
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

# --- AFTER ---
activate_env() {
    local env_name=${1:-"citadel-env"}
    local env_path="$CITADEL_ROOT/$env_name"
    if [ ! -f "$env_path/bin/activate" ]; then
        handle_error "Environment '$env_name' not found or is incomplete."
    fi
    log "Activation instructions for: $env_name"
    echo "✅ To activate the environment, run the following command in your terminal:"
    echo ""
    echo "   source $env_path/bin/activate"
    echo ""
}
2. Unreliable Environment Testing and Reporting
The Problem: In the test_environments and generate_status_report functions, you use source "$env_path/bin/activate" && python --version inside a command substitution $(...). The activate script can sometimes print other text, which would corrupt your output and logs. A much more robust method is to call the Python and Pip executables directly from the virtual environment's bin directory.

The Fix: Replace source ... && python with a direct call to $env_path/bin/python.

In generate_status_report():

Bash

# --- BEFORE ---
echo "  Python: $(source "$env_path/bin/activate" && python --version 2>&1)" >> "$status_file"
echo "  Packages: $(source "$env_path/bin/activate" && pip list --format=freeze | wc -l)" >> "$status_file"

# --- AFTER ---
echo "  Python: $("$env_path/bin/python" --version 2>&1)" >> "$status_file"
echo "  Packages: $("$env_path/bin/pip" list | wc -l)" >> "$status_file"
In test_environments():

Bash

# --- BEFORE ---
if ! (source "$env_path/bin/activate" && python --version); then
    handle_error "Failed to activate environment $env_name"
fi

# --- AFTER ---
if ! "$env_path/bin/python" --version >/dev/null 2>&1; then
    handle_error "Failed to execute Python in environment '$env_name'"
fi
3. Inefficient Configuration Parsing
The Problem: The show_usage function inside env-manager.sh parses the JSON configuration file inside a for loop, reading the file once for every single environment to get its purpose. This is inefficient.

The Fix: Parse the entire environments block once with Python and format the output for shell processing.

In create_env_manager() -> show_usage():

Bash

# --- BEFORE ---
load_env_config
for env in $ENV_NAMES; do
    local purpose=$(python3 -c "
import json
config = json.load(open('$CONFIG_FILE'))
print(config['environments']['$env']['purpose'])
" 2>/dev/null || echo "Unknown purpose")
    echo "  $env - $purpose"
done

# --- AFTER ---
load_env_config
python3 -c "
import json
try:
    with open('$CONFIG_FILE') as f:
        config = json.load(f)
    for name, details in config.get('environments', {}).items():
        print(f\"   {name} - {details.get('purpose', 'No purpose defined')}\")
except (IOError, json.JSONDecodeError) as e:
    print(f'   Could not read purposes: {e}', file=sys.stderr)
"


-------------------------------------------------------------------------------------------------------------------------------------
Fully Revised Script
Here is the complete, corrected script with all fixes applied. I also improved quoting and error messages for better stability. Taking into account our previous discussion, the changes to prevent source in subshells will also fix potential logging issues by ensuring that only the intended command output is captured.

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
    # Added tee redirection to stderr to ensure logs are captured even if stdout is piped
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" >&2
}

# Error handling
handle_error() {
    log "❌ ERROR: $1"
    # Ensure error handler is executable before calling
    if [ -x "$ERROR_HANDLER" ]; then
        $ERROR_HANDLER rollback
    else
        log "Error handler not found or not executable at $ERROR_HANDLER"
    fi
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

    # Use single quotes around 'EOF' to prevent expansion in the outer script
    tee "$script_path" <<'EOF'
#!/bin/bash
# env-manager.sh - Manage Python virtual environments with error handling

set -euo pipefail

CONFIG_FILE="/opt/citadel/configs/python-config.json"
CITADEL_ROOT="/opt/citadel"
LOG_FILE="/opt/citadel/logs/env-manager.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" >&2
}

# Error handling
handle_error() {
    log "❌ ERROR: $1"
    exit 1
}

# Load environment configuration from JSON
load_env_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    # Extract environment names from config
    ENV_NAMES=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE') as f:
        config = json.load(f)
    envs = list(config.get('environments', {}).keys())
    print(' '.join(envs))
except (IOError, json.JSONDecodeError) as e:
    print(f'Failed to parse config: {e}', file=sys.stderr)
    sys.exit(1)
")
    if [ -z "$ENV_NAMES" ]; then
      log "No environments found in $CONFIG_FILE"
    fi
}

# Show usage
show_usage() {
    echo "Usage: $0 [activate|deactivate|create|list|info|delete] [env_name]"
    echo ""
    echo "Commands:"
    echo "  activate [env]   - Show command to activate a virtual environment"
    echo "  deactivate       - Display instructions for deactivating"
    echo "  create [env]     - Create a new virtual environment"
    echo "  list             - List all configured environments and their status"
    echo "  info             - Show current active environment info"
    echo "  delete [env]     - Delete a virtual environment"
    echo ""
    echo "Available environments (from config):"
    load_env_config
    # Efficiently parse purposes once
    python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE') as f:
        config = json.load(f)
    for name, details in config.get('environments', {}).items():
        print(f\"  {name} - {details.get('purpose', 'No purpose defined')}\")
except (IOError, json.JSONDecodeError) as e:
    print(f'   Could not read purposes: {e}', file=sys.stderr)
"
}

# Create virtual environment
create_env() {
    local env_name=${1:-"citadel-env"}
    local env_path="$CITADEL_ROOT/$env_name"
    log "Creating environment: $env_name at $env_path"
    if [ -d "$env_path" ]; then
        log "WARNING: Environment '$env_name' already exists."
        read -p "Delete and recreate? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "Removing existing environment: $env_name"
            rm -rf "$env_path"
        else
            log "Skipping environment creation."
            return 0
        fi
    fi
    # Create virtual environment
    if ! python3.12 -m venv "$env_path"; then
        handle_error "Failed to create virtual environment: $env_name"
    fi
    # Upgrade base packages using the venv's python
    log "Upgrading base packages (pip, setuptools, wheel)..."
    if ! "$env_path/bin/python" -m pip install --upgrade pip setuptools wheel; then
        # This is a non-critical warning
        log "WARNING: Failed to upgrade base packages."
    fi
    log "✅ Environment '$env_name' created successfully."
}

# Show activation instructions
activate_env() {
    local env_name=${1:-"citadel-env"}
    local env_path="$CITADEL_ROOT/$env_name"
    if [ ! -f "$env_path/bin/activate" ]; then
        handle_error "Environment '$env_name' not found at $env_path. Try creating it first."
    fi
    log "Activation instructions for: $env_name"
    echo "✅ To activate the environment, run the following command in your terminal:"
    echo ""
    echo "   source $env_path/bin/activate"
    echo ""
}

# List environments
list_envs() {
    echo "Available environments:"
    load_env_config
    for env in $ENV_NAMES; do
        local env_path="$CITADEL_ROOT/$env"
        if [ -f "$env_path/bin/python" ]; then
            local python_version=$("$env_path/bin/python" --version 2>/dev/null || echo "Unknown")
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
        echo "  Environment path: $VIRTUAL_ENV"
        echo "  Python version: $(python --version)"
        echo "  Python path: $(which python)"
        echo "  Pip version: $(pip --version)"
        echo "  Installed packages: $(pip list | wc -l)"
    else
        echo "No virtual environment active."
        echo "System Python: $(python3 --version 2>/dev/null || echo 'Not found')"
    fi
}

# Delete environment
delete_env() {
    local env_name=${1:-""}
    if [ -z "$env_name" ]; then
        handle_error "Environment name is required for deletion."
        show_usage
        return 1
    fi
    local env_path="$CITADEL_ROOT/$env_name"
    if [ ! -d "$env_path" ]; then
        handle_error "Environment '$env_name' not found at $env_path"
    fi
    read -p "Delete environment '$env_name'? This cannot be undone (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "Deleting environment: $env_name"
        rm -rf "$env_path"
        log "✅ Environment '$env_name' deleted."
    else
        log "Environment deletion cancelled."
    fi
}

# Main command processing
case "${1:-}" in
    activate)
        activate_env "${2:-}"
        ;;
    deactivate)
        echo "To deactivate, type 'deactivate' in your shell."
        echo "This command is only available if an environment is active."
        ;;
    create)
        create_env "${2:-}"
        ;;
    list)
        list_envs
        ;;
    info)
        show_info
        ;;
    delete)
        delete_env "${2:-}"
        ;;
    *)
        show_usage
        exit 1
        ;;
esac
EOF

    chmod +x "$script_path"
    log "✅ Environment manager script created: $script_path"

    if [ ! -f "$script_path" ]; then
        handle_error "Failed to create environment manager"
    fi
}

# Step 3: Create Virtual Environments from Configuration
create_configured_environments() {
    log "Creating virtual environments from configuration..."

    local env_names
    env_names=$(python3 -c "
import json, sys
try:
    with open('$CONFIG_FILE') as f:
        config = json.load(f)
    print(' '.join(config.get('environments', {}).keys()))
except Exception as e:
    print(f'Error reading config: {e}', file=sys.stderr)
    sys.exit(1)
")
    
    if [ -z "$env_names" ]; then
      log "No environments defined in config file. Skipping creation."
      return
    fi

    for env_name in $env_names; do
        log "--- Starting creation for '$env_name' ---"
        # Create environment using the manager. Pipe output to /dev/null to avoid clutter.
        if ! /opt/citadel/scripts/env-manager.sh create "$env_name" >/dev/null; then
            handle_error "Failed to create environment: $env_name"
        fi
        log "✅ Environment '$env_name' created successfully via manager."
    done
}

# Step 4: Create Enhanced Activation Script
create_activation_script() {
    local script_path="/opt/citadel/scripts/activate-citadel.sh"

    log "Creating enhanced activation script..."

    # Use sudo tee with a single-quoted EOF to prevent local expansion and write the script correctly
    sudo tee "$script_path" <<'EOF'
#!/bin/bash
# activate-citadel.sh - Activate Citadel AI environment with optimizations

set -e

CITADEL_ROOT="/opt/citadel"
CITADEL_USER="$(whoami)"
CONFIG_FILE="/opt/citadel/configs/python-config.json"

echo "🚀 Activating Citadel AI Environment for user: $CITADEL_USER"
echo "🌐 Hana-X Lab Environment (db server - 192.168.10.35)"
echo "========================================================="

# Validate environment exists
if [ ! -f "$CITADEL_ROOT/citadel-env/bin/activate" ]; then
    echo "❌ Virtual environment 'citadel-env' not found!"
    echo "Run: /opt/citadel/scripts/env-manager.sh create citadel-env"
    return 1 # Use return instead of exit for sourced scripts
fi

# Activate virtual environment
source "$CITADEL_ROOT/citadel-env/bin/activate"
echo "✅ Virtual environment activated."

# Function to safely get config values
get_config() {
    python3 -c "
import json, sys
key_path = '$1'.split('.')
try:
    with open('$CONFIG_FILE') as f:
        data = json.load(f)
    for key in key_path:
        data = data[key]
    print(data)
except Exception:
    print('$2', file=sys.stderr) # Print default value on error
"
}

# Load optimization configuration
if [ -f "$CONFIG_FILE" ]; then
    # Apply memory optimizations
    export MALLOC_ARENA_MAX=$(get_config "optimization.memory.malloc_arena_max" "4")
    
    # Apply threading optimizations
    max_threads=$(get_config "optimization.threading.max_threads" "8")
    export OMP_NUM_THREADS=$max_threads
    export MKL_NUM_THREADS=$max_threads
    export NUMEXPR_NUM_THREADS=$max_threads
    
    # Apply CUDA optimizations
    export CUDA_LAUNCH_BLOCKING=$(get_config "optimization.cuda.launch_blocking" "0")
    export TF_FORCE_GPU_ALLOW_GROWTH=$(get_config "optimization.cuda.tf_force_gpu_allow_growth" "true")

    echo "✅ Optimizations applied from configuration."
fi

# Set environment variables
export CITADEL_ROOT="$CITADEL_ROOT"
export CITADEL_MODELS="$CITADEL_ROOT/models"
export CITADEL_CONFIGS="$CITADEL_ROOT/configs"
export CITADEL_LOGS="$CITADEL_ROOT/logs"

# Set cache directories from config
models_cache=$(get_config "paths.models_cache" "$HOME/.cache/huggingface")
export HF_HOME="$models_cache"
export TRANSFORMERS_CACHE="$models_cache/transformers"
export HF_DATASETS_CACHE="$models_cache/datasets"

# Display environment info
echo ""
echo "Environment Information:"
echo "  Python: $(python --version 2>/dev/null || echo 'Not available')"
echo "  Virtual Env: $(basename "$VIRTUAL_ENV")"
echo "  Models Cache: $HF_HOME"
echo ""
echo "🎯 Citadel AI environment ready!"
EOF

    chmod +x "$script_path"
    log "✅ Activation script created: $script_path"
}

# Step 5: Comprehensive Environment Testing
test_environments() {
    log "=== Starting Virtual Environment Testing ==="

    # Test environment manager
    log "Testing: env-manager.sh list"
    if ! /opt/citadel/scripts/env-manager.sh list; then
        handle_error "'env-manager.sh list' test failed"
    fi

    local env_names
    env_names=$(python3 -c "import json, sys; print(' '.join(json.load(open('$CONFIG_FILE')).get('environments', {}).keys()))")

    for env_name in $env_names; do
        log "Testing environment: $env_name"
        local env_path="/opt/citadel/$env_name"
        if [ ! -d "$env_path" ]; then
            handle_error "Environment directory for '$env_name' not found after creation."
        fi

        # Test python execution directly
        if ! "$env_path/bin/python" --version >/dev/null 2>&1; then
            handle_error "Failed to execute Python in environment '$env_name'"
        fi

        # Test pip execution
        if ! "$env_path/bin/pip" --version >/dev/null 2>&1; then
            handle_error "Failed to execute pip in environment '$env_name'"
        fi
        log "✅ Environment '$env_name' tested successfully."
    done

    # Test activation script in a subshell to ensure it runs without errors
    log "Testing: activate-citadel.sh"
    if ! (source /opt/citadel/scripts/activate-citadel.sh && echo 'Activation script sourced without errors.'); then
        handle_error "Activation script 'activate-citadel.sh' failed to source."
    fi

    log "✅ All virtual environment tests passed."
}

# Step 6: Generate Status Report
generate_status_report() {
    local status_file="/opt/citadel/logs/virtual-environments-status.txt"
    log "Generating status report..."

    # Use a function to avoid repeating the python call
    get_env_names() {
        python3 -c "import json, sys; print(' '.join(json.load(open('$CONFIG_FILE')).get('environments', {}).keys()))"
    }

    # Start report
    {
        echo "Virtual Environments Setup Status Report"
        echo "Generated: $(date)"
        echo ""
        echo "Configuration File: $CONFIG_FILE"
        echo "Environment Manager: /opt/citadel/scripts/env-manager.sh"
        echo "Activation Script: /opt/citadel/scripts/activate-citadel.sh"
        echo ""
        echo "Created Environments:"
        /opt/citadel/scripts/env-manager.sh list
        echo ""
        echo "Environment Details:"
    } > "$status_file"

    # Add details for each environment
    for env_name in $(get_env_names); do
        local env_path="/opt/citadel/$env_name"
        if [ -f "$env_path/bin/python" ]; then
            {
                echo ""
                echo "$env_name:"
                echo "  Path: $env_path"
                # Use direct calls for robustness
                echo "  Python: $("$env_path/bin/python" --version 2>&1)"
                # Get a more accurate package count, excluding the header
                echo "  Packages Installed: $("$env_path/bin/pip" list | tail -n +3 | wc -l)"
            } >> "$status_file"
        fi
    done
    
    echo "" >> "$status_file"
    echo "Setup Status: SUCCESS" >> "$status_file"

    log "✅ Status report created: $status_file"
}

# Main execution function
main() {
    log "--- Starting PLANB-04b Virtual Environments Setup Module ---"

    validate_prerequisites
    create_env_manager
    create_configured_environments
    create_activation_script
    test_environments
    generate_status_report

    log ""
    log "🎉 Virtual Environments module completed successfully!"
    log "✅ All environments created and tested."
    log "➡️ To list environments, run: /opt/citadel/scripts/env-manager.sh list"
    log "➡️ To activate the main env, run: source /opt/citadel/scripts/activate-citadel.sh"
    log ""
}

# Execute main function, passing all arguments to it
main "$@"