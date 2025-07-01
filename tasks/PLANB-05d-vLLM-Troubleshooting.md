# PLANB-05d: vLLM Troubleshooting Guide

**Task:** Comprehensive troubleshooting and error resolution for vLLM installation  
**Duration:** Variable (issue-dependent)  
**Prerequisites:** PLANB-05a through PLANB-05c attempted  

## Overview

This document provides systematic troubleshooting procedures for common vLLM installation and operational issues, with emphasis on configuration-based error resolution and rollback procedures.

## Configuration-Based Troubleshooting

### Configuration System Issues

#### Issue: Configuration Loading Fails
**Symptoms**: `ModuleNotFoundError`, configuration validation errors

**Resolution Steps**:
```bash
# 1. Verify configuration files exist
ls -la configs/vllm_settings.py
ls -la .env

# 2. Test configuration loading in isolation
python -c "
try:
    from configs.vllm_settings import load_vllm_settings
    print('✅ Configuration module imports successfully')
    
    install_settings, model_settings, test_settings = load_vllm_settings()
    print('✅ Configuration loads successfully')
    print(f'Environment: {install_settings.dev_env_path}')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    print('Solution: Ensure configs/vllm_settings.py exists')
    
except Exception as e:
    print(f'❌ Configuration error: {e}')
    print('Solution: Check .env file and required variables')
"

# 3. Validate environment variables
python -c "
import os
required_vars = ['HF_TOKEN', 'DEV_ENV_PATH', 'MODEL_STORAGE_PATH']
missing = [var for var in required_vars if not os.getenv(var)]
if missing:
    print(f'❌ Missing environment variables: {missing}')
    print('Solution: Update .env file with missing variables')
else:
    print('✅ All required environment variables present')
"
```

#### Issue: Environment Variable Conflicts
**Symptoms**: Unexpected configuration values, environment conflicts

**Resolution Steps**:
```bash
# 1. Check environment variable precedence
python -c "
import os
from configs.vllm_settings import load_vllm_settings

print('=== Environment Variable Analysis ===')

# Check for conflicts
env_vars = ['HF_TOKEN', 'DEV_ENV_PATH', 'GPU_MEMORY_UTILIZATION', 'MAX_JOBS']
for var in env_vars:
    env_value = os.getenv(var)
    print(f'{var}: {env_value if env_value else \"Not set\"}')

print('\\n=== Configuration Resolution ===')
try:
    install_settings, _, _ = load_vllm_settings()
    print(f'HF Token: {\"Set\" if install_settings.hf_token else \"Missing\"}')
    print(f'Dev Env: {install_settings.dev_env_path}')
    print(f'GPU Memory: {install_settings.gpu_memory_utilization}')
    print(f'Max Jobs: {install_settings.max_jobs}')
except Exception as e:
    print(f'Configuration error: {e}')
"

# 2. Reset environment if needed
unset HF_TOKEN DEV_ENV_PATH GPU_MEMORY_UTILIZATION MAX_JOBS
source .env
```

## Installation Issues

### vLLM Installation Failures

#### Issue: Compilation Errors During Installation
**Symptoms**: GCC errors, CUDA compilation failures

**Error Handling with Rollback**:
```bash
# 1. Create installation checkpoint
pip freeze > /tmp/pre_vllm_installation.txt
echo "Installation checkpoint created"

# 2. Attempt installation with error handling
install_vllm_with_rollback() {
    echo "Attempting vLLM installation..."
    
    # Load configuration
    python -c "
from configs.vllm_settings import get_environment_variables, load_vllm_settings
install_settings, _, _ = load_vllm_settings()
env_vars = get_environment_variables(install_settings)

import os
for key, value in env_vars.items():
    os.environ[key] = value
    print(f'export {key}=\"{value}\"')
" > /tmp/vllm_env.sh
    
    source /tmp/vllm_env.sh
    
    # Attempt installation
    if pip install vllm; then
        echo "✅ vLLM installation successful"
        return 0
    else
        echo "❌ vLLM installation failed, initiating rollback..."
        rollback_installation
        return 1
    fi
}

# 3. Rollback function
rollback_installation() {
    echo "🔄 Rolling back to previous state..."
    
    # Uninstall failed packages
    pip uninstall vllm vllm-flash-attn flash-attn -y
    
    # Clear cache
    pip cache purge
    
    # Restore previous environment
    pip uninstall -y $(pip freeze | grep -v -f /tmp/pre_vllm_installation.txt)
    
    echo "✅ Rollback completed"
}

# Execute installation
install_vllm_with_rollback
```

#### Issue: Memory Issues During Compilation
**Symptoms**: OOM errors, system freeze during compilation

**Resolution with Resource Management**:
```bash
# 1. Check available resources
echo "=== System Resource Check ==="
free -h
df -h
echo "Current MAX_JOBS: $MAX_JOBS"

# 2. Reduce compilation parallelism
python -c "
from configs.vllm_settings import load_vllm_settings
install_settings, _, _ = load_vllm_settings()

import os
import psutil

# Calculate safe MAX_JOBS based on available memory
available_memory_gb = psutil.virtual_memory().available / (1024**3)
safe_max_jobs = max(1, min(install_settings.max_jobs, int(available_memory_gb / 2)))

print(f'Available memory: {available_memory_gb:.1f}GB')
print(f'Current MAX_JOBS: {install_settings.max_jobs}')
print(f'Recommended MAX_JOBS: {safe_max_jobs}')

# Update environment
os.environ['MAX_JOBS'] = str(safe_max_jobs)
print(f'Updated MAX_JOBS to: {safe_max_jobs}')
"

# 3. Install with reduced parallelism
export MAX_JOBS=2
pip install vllm --no-cache-dir
```

### Dependency Conflicts

#### Issue: PyTorch Version Conflicts
**Symptoms**: Version incompatibility errors, import failures

**Systematic Resolution**:
```bash
# 1. Diagnose version conflicts
python -c "
import torch
import sys

print('=== PyTorch Compatibility Analysis ===')
print(f'Python version: {sys.version}')
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'CUDA version: {torch.version.cuda if torch.cuda.is_available() else \"N/A\"}')

# Check compatibility
torch_version = torch.__version__.split('.')
major, minor = int(torch_version[0]), int(torch_version[1])

if major >= 2 and minor >= 1:
    print('✅ PyTorch version compatible with vLLM')
else:
    print('❌ PyTorch version may cause issues')
    print('Recommended: Upgrade to PyTorch 2.1+')
"

# 2. Update PyTorch with rollback support
backup_torch_installation() {
    pip freeze | grep torch > /tmp/torch_backup.txt
    echo "PyTorch installation backed up"
}

restore_torch_installation() {
    pip uninstall torch torchvision torchaudio -y
    pip install -r /tmp/torch_backup.txt
    echo "PyTorch installation restored"
}

# 3. Perform safe PyTorch update
backup_torch_installation

if pip install --upgrade torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124; then
    echo "✅ PyTorch updated successfully"
else
    echo "❌ PyTorch update failed, restoring backup"
    restore_torch_installation
fi
```

## Runtime Issues

### CUDA and GPU Problems

#### Issue: CUDA Not Available
**Symptoms**: `torch.cuda.is_available()` returns False

**Comprehensive Diagnosis and Fix**:
```bash
# 1. Multi-level CUDA diagnosis
diagnose_cuda() {
    echo "=== CUDA Diagnosis ==="
    
    # Check NVIDIA driver
    if command -v nvidia-smi &> /dev/null; then
        echo "✅ NVIDIA driver installed"
        nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits
    else
        echo "❌ NVIDIA driver not found"
        return 1
    fi
    
    # Check CUDA toolkit
    if command -v nvcc &> /dev/null; then
        echo "✅ CUDA toolkit installed"
        nvcc --version | grep "release"
    else
        echo "❌ CUDA toolkit not found"
    fi
    
    # Check CUDA environment
    echo "CUDA_HOME: ${CUDA_HOME:-Not set}"
    echo "PATH contains CUDA: $(echo $PATH | grep -o cuda || echo 'No')"
    
    # Check PyTorch CUDA
    python -c "
import torch
print(f'PyTorch CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA devices: {torch.cuda.device_count()}')
    print(f'CUDA version: {torch.version.cuda}')
else:
    print('PyTorch compiled without CUDA support')
"
}

# 2. Fix CUDA issues
fix_cuda_issues() {
    diagnose_cuda
    
    # Reinstall PyTorch with CUDA if needed
    if ! python -c "import torch; assert torch.cuda.is_available()"; then
        echo "Reinstalling PyTorch with CUDA support..."
        pip uninstall torch torchvision torchaudio -y
        pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
    fi
}

fix_cuda_issues
```

