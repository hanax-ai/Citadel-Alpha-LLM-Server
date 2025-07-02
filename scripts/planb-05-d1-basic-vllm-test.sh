#!/bin/bash
"""
PLANB-05-D1: Basic vLLM Test Execution Script
Shell wrapper for basic vLLM functionality validation
"""

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/vllm-basic-test-$(date +%Y%m%d_%H%M%S).log"

# Logging functions
log_info() {
    echo "[INFO] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo "[ERROR] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE" >&2
}

log_success() {
    echo "[SUCCESS] $(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Environment validation
validate_environment() {
    log_info "Validating environment for vLLM basic test..."
    
    # Check if virtual environment exists
    local venv_path="/opt/citadel/dev-env"
    if [[ ! -d "$venv_path" ]]; then
        log_error "Virtual environment not found: $venv_path"
        log_error "Please run PLANB-04 Python Environment setup first"
        return 1
    fi
    
    # Check if .env file exists
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log_error ".env file not found in project root"
        log_error "Please create .env file with required variables (HF_TOKEN, etc.)"
        return 1
    fi
    
    log_success "Environment validation passed"
    return 0
}

# Activate virtual environment
activate_environment() {
    log_info "Activating Python virtual environment..."
    
    local venv_path="/opt/citadel/dev-env"
    local activate_script="$venv_path/bin/activate"
    
    if [[ ! -f "$activate_script" ]]; then
        log_error "Virtual environment activation script not found: $activate_script"
        return 1
    fi
    
    # Reason: Source the virtual environment to access installed packages
    source "$activate_script"
    
    # Verify Python and pip are available
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not available in virtual environment"
        return 1
    fi
    
    log_success "Virtual environment activated successfully"
    return 0
}

# Run basic vLLM test
run_basic_test() {
    log_info "Starting basic vLLM functionality test..."
    
    local test_script="$PROJECT_ROOT/tests/test_vllm_basic_validation.py"
    
    if [[ ! -f "$test_script" ]]; then
        log_error "Test script not found: $test_script"
        return 1
    fi
    
    # Set environment variables for test execution
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    
    # Run the test with timeout (5 minutes max)
    if timeout 300 python3 "$test_script"; then
        log_success "Basic vLLM test completed successfully"
        return 0
    else
        local exit_code=$?
        if [[ $exit_code -eq 124 ]]; then
            log_error "Test timed out after 5 minutes"
        else
            log_error "Test failed with exit code: $exit_code"
        fi
        return $exit_code
    fi
}

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    
    # Clean up test cache if it exists
    local test_cache="/tmp/vllm_test_cache"
    if [[ -d "$test_cache" ]]; then
        rm -rf "$test_cache"
        log_info "Cleaned up test cache: $test_cache"
    fi
}

# Main execution function
main() {
    log_info "PLANB-05-D1: Starting Basic vLLM Test"
    log_info "========================================"
    
    # Trap cleanup on exit
    trap cleanup EXIT
    
    # Validate environment
    if ! validate_environment; then
        log_error "Environment validation failed"
        exit 1
    fi
    
    # Activate virtual environment
    if ! activate_environment; then
        log_error "Failed to activate virtual environment"
        exit 1
    fi
    
    # Run basic test
    if ! run_basic_test; then
        log_error "Basic vLLM test failed"
        exit 1
    fi
    
    log_success "PLANB-05-D1: Basic vLLM Test completed successfully"
    log_info "Log file saved to: $LOG_FILE"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi