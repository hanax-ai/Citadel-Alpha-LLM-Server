# PLANB-05: Model Catalog and Configuration Guide

**Document Type:** Model Reference and Configuration Guide  
**Created:** July 1, 2025  
**Purpose:** Comprehensive catalog of all models used in Citadel Alpha LLM Server  

## Overview

This document provides a complete catalog of all language models supported, tested, and configured for use with the Citadel Alpha LLM Server implementation. Models are categorized by size, capability, and use case to facilitate optimal deployment decisions.

## Model Categories

### Testing and Validation Models

#### Small Test Models
Used for installation validation, testing, and development purposes.

| Model | Size | Purpose | Memory Req. | Notes |
|-------|------|---------|-------------|-------|
| `facebook/opt-125m` | 125M | Primary test model | ~500MB | Default validation model |
| `facebook/opt-350m` | 350M | Extended testing | ~1.5GB | Alternative test model |
| `microsoft/DialoGPT-small` | 117M | Conversation testing | ~500MB | Dialog validation |

**Configuration:**
```yaml
test_models:
  primary: "facebook/opt-125m"
  secondary: "facebook/opt-350m"
  dialog: "microsoft/DialoGPT-small"
```

### Production-Ready Models

#### Small to Medium Models (< 10B parameters)
Suitable for development, prototyping, and resource-constrained deployments.

| Model | Size | Specialty | Memory Req. | Use Case |
|-------|------|-----------|-------------|----------|
| `microsoft/Phi-3-mini-4k-instruct` | 3.8B | Instruction following | ~8GB | General purpose, fast inference |
| `openchat/openchat-3.5-0106` | 7B | Conversational AI | ~14GB | Chat applications |
| `MILVLG/imp-v1-3b` | 3B | Multimodal (VL) | ~6GB | Vision-language tasks |

**Key Features:**
- Fast inference times
- Lower GPU memory requirements
- Suitable for real-time applications
- Good for development and testing

#### Large Models (10B+ parameters)
High-capability models for production workloads requiring maximum performance.

| Model | Size | Specialty | Memory Req. | Use Case |
|-------|------|-----------|-------------|----------|
| `mistralai/Mixtral-8x7B-Instruct-v0.1` | 8x7B MoE | General instruction | ~24GB | Multi-domain expertise |
| `01-ai/Yi-34B-Chat` | 34B | Conversational AI | ~68GB | Advanced chat applications |
| `NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO` | 8x7B MoE | Instruction + DPO | ~24GB | High-quality responses |
| `deepseek-ai/deepseek-coder-14b-instruct-v1.5` | 14B | Code generation | ~28GB | Programming assistance |

**Hardware Requirements:**
- Minimum 32GB VRAM (RTX 4070 Ti SUPER dual setup)
- Recommended tensor parallelism for 34B+ models
- High-speed storage for model loading

## Model Configuration Matrix

### Performance Characteristics

```yaml
performance_profiles:
  opt-125m:
    throughput: "50+ req/s"
    latency: "< 100ms"
    memory: "500MB"
    
  phi-3-mini:
    throughput: "20+ req/s"
    latency: "< 200ms"
    memory: "8GB"
    
  mixtral-8x7b:
    throughput: "5-10 req/s"
    latency: "< 500ms"
    memory: "24GB"
    
  yi-34b:
    throughput: "2-5 req/s"
    latency: "< 1000ms"
    memory: "68GB"
```

### GPU Memory Optimization

| Model Size | Single GPU (16GB) | Dual GPU (32GB) | Recommended Config |
|------------|------------------|-----------------|-------------------|
| < 1B | ✅ gpu_mem=0.3 | ✅ gpu_mem=0.2 | Single GPU |
| 1B-7B | ✅ gpu_mem=0.7 | ✅ gpu_mem=0.4 | Single GPU |
| 7B-15B | ❌ | ✅ gpu_mem=0.7 | Single GPU, high memory |
| 15B+ | ❌ | ✅ tensor_parallel=2 | Dual GPU required |

## Model Access and Authentication

### Hugging Face Integration

All models require proper Hugging Face authentication and configuration:

```bash
# Environment variables required
HF_TOKEN=hf_your_token_here
HF_HOME=/mnt/citadel-models/cache
TRANSFORMERS_CACHE=/mnt/citadel-models/cache/transformers
```

### Model-Specific Access

| Model | Access Type | License | Special Requirements |
|-------|------------|---------|---------------------|
| Facebook OPT models | Public | MIT-like | None |
| Microsoft Phi-3 | Public | MIT | None |
| Mixtral models | Public | Apache 2.0 | None |
| Yi models | Gated | Custom | HF approval required |
| Nous Hermes | Public | Apache 2.0 | None |
| DeepSeek Coder | Public | Custom | Commercial use restrictions |

## Deployment Configurations

### Standard Deployment Profiles

