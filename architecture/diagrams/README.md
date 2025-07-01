# Architecture Diagrams
**Citadel Alpha LLM Server - Visual Architecture Reference**

This directory contains comprehensive Mermaid diagrams illustrating the complete architecture and component interactions of the Citadel Alpha LLM Server.

## Diagram Overview

| Diagram | File | Purpose | Key Components |
|---------|------|---------|----------------|
| **System Overview** | [`01-system-overview.mermaid`](01-system-overview.mermaid) | Complete system architecture | Client → Service → vLLM → GPU → Storage layers |
| **Service Interactions** | [`02-service-interactions.mermaid`](02-service-interactions.mermaid) | SystemD service relationships | Service dependencies, health monitoring, configuration |
| **Data Flow** | [`03-data-flow.mermaid`](03-data-flow.mermaid) | Request processing pipeline | Request → Processing → GPU → Response flow |
| **Storage Architecture** | [`04-storage-architecture.mermaid`](04-storage-architecture.mermaid) | Multi-tier storage system | NVMe/HDD, symlinks, backups, cache integration |
| **Monitoring** | [`05-monitoring-architecture.mermaid`](05-monitoring-architecture.mermaid) | Observability stack | Prometheus, Grafana, alerting, metrics collection |
| **Configuration** | [`06-configuration-deployment.mermaid`](06-configuration-deployment.mermaid) | Config management & deployment | Pydantic settings, validation, deployment pipeline |
| **Network Topology** | [`07-network-topology.mermaid`](07-network-topology.mermaid) | Network architecture | Hana-X Lab network, ports, security, endpoints |

## Diagram Usage

### For Engineering Teams
- **New Team Members**: Start with [`01-system-overview.mermaid`](01-system-overview.mermaid)
- **DevOps Engineers**: Focus on [`02-service-interactions.mermaid`](02-service-interactions.mermaid) and [`06-configuration-deployment.mermaid`](06-configuration-deployment.mermaid)
- **ML Engineers**: Study [`03-data-flow.mermaid`](03-data-flow.mermaid) and [`01-system-overview.mermaid`](01-system-overview.mermaid)
- **System Administrators**: Review [`04-storage-architecture.mermaid`](04-storage-architecture.mermaid) and [`05-monitoring-architecture.mermaid`](05-monitoring-architecture.mermaid)
- **Network Engineers**: Examine [`07-network-topology.mermaid`](07-network-topology.mermaid)

### Viewing Diagrams

#### Option 1: Mermaid Live Editor
1. Copy diagram content from any `.mermaid` file
2. Paste into [Mermaid Live Editor](https://mermaid.live/)
3. View interactive, zoomable diagram

#### Option 2: VSCode Mermaid Extension
1. Install "Mermaid Markdown Syntax Highlighting" extension
2. Open `.mermaid` files directly in VSCode
3. Use preview mode for rendered diagrams

#### Option 3: GitHub Integration
- GitHub automatically renders Mermaid diagrams in markdown files
- View diagrams directly in repository browser

## Diagram Conventions

### Color Coding
- **Blue (#e1f5fe)**: Client/External layers
- **Purple (#f3e5f5)**: Service/Application layers  
- **Orange (#fff3e0)**: Processing/Engine layers
- **Green (#e8f5e8)**: Storage/Infrastructure layers
- **Yellow (#fff8e1)**: Monitoring/Observability layers
- **Pink (#ffebee)**: Configuration/Management layers

### Connection Types
- **Solid Lines**: Direct dependencies or data flow
- **Dashed Lines**: Logical relationships or occasional interactions
- **Dotted Lines**: Configuration or monitoring relationships

### Node Annotations
- **Service Ports**: Explicitly shown (e.g., `Port 11400`)
- **Resource Specs**: Hardware specifications included
- **Path References**: File system paths and symlinks
- **IP Addresses**: Network endpoints specified

## Integration with Documentation

These diagrams complement the comprehensive architecture documentation:

- **[System Overview](../LLM-Server-Architecture-Overview.md)**: References diagrams 01, 02, 07
- **[vLLM Framework](../vLLM-Framework-Architecture.md)**: References diagrams 01, 03
- **[Service Architecture](../Service-Architecture.md)**: References diagrams 02, 05, 06
- **[Storage Architecture](../Storage-Architecture.md)**: References diagrams 04
- **[Engineering Onboarding](../Engineering-Team-Onboarding.md)**: References all diagrams

## Maintenance Guidelines

### Updating Diagrams
1. **Architecture Changes**: Update diagrams when system architecture evolves
2. **Component Additions**: Add new components to relevant diagrams
3. **Port Changes**: Update port allocations in network and service diagrams
4. **Configuration Updates**: Reflect configuration changes in deployment diagram

### Consistency Requirements
- **Naming**: Use consistent component names across all diagrams
- **Color Schemes**: Maintain color coding conventions
- **Reference Accuracy**: Ensure file paths and ports match implementation
- **Documentation Sync**: Keep diagrams aligned with architecture documents

## Quick Reference

### System Components
- **vLLM Services**: Ports 11400-11500 (model-specific)
- **Health Checks**: Ports 8000-8001  
- **Monitoring**: Ports 9090 (Prometheus), 3000 (Grafana), 9093 (AlertManager)
- **Storage**: 3.6TB NVMe (`/mnt/citadel-models`), 7.3TB HDD (`/mnt/citadel-backup`)
- **Network**: 192.168.10.36 (Hana-X Lab)

### Key Integrations
- **GPU**: NVIDIA RTX 4070 Ti SUPER (16GB VRAM)
- **Framework**: vLLM 0.6.1+ with Flash Attention 2
- **OS**: Ubuntu 24.04 LTS with SystemD
- **Configuration**: Pydantic-based settings management
- **Monitoring**: Prometheus + Grafana + AlertManager stack

---

**Total Diagrams**: 7 comprehensive architectural views  
**Total Lines**: 800+ lines of detailed Mermaid notation  
**Coverage**: Complete system architecture from client to hardware

These diagrams provide visual representation of the entire Citadel Alpha LLM Server architecture, enabling teams to understand component relationships, data flows, and system interactions at multiple levels of abstraction.