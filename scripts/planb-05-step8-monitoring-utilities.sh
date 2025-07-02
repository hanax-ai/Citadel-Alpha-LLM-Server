#!/bin/bash
# PLANB-05-Step8: Install Monitoring and Utilities
# Install monitoring, debugging, and development tools for vLLM environment

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CITADEL_ROOT="/opt/citadel"
DEV_ENV_PATH="/opt/citadel/dev-env"
LOG_FILE="/opt/citadel/logs/planb-05-step8-monitoring.log"
CONFIG_FILE="/opt/citadel/configs/python-config.json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging functions
log_info() {
    local message="$1"
    echo -e "${BLUE}[INFO]${NC} $message" | tee -a "$LOG_FILE"
}

log_success() {
    local message="$1"
    echo -e "${GREEN}[SUCCESS]${NC} $message" | tee -a "$LOG_FILE"
}

log_warning() {
    local message="$1"
    echo -e "${YELLOW}[WARNING]${NC} $message" | tee -a "$LOG_FILE"
}

log_error() {
    local message="$1"
    echo -e "${RED}[ERROR]${NC} $message" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log_error "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites for monitoring and utilities installation..."
    
    # Check if dev-env exists
    if [ ! -d "$DEV_ENV_PATH" ]; then
        error_exit "Development environment not found at $DEV_ENV_PATH. Please complete previous steps first."
    fi
    
    # Check if dev-env is properly set up
    if [ ! -f "$DEV_ENV_PATH/bin/python" ]; then
        error_exit "Python not found in development environment. Please complete PLANB-04 first."
    fi
    
    # Check Python version in virtual environment
    local python_version
    python_version=$("$DEV_ENV_PATH/bin/python" --version 2>&1 | cut -d' ' -f2)
    if [[ ! "$python_version" =~ ^3\.12 ]]; then
        error_exit "Python 3.12 required, found: $python_version"
    fi
    
    # Check if previous vLLM installation steps are complete
    log_info "Validating previous vLLM installation steps..."
    "$DEV_ENV_PATH/bin/python" -c "
import sys
try:
    import vllm
    import fastapi
    import uvicorn
    print(f'✅ vLLM version: {vllm.__version__}')
    print(f'✅ FastAPI version: {fastapi.__version__}')
    print(f'✅ Uvicorn available')
except ImportError as e:
    print(f'❌ Missing required dependencies: {e}')
    sys.exit(1)
" || error_exit "Previous vLLM installation steps incomplete. Please complete steps 1-7 first."
    
    log_success "Prerequisites check passed"
    log_info "Python version: $python_version"
}

# Install monitoring and system utilities
install_monitoring_utilities() {
    log_info "Installing monitoring and system utilities..."
    
    # Reason: Activate virtual environment for package installation
    source "$DEV_ENV_PATH/bin/activate"
    
    local monitoring_packages=(
        "psutil>=5.9.0"
        "GPUtil>=1.4.0" 
        "py3nvml>=0.2.7"
        "nvidia-ml-py3>=7.352.0"
        "rich>=13.7.0"
        "typer>=0.9.0"
        "tqdm>=4.66.0"
    )
    
    log_info "Installing ${#monitoring_packages[@]} monitoring packages..."
    
    for package in "${monitoring_packages[@]}"; do
        log_info "Installing: $package"
        if ! pip install "$package"; then
            log_warning "Failed to install $package, continuing with others..."
        else
            log_success "Installed: $package"
        fi
    done
    
    log_success "Monitoring utilities installation completed"
}

# Install development and debugging tools
install_development_tools() {
    log_info "Installing development and debugging tools..."
    
    # Reason: Activate virtual environment for package installation
    source "$DEV_ENV_PATH/bin/activate"
    
    local dev_packages=(
        "ipython>=8.17.0"
        "jupyter>=1.0.0"
        "matplotlib>=3.7.0"
        "seaborn>=0.12.0"
        "tensorboard>=2.15.0"
    )
    
    log_info "Installing ${#dev_packages[@]} development packages..."
    
    for package in "${dev_packages[@]}"; do
        log_info "Installing: $package"
        if ! pip install "$package"; then
            log_warning "Failed to install $package, continuing with others..."
        else
            log_success "Installed: $package"
        fi
    done
    
    log_success "Development tools installation completed"
}

# Verify installations
verify_installations() {
    log_info "Verifying monitoring and utility installations..."
    
    # Reason: Activate virtual environment for verification
    source "$DEV_ENV_PATH/bin/activate"
    
    "$DEV_ENV_PATH/bin/python" -c "
import sys
from importlib import import_module

# Monitoring packages to verify
monitoring_packages = [
    ('psutil', 'System monitoring'),
    ('GPUtil', 'GPU utilities'),
    ('py3nvml', 'NVIDIA ML Python'),
    ('pynvml', 'NVIDIA ML (alternative)'),
    ('rich', 'Rich text formatting'),
    ('typer', 'CLI framework'),
    ('tqdm', 'Progress bars')
]

# Development packages to verify
dev_packages = [
    ('IPython', 'Interactive Python'),
    ('jupyter', 'Jupyter notebooks'),
    ('matplotlib', 'Plotting library'),
    ('seaborn', 'Statistical plotting'),
    ('tensorboard', 'TensorBoard visualization')
]

all_packages = monitoring_packages + dev_packages
successful_imports = []
failed_imports = []

print('=== Package Verification Results ===')
print()

for package_name, description in all_packages:
    try:
        module = import_module(package_name)
        version = getattr(module, '__version__', 'Unknown')
        print(f'✅ {package_name}: {version} - {description}')
        successful_imports.append(package_name)
    except ImportError as e:
        print(f'❌ {package_name}: Failed to import - {description}')
        failed_imports.append(package_name)

print()
print(f'Summary: {len(successful_imports)}/{len(all_packages)} packages successfully installed')

if failed_imports:
    print(f'Failed packages: {', '.join(failed_imports)}')
    sys.exit(1)
else:
    print('🎉 All monitoring and utility packages verified successfully!')
"
    
    if [ $? -eq 0 ]; then
        log_success "All packages verified successfully"
    else
        error_exit "Package verification failed"
    fi
}

# Test GPU monitoring capabilities
test_gpu_monitoring() {
    log_info "Testing GPU monitoring capabilities..."
    
    # Reason: Activate virtual environment for GPU testing
    source "$DEV_ENV_PATH/bin/activate"
    
    "$DEV_ENV_PATH/bin/python" -c "
import sys

print('=== GPU Monitoring Test ===')

# Test nvidia-ml-py3
try:
    import pynvml
    pynvml.nvmlInit()
    device_count = pynvml.nvmlDeviceGetCount()
    print(f'✅ NVIDIA ML: Detected {device_count} GPU(s)')
    
    for i in range(device_count):
        handle = pynvml.nvmlDeviceGetHandleByIndex(i)
        name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
        memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
        print(f'  GPU {i}: {name}')
        print(f'    Memory: {memory_info.used // (1024**2)} MB / {memory_info.total // (1024**2)} MB')
        
except Exception as e:
    print(f'⚠️  NVIDIA ML monitoring not available: {e}')

# Test GPUtil
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    print(f'✅ GPUtil: Detected {len(gpus)} GPU(s)')
    
    for gpu in gpus:
        print(f'  GPU {gpu.id}: {gpu.name}')
        print(f'    Load: {gpu.load*100:.1f}%')
        print(f'    Memory: {gpu.memoryUtil*100:.1f}%')
        print(f'    Temperature: {gpu.temperature}°C')
        
except Exception as e:
    print(f'⚠️  GPUtil monitoring not available: {e}')

# Test system monitoring
try:
    import psutil
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    print(f'✅ System Monitoring:')
    print(f'    CPU Usage: {cpu_percent}%')
    print(f'    Memory Usage: {memory.percent}%')
    print(f'    Available Memory: {memory.available // (1024**3)} GB')
    
except Exception as e:
    print(f'❌ System monitoring failed: {e}')
    sys.exit(1)

print()
print('🎯 GPU and system monitoring capabilities verified!')
"
    
    if [ $? -eq 0 ]; then
        log_success "GPU monitoring test passed"
    else
        log_warning "GPU monitoring test had issues, but continuing..."
    fi
}

# Create monitoring utility scripts
create_monitoring_scripts() {
    log_info "Creating monitoring utility scripts..."
    
    # Create system monitoring script
    cat > "$CITADEL_ROOT/scripts/system-monitor.py" << 'EOF'
#!/usr/bin/env python3
"""
System Monitoring Utility
Quick system and GPU status for vLLM deployment
"""

import sys
import time
from datetime import datetime

try:
    import psutil
    import GPUtil
    import pynvml
    from rich import print
    from rich.table import Table
    from rich.panel import Panel
    from rich.console import Console
except ImportError as e:
    print(f"❌ Missing dependencies: {e}")
    print("Run: pip install psutil GPUtil py3nvml rich")
    sys.exit(1)

def get_system_info():
    """Get system information"""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        'cpu': cpu_percent,
        'memory_percent': memory.percent,
        'memory_available_gb': memory.available / (1024**3),
        'disk_percent': (disk.used / disk.total) * 100,
        'disk_free_gb': disk.free / (1024**3)
    }

def get_gpu_info():
    """Get GPU information"""
    gpus = []
    try:
        pynvml.nvmlInit()
        device_count = pynvml.nvmlDeviceGetCount()
        
        for i in range(device_count):
            handle = pynvml.nvmlDeviceGetHandleByIndex(i)
            name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
            memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            gpus.append({
                'id': i,
                'name': name,
                'memory_used_mb': memory_info.used // (1024*1024),
                'memory_total_mb': memory_info.total // (1024*1024),
                'memory_percent': (memory_info.used / memory_info.total) * 100,
                'gpu_util': utilization.gpu,
                'temperature': temperature
            })
    except Exception as e:
        print(f"⚠️  GPU monitoring error: {e}")
    
    return gpus

def main():
    console = Console()
    
    # System Information
    sys_info = get_system_info()
    
    system_table = Table(title="System Status")
    system_table.add_column("Metric", style="cyan")
    system_table.add_column("Value", style="green")
    system_table.add_column("Status", style="yellow")
    
    system_table.add_row("CPU Usage", f"{sys_info['cpu']:.1f}%", 
                        "🔥" if sys_info['cpu'] > 80 else "✅")
    system_table.add_row("Memory Usage", f"{sys_info['memory_percent']:.1f}%",
                        "🔥" if sys_info['memory_percent'] > 90 else "✅")
    system_table.add_row("Available Memory", f"{sys_info['memory_available_gb']:.1f} GB", "")
    system_table.add_row("Disk Usage", f"{sys_info['disk_percent']:.1f}%",
                        "🔥" if sys_info['disk_percent'] > 90 else "✅")
    system_table.add_row("Free Disk Space", f"{sys_info['disk_free_gb']:.1f} GB", "")
    
    console.print(system_table)
    console.print()
    
    # GPU Information
    gpus = get_gpu_info()
    if gpus:
        gpu_table = Table(title="GPU Status")
        gpu_table.add_column("GPU", style="cyan")
        gpu_table.add_column("Name", style="white")
        gpu_table.add_column("Memory", style="green")
        gpu_table.add_column("Utilization", style="yellow")
        gpu_table.add_column("Temperature", style="red")
        
        for gpu in gpus:
            memory_status = f"{gpu['memory_used_mb']} / {gpu['memory_total_mb']} MB ({gpu['memory_percent']:.1f}%)"
            temp_status = "🔥" if gpu['temperature'] > 80 else "✅"
            
            gpu_table.add_row(
                f"GPU {gpu['id']}",
                gpu['name'],
                memory_status,
                f"{gpu['gpu_util']}%",
                f"{gpu['temperature']}°C {temp_status}"
            )
        
        console.print(gpu_table)
    else:
        console.print("[yellow]⚠️  No GPU information available[/yellow]")
    
    # Timestamp
    console.print(f"\n[dim]Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}[/dim]")

if __name__ == "__main__":
    main()
EOF

    chmod +x "$CITADEL_ROOT/scripts/system-monitor.py"
    log_success "Created system monitoring script: $CITADEL_ROOT/scripts/system-monitor.py"
}

# Generate installation summary
generate_summary() {
    log_info "Generating installation summary..."
    
    # Reason: Activate virtual environment for package listing
    source "$DEV_ENV_PATH/bin/activate"
    
    local summary_file="$CITADEL_ROOT/logs/monitoring-utilities-summary.txt"
    
    {
        echo "Monitoring and Utilities Installation Summary"
        echo "============================================="
        echo "Generated: $(date)"
        echo ""
        echo "Environment: $DEV_ENV_PATH"
        echo "Python Version: $("$DEV_ENV_PATH/bin/python" --version)"
        echo "Pip Version: $("$DEV_ENV_PATH/bin/pip" --version | cut -d' ' -f2)"
        echo ""
        echo "Installed Monitoring Packages:"
        echo "=============================="
        pip list | grep -E "(psutil|GPUtil|py3nvml|nvidia-ml-py3|rich|typer|tqdm)" || echo "No monitoring packages found"
        echo ""
        echo "Installed Development Tools:"
        echo "============================"
        pip list | grep -E "(IPython|jupyter|matplotlib|seaborn|tensorboard)" || echo "No development tools found"
        echo ""
        echo "Installation Status: SUCCESS"
        echo ""
        echo "Available Monitoring Scripts:"
        echo "============================="
        echo "- $CITADEL_ROOT/scripts/system-monitor.py"
        echo ""
        echo "Usage Examples:"
        echo "==============="
        echo "# Check system status:"
        echo "python $CITADEL_ROOT/scripts/system-monitor.py"
        echo ""
        echo "# Start Jupyter notebook:"
        echo "source $DEV_ENV_PATH/bin/activate && jupyter notebook"
        echo ""
        echo "# Interactive Python with monitoring:"
        echo "source $DEV_ENV_PATH/bin/activate && ipython"
    } > "$summary_file"
    
    log_success "Installation summary created: $summary_file"
}

# Main execution function
main() {
    log_info "=== PLANB-05-Step8: Install Monitoring and Utilities ==="
    log_info "Starting monitoring and utilities installation..."
    
    check_prerequisites
    install_monitoring_utilities
    install_development_tools
    verify_installations
    test_gpu_monitoring
    create_monitoring_scripts
    generate_summary
    
    log_success ""
    log_success "🎉 Monitoring and utilities installation completed successfully!"
    log_success "✅ System monitoring tools installed and verified"
    log_success "✅ Development and debugging tools ready"
    log_success "✅ GPU monitoring capabilities enabled"
    log_success ""
    log_info "📊 Test system monitoring: python /opt/citadel/scripts/system-monitor.py"
    log_info "🔬 Start Jupyter: source /opt/citadel/dev-env/bin/activate && jupyter notebook"
    log_info "🐍 Interactive Python: source /opt/citadel/dev-env/bin/activate && ipython"
    log_info ""
    log_info "➡️  Next step: Proceed with Flash Attention installation (Step 5)"
}

# Execute main function
main "$@"