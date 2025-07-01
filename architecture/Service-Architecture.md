# Service Architecture

**Component**: Systemd Service Management  
**Integration**: Citadel AI LLM Server  
**Document Version**: 1.0  
**Created**: July 1, 2025  
**Dependencies**: vLLM Framework, Storage Management  

## Service Overview

The Citadel AI LLM Server employs a hierarchical systemd service architecture that provides automated management, health monitoring, and graceful startup/shutdown of all system components. The service layer orchestrates infrastructure services, model instances, and monitoring systems with comprehensive dependency management and failure recovery.

## Service Hierarchy Architecture

```mermaid
graph TD
    subgraph "Main Target"
        A[citadel-ai.target]
    end
    
    subgraph "Infrastructure Services"
        B[citadel-storage.service]
        C[citadel-gpu.service]
    end
    
    subgraph "Model Services Target"
        D[citadel-models.target]
    end
    
    subgraph "Model Service Instances"
        E[citadel-mixtral.service<br/>Port 11400]
        F[citadel-yi34b.service<br/>Port 11404]
        G[citadel-hermes.service<br/>Port 11401]
        H[citadel-openchat.service<br/>Port 11402]
        I[citadel-phi3.service<br/>Port 11403]
        J[citadel-coder.service<br/>Port 11405]
        K[citadel-vision.service<br/>Port 11500]
    end
    
    subgraph "Monitoring Services"
        L[citadel-monitor.service]
    end
    
    A --> B
    A --> C
    A --> D
    A --> L
    B --> D
    C --> D
    D --> E
    D --> F
    D --> G
    D --> H
    D --> I
    D --> J
    D --> K
    L --> E
    L --> F
    L --> G
    L --> H
    L --> I
    L --> J
    L --> K
```

## Service Dependency Chain

```mermaid
sequenceDiagram
    participant System as System Boot
    participant Storage as citadel-storage
    participant GPU as citadel-gpu
    participant Models as citadel-models.target
    participant Monitor as citadel-monitor
    participant Model as Model Services
    
    System->>Storage: Start storage service
    Storage->>Storage: Verify mount points
    Storage->>Storage: Setup symlinks
    Storage-->>System: Storage ready
    
    System->>GPU: Start GPU service
    GPU->>GPU: Optimize GPU settings
    GPU->>GPU: Verify GPU availability
    GPU-->>System: GPU ready
    
    System->>Models: Start models target
    Models->>Model: Start model services
    Model->>Model: Load vLLM engines
    Model->>Model: Initialize API servers
    Model-->>Models: Models ready
    
    System->>Monitor: Start monitoring
    Monitor->>Monitor: Initialize health checks
    Monitor->>Model: Monitor model health
    Monitor-->>System: Monitoring active
```

## Infrastructure Services

### Storage Service (`citadel-storage.service`)
```yaml
[Unit]
Description=Citadel AI Storage Verification and Setup
After=local-fs.target
Requires=local-fs.target
Before=citadel-models.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
EnvironmentFile=/etc/systemd/system/citadel-ai.env
ExecStart=/opt/citadel/services/scripts/storage-setup.sh
ExecStop=/opt/citadel/services/scripts/storage-cleanup.sh
TimeoutStartSec=120
TimeoutStopSec=60

[Install]
WantedBy=citadel-ai.target
```

#### Storage Service Functions
1. **Mount Point Verification**: Ensures `/mnt/citadel-models` and `/mnt/citadel-backup` are mounted
2. **Symlink Validation**: Verifies `/opt/citadel/models` → `/mnt/citadel-models/active` links
3. **Directory Creation**: Creates necessary cache and staging directories
4. **Permission Setting**: Establishes proper ownership and permissions

### GPU Service (`citadel-gpu.service`)
```yaml
[Unit]
Description=Citadel AI GPU Optimization and Monitoring
After=nvidia-persistenced.service
Requires=nvidia-persistenced.service
Before=citadel-models.target

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
Group=root
EnvironmentFile=/etc/systemd/system/citadel-ai.env
ExecStart=/opt/citadel/scripts/gpu-optimize.sh
ExecStop=/opt/citadel/scripts/gpu-restore.sh
TimeoutStartSec=60
TimeoutStopSec=30

[Install]
WantedBy=citadel-ai.target
```

