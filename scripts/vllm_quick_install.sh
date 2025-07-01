#!/bin/bash
# PLANB-05: Quick vLLM Installation (15-30 minutes)

set -euo pipefail

DEV_ENV_PATH="/opt/citadel/dev-env"
HF_TOKEN="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"

echo "🚀 PLANB-05 Quick vLLM Installation"
echo "=================================="

# Activate environment and install vLLM with all dependencies
source "$DEV_ENV_PATH/bin/activate" && \
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
    py3nvml>=0.2.7

# Configure HF authentication
echo "$HF_TOKEN" | huggingface-cli login --token

# Verify installation
echo "=== Installation Verification ==="
python -c "import vllm; print(f'✅ vLLM version: {vllm.__version__}')"
python -c "import torch; print(f'✅ PyTorch: {torch.__version__}')"
python -c "import transformers; print(f'✅ Transformers: {transformers.__version__}')"
python -c "import torch; print(f'✅ CUDA available: {torch.cuda.is_available()}')"
echo "🎉 Quick installation completed successfully!"