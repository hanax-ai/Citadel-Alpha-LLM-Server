#!/bin/bash
# PLANB-05: Quick vLLM Installation with Configuration Management

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "🚀 PLANB-05 Quick vLLM Installation"
echo "Project root: $PROJECT_ROOT"
echo "=================================="

# Load configuration and set environment variables
echo "Loading configuration..."
python3 -c "
import sys
import os
sys.path.insert(0, '$PROJECT_ROOT')

from configs.vllm_settings import load_vllm_settings, get_environment_variables

try:
    # Load settings
    install_settings, model_settings, test_settings = load_vllm_settings()
    print(f'✅ Configuration loaded successfully')
    print(f'Environment path: {install_settings.dev_env_path}')
    
    # Generate environment setup
    env_vars = get_environment_variables(install_settings)
    
    # Export environment variables for bash
    for key, value in env_vars.items():
        print(f'export {key}=\"{value}\"')
    
    print(f'export DEV_ENV_PATH=\"{install_settings.dev_env_path}\"')
    
except Exception as e:
    print(f'❌ Configuration failed: {e}', file=sys.stderr)
    print('Please ensure .env file exists with required variables', file=sys.stderr)
    sys.exit(1)
" > /tmp/vllm_env_setup.sh

if [ $? -ne 0 ]; then
    echo "❌ Configuration loading failed"
    exit 1
fi

# Source the environment setup
source /tmp/vllm_env_setup.sh

# Verify environment path exists
if [ ! -d "$DEV_ENV_PATH" ]; then
    echo "❌ Development environment not found: $DEV_ENV_PATH"
    echo "Please ensure PLANB-04 is completed first"
    exit 1
fi

# Activate environment and install vLLM with all dependencies
echo "Activating environment: $DEV_ENV_PATH"
source "$DEV_ENV_PATH/bin/activate"

echo "Installing vLLM and dependencies..."
pip install vllm && \
pip install \
    transformers>=4.36.0 \
    tokenizers>=0.15.0 \
    accelerate>=0.25.0 \
    bitsandbytes>=0.41.0 \
    scipy>=1.11.0 \
    numpy>=1.24.0 \
    requests>=2.31.0 \
    aiohttp>=3.9.0 \
    fastapi>=0.104.0 \
    uvicorn>=0.24.0 \
    pydantic>=2.5.0 \
    huggingface-hub>=0.19.0 && \
pip install \
    prometheus-client>=0.19.0 \
    psutil>=5.9.0 \
    GPUtil>=1.4.0 \
    py3nvml>=0.2.7 \
    rich>=13.7.0

# Configure HF authentication using environment variable
echo "Configuring Hugging Face authentication..."
if [ -n "$HF_TOKEN" ]; then
    echo "$HF_TOKEN" | huggingface-cli login --token
    echo "✅ Hugging Face authentication configured"
else
    echo "⚠️ HF_TOKEN not set, skipping authentication"
fi

# Verify installation using configuration
echo "=== Installation Verification ==="
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')

from configs.vllm_settings import load_vllm_settings

try:
    # Load settings for verification
    install_settings, model_settings, test_settings = load_vllm_settings()
    
    # Test imports and versions
    import vllm
    import torch
    import transformers
    import fastapi
    
    print(f'✅ vLLM version: {vllm.__version__}')
    print(f'✅ PyTorch: {torch.__version__}')
    print(f'✅ Transformers: {transformers.__version__}')
    print(f'✅ FastAPI: {fastapi.__version__}')
    print(f'✅ CUDA available: {torch.cuda.is_available()}')
    
    if torch.cuda.is_available():
        print(f'✅ GPU count: {torch.cuda.device_count()}')
        for i in range(torch.cuda.device_count()):
            print(f'  GPU {i}: {torch.cuda.get_device_name(i)}')
    
    print('✅ Configuration integration verified')
    print(f'Test model: {test_settings.test_model}')
    print(f'GPU memory utilization: {install_settings.gpu_memory_utilization}')
    
except Exception as e:
    print(f'❌ Verification failed: {e}')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "🎉 Quick installation completed successfully!"
    echo "Next step: Run validation tests with 'python tests/validation/test_vllm_installation.py'"
else
    echo "❌ Installation verification failed"
    exit 1
fi

# Cleanup
rm -f /tmp/vllm_env_setup.sh