#### Development Profile
```yaml
profile: development
models:
  - facebook/opt-125m
  - microsoft/Phi-3-mini-4k-instruct
gpu_memory_utilization: 0.3
tensor_parallel_size: 1
port_range: 8000-8010
```

#### Production Profile
```yaml
profile: production
models:
  - mistralai/Mixtral-8x7B-Instruct-v0.1
  - openchat/openchat-3.5-0106
  - deepseek-ai/deepseek-coder-14b-instruct-v1.5
gpu_memory_utilization: 0.7
tensor_parallel_size: 1
port_range: 11400-11500
```

#### High-Capacity Profile
```yaml
profile: high_capacity
models:
  - 01-ai/Yi-34B-Chat
  - NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO
gpu_memory_utilization: 0.8
tensor_parallel_size: 2
port_range: 11400-11500
```

## Model Loading and Caching

### Storage Requirements

```yaml
storage_allocation:
  test_models: "2GB"
  small_models: "50GB"
  large_models: "200GB"
  cache_buffer: "100GB"
  total_recommended: "352GB"
```

### Cache Management

Models are cached in the configured directory structure:
```
/mnt/citadel-models/
├── cache/
│   ├── transformers/          # Transformers library cache
│   ├── hub/                   # HuggingFace hub cache
│   └── temp/                  # Temporary download cache
├── models/                    # Local model storage
└── configs/                   # Model-specific configurations
```

## Performance Benchmarks

### Throughput Benchmarks (RTX 4070 Ti SUPER)

| Model | Batch Size 1 | Batch Size 4 | Batch Size 8 | Max Context |
|-------|--------------|--------------|--------------|-------------|
| facebook/opt-125m | 50 req/s | 120 req/s | 200 req/s | 2048 |
| microsoft/Phi-3-mini | 20 req/s | 40 req/s | 60 req/s | 4096 |
| openchat/openchat-3.5 | 8 req/s | 15 req/s | 25 req/s | 8192 |
| mistralai/Mixtral-8x7B | 5 req/s | 8 req/s | 12 req/s | 32768 |

*Benchmarks measured with 50-token responses, GPU memory utilization 0.7*

## Model Selection Guidelines

### Use Case Mapping

#### For Development and Testing
- **Primary:** `facebook/opt-125m`
- **Secondary:** `microsoft/Phi-3-mini-4k-instruct`
- **Reasoning:** Fast loading, low resource usage, reliable performance

#### For General Purpose Applications
- **Recommended:** `openchat/openchat-3.5-0106`
- **Alternative:** `microsoft/Phi-3-mini-4k-instruct`
- **Reasoning:** Good balance of capability and performance

#### For Specialized Tasks

**Code Generation:**
- **Primary:** `deepseek-ai/deepseek-coder-14b-instruct-v1.5`
- **Fallback:** `microsoft/Phi-3-mini-4k-instruct`

**High-Quality Conversations:**
- **Primary:** `NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO`
- **High-end:** `01-ai/Yi-34B-Chat`

**Multi-Domain Expertise:**
- **Primary:** `mistralai/Mixtral-8x7B-Instruct-v0.1`
- **Reasoning:** Mixture of Experts architecture provides broad knowledge

## Configuration Integration

### With vLLM Settings

Models integrate with the configuration management system:

```python
from configs.vllm_settings import load_vllm_settings

install_settings, model_settings, test_settings = load_vllm_settings()

# Supported models from configuration
supported_models = model_settings.supported_models
test_model = test_settings.test_model
```

### Environment-Specific Overrides

```yaml
# Development environment
models:
  default: "facebook/opt-125m"
  alternatives: ["microsoft/Phi-3-mini-4k-instruct"]

# Production environment  
models:
  default: "mistralai/Mixtral-8x7B-Instruct-v0.1"
  alternatives: ["openchat/openchat-3.5-0106", "deepseek-ai/deepseek-coder-14b-instruct-v1.5"]
```

## Operational Procedures

### Model Health Monitoring

Regular health checks should verify:
- Model loading times
- Memory utilization
- Inference throughput
- Response quality

### Model Rotation Strategy

For production deployments:
1. **Primary Model:** High-capability model for main workload
2. **Fallback Model:** Smaller, faster model for high-load periods
3. **Test Model:** Always available for health checks

### Backup and Recovery

Critical models should be:
- Cached locally in `/mnt/citadel-models/`
- Backed up to secondary storage
- Verified through regular integrity checks

## Future Model Integration

### Planned Additions

Models under evaluation for future integration:
- Latest Llama 3 variants
- Updated Mixtral models
- Specialized domain models
- Multimodal capabilities

### Integration Process

1. Evaluate model compatibility with vLLM
2. Test with existing hardware configuration
3. Benchmark performance against current models
4. Update configuration files
5. Document in this catalog

---

**Maintenance:** This document should be updated when new models are added, performance characteristics change, or hardware configuration is modified.

**Last Updated:** July 1, 2025  
**Next Review:** August 1, 2025