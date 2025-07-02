#!/bin/bash
# planb-03-post-install-optimization.sh
# Post-installation GPU optimization and service configuration for PLANB-03
# Run after system reboot to complete GPU setup

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CONFIG_FILE="/opt/citadel/configs/gpu-config.json"
LOG_FILE="/opt/citadel/logs/planb-03-post-install.log"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1" | tee -a "$LOG_FILE"
}

# Error handling function
handle_error() {
    local exit_code=$?
    log_error "Command failed with exit code $exit_code: $1"
    exit $exit_code
}

# Trap errors
trap 'handle_error "Line $LINENO"' ERR

# Initialize logging
setup_logging() {
    log_step "Setting up post-installation logging"
    sudo mkdir -p "$(dirname "$LOG_FILE")"
    sudo touch "$LOG_FILE"
    sudo chmod 664 "$LOG_FILE"
}

# Verify driver installation
verify_driver_installation() {
    log_step "Verifying NVIDIA driver installation"
    
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        log_error "nvidia-smi not found - driver installation may have failed"
        exit 1
    fi
    
    if ! nvidia-smi >/dev/null 2>&1; then
        log_error "nvidia-smi failed - drivers may not be loaded properly"
        exit 1
    fi
    
    # Get driver version
    local driver_version
    driver_version=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -1)
    log_info "✅ NVIDIA driver verified: $driver_version"
}

# Detect and update GPU specifications
detect_gpu_specifications() {
    log_step "Detecting GPU specifications"
    
    # Verify Python 3 is available
    if ! command -v python3 >/dev/null 2>&1; then
        log_error "Python 3 is not installed or not in PATH - required for GPU detection"
        exit 1
    fi
    
    if ! python3 "$SCRIPT_DIR/gpu_manager.py" detect; then
        log_warn "GPU detection failed - using default values"
        return 0
    fi
    
    # Update configuration with detected specs using external script
    log_info "Updating GPU configuration with detected specifications..."
    if python3 "$SCRIPT_DIR/update_gpu_config.py" \
        --project-root "$PROJECT_ROOT" \
        --config-file "$CONFIG_FILE" \
        --script-dir "$SCRIPT_DIR"; then
        log_info "✅ GPU specifications detected and updated"
    else
        local exit_code=$?
        case $exit_code in
            1)
                log_warn "No GPU specifications detected - using defaults"
                ;;
            2)
                log_error "Required Python modules not found"
                return 1
                ;;
            3)
                log_error "Configuration file not found"
                return 1
                ;;
            *)
                log_error "GPU configuration update failed with exit code $exit_code"
                return 1
                ;;
        esac
    fi
}

# Apply GPU optimizations
apply_gpu_optimizations() {
    log_step "Applying GPU performance optimizations"
    
    if ! python3 "$SCRIPT_DIR/gpu_manager.py" optimize; then
        log_warn "GPU optimization failed - performance may not be optimal"
        return 0
    fi
    
    log_info "✅ GPU performance optimizations applied"
}

# Configure GPU persistence daemon
configure_persistence_daemon() {
    log_step "Configuring NVIDIA persistence daemon"
    
    # Check if nvidia-persistenced exists
    local persistenced_path
    persistenced_path=$(which nvidia-persistenced 2>/dev/null || \
                       find /usr/bin /usr/local/bin /bin /usr/sbin /usr/local/sbin /sbin \
                       -name "nvidia-persistenced" -type f 2>/dev/null | head -1 || echo "")
    
    if [[ -z "$persistenced_path" ]]; then
        log_warn "nvidia-persistenced not found - skipping persistence configuration"
        return 0
    fi
    
    # Create systemd service
    sudo tee /etc/systemd/system/nvidia-persistenced.service << EOF
[Unit]
Description=NVIDIA Persistence Daemon
After=syslog.target network.target

[Service]
Type=forking
PIDFile=/var/run/nvidia-persistenced/nvidia-persistenced.pid
Restart=always
ExecStart=$persistenced_path --verbose
ExecStopPost=/bin/rm -rf /var/run/nvidia-persistenced

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and start the service
    sudo systemctl daemon-reload
    sudo systemctl enable nvidia-persistenced
    
    if sudo systemctl start nvidia-persistenced; then
        log_info "✅ NVIDIA persistence daemon configured and started"
    else
        log_warn "Failed to start nvidia-persistenced service"
    fi
}

# Create GPU optimization service
create_gpu_optimization_service() {
    log_step "Creating GPU optimization service"
    
    # Check dependencies
    local after_service=""
    local requires_service=""
    if sudo systemctl list-unit-files | grep -q "nvidia-persistenced.service"; then
        after_service="After=nvidia-persistenced.service"
        requires_service="Requires=nvidia-persistenced.service"
    fi
    
    # Create systemd service for GPU optimization
    sudo tee /etc/systemd/system/gpu-optimize.service << EOF
[Unit]
Description=GPU Optimization for AI Workloads
$after_service
$requires_service

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 $SCRIPT_DIR/gpu_manager.py optimize
RemainAfterExit=yes
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
    
    # Enable and test the service
    sudo systemctl daemon-reload
    sudo systemctl enable gpu-optimize.service
    
    if sudo systemctl start gpu-optimize.service; then
        log_info "✅ GPU optimization service created and started"
    else
        log_warn "GPU optimization service failed to start"
        sudo systemctl status gpu-optimize.service
    fi
}

