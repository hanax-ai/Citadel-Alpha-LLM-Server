# Citadel AI OS Plan B - Complete Installation Guide

**Version:** 5.0  
**Target OS:** Ubuntu Server 24.04 LTS  
**Python Version:** 3.12  
**NVIDIA Driver:** 570.x series  
**Last Updated:** June 30, 2025

## Overview

This Plan B provides a complete fresh installation guide for Citadel AI OS with updated specifications:

- **Operating System**: Ubuntu Server 24.04 LTS (fresh installation)
- **Python**: 3.12 with latest vLLM compatibility
- **NVIDIA**: Driver 570.x series with CUDA 12.4+
- **Storage**: Dedicated 4TB SSD for models with backup configuration
- **Architecture**: Updated for modern hardware and software stack

## Deployment Environment

**Target Environment**: Hana-X Lab
**Target Server**: db (192.168.10.35) - PostgreSQL Database Server
**Network**: 192.168.10.0/24
**User Account**: agent0
**Operating System**: Ubuntu Server 24.04 LTS

### Hana-X Lab Network Topology

```
Network Layout (192.168.10.0/24):
├── 192.168.10.50 - hana-x-jr0     # Windows Admin Workstation (ThinkPad)
├── 192.168.10.33 - dev            # AI Development Node
├── 192.168.10.29 - llm            # LLM Foundation Model Node
├── 192.168.10.30 - vectordb       # Vector Database + Embedding Server
├── 192.168.10.31 - orca           # Agent Simulation & Orchestration Node
├── 192.168.10.34 - qa             # QA/Test Server
├── 192.168.10.36 - dev-ops        # CI/CD + Monitoring Node
├── 192.168.10.35 - db             # PostgreSQL Database Server (TARGET)
└── 192.168.10.19 - agent0         # Agent Workstation (Desktop)
```

**Hardware Specifications (Target Server: db)**
- **Model**: Dell Precision 3630 Tower
- **OS**: Ubuntu 24.04.2 LTS
- **Kernel**: Linux 6.11.0-26-generic
- **Architecture**: x86-64
- **Network Interface**: eno1 (192.168.10.35/24)

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

## Installation Tasks

1. **[PLANB-01] Fresh Ubuntu Server 24.04 Installation**
2. **[PLANB-02] Storage Configuration and Mounting**
3. **[PLANB-03] NVIDIA 570.x Driver Installation**
4. **[PLANB-04] Python 3.12 Environment Setup**
5. **[PLANB-05] Latest vLLM Installation with Compatibility**
6. **[PLANB-06] Model Storage Symlink Configuration**
7. **[PLANB-07] Service Configuration and Testing**
8. **[PLANB-08] Backup and Monitoring Setup**

## Key Improvements from Previous Version

- ✅ **Storage Optimization**: Dedicated SSD for models with symlink integration
- ✅ **OS Modernization**: Ubuntu Server 24.04 with latest security updates
- ✅ **Python Upgrade**: Python 3.12 for better performance and compatibility
- ✅ **Driver Update**: NVIDIA 570.x for latest GPU optimizations
- ✅ **vLLM Compatibility**: Latest vLLM version with proper PyTorch alignment
- ✅ **Backup Strategy**: Integrated backup solution with 7.3TB storage
- ✅ **Auto-mounting**: Persistent storage mounts with fstab configuration

## Directory Structure

```
Plan B/
├── README.md                           # This overview document
├── tasks/                              # Individual installation tasks
│   ├── PLANB-01-Ubuntu-Installation.md
│   ├── PLANB-02-Storage-Configuration.md
│   ├── PLANB-03-NVIDIA-Driver-Setup.md
│   ├── PLANB-04-Python-Environment.md
│   ├── PLANB-05-vLLM-Installation.md
│   ├── PLANB-06-Storage-Symlinks.md
│   ├── PLANB-07-Service-Configuration.md
│   └── PLANB-08-Backup-Monitoring.md
├── scripts/                            # Installation scripts
│   ├── ubuntu-post-install.sh
│   ├── storage-setup.sh
│   ├── nvidia-570-install.sh
│   ├── python312-setup.sh
│   ├── vllm-latest-install.sh
│   ├── symlink-setup.sh
│   ├── service-setup.sh
│   └── backup-config.sh
├── configs/                            # Configuration files
│   ├── fstab.citadel
│   ├── vllm-latest.yaml
│   ├── systemd-services/
│   └── nginx-proxy.conf
└── validation/                         # Testing and validation
    ├── system-validation.py
    ├── storage-test.py
    ├── model-benchmark.py
    └── integration-test.py
```

## Quick Start

1. Follow tasks PLANB-01 through PLANB-08 in sequence
2. Each task includes validation steps
3. All scripts are in the `scripts/` directory
4. Configuration files are in `configs/`
5. Validation tools are in `validation/`

## Support and Troubleshooting

Each task includes:
- Prerequisites check
- Step-by-step instructions
- Validation procedures
- Troubleshooting guide
- Rollback procedures

---

**Ready to begin? Start with [PLANB-01-Ubuntu-Installation.md](tasks/PLANB-01-Ubuntu-Installation.md)**