#### GPU Service Functions
1. **GPU Optimization**: Sets performance profiles and power limits
2. **Memory Management**: Configures GPU memory allocation strategies
3. **Driver Verification**: Ensures NVIDIA drivers and CUDA are functional
4. **Thermal Management**: Establishes thermal monitoring and protection

## Model Service Architecture

### Model Service Template
```yaml
[Unit]
Description=Citadel AI Model Service - {MODEL_NAME}
PartOf=citadel-models.target
After=citadel-storage.service citadel-gpu.service
Requires=citadel-storage.service citadel-gpu.service

[Service]
Type=simple
User=agent0
Group=agent0
WorkingDirectory=/opt/citadel
EnvironmentFile=/etc/systemd/system/citadel-ai.env
Environment=MODEL_NAME={MODEL_NAME}
Environment=MODEL_PORT={MODEL_PORT}
Environment=MODEL_PATH={MODEL_PATH}

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768
LimitMEMLOCK=infinity

# Service configuration
ExecStart=/opt/citadel/services/scripts/start-model.sh {MODEL_NAME}
ExecStop=/opt/citadel/services/scripts/stop-model.sh {MODEL_NAME}
ExecReload=/bin/kill -HUP $MAINPID

# Restart configuration
Restart=always
RestartSec=30
StartLimitInterval=300
StartLimitBurst=3

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=citadel-{MODEL_NAME}

# Security settings
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/citadel /mnt/citadel-models /tmp
PrivateTmp=true

[Install]
WantedBy=citadel-models.target
```

### Model Service Instances

```mermaid
graph LR
    subgraph "Model Services Configuration"
        A[citadel-mixtral.service] --> A1[Port 11400<br/>Tensor Parallel: 2<br/>GPU Memory: 90%]
        B[citadel-yi34b.service] --> B1[Port 11404<br/>Tensor Parallel: 2<br/>GPU Memory: 85%]
        C[citadel-hermes.service] --> C1[Port 11401<br/>Tensor Parallel: 2<br/>GPU Memory: 90%]
        D[citadel-openchat.service] --> D1[Port 11402<br/>Tensor Parallel: 1<br/>GPU Memory: 70%]
        E[citadel-phi3.service] --> E1[Port 11403<br/>Tensor Parallel: 1<br/>GPU Memory: 60%]
        F[citadel-coder.service] --> F1[Port 11405<br/>Tensor Parallel: 1<br/>GPU Memory: 80%]
        G[citadel-vision.service] --> G1[Port 11500<br/>Tensor Parallel: 1<br/>GPU Memory: 70%]
    end
```

### Model Service Startup Scripts

The `start-model.sh` script implements model-specific configuration:

```bash
#!/bin/bash
# start-model.sh - Start individual model service

case "$MODEL_NAME" in
    mixtral)
        MODEL_PATH="/opt/citadel/models/mixtral-8x7b-instruct"
        PORT=11400
        TENSOR_PARALLEL=2
        GPU_MEMORY=0.90
        MAX_MODEL_LEN=32768
        ;;
    yi34b)
        MODEL_PATH="/opt/citadel/models/yi-34b-chat"
        PORT=11404
        TENSOR_PARALLEL=2
        GPU_MEMORY=0.85
        MAX_MODEL_LEN=4096
        ;;
    # Additional model configurations...
esac

# Start vLLM server with optimized parameters
exec python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_PATH" \
    --host "0.0.0.0" \
    --port "$PORT" \
    --tensor-parallel-size "$TENSOR_PARALLEL" \
    --gpu-memory-utilization "$GPU_MEMORY" \
    --max-model-len "$MAX_MODEL_LEN" \
    --served-model-name "$MODEL_NAME" \
    --trust-remote-code \
    --enable-chunked-prefill \
    --enable-prefix-caching \
    --disable-log-stats
```

## Health Monitoring Architecture

### Health Monitor Service (`citadel-monitor.service`)
```yaml
[Unit]
Description=Citadel AI Health Monitoring Service
After=citadel-models.target
Requires=citadel-models.target

[Service]
Type=simple
User=agent0
Group=agent0
WorkingDirectory=/opt/citadel
EnvironmentFile=/etc/systemd/system/citadel-ai.env
ExecStart=/opt/citadel/services/scripts/health-monitor.sh

# Restart configuration
Restart=always
RestartSec=60

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=citadel-monitor

[Install]
WantedBy=citadel-ai.target
```

