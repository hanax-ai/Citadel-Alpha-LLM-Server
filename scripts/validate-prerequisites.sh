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
    
    # Check available disk space (need at least 10GB)
    AVAILABLE_SPACE=$(df /opt/citadel | awk 'NR==2 {print $4}')
    REQUIRED_SPACE=$((10 * 1024 * 1024)) # 10GB in KB
    
    if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
        handle_error "Insufficient disk space: need 10GB, have $(($AVAILABLE_SPACE / 1024 / 1024))GB"
    fi
    
    # Check available memory (need at least 4GB)
    AVAILABLE_MEMORY=$(free -m | awk 'NR==2{print $7}')
    REQUIRED_MEMORY=4096
    
    if [ "$AVAILABLE_MEMORY" -lt "$REQUIRED_MEMORY" ]; then
        handle_error "Insufficient memory: need 4GB, have ${AVAILABLE_MEMORY}MB available"
    fi
    
    # Check internet connectivity (basic IP reachability)
    if ! ping -c 1 8.8.8.8 >/dev/null 2>&1; then
        handle_error "No internet connectivity - required for package downloads (ping to 8.8.8.8 failed)"
    fi

    # Check DNS resolution (pypi.org)
    if ! curl -I --connect-timeout 5 https://pypi.org >/dev/null 2>&1; then
        handle_error "DNS resolution or HTTPS connectivity failed for pypi.org - required for Python package installation"
    fi

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