### Model Loading Issues

#### Issue: Model Download Failures
**Symptoms**: Connection errors, authentication failures, disk space issues

**Robust Model Loading with Retry Logic**:
```bash
# Model loading with comprehensive error handling
python -c "
import os
import time
import shutil
from pathlib import Path
from configs.vllm_settings import load_vllm_settings

def safe_model_download(model_name, max_retries=3):
    \"\"\"Download model with retry logic and error handling\"\"\"
    
    install_settings, _, test_settings = load_vllm_settings()
    
    # Set up environment
    os.environ['HF_TOKEN'] = install_settings.hf_token
    os.environ['HF_HOME'] = install_settings.hf_cache_dir
    
    for attempt in range(max_retries):
        try:
            print(f'Attempt {attempt + 1}/{max_retries}: Loading {model_name}')
            
            from vllm import LLM
            
            # Check available disk space
            cache_path = Path(install_settings.hf_cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)
            
            disk_usage = shutil.disk_usage(cache_path)
            free_gb = disk_usage.free / (1024**3)
            
            if free_gb < 5:  # Require at least 5GB free
                print(f'❌ Insufficient disk space: {free_gb:.1f}GB available')
                return False
            
            # Attempt model loading
            llm = LLM(
                model=model_name,
                gpu_memory_utilization=0.3,  # Conservative setting
                download_dir=str(cache_path),
                tensor_parallel_size=1
            )
            
            print(f'✅ Model {model_name} loaded successfully')
            return True
            
        except Exception as e:
            print(f'❌ Attempt {attempt + 1} failed: {e}')
            
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f'Waiting {wait_time}s before retry...')
                time.sleep(wait_time)
            else:
                print(f'❌ All attempts failed for {model_name}')
                return False
    
    return False

# Test model loading
test_model = 'facebook/opt-125m'
success = safe_model_download(test_model)
print(f'Model loading test: {\"PASSED\" if success else \"FAILED\"}')
"
```

## Performance Issues

### Throughput Problems

#### Issue: Low Inference Throughput
**Symptoms**: Slow response times, low requests/second

**Performance Optimization with Monitoring**:
```bash
# Performance analysis and optimization
python -c "
import time
import torch
import psutil
from vllm import LLM, SamplingParams
from configs.vllm_settings import load_vllm_settings

def performance_analysis():
    \"\"\"Comprehensive performance analysis\"\"\"
    
    install_settings, _, test_settings = load_vllm_settings()
    
    print('=== Performance Analysis ===')
    
    # System resources
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    
    print(f'CPU cores: {cpu_count}')
    print(f'Memory: {memory.total / (1024**3):.1f}GB total, {memory.available / (1024**3):.1f}GB available')
    
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f'GPU {i}: {props.name}, {props.total_memory / (1024**3):.1f}GB')
    
    # Performance test with different configurations
    configs = [
        {'gpu_memory_utilization': 0.3, 'tensor_parallel_size': 1},
        {'gpu_memory_utilization': 0.5, 'tensor_parallel_size': 1},
        {'gpu_memory_utilization': 0.7, 'tensor_parallel_size': 1},
    ]
    
    best_config = None
    best_throughput = 0
    
    for config in configs:
        try:
            print(f'\\nTesting config: {config}')
            
            llm = LLM(
                model=test_settings.test_model,
                **config
            )
            
            # Warmup
            llm.generate(['warmup'], SamplingParams(max_tokens=1))
            
            # Performance test
            prompts = ['Hello world!'] * 5
            sampling_params = SamplingParams(max_tokens=10)
            
            start_time = time.time()
            outputs = llm.generate(prompts, sampling_params)
            end_time = time.time()
            
            throughput = len(prompts) / (end_time - start_time)
            
            print(f'Throughput: {throughput:.2f} requests/second')
            
            if throughput > best_throughput:
                best_throughput = throughput
                best_config = config
            
            del llm  # Free memory
            torch.cuda.empty_cache()
            
        except Exception as e:
            print(f'Config failed: {e}')
            continue
    
    if best_config:
        print(f'\\n✅ Best configuration: {best_config}')
        print(f'Best throughput: {best_throughput:.2f} requests/second')
        
        # Update configuration recommendation
        print('\\nRecommendation: Update .env with optimal settings:')
        print(f'GPU_MEMORY_UTILIZATION={best_config[\"gpu_memory_utilization\"]}')
        print(f'TENSOR_PARALLEL_SIZE={best_config[\"tensor_parallel_size\"]}')
    else:
        print('❌ No working configuration found')

performance_analysis()
"
```

