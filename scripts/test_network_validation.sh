#!/bin/bash
# Test script for network validation

# Source the main script functions
cd /home/agent0/Citadel-Alpha-LLM-Server-1/scripts

# Define required functions for testing
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

handle_error() {
    echo "ERROR: $1"
    exit 1
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

# Run the test
echo "Starting network validation test..."
validate_network_connectivity
echo "Network validation test completed successfully!"
