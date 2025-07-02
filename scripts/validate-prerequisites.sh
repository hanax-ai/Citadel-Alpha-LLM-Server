#!/bin/bash
# validate-prerequisites.sh - Validate prerequisites for Python environment setup

set -euo pipefail

CONFIG_FILE="/opt/citadel/configs/python-config.json"
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
    exit 1
}

# Check if configuration file exists
validate_config() {
    if [ ! -f "$CONFIG_FILE" ]; then
        handle_error "Configuration file not found: $CONFIG_FILE"
    fi
    
    # Check if Python 3 is available for JSON validation
    if ! command -v python3 >/dev/null 2>&1; then
        handle_error "Python 3 is required but not installed - cannot validate configuration file"
    fi
    
    if ! python3 -m json.tool "$CONFIG_FILE" >/dev/null 2>&1; then
        handle_error "Invalid JSON in configuration file: $CONFIG_FILE"
    fi
    
    log "✅ Configuration file validated"
}

# Check previous tasks completion
validate_previous_tasks() {
    log "Validating previous task completion..."
    
    # Check PLANB-01: Ubuntu installation
    if ! command -v lsb_release >/dev/null 2>&1; then
        handle_error "PLANB-01 not completed: Ubuntu system tools not found"
    fi
    
    if ! lsb_release -rs | grep -q "24.04"; then
        handle_error "PLANB-01 not completed: Ubuntu 24.04 not detected"
    fi
    
    # Check PLANB-02: Storage configuration
    if [ ! -d "/opt/citadel" ]; then
        handle_error "PLANB-02 not completed: /opt/citadel directory not found"
    fi
    
    if [ ! -d "/mnt/citadel-models" ]; then
        handle_error "PLANB-02 not completed: Model storage not mounted"
    fi
    
    # Check PLANB-03: NVIDIA drivers
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        handle_error "PLANB-03 not completed: NVIDIA drivers not installed"
    fi
    
    if ! nvidia-smi >/dev/null 2>&1; then
        handle_error "PLANB-03 not completed: NVIDIA drivers not working"
    fi
    
    log "✅ Previous tasks validation completed"
}

# Check system resources
validate_resources() {
    log "Validating system resources..."
    
    # Check available disk space (need at least 10GB) using explicit byte output
    AVAILABLE_SPACE=$(df --output=avail -B1 /opt/citadel | tail -n1)
    REQUIRED_SPACE=$((10 * 1024 * 1024 * 1024)) # 10GB in bytes
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        AVAILABLE_GB=$((AVAILABLE_SPACE / 1024 / 1024 / 1024))
        handle_error "Insufficient disk space: need 10GB, have ${AVAILABLE_GB}GB"
    fi
    
    # Check available memory (need at least 4GB) using robust free command
    # Handle different versions of free command (with/without available column)
    local FREE_OUTPUT=$(free -m)
    local HEADER_LINE=$(echo "$FREE_OUTPUT" | head -n1)
    local MEM_LINE=$(echo "$FREE_OUTPUT" | awk '/^Mem:/')
    
    if echo "$HEADER_LINE" | grep -q "available"; then
        # New format with available column (procps >= 3.3.10)
        AVAILABLE_MEMORY=$(echo "$MEM_LINE" | awk '{print $7}')
    else
        # Old format without available column, use free column
        AVAILABLE_MEMORY=$(echo "$MEM_LINE" | awk '{print $4}')
    fi
    
    REQUIRED_MEMORY=4096
    
    if [ -z "$AVAILABLE_MEMORY" ] || ! [[ "$AVAILABLE_MEMORY" =~ ^[0-9]+$ ]]; then
        handle_error "Could not determine available memory from free command"
    fi
    
    if [ "$AVAILABLE_MEMORY" -lt "$REQUIRED_MEMORY" ]; then
        handle_error "Insufficient memory: need 4GB, have ${AVAILABLE_MEMORY}MB available"
    fi
    
    # Check network connectivity with robust validation
    validate_network_connectivity

    log "✅ System resources validated"
}