## System Integration Issues

### Service Integration Problems

#### Issue: Server Won't Start
**Symptoms**: Server startup failures, port conflicts

**Server Diagnosis and Recovery**:
```bash
# Comprehensive server troubleshooting
troubleshoot_server() {
    echo "=== Server Troubleshooting ==="
    
    # Check port availability
    local port=${1:-8000}
    
    if lsof -i :$port; then
        echo "❌ Port $port is already in use"
        echo "Processes using port $port:"
        lsof -i :$port
        
        read -p "Kill existing processes? (y/N): " kill_procs
        if [[ $kill_procs =~ ^[Yy]$ ]]; then
            lsof -ti :$port | xargs kill -9
            echo "✅ Port $port cleared"
        fi
    else
        echo "✅ Port $port is available"
    fi
    
    # Test server startup with error capture
    python -c "
import sys
import subprocess
import time
from pathlib import Path

# Use existing server script
server_script = Path('scripts/start_vllm_server.py')
if not server_script.exists():
    print('❌ Server script not found')
    sys.exit(1)

test_model = 'facebook/opt-125m'
cmd = [sys.executable, str(server_script), test_model, '--port', '$port']

print(f'Starting server: {\" \".join(cmd)}')

try:
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for startup
    time.sleep(10)
    
    if process.poll() is None:
        print('✅ Server started successfully')
        process.terminate()
        process.wait()
    else:
        stdout, stderr = process.communicate()
        print(f'❌ Server failed to start')
        print(f'STDOUT: {stdout}')
        print(f'STDERR: {stderr}')
        
except Exception as e:
    print(f'❌ Server startup error: {e}')
"
}

# Run server troubleshooting
troubleshoot_server 8000
```

## Recovery Procedures

### Complete System Recovery

#### Emergency Reset Procedure
```bash
# Complete vLLM environment reset
emergency_reset() {
    echo "🚨 EMERGENCY RESET: This will remove all vLLM installations"
    read -p "Continue? (type 'RESET' to confirm): " confirm
    
    if [[ $confirm != "RESET" ]]; then
        echo "Reset cancelled"
        return 1
    fi
    
    echo "🔄 Beginning emergency reset..."
    
    # 1. Stop all vLLM processes
    pkill -f vllm
    pkill -f "python.*vllm"
    
    # 2. Remove vLLM packages
    pip uninstall vllm vllm-flash-attn flash-attn -y
    
    # 3. Clear caches
    pip cache purge
    rm -rf ~/.cache/huggingface
    rm -rf /tmp/vllm*
    
    # 4. Clear GPU memory
    python -c "
import torch
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    print('✅ GPU cache cleared')
"
    
    # 5. Verify clean state
    if python -c "import vllm" 2>/dev/null; then
        echo "❌ vLLM still present after reset"
        return 1
    else
        echo "✅ Emergency reset completed"
        echo "To reinstall: Follow PLANB-05a through PLANB-05c"
        return 0
    fi
}

# Provide reset option
echo "Emergency reset available: run 'emergency_reset' function"
```

### Diagnostic Report Generation