### Health Monitoring Flow
```mermaid
sequenceDiagram
    participant Monitor as Health Monitor
    participant Model as Model Service
    participant API as API Endpoint
    participant Systemd as Systemd
    participant Log as Log System
    
    loop Every 60 seconds
        Monitor->>Model: Check process status
        Model-->>Monitor: Process running
        
        Monitor->>API: GET /health
        API-->>Monitor: 200 OK / Error
        
        alt Service Healthy
            Monitor->>Log: Log healthy status
        else Service Unhealthy
            Monitor->>Log: Log failure
            Monitor->>Systemd: Restart service
            Systemd->>Model: Stop service
            Systemd->>Model: Start service
            Monitor->>Log: Log restart action
        end
    end
```

### Health Check Implementation
```bash
#!/bin/bash
# health-monitor.sh - Continuous health monitoring

MONITOR_INTERVAL=60
declare -A MODEL_PORTS=(
    ["mixtral"]=11400
    ["yi34b"]=11404
    ["hermes"]=11401
    ["openchat"]=11402
    ["phi3"]=11403
    ["coder"]=11405
    ["vision"]=11500
)

check_service_health() {
    local model_name="$1"
    local port="$2"
    
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

restart_service() {
    local service_name="$1"
    log_message "Restarting service: $service_name"
    systemctl restart "$service_name" || log_message "Failed to restart $service_name"
}

while true; do
    for model_name in "${!MODEL_PORTS[@]}"; do
        port="${MODEL_PORTS[$model_name]}"
        
        if check_service_health "$model_name" "$port"; then
            log_message "✅ $model_name (port $port) - healthy"
        else
            log_message "❌ $model_name (port $port) - unhealthy"
            restart_service "citadel-$model_name.service"
        fi
    done
    
    sleep "$MONITOR_INTERVAL"
done
```

## Service Management Tools

### Citadel Service Control Script
The `citadel-service.sh` script provides unified service management:

```bash
#!/bin/bash
# citadel-service.sh - Citadel AI service management

Commands:
  start [service]     - Start all services or specific service
  stop [service]      - Stop all services or specific service
  restart [service]   - Restart all services or specific service
  status [service]    - Show status of all services or specific service
  logs [service]      - Show logs for all services or specific service
  enable              - Enable all services for auto-start
  disable             - Disable auto-start for all services
  health              - Run health check on all services

Service names:
  all, storage, gpu, models, monitor
  mixtral, yi34b, hermes, openchat, phi3, coder, vision
```

### Service Management Flow
```mermaid
graph TD
    A[citadel Command] --> B{Command Type}
    
    B -->|start| C[Start Services]
    B -->|stop| D[Stop Services]
    B -->|restart| E[Restart Services]
    B -->|status| F[Show Status]
    B -->|health| G[Health Check]
    
    C --> C1[Check Dependencies]
    C --> C2[Start in Order]
    C --> C3[Verify Startup]
    
    D --> D1[Stop Gracefully]
    D --> D2[Wait for Shutdown]
    D --> D3[Force Kill if Needed]
    
    E --> D
    E --> C
    
    F --> F1[Query Systemd Status]
    F --> F2[Check Process Health]
    F --> F3[Display Summary]
    
    G --> G1[Test All Endpoints]
    G --> G2[Check Resource Usage]
    G --> G3[Generate Report]
```

## Incremental Deployment Strategy

### Phased Service Deployment
```mermaid
graph LR
    A[Phase 1: Infrastructure] --> B[Phase 2: Test Model]
    B --> C[Phase 3: All Models]
    C --> D[Phase 4: Monitoring]
    
    A --> A1[citadel-storage.service<br/>citadel-gpu.service]
    B --> B1[citadel-phi3.service<br/>Single model test]
    C --> C1[All model services<br/>citadel-models.target]
    D --> D1[citadel-monitor.service<br/>citadel-ai.target]
```