# Configure multi-GPU settings
configure_multi_gpu() {
    log_step "Configuring multi-GPU settings"
    
    # Create NVIDIA kernel module configuration
    sudo tee /etc/modprobe.d/nvidia.conf << 'EOF'
# NVIDIA driver configuration for multi-GPU setup
options nvidia NVreg_DeviceFileUID=0 NVreg_DeviceFileGID=44 NVreg_DeviceFileMode=0660
options nvidia NVreg_ModifyDeviceFiles=1
options nvidia NVreg_EnableGpuFirmware=1

# Performance optimizations
options nvidia NVreg_UsePageAttributeTable=1
options nvidia NVreg_EnableMSI=1
options nvidia NVreg_TCEBypassMode=1
EOF
    
    # Create backup of current initramfs before updating
    log_info "Creating backup of current initramfs..."
    local kernel_version
    kernel_version=$(uname -r)
    local initramfs_path="/boot/initrd.img-${kernel_version}"
    local backup_path="/boot/initrd.img-${kernel_version}.backup-$(date +%Y%m%d-%H%M%S)"
    
    if [[ -f "$initramfs_path" ]]; then
        if sudo cp "$initramfs_path" "$backup_path"; then
            log_info "✅ Initramfs backup created: $backup_path"
        else
            log_warn "Failed to create initramfs backup - proceeding with caution"
        fi
    else
        log_warn "Current initramfs not found at $initramfs_path"
    fi
    
    # Update initramfs with error handling
    log_info "Updating initramfs with new NVIDIA configuration..."
    if sudo update-initramfs -u; then
        log_info "✅ Initramfs updated successfully"
    else
        log_error "Failed to update initramfs - this could cause boot issues"
        log_error "Backup available at: $backup_path (if created)"
        log_error "Manual recovery may be required before reboot"
        exit 1
    fi
    
    log_info "✅ Multi-GPU configuration applied"
}

# Create monitoring scripts
create_monitoring_scripts() {
    log_step "Creating GPU monitoring scripts"
    
    # Create GPU status monitoring script
    sudo tee /opt/citadel/scripts/gpu-monitor.sh << 'EOF'
#!/bin/bash
# gpu-monitor.sh - Monitor GPU status and performance

echo "=== GPU Status Report $(date) ==="
echo ""

echo "GPU Information:"
nvidia-smi -L
echo ""

echo "Driver Information:"
nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits
echo ""

echo "GPU Utilization:"
nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits
echo ""

echo "Memory Usage:"
nvidia-smi --query-gpu=memory.used,memory.free,memory.total --format=csv,noheader,nounits
echo ""

echo "GPU Clocks:"
nvidia-smi --query-gpu=clocks.gr,clocks.mem,clocks.max.gr,clocks.max.mem --format=csv,noheader,nounits
echo ""

echo "Process Information:"
nvidia-smi pmon -c 1
echo ""

echo "Detailed Status:"
nvidia-smi
EOF
    
    chmod +x /opt/citadel/scripts/gpu-monitor.sh
    
    # Create GPU topology script
    sudo tee /opt/citadel/scripts/gpu-topology.sh << 'EOF'
#!/bin/bash
# gpu-topology.sh - Display and optimize GPU topology

echo "=== GPU Topology Information ==="
nvidia-smi topo -m
echo ""

echo "=== PCIe Information ==="
lspci | grep -i nvidia
echo ""

echo "=== NUMA Topology ==="
if command -v numactl >/dev/null 2>&1; then
    numactl --hardware | grep -A 20 "available:" || echo "NUMA hardware information not available"
else
    echo "numactl not installed - NUMA topology information unavailable"
fi
EOF
    
    chmod +x /opt/citadel/scripts/gpu-topology.sh
    
    log_info "✅ GPU monitoring scripts created"
}

# Run validation tests
run_validation_tests() {
    log_step "Running post-installation validation tests"
    
    if python3 "$PROJECT_ROOT/tests/test_planb_03_validation.py"; then
        log_info "✅ All validation tests passed"
        return 0
    else
        log_warn "Some validation tests failed - check test output"
        return 1
    fi
}

# Display system status
display_system_status() {
    log_step "Displaying final system status"
    
    echo
    echo "==============================================="
    echo "PLANB-03 Post-Installation Status Summary"
    echo "==============================================="
    
    # GPU status
    if python3 "$SCRIPT_DIR/gpu_manager.py" status >/dev/null 2>&1; then
        echo "✅ GPU Status: Operational"
        nvidia-smi -L
    else
        echo "❌ GPU Status: Issues detected"
    fi
    
    # Services status
    echo
    echo "Service Status:"
    for service in nvidia-persistenced gpu-optimize; do
        if sudo systemctl is-active "$service" >/dev/null 2>&1; then
            echo "  ✅ $service: Active"
        else
            echo "  ❌ $service: Inactive"
        fi
    done
    
    echo
    echo "Next Steps:"
    echo "1. Verify GPU functionality with: python3 tests/test_planb_03_validation.py"
    echo "2. Monitor GPU status with: /opt/citadel/scripts/gpu-monitor.sh"
    echo "3. Proceed to PLANB-04 (Python Environment Setup)"
    echo
}

# Main execution
main() {
    echo "======================================================"
    echo "PLANB-03: Post-Installation GPU Optimization"
    echo "======================================================"
    echo
    
    setup_logging
    verify_driver_installation
    detect_gpu_specifications
    apply_gpu_optimizations
    configure_persistence_daemon
    create_gpu_optimization_service
    configure_multi_gpu
    create_monitoring_scripts
    
    # Run validation (non-fatal if fails)
    if run_validation_tests; then
        validation_status="✅ PASSED"
    else
        validation_status="⚠️  PARTIAL"
    fi
    
    display_system_status
    
    echo
    log_info "🎉 PLANB-03 post-installation optimization completed!"
    log_info "Validation Status: $validation_status"
    echo
}

# Run main function
main "$@"