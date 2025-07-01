# PLANB-05c: vLLM Validation and Testing

**Task:** Comprehensive validation and testing of vLLM installation  
**Duration:** 20-30 minutes  
**Prerequisites:** PLANB-05b-vLLM-Installation.md completed  

## Overview

This document covers comprehensive validation and testing procedures for the vLLM installation using the configured test suite and validation framework.

## Validation Framework

### Configuration-Based Testing

The validation system uses the centralized configuration management:

```bash
# Run the comprehensive validation suite
python tests/validation/test_vllm_installation.py
```

### Manual Validation Steps

For step-by-step validation, follow these procedures:

#### Step 1: Configuration Validation

```bash
# Test configuration loading
python -c "
from configs.vllm_settings import load_vllm_settings
try:
    install_settings, model_settings, test_settings = load_vllm_settings()
    print('✅ Configuration validation: PASSED')
    print(f'  Environment: {install_settings.dev_env_path}')
    print(f'  GPU Memory: {install_settings.gpu_memory_utilization}')
    print(f'  Test Model: {test_settings.test_model}')
except Exception as e:
    print(f'❌ Configuration validation: FAILED - {e}')
"
```

#### Step 2: Import and Version Validation

```bash
# Test core imports and version compatibility
python -c "
import sys
import vllm
import torch
import transformers

print('=== Import and Version Validation ===')
print(f'✅ Python: {sys.version}')
print(f'✅ vLLM: {vllm.__version__}')
print(f'✅ PyTorch: {torch.__version__}')
print(f'✅ Transformers: {transformers.__version__}')

# Version compatibility checks
version_parts = vllm.__version__.split('.')
major, minor = int(version_parts[0]), int(version_parts[1])

if major == 0 and minor >= 6:
    print('✅ vLLM version compatibility: PASSED (0.6.x+)')
elif major >= 1:
    print('✅ vLLM version compatibility: PASSED (1.x+)')
else:
    print('⚠️ vLLM version compatibility: WARNING')
"
```

#### Step 3: CUDA and GPU Validation

```bash
# Test CUDA availability and GPU setup
python -c "
import torch
from configs.vllm_settings import load_vllm_settings

print('=== CUDA and GPU Validation ===')

if torch.cuda.is_available():
    print(f'✅ CUDA available: {torch.version.cuda}')
    print(f'✅ GPU count: {torch.cuda.device_count()}')
    
    for i in range(torch.cuda.device_count()):
        gpu_name = torch.cuda.get_device_name(i)
        gpu_memory = torch.cuda.get_device_properties(i).total_memory / 1e9
        print(f'  GPU {i}: {gpu_name} ({gpu_memory:.1f}GB)')
    
    # Test GPU memory allocation
    try:
        test_tensor = torch.cuda.FloatTensor(100, 100)
        print('✅ GPU memory allocation: PASSED')
        del test_tensor
        torch.cuda.empty_cache()
    except Exception as e:
        print(f'❌ GPU memory allocation: FAILED - {e}')
else:
    print('❌ CUDA not available')
"
```

#### Step 4: Hugging Face Authentication

```bash
# Test HF authentication with configuration
python -c "
from configs.vllm_settings import load_vllm_settings
from huggingface_hub import whoami
import os

try:
    install_settings, _, _ = load_vllm_settings()
    os.environ['HF_TOKEN'] = install_settings.hf_token
    
    user_info = whoami()
    print('✅ Hugging Face authentication: PASSED')
    print(f'  User: {user_info[\"name\"]}')
    print(f'  Cache: {install_settings.hf_cache_dir}')
except Exception as e:
    print(f'❌ Hugging Face authentication: FAILED - {e}')
"
```

## Functional Testing

### Basic Engine Testing

```bash
# Test vLLM engine functionality
python -c "
from vllm import LLM, SamplingParams
from configs.vllm_settings import load_vllm_settings
import time

print('=== vLLM Engine Functional Test ===')

try:
    # Load configuration
    install_settings, _, test_settings = load_vllm_settings()
    
    # Initialize LLM with configuration
    llm = LLM(
        model=test_settings.test_model,
        tensor_parallel_size=install_settings.tensor_parallel_size,
        gpu_memory_utilization=install_settings.gpu_memory_utilization,
        download_dir=test_settings.test_cache_dir
    )
    
    # Test generation
    prompts = ['Hello, how are you today?']
    sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=50)
    
    start_time = time.time()
    outputs = llm.generate(prompts, sampling_params)
    end_time = time.time()
    
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f'✅ Engine test: PASSED ({end_time - start_time:.2f}s)')
        print(f'  Prompt: {prompt}')
        print(f'  Generated: {generated_text.strip()}')
    
except Exception as e:
    print(f'❌ Engine test: FAILED - {e}')
"
```