# Check for conflicting installations
validate_conflicts() {
    log "Checking for potential conflicts..."
    
    # Check if Python 3.12 is already installed
    if command -v python3.12 >/dev/null 2>&1; then
        log "WARNING: Python 3.12 already installed - will verify compatibility"
    fi
    
    # Check for existing virtual environments
    if [ -d "/opt/citadel/citadel-env" ]; then
        log "WARNING: citadel-env already exists - will backup and recreate"
    fi
    
    log "✅ Conflict validation completed"
}

# Robust network connectivity validation
validate_network_connectivity() {
    log "Validating network connectivity..."
    
    local network_ok=false
    local connectivity_methods=0
    local successful_methods=0
    
    # Method 1: Test DNS servers with retries
    local dns_servers=("8.8.8.8" "1.1.1.1" "9.9.9.9")
    for dns in "${dns_servers[@]}"; do
        connectivity_methods=$((connectivity_methods + 1))
        log "Testing connectivity to DNS server: $dns"
        if ping -c 1 -W 3 "$dns" >/dev/null 2>&1; then
            log "✅ DNS connectivity successful via $dns"
            successful_methods=$((successful_methods + 1))
            network_ok=true
            break
        else
            log "⚠️  DNS connectivity failed via $dns"
        fi
    done
    
    # Method 2: Test Python package repositories
    local pypi_mirrors=("https://pypi.org" "https://pypi.python.org" "https://files.pythonhosted.org")
    for mirror in "${pypi_mirrors[@]}"; do
        connectivity_methods=$((connectivity_methods + 1))
        log "Testing PyPI connectivity: $mirror"
        if curl -I --connect-timeout 5 --max-time 10 "$mirror" >/dev/null 2>&1; then
            log "✅ PyPI connectivity successful via $mirror"
            successful_methods=$((successful_methods + 1))
            network_ok=true
            break
        else
            log "⚠️  PyPI connectivity failed via $mirror"
        fi
    done
    
    # Method 3: Test Ubuntu package repositories
    local ubuntu_mirrors=("http://archive.ubuntu.com" "http://security.ubuntu.com" "http://ports.ubuntu.com")
    for mirror in "${ubuntu_mirrors[@]}"; do
        connectivity_methods=$((connectivity_methods + 1))
        log "Testing Ubuntu repository connectivity: $mirror"
        if curl -I --connect-timeout 5 --max-time 10 "$mirror" >/dev/null 2>&1; then
            log "✅ Ubuntu repository connectivity successful via $mirror"
            successful_methods=$((successful_methods + 1))
            network_ok=true
            break
        else
            log "⚠️  Ubuntu repository connectivity failed via $mirror"
        fi
    done
    
    # Method 4: Fallback - Test apt package manager connectivity
    if [ "$network_ok" = false ]; then
        connectivity_methods=$((connectivity_methods + 1))
        log "Testing package manager connectivity via apt-get update..."
        
        # Create a temporary apt list backup and test update
        local temp_dir=$(mktemp -d)
        local apt_test_exit_code=0
        
        # Test apt connectivity (suppress output but capture exit code)
        if timeout 30 apt-get update -o Dir::State::Lists="$temp_dir" >/dev/null 2>&1; then
            apt_test_exit_code=0
            log "✅ Package manager connectivity successful"
            successful_methods=$((successful_methods + 1))
            network_ok=true
        else
            apt_test_exit_code=$?
            log "⚠️  Package manager connectivity failed (exit code: $apt_test_exit_code)"
        fi
        
        # Clean up temporary directory
        rm -rf "$temp_dir" 2>/dev/null || true
    fi
    
    # Final validation
    if [ "$network_ok" = false ]; then
        log "Network connectivity summary: $successful_methods/$connectivity_methods methods successful"
        handle_error "No network connectivity detected - required for package downloads. Tried DNS servers, PyPI mirrors, Ubuntu repositories, and package manager update."
    else
        log "✅ Network connectivity validated ($successful_methods/$connectivity_methods methods successful)"
    fi
}

# Main validation function
main() {
    log "Starting prerequisites validation for PLANB-04"
    
    validate_config
    validate_previous_tasks
    validate_resources
    validate_conflicts
    
    log "✅ All prerequisites validated successfully"
    echo "Prerequisites validation completed - system ready for Python environment setup"
}

main "$@"