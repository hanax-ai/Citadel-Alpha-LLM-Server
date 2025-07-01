# Citadel AI OS Plan B - LLM Server Implementation Guide

**Version:** 6.0
**Target OS:** Ubuntu Server 24.04 LTS
**Python Version:** 3.12
**NVIDIA Driver:** 570.x series
**Last Updated:** July 1, 2025

## Project Purpose

Citadel AI OS Plan B establishes a production-ready **Large Language Model (LLM) inference server** optimized for:
- High-performance model serving with vLLM framework
- Multi-GPU acceleration (RTX 4070 Ti SUPER)
- Enterprise-grade reliability and monitoring
- Integration with Hana-X Lab AI infrastructure ecosystem

## Overview

This Plan B provides a complete fresh installation guide for **LLM inference server deployment** with updated specifications:

- **Operating System**: Ubuntu Server 24.04 LTS (fresh installation)
- **Python**: 3.12 with latest vLLM compatibility (0.6.1+)
- **NVIDIA**: Driver 570.x series with CUDA 12.4+
- **Storage**: Dedicated 3.6TB NVMe for models with backup configuration
- **Architecture**: Updated for modern LLM workloads and GPU optimization

## Deployment Environment

**Target Environment**: Hana-X Lab
**Target Server**: dev-ops (192.168.10.36) - LLM Inference Server
**Network**: 192.168.10.0/24
**User Account**: agent0
**Operating System**: Ubuntu Server 24.04 LTS
**Role**: Large Language Model Inference Server (vLLM + GPU acceleration)

### Hana-X Lab Network Topology

```
Network Layout (192.168.10.0/24):
├── 192.168.10.50 - hana-x-jr0     # Windows Admin Workstation (ThinkPad)
├── 192.168.10.33 - dev            # AI Development Node
├── 192.168.10.29 - llm            # LLM Foundation Model Node
├── 192.168.10.30 - vectordb       # Vector Database + Embedding Server
├── 192.168.10.31 - orca           # Agent Simulation & Orchestration Node
├── 192.168.10.34 - qa             # QA/Test Server
├── 192.168.10.36 - dev-ops        # LLM Inference Server (TARGET)
├── 192.168.10.35 - db             # PostgreSQL Database Server
└── 192.168.10.19 - agent0         # Agent Workstation (Desktop)
```

**Hardware Specifications (Target Server: dev-ops)**
- **Model**: Dell Precision 3630 Tower
- **OS**: Ubuntu 24.04.2 LTS
- **Kernel**: Linux 6.11.0-26-generic
- **Architecture**: x86-64
- **Network Interface**: eno1 (192.168.10.36/24)
- **GPU**: RTX 4070 Ti SUPER (32GB VRAM)
- **RAM**: 128GB (Large context processing and multi-model serving)

### Hardware Optimization Rationale
- **32GB VRAM (RTX 4070 Ti SUPER)**: Enables serving 34B parameter models
- **3.6TB NVMe Model Storage**: Fast model loading and caching
- **128GB RAM**: Large context processing and multi-model serving

## Storage Configuration

```
Device Map:
├── nvme0n1 (Primary NVMe - OS)
│   ├── nvme0n1p1 (1G vfat)     → /boot/efi
│   ├── nvme0n1p2 (2G ext4)     → /boot
│   └── nvme0n1p3 (3.6T LVM)    → / (Root FS - 100G allocated)
├── nvme1n1 (3.6T ext4)         → /mnt/citadel-models (Model Storage)
├── sda (7.3T ext4)             → /mnt/citadel-backup (Backup/General Storage)
└── sdb1 (58.6G vfat USB)       → Ubuntu Server Installation Media
```

## LLM Server Capabilities

### Supported Models
- **Large Models**: Mixtral 8x7B, Yi-34B, Nous Hermes 2, OpenChat 3.5
- **Specialized Models**: Phi-3 Mini, DeepCoder 14B, MiMo VL 7B
- **Custom Models**: Model loading via Hugging Face integration with HF token automation
- **Framework**: vLLM 0.6.1+ with Python 3.12 compatibility

### API Endpoints
- **OpenAI-compatible REST API**: Ports 11400-11500 range
- **Health Monitoring**: `/health` and `/metrics` endpoints
- **Real-time Inference**: Streaming support with GPU acceleration
- **Model Management**: Dynamic model loading and unloading capabilities

### Service Architecture
- **vLLM Framework**: Latest version (0.6.1+) with enhanced performance
- **GPU Acceleration**: Optimized for RTX 4070 Ti SUPER
- **Environment Integration**: Uses `/opt/citadel/dev-env` per Plan B standards
- **Authentication**: Integrated Hugging Face token management

## Installation Tasks

1. **[PLANB-01] Fresh Ubuntu Server 24.04 Installation**
2. **[PLANB-02] Storage Configuration and Mounting**
3. **[PLANB-03] NVIDIA 570.x Driver Installation**
4. **[PLANB-04] Python 3.12 Environment Setup**
5. **[PLANB-05] Latest vLLM Installation with Compatibility** ⭐ **READY FOR DEPLOYMENT**
6. **[PLANB-06] Model Storage Symlink Configuration**
7. **[PLANB-07] Service Configuration and Testing**
8. **[PLANB-08] Backup and Monitoring Setup**

### PLANB-05 Implementation Status: 🟢 **DEPLOYMENT READY**

The vLLM implementation package has been **thoroughly reviewed and validated** with comprehensive scripts:

- ✅ **5 Production-Ready Scripts** extracted and organized in [`/scripts/`](scripts/)
- ✅ **Comprehensive Testing Suite** with 6-layer validation
- ✅ **Multiple Installation Options**: Quick (15-30 min) and detailed (60-90 min)
- ✅ **Full Compliance**: All scripts under 500-line limit per project standards

## Key Improvements from Previous Version

- ✅ **LLM Optimization**: Dedicated vLLM 0.6.1+ with Python 3.12 compatibility resolution
- ✅ **Storage Optimization**: 3.6TB NVMe SSD for models with symlink integration
- ✅ **GPU Acceleration**: RTX 4070 Ti SUPER optimization for 34B parameter models
- ✅ **OS Modernization**: Ubuntu Server 24.04 with latest security updates
- ✅ **Python Upgrade**: Python 3.12 for enhanced performance and vLLM compatibility
- ✅ **Driver Update**: NVIDIA 570.x for latest GPU optimizations
- ✅ **HF Integration**: Automated Hugging Face token setup and model management
- ✅ **Service Architecture**: OpenAI-compatible API with comprehensive monitoring
- ✅ **Backup Strategy**: Integrated backup solution with 7.3TB storage
- ✅ **Production Readiness**: Enhanced validation with 6-layer testing suite

## Directory Structure

```
Citadel-Alpha-LLM-Server-1/
├── README.md                           # This LLM server implementation guide
├── planning/                           # Implementation planning and analysis
│   ├── ASSIGNMENT-REPORT.md           # Implementation readiness report
│   ├── README-ANALYSIS-ASSESSMENT.md  # Documentation review and recommendations
│   ├── PLANB-05-IMPLEMENTATION-GUIDE.md   # Comprehensive vLLM implementation (978 lines)
│   └── PLANB-05-IMPLEMENTATION-SUMMARY.md # Implementation summary (197 lines)
├── tasks/                              # Individual installation tasks
│   ├── PLANB-01-Ubuntu-Installation.md
│   ├── PLANB-02-Storage-Configuration.md
│   ├── PLANB-03-NVIDIA-Driver-Setup.md
│   ├── PLANB-04-Python-Environment.md
│   ├── PLANB-05-vLLM-Installation.md
│   ├── PLANB-06-Storage-Symlinks.md
│   ├── PLANB-07-Service-Configuration.md
│   ├── PLANB-08-Backup-Monitoring.md
│   └── task-results/                   # Task completion documentation
├── scripts/                            # Production-ready installation scripts ⭐
│   ├── vllm_latest_installation.sh     # Main installation (382 lines) - Interactive
│   ├── vllm_quick_install.sh          # Quick installation (34 lines) - Fast deployment
│   ├── test_vllm_installation.py      # Comprehensive testing (197 lines) - 6-layer validation
│   ├── start_vllm_server.py           # Server management (66 lines) - OpenAI API
│   └── test_vllm_client.py            # Client testing (83 lines) - API validation
├── configs/                            # Configuration files
│   ├── systemd-services/
│   └── [Configuration files as needed]
└── validation/                         # Testing and validation
    └── planb_05_pre_install_validation.py  # Pre-installation validation
```

## Quick Start

### For LLM Server Deployment:

1. **Follow tasks PLANB-01 through PLANB-08 in sequence**
2. **PLANB-05 vLLM Installation - READY FOR IMMEDIATE DEPLOYMENT:**
   - **Quick Path** (15-30 min): [`./scripts/vllm_quick_install.sh`](scripts/vllm_quick_install.sh)
   - **Detailed Path** (60-90 min): [`./scripts/vllm_latest_installation.sh`](scripts/vllm_latest_installation.sh)
   - **Comprehensive Testing**: [`./scripts/test_vllm_installation.py`](scripts/test_vllm_installation.py)

3. **Installation Options:**
   - All scripts are production-ready in [`scripts/`](scripts/) directory
   - Configuration files available in [`configs/`](configs/)
   - Validation tools in [`validation/`](validation/)
   - Comprehensive documentation in [`planning/`](planning/)

### Implementation Readiness Status:
- 🟢 **PLANB-05**: Complete with 5 validated scripts and comprehensive testing
- 🔄 **PLANB-01-04**: Sequential prerequisites
- 🔄 **PLANB-06-08**: Service integration and monitoring

## Support and Troubleshooting

Each task includes:
- Prerequisites check
- Step-by-step instructions
- Validation procedures
- Troubleshooting guide
- Rollback procedures

### Enhanced vLLM Implementation Support:
- **Pre-Implementation Validation**: Enhanced checking protocols
- **Multiple Installation Paths**: Quick and detailed options with full control
- **6-Layer Testing Suite**: Comprehensive validation and performance benchmarking
- **Production Readiness**: Full compliance with Plan B architecture standards
- **Rollback Procedures**: Complete recovery options for risk mitigation

## Production Readiness Features

- **Service Integration**: OpenAI-compatible API with health monitoring
- **Model Management**: Dynamic loading with Hugging Face integration
- **Performance Optimization**: GPU acceleration and memory management
- **Monitoring**: Comprehensive metrics and health check endpoints
- **Backup and Recovery**: Integrated with 7.3TB backup storage
- **Security**: Appropriate access controls for dev/test environment

---

**Ready to begin LLM server deployment? Start with [PLANB-01-Ubuntu-Installation.md](tasks/PLANB-01-Ubuntu-Installation.md)**

**For immediate vLLM deployment: Review [PLANB-05 Implementation Guide](planning/PLANB-05-IMPLEMENTATION-GUIDE.md) and execute scripts in [/scripts/](scripts/)**