```bash
# Generate comprehensive diagnostic report
generate_diagnostic_report() {
    local report_file="/tmp/vllm_diagnostic_$(date +%Y%m%d_%H%M%S).txt"
    
    echo "Generating diagnostic report: $report_file"
    
    {
        echo "=== vLLM Diagnostic Report ==="
        echo "Generated: $(date)"
        echo "Host: $(hostname)"
        echo "User: $(whoami)"
        echo
        
        echo "=== System Information ==="
        uname -a
        cat /etc/os-release | head -5
        echo
        
        echo "=== Python Environment ==="
        python --version
        which python
        pip --version
        echo
        
        echo "=== CUDA Information ==="
        nvidia-smi 2>/dev/null || echo "nvidia-smi not available"
        nvcc --version 2>/dev/null || echo "nvcc not available"
        echo "CUDA_HOME: ${CUDA_HOME:-Not set}"
        echo
        
        echo "=== Configuration Status ==="
        python -c "
try:
    from configs.vllm_settings import load_vllm_settings
    install_settings, model_settings, test_settings = load_vllm_settings()
    print(f'Environment: {install_settings.dev_env_path}')
    print(f'GPU Memory: {install_settings.gpu_memory_utilization}')
    print(f'Test Model: {test_settings.test_model}')
    print('Configuration: ✅ LOADED')
except Exception as e:
    print(f'Configuration: ❌ FAILED - {e}')
" 2>&1
        echo
        
        echo "=== Package Status ==="
        pip list | grep -E "(vllm|torch|transformers|fastapi)" 2>/dev/null || echo "No relevant packages found"
        echo
        
        echo "=== Import Status ==="
        python -c "
packages = ['vllm', 'torch', 'transformers', 'fastapi']
for pkg in packages:
    try:
        module = __import__(pkg)
        version = getattr(module, '__version__', 'unknown')
        print(f'{pkg}: ✅ {version}')
    except ImportError:
        print(f'{pkg}: ❌ Not available')
" 2>&1
        echo
        
        echo "=== Error Log Scan ==="
        grep -r "ERROR\|CRITICAL" /var/log/ 2>/dev/null | grep -i vllm | tail -10 || echo "No error logs found"
        
    } > "$report_file"
    
    echo "✅ Diagnostic report saved: $report_file"
    echo "Share this file when requesting support"
}

# Make function available
echo "Generate diagnostic report: run 'generate_diagnostic_report'"
```

## Prevention and Monitoring

### Proactive Health Checks

```bash
# Set up monitoring script
cat > /opt/citadel/scripts/vllm_health_check.py << 'EOF'
#!/usr/bin/env python3
"""
vLLM Health Check Script
Monitors vLLM installation health and reports issues
"""

import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from configs.vllm_settings import load_vllm_settings

def health_check():
    """Perform comprehensive health check"""
    
    print(f"=== vLLM Health Check - {datetime.now()} ===")
    
    issues = []
    
    # Configuration check
    try:
        install_settings, model_settings, test_settings = load_vllm_settings()
        print("✅ Configuration: OK")
    except Exception as e:
        issues.append(f"Configuration: {e}")
        print(f"❌ Configuration: {e}")
    
    # Import check
    try:
        import vllm, torch, transformers
        print("✅ Imports: OK")
        print(f"   vLLM: {vllm.__version__}")
        print(f"   PyTorch: {torch.__version__}")
    except Exception as e:
        issues.append(f"Imports: {e}")
        print(f"❌ Imports: {e}")
    
    # CUDA check
    try:
        import torch
        if torch.cuda.is_available():
            print("✅ CUDA: OK")
            print(f"   Devices: {torch.cuda.device_count()}")
        else:
            issues.append("CUDA not available")
            print("❌ CUDA: Not available")
    except Exception as e:
        issues.append(f"CUDA: {e}")
        print(f"❌ CUDA: {e}")
    
    # Report summary
    if issues:
        print(f"\n⚠️ Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    else:
        print("\n🎉 All checks passed!")
        return 0

if __name__ == "__main__":
    sys.exit(health_check())
EOF

chmod +x /opt/citadel/scripts/vllm_health_check.py
echo "✅ Health check script created: /opt/citadel/scripts/vllm_health_check.py"
```

---

**Status**: ✅ **Troubleshooting Guide Complete**  
**Coverage**: Configuration, Installation, Runtime, Performance, Recovery  
**Critical**: Systematic approach to error resolution with rollback procedures