### Deployment Script (`citadel-deploy`)
```bash
#!/bin/bash
# deploy-services.sh - Incremental service deployment

deploy_phase1() {
    echo "=== Phase 1: Infrastructure Services ==="
    sudo systemctl enable citadel-storage.service
    sudo systemctl start citadel-storage.service
    sudo systemctl enable citadel-gpu.service
    sudo systemctl start citadel-gpu.service
    echo "✅ Phase 1 completed successfully"
}

deploy_phase2() {
    local test_model="${1:-phi3}"
    echo "=== Phase 2: Test Model Service ==="
    sudo systemctl enable "citadel-$test_model.service"
    sudo systemctl start "citadel-$test_model.service"
    # Test model endpoint
    if curl -s "http://localhost:11403/health" > /dev/null; then
        echo "✅ Phase 2 completed successfully"
    else
        echo "❌ Model endpoint test failed"
        exit 1
    fi
}
```

## Service Security and Isolation

### Security Configuration
```yaml
# Security settings for model services
[Service]
# Process isolation
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/citadel /mnt/citadel-models /tmp
PrivateTmp=true

# Resource limits
LimitNOFILE=65536
LimitNPROC=32768
LimitMEMLOCK=infinity

# User isolation
User=agent0
Group=agent0
```

### Service Isolation Architecture
```mermaid
graph TB
    subgraph "User Space"
        A[agent0 User Context]
        B[Model Processes]
        C[Isolated Tmp Dirs]
    end
    
    subgraph "System Space"
        D[Root Infrastructure Services]
        E[GPU Management]
        F[Storage Management]
    end
    
    subgraph "Network Isolation"
        G[Port-based Isolation]
        H[Firewall Rules]
        I[Network Namespaces]
    end
    
    A --> B
    B --> C
    D --> E
    D --> F
    B --> G
    G --> H
    H --> I
```

## Performance and Resource Management

### Resource Allocation Strategy
```mermaid
graph TD
    A[16GB GPU VRAM] --> B[Model Memory Allocation]
    C[128GB System RAM] --> D[Process Memory Allocation]
    E[CPU Cores] --> F[Process Scheduling]
    
    B --> B1[Mixtral: ~14GB]
    B --> B2[Yi-34B: ~30GB - Multi-GPU]
    B --> B3[Phi-3: ~4GB]
    
    D --> D1[Model Processes: 8GB each]
    D --> D2[System Services: 2GB]
    D --> D3[Cache Buffers: 32GB]
    
    F --> F1[High Priority: Model Services]
    F --> F2[Normal Priority: Monitoring]
    F --> F3[Low Priority: Backup]
```

### Service Performance Monitoring
- **CPU Usage**: Per-service CPU utilization tracking
- **Memory Usage**: RAM and GPU memory monitoring
- **Network I/O**: Request/response metrics per service
- **Disk I/O**: Model loading and cache access patterns
- **Service Health**: Endpoint availability and response times

## Troubleshooting and Diagnostics

### Service Debugging Commands
```bash
# Check service status
systemctl status citadel-mixtral.service

# View service logs
journalctl -u citadel-mixtral.service -f

# Test service endpoint
curl -X POST http://localhost:11400/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "mixtral", "messages": [{"role": "user", "content": "Hello"}]}'

# Check resource usage
systemctl show citadel-mixtral.service --property=MainPID
ps -p <PID> -o pid,ppid,cmd,%mem,%cpu

# Monitor GPU usage
nvidia-smi -l 1
```

### Common Service Issues
1. **Service Start Failures**: Check dependencies, permissions, and configuration
2. **Port Conflicts**: Verify port availability and network configuration
3. **Memory Issues**: Monitor GPU memory allocation and system RAM usage
4. **Performance Problems**: Check CPU/GPU utilization and thermal throttling

## Integration with Other Components

### Framework Integration
- **vLLM Framework**: Services start vLLM processes with optimized parameters
- **Configuration Management**: Services load settings from Pydantic configurations
- **Storage Management**: Services depend on storage verification and symlink setup

### Monitoring Integration
- **Health Endpoints**: All model services expose `/health` and `/metrics` endpoints
- **Log Aggregation**: Systemd journal integration with centralized logging
- **Alerting System**: Service failures trigger automatic restart and notification

---

**Related Components**: [vLLM Framework Architecture](vLLM-Framework-Architecture.md), [Storage Architecture](Storage-Architecture.md), [Monitoring Architecture](Monitoring-Architecture.md)