### Performance Validation

```bash
# Run performance benchmarks using configuration
python -c "
from vllm import LLM, SamplingParams
from configs.vllm_settings import load_vllm_settings
import time

print('=== Performance Validation ===')

try:
    # Load configuration
    install_settings, _, test_settings = load_vllm_settings()
    
    if not test_settings.enable_performance_tests:
        print('⏭️ Performance tests disabled in configuration')
        exit(0)
    
    # Initialize LLM
    llm = LLM(
        model=test_settings.test_model,
        tensor_parallel_size=install_settings.tensor_parallel_size,
        gpu_memory_utilization=install_settings.gpu_memory_utilization
    )
    
    # Performance test
    prompts = ['Hello world!'] * 10
    sampling_params = SamplingParams(max_tokens=20)
    
    print(f'Testing with {len(prompts)} requests...')
    start_time = time.time()
    outputs = llm.generate(prompts, sampling_params)
    end_time = time.time()
    
    total_time = end_time - start_time
    throughput = len(prompts) / total_time
    
    print(f'✅ Performance test: COMPLETED')
    print(f'  Requests: {len(prompts)}')
    print(f'  Total time: {total_time:.2f}s')
    print(f'  Throughput: {throughput:.2f} requests/second')
    
    # Check against minimum requirements
    if throughput >= test_settings.min_throughput:
        print(f'✅ Throughput requirement: PASSED (>= {test_settings.min_throughput:.2f})')
    else:
        print(f'⚠️ Throughput requirement: BELOW MINIMUM ({test_settings.min_throughput:.2f})')
    
except Exception as e:
    print(f'❌ Performance test: FAILED - {e}')
"
```

## Server Testing

### API Server Validation

Start the vLLM server using the configured script:

```bash
# Start server with configuration (in background)
python scripts/start_vllm_server.py facebook/opt-125m --port 8000 &
SERVER_PID=$!

# Wait for server to start
sleep 30

# Test server endpoints
python scripts/test_vllm_client.py --url http://localhost:8000 --model facebook/opt-125m

# Stop server
kill $SERVER_PID
```

### Health Check Validation

```bash
# Test server health endpoint
python -c "
import requests
import time

print('=== Server Health Check ===')

base_url = 'http://localhost:8000'
max_retries = 5
retry_delay = 5

for attempt in range(max_retries):
    try:
        response = requests.get(f'{base_url}/health', timeout=10)
        if response.status_code == 200:
            print('✅ Server health check: PASSED')
            break
        else:
            print(f'⚠️ Health check attempt {attempt + 1}: HTTP {response.status_code}')
    except Exception as e:
        print(f'⚠️ Health check attempt {attempt + 1}: {e}')
    
    if attempt < max_retries - 1:
        time.sleep(retry_delay)
else:
    print('❌ Server health check: FAILED after all retries')
"
```

## Dependency Validation

### Comprehensive Dependency Check

```bash
# Test all critical dependencies
python -c "
print('=== Dependency Validation ===')

dependencies = [
    ('vllm', 'vLLM core'),
    ('torch', 'PyTorch'),
    ('transformers', 'Transformers'),
    ('tokenizers', 'Tokenizers'),
    ('fastapi', 'FastAPI'),
    ('uvicorn', 'Uvicorn'),
    ('pydantic', 'Pydantic'),
    ('huggingface_hub', 'HF Hub'),
    ('accelerate', 'Accelerate'),
    ('requests', 'Requests'),
    ('aiohttp', 'AioHTTP'),
    ('psutil', 'PSUtil'),
    ('rich', 'Rich'),
    ('prometheus_client', 'Prometheus')
]

passed = 0
total = len(dependencies)

for package, description in dependencies:
    try:
        module = __import__(package)
        version = getattr(module, '__version__', 'unknown')
        print(f'✅ {description}: {version}')
        passed += 1
    except ImportError:
        print(f'❌ {description}: NOT INSTALLED')

print(f'\\nDependency Summary: {passed}/{total} passed')

if passed == total:
    print('🎉 All dependencies validated successfully!')
else:
    print('⚠️ Some dependencies missing or failed')
"
```

## Integration Testing

### Model Loading Test

```bash
# Test model loading with different configurations
python -c "
from vllm import LLM
from configs.vllm_settings import load_vllm_settings

print('=== Model Loading Integration Test ===')

install_settings, model_settings, test_settings = load_vllm_settings()

# Test with different GPU memory settings
memory_configs = [0.3, 0.5, 0.7]

for memory_util in memory_configs:
    try:
        print(f'Testing with GPU memory utilization: {memory_util}')
        
        llm = LLM(
            model=test_settings.test_model,
            gpu_memory_utilization=memory_util,
            tensor_parallel_size=1
        )
        
        print(f'✅ Model loading with {memory_util} GPU memory: PASSED')
        del llm  # Free memory
        
    except Exception as e:
        print(f'❌ Model loading with {memory_util} GPU memory: FAILED - {e}')
        continue
"
```

### Multi-Model Support Test

```bash
# Test multiple model support
python -c "
from configs.vllm_settings import load_vllm_settings

print('=== Multi-Model Support Test ===')

_, model_settings, _ = load_vllm_settings()

print(f'Supported models: {len(model_settings.supported_models)}')
for i, model in enumerate(model_settings.supported_models[:3]):  # Test first 3
    print(f'  {i+1}. {model}')

print('\\n✅ Model configuration loaded successfully')
print(f'Default download timeout: {model_settings.download_timeout}s')
print(f'Max context length: {model_settings.max_context_length}')
"
```

## Validation Results

### Generate Validation Report

```bash
# Generate comprehensive validation report
python -c "
import sys
from datetime import datetime
from configs.vllm_settings import load_vllm_settings

print('=== PLANB-05 vLLM Validation Report ===')
print(f'Generated: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print()

# Configuration summary
try:
    install_settings, model_settings, test_settings = load_vllm_settings()
    print('Configuration Status: ✅ LOADED')
    print(f'  Environment: {install_settings.dev_env_path}')
    print(f'  GPU Memory: {install_settings.gpu_memory_utilization}')
    print(f'  Tensor Parallel: {install_settings.tensor_parallel_size}')
    print(f'  Test Model: {test_settings.test_model}')
except Exception as e:
    print(f'Configuration Status: ❌ FAILED - {e}')

print()

# Import status
try:
    import vllm, torch, transformers
    print('Import Status: ✅ SUCCESS')
    print(f'  vLLM: {vllm.__version__}')
    print(f'  PyTorch: {torch.__version__}')
    print(f'  Transformers: {transformers.__version__}')
    print(f'  CUDA: {torch.cuda.is_available()}')
except Exception as e:
    print(f'Import Status: ❌ FAILED - {e}')
"
```

## Troubleshooting Validation Issues

### Common Validation Failures

1. **Configuration Loading Fails**
   ```bash
   # Check .env file
   ls -la .env
   head -5 .env
   
   # Validate environment variables
   python -c "import os; print([k for k in os.environ.keys() if 'HF_' in k or 'CUDA_' in k])"
   ```

2. **CUDA Not Available**
   ```bash
   # Check NVIDIA setup
   nvidia-smi
   nvcc --version
   echo $CUDA_HOME
   
   # Reinstall PyTorch with CUDA
   pip uninstall torch torchvision torchaudio -y
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
   ```

3. **Model Loading Fails**
   ```bash
   # Check disk space and memory
   df -h
   free -h
   
   # Reduce GPU memory utilization
   # Edit .env: GPU_MEMORY_UTILIZATION=0.3
   ```

4. **Performance Below Expectations**
   ```bash
   # Check GPU utilization
   nvidia-smi
   
   # Verify Flash Attention installation
   python -c "import flash_attn; print('Flash Attention available')" 2>/dev/null || echo "Flash Attention not available"
   ```

## Validation Checklist

Complete validation checklist:

- [ ] ✅ Configuration management system functional
- [ ] ✅ vLLM imports successfully with correct version
- [ ] ✅ CUDA available and GPU accessible
- [ ] ✅ All dependencies installed and compatible
- [ ] ✅ Hugging Face authentication working
- [ ] ✅ Basic model loading and generation functional
- [ ] ✅ Performance meets minimum requirements
- [ ] ✅ API server starts and responds to health checks
- [ ] ✅ Client can connect and receive responses
- [ ] ✅ Multi-model configuration loaded
- [ ] ✅ Error handling and rollback procedures tested

## Next Steps

After successful validation:
- **[PLANB-06-Storage-Symlinks.md](PLANB-06-Storage-Symlinks.md)** for storage configuration
- **[PLANB-05d-vLLM-Troubleshooting.md](PLANB-05d-vLLM-Troubleshooting.md)** if issues persist

---

**Status**: ✅ **Validation Complete**  
**Estimated Time**: 20-30 minutes  
**Complexity**: Medium  
**Critical**: Comprehensive validation ensures production readiness