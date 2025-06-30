# PLANB-07: Service Configuration and Systemd Integration

**Task:** Configure systemd services for automated startup and management of AI models  
**Duration:** 45-60 minutes  
**Prerequisites:** PLANB-01 through PLANB-06 completed, vLLM installed, symlinks configured  

## Overview

This task configures systemd services for automated management of vLLM model services, creates service orchestration scripts, and establishes health monitoring for the Citadel AI OS deployment.

## Service Architecture

### Service Hierarchy
```
systemd Services:
├── citadel-ai.target                   # Main target for all services
├── citadel-storage.service             # Storage verification and mounting
├── citadel-gpu.service                 # GPU optimization and monitoring
├── citadel-models.target               # Model services target
│   ├── citadel-mixtral.service         # Mixtral 8x7B service
│   ├── citadel-yi34b.service           # Yi-34B service
│   ├── citadel-hermes.service          # Nous Hermes 2 service
│   ├── citadel-openchat.service        # OpenChat 3.5 service
│   ├── citadel-phi3.service            # Phi-3 Mini service
│   ├── citadel-coder.service           # DeepCoder 14B service
│   └── citadel-vision.service          # MiMo VL 7B service
└── citadel-monitor.service             # Health monitoring service
```

### Service Dependencies
```yaml
dependency_chain:
  citadel-storage.service:
    - requires: local-fs.target
    - before: citadel-models.target
  
  citadel-gpu.service:
    - requires: nvidia-persistenced.service
    - before: citadel-models.target
  
  citadel-models.target:
    - requires: citadel-storage.service, citadel-gpu.service
    - wants: all model services
  
  citadel-monitor.service:
    - requires: citadel-models.target
    - after: citadel-models.target
```

## Service Configuration Steps

### Step 1: Create Base Service Infrastructure

1. **Create Service Configuration Directory**
   ```bash
   # Create systemd service directory structure
   sudo mkdir -p /etc/systemd/system/citadel-ai.target.wants
   mkdir -p /opt/citadel/services
   mkdir -p /opt/citadel/services/{scripts,configs,logs}
   
   # Set proper ownership
   sudo chown -R agent0:agent0 /opt/citadel/services
   chmod 755 /opt/citadel/services
   ```

2. **Create Service Environment File**
   ```bash
   # Create service environment configuration
   sudo tee /etc/systemd/system/citadel-ai.env << 'EOF'
   # Citadel AI Service Environment Variables
   
   # Core paths
   CITADEL_ROOT=/opt/citadel
   CITADEL_USER=agent0
   CITADEL_GROUP=agent0
   
   # Python environment
   CITADEL_VENV=/opt/citadel/vllm-env
   PYTHON_PATH=/opt/citadel/vllm-env/bin/python
   
   # Storage paths
   CITADEL_MODELS=/opt/citadel/models
   CITADEL_LOGS=/opt/citadel/logs
   CITADEL_CONFIGS=/opt/citadel/configs
   
   # Hugging Face configuration
   HF_TOKEN=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
   HUGGINGFACE_HUB_TOKEN=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
   HF_HOME=/mnt/citadel-models/cache
   TRANSFORMERS_CACHE=/mnt/citadel-models/cache/transformers
   HF_DATASETS_CACHE=/mnt/citadel-models/cache/datasets
   
   # Network configuration (Hana-X Lab)
   CITADEL_BIND_ADDRESS=192.168.10.35
   CITADEL_HOSTNAME=db
   CITADEL_NETWORK=192.168.10.0/24
   
   # GPU configuration
   CUDA_VISIBLE_DEVICES=0,1
   NVIDIA_VISIBLE_DEVICES=all
   NVIDIA_DRIVER_CAPABILITIES=compute,utility
   
   # vLLM configuration
   VLLM_CACHE_ROOT=/mnt/citadel-models/cache/vllm
   
   # Service configuration
   CITADEL_LOG_LEVEL=INFO
   CITADEL_MAX_RESTART_ATTEMPTS=3
   CITADEL_RESTART_DELAY=30
   EOF
   
   # Set proper permissions
   sudo chmod 644 /etc/systemd/system/citadel-ai.env
   ```

### Step 2: Create Core Infrastructure Services

1. **Create Storage Service**
   ```bash
   # Create storage verification and setup service
   sudo tee /etc/systemd/system/citadel-storage.service << 'EOF'
   [Unit]
   Description=Citadel AI Storage Verification and Setup
   Documentation=file:///opt/citadel/docs/storage.md
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
   EOF
   ```

2. **Create GPU Service**
   ```bash
   # Create GPU optimization and monitoring service
   sudo tee /etc/systemd/system/citadel-gpu.service << 'EOF'
   [Unit]
   Description=Citadel AI GPU Optimization and Monitoring
   Documentation=file:///opt/citadel/docs/gpu.md
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
   EOF
   ```

3. **Create Main Target**
   ```bash
   # Create main Citadel AI target
   sudo tee /etc/systemd/system/citadel-ai.target << 'EOF'
   [Unit]
   Description=Citadel AI Operating System
   Documentation=file:///opt/citadel/docs/overview.md
   Requires=citadel-storage.service citadel-gpu.service
   After=citadel-storage.service citadel-gpu.service
   Wants=citadel-models.target citadel-monitor.service
   
   [Install]
   WantedBy=multi-user.target
   EOF
   ```

### Step 3: Create Model Services

1. **Create Model Service Template**
   ```bash
   # Create service template for individual models
   tee /opt/citadel/services/configs/model-service-template << 'EOF'
   [Unit]
   Description=Citadel AI Model Service - MODEL_NAME
   Documentation=file:///opt/citadel/docs/models/MODEL_NAME.md
   PartOf=citadel-models.target
   After=citadel-storage.service citadel-gpu.service
   Requires=citadel-storage.service citadel-gpu.service
   
   [Service]
   Type=simple
   User=agent0
   Group=agent0
   WorkingDirectory=/opt/citadel
   EnvironmentFile=/etc/systemd/system/citadel-ai.env
   Environment=MODEL_NAME=MODEL_NAME
   Environment=MODEL_PORT=MODEL_PORT
   Environment=MODEL_PATH=MODEL_PATH
   
   # Resource limits
   LimitNOFILE=65536
   LimitNPROC=32768
   LimitMEMLOCK=infinity
   
   # Service configuration
   ExecStart=/opt/citadel/services/scripts/start-model.sh MODEL_NAME
   ExecStop=/opt/citadel/services/scripts/stop-model.sh MODEL_NAME
   ExecReload=/bin/kill -HUP $MAINPID
   
   # Restart configuration
   Restart=always
   RestartSec=30
   StartLimitInterval=300
   StartLimitBurst=3
   
   # Logging
   StandardOutput=journal
   StandardError=journal
   SyslogIdentifier=citadel-MODEL_NAME
   
   # Security settings
   NoNewPrivileges=true
   ProtectSystem=strict
   ProtectHome=true
   ReadWritePaths=/opt/citadel /mnt/citadel-models /tmp
   PrivateTmp=true
   
   [Install]
   WantedBy=citadel-models.target
   EOF
   ```

2. **Create Individual Model Services**
   ```bash
   # Create service generator script
   tee /opt/citadel/services/scripts/create-model-services.sh << 'EOF'
   #!/bin/bash
   # create-model-services.sh - Generate systemd services for all models
   
   # Model configuration
   declare -A MODELS=(
       ["mixtral"]="11400:/opt/citadel/models/mixtral-8x7b-instruct"
       ["yi34b"]="11404:/opt/citadel/models/yi-34b-chat"
       ["hermes"]="11401:/opt/citadel/models/nous-hermes-2-mixtral"
       ["openchat"]="11402:/opt/citadel/models/openchat-3.5"
       ["phi3"]="11403:/opt/citadel/models/phi-3-mini-128k"
       ["coder"]="11405:/opt/citadel/models/deepcoder-14b-instruct"
       ["vision"]="11500:/opt/citadel/models/mimo-vl-7b-rl"
   )
   
   echo "Creating model services..."
   
   for model_name in "${!MODELS[@]}"; do
       IFS=':' read -r port path <<< "${MODELS[$model_name]}"
       
       echo "Creating service for $model_name (port $port)"
       
       # Create service file from template
       sed -e "s/MODEL_NAME/$model_name/g" \
           -e "s/MODEL_PORT/$port/g" \
           -e "s|MODEL_PATH|$path|g" \
           /opt/citadel/services/configs/model-service-template > \
           "/tmp/citadel-$model_name.service"
       
       # Install service file
       sudo mv "/tmp/citadel-$model_name.service" "/etc/systemd/system/"
       sudo chmod 644 "/etc/systemd/system/citadel-$model_name.service"
       
       echo "✅ Service created: citadel-$model_name.service"
   done
   
   echo "Model services created successfully"
   EOF
   
   chmod +x /opt/citadel/services/scripts/create-model-services.sh
   /opt/citadel/services/scripts/create-model-services.sh
   ```

3. **Create Models Target**
   ```bash
   # Create models target
   sudo tee /etc/systemd/system/citadel-models.target << 'EOF'
   [Unit]
   Description=Citadel AI Model Services
   Documentation=file:///opt/citadel/docs/models.md
   Requires=citadel-storage.service citadel-gpu.service
   After=citadel-storage.service citadel-gpu.service
   Wants=citadel-mixtral.service citadel-yi34b.service citadel-hermes.service citadel-openchat.service citadel-phi3.service citadel-coder.service citadel-vision.service
   
   [Install]
   WantedBy=citadel-ai.target
   EOF
   ```

### Step 4: Create Service Management Scripts

1. **Create Model Start Script**
   ```bash
   # Create model startup script
   tee /opt/citadel/services/scripts/start-model.sh << 'EOF'
   #!/bin/bash
   # start-model.sh - Start individual model service
   
   set -euo pipefail
   
   MODEL_NAME="${1:-}"
   if [ -z "$MODEL_NAME" ]; then
       echo "Usage: $0 <model_name>"
       exit 1
   fi
   
   # Source environment
   source /opt/citadel/configs/storage-env.sh
   source /opt/citadel/vllm-env/bin/activate
   
   # Model configuration
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
       hermes)
           MODEL_PATH="/opt/citadel/models/nous-hermes-2-mixtral"
           PORT=11401
           TENSOR_PARALLEL=2
           GPU_MEMORY=0.90
           MAX_MODEL_LEN=32768
           ;;
       openchat)
           MODEL_PATH="/opt/citadel/models/openchat-3.5"
           PORT=11402
           TENSOR_PARALLEL=1
           GPU_MEMORY=0.70
           MAX_MODEL_LEN=8192
           ;;
       phi3)
           MODEL_PATH="/opt/citadel/models/phi-3-mini-128k"
           PORT=11403
           TENSOR_PARALLEL=1
           GPU_MEMORY=0.60
           MAX_MODEL_LEN=128000
           ;;
       coder)
           MODEL_PATH="/opt/citadel/models/deepcoder-14b-instruct"
           PORT=11405
           TENSOR_PARALLEL=1
           GPU_MEMORY=0.80
           MAX_MODEL_LEN=16384
           ;;
       vision)
           MODEL_PATH="/opt/citadel/models/mimo-vl-7b-rl"
           PORT=11500
           TENSOR_PARALLEL=1
           GPU_MEMORY=0.70
           MAX_MODEL_LEN=4096
           ;;
       *)
           echo "Unknown model: $MODEL_NAME"
           exit 1
           ;;
   esac
   
   # Verify model path exists
   if [ ! -d "$MODEL_PATH" ]; then
       echo "Model path not found: $MODEL_PATH"
       exit 1
   fi
   
   echo "Starting $MODEL_NAME model service..."
   echo "  Model path: $MODEL_PATH"
   echo "  Port: $PORT"
   echo "  Tensor parallel: $TENSOR_PARALLEL"
   
   # Start vLLM server
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
   EOF
   
   chmod +x /opt/citadel/services/scripts/start-model.sh
   ```

2. **Create Model Stop Script**
   ```bash
   # Create model stop script
   tee /opt/citadel/services/scripts/stop-model.sh << 'EOF'
   #!/bin/bash
   # stop-model.sh - Stop individual model service
   
   MODEL_NAME="${1:-}"
   if [ -z "$MODEL_NAME" ]; then
       echo "Usage: $0 <model_name>"
       exit 1
   fi
   
   echo "Stopping $MODEL_NAME model service..."
   
   # Find and terminate the process gracefully
   pkill -f "vllm.entrypoints.openai.api_server.*$MODEL_NAME" || true
   
   # Wait for graceful shutdown
   sleep 5
   
   # Force kill if still running
   pkill -9 -f "vllm.entrypoints.openai.api_server.*$MODEL_NAME" || true
   
   echo "$MODEL_NAME service stopped"
   EOF
   
   chmod +x /opt/citadel/services/scripts/stop-model.sh
   ```

3. **Create Storage Setup Script**
   ```bash
   # Create storage setup script
   tee /opt/citadel/services/scripts/storage-setup.sh << 'EOF'
   #!/bin/bash
   # storage-setup.sh - Verify and setup storage for services
   
   set -euo pipefail
   
   echo "Setting up Citadel AI storage..."
   
   # Verify mount points
   if ! mountpoint -q /mnt/citadel-models; then
       echo "❌ Model storage not mounted"
       exit 1
   fi
   
   if ! mountpoint -q /mnt/citadel-backup; then
       echo "❌ Backup storage not mounted"
       exit 1
   fi
   
   echo "✅ Storage mount points verified"
   
   # Verify symlinks
   if [ ! -L "/opt/citadel/models" ]; then
       echo "❌ Models symlink missing"
       exit 1
   fi
   
   echo "✅ Symlinks verified"
   
   # Create necessary directories
   mkdir -p /opt/citadel/logs
   mkdir -p /mnt/citadel-models/cache/vllm
   mkdir -p /mnt/citadel-models/cache/transformers
   
   # Set permissions
   chown -R agent0:agent0 /opt/citadel/logs
   chown -R agent0:agent0 /mnt/citadel-models/cache
   
   echo "✅ Storage setup completed"
   EOF
   
   chmod +x /opt/citadel/services/scripts/storage-setup.sh
   ```

### Step 5: Create Monitoring Service

1. **Create Health Monitoring Service**
   ```bash
   # Create monitoring service
   sudo tee /etc/systemd/system/citadel-monitor.service << 'EOF'
   [Unit]
   Description=Citadel AI Health Monitoring Service
   Documentation=file:///opt/citadel/docs/monitoring.md
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
   EOF
   ```

2. **Create Health Monitor Script**
   ```bash
   # Create health monitoring script
   tee /opt/citadel/services/scripts/health-monitor.sh << 'EOF'
   #!/bin/bash
   # health-monitor.sh - Continuous health monitoring
   
   set -euo pipefail
   
   # Source environment
   source /opt/citadel/configs/storage-env.sh
   source /opt/citadel/vllm-env/bin/activate
   
   MONITOR_INTERVAL=60
   LOG_FILE="/opt/citadel/logs/health-monitor.log"
   
   # Model ports to monitor
   declare -A MODEL_PORTS=(
       ["mixtral"]=11400
       ["yi34b"]=11404
       ["hermes"]=11401
       ["openchat"]=11402
       ["phi3"]=11403
       ["coder"]=11405
       ["vision"]=11500
   )
   
   log_message() {
       echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
   }
   
   check_service_health() {
       local model_name="$1"
       local port="$2"
       
       if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
           return 0
       else
           return 1
       fi
   }
   
   check_gpu_health() {
       if nvidia-smi > /dev/null 2>&1; then
           return 0
       else
           return 1
       fi
   }
   
   check_storage_health() {
       if [ -d "/opt/citadel/models" ] && [ -d "/mnt/citadel-models" ]; then
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
   
   log_message "Health monitor started"
   
   while true; do
       # Check GPU health
       if ! check_gpu_health; then
           log_message "❌ GPU health check failed"
       fi
       
       # Check storage health
       if ! check_storage_health; then
           log_message "❌ Storage health check failed"
       fi
       
       # Check model services
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
   EOF
   
   chmod +x /opt/citadel/services/scripts/health-monitor.sh
   ```

### Step 6: Create Service Management Commands

1. **Create Service Control Script**
   ```bash
   # Create comprehensive service control script
   tee /opt/citadel/scripts/citadel-service.sh << 'EOF'
   #!/bin/bash
   # citadel-service.sh - Citadel AI service management
   
   set -euo pipefail
   
   show_usage() {
       cat << 'USAGE'
   Citadel AI Service Management
   
   Usage: citadel-service.sh <command> [options]
   
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
     all                 - All Citadel AI services (default)
     storage             - Storage service
     gpu                 - GPU service
     models              - All model services
     monitor             - Health monitoring service
     mixtral, yi34b, hermes, openchat, phi3, coder, vision
   
   Examples:
     citadel-service.sh start           # Start all services
     citadel-service.sh stop mixtral    # Stop Mixtral service
     citadel-service.sh status models   # Status of all model services
     citadel-service.sh logs phi3       # Show Phi-3 logs
   USAGE
   }
   
   get_service_name() {
       local service="$1"
       case "$service" in
           all) echo "citadel-ai.target" ;;
           storage) echo "citadel-storage.service" ;;
           gpu) echo "citadel-gpu.service" ;;
           models) echo "citadel-models.target" ;;
           monitor) echo "citadel-monitor.service" ;;
           mixtral|yi34b|hermes|openchat|phi3|coder|vision)
               echo "citadel-$service.service" ;;
           *) echo "$service" ;;
       esac
   }
   
   service_command() {
       local command="$1"
       local service="${2:-all}"
       local service_name
       
       service_name=$(get_service_name "$service")
       
       case "$command" in
           start)
               echo "Starting $service..."
               sudo systemctl start "$service_name"
               ;;
           stop)
               echo "Stopping $service..."
               sudo systemctl stop "$service_name"
               ;;
           restart)
               echo "Restarting $service..."
               sudo systemctl restart "$service_name"
               ;;
           status)
               sudo systemctl status "$service_name"
               ;;
           logs)
               sudo journalctl -u "$service_name" -f
               ;;
           enable)
               echo "Enabling $service for auto-start..."
               sudo systemctl enable "$service_name"
               ;;
           disable)
               echo "Disabling auto-start for $service..."
               sudo systemctl disable "$service_name"
               ;;
           *)
               echo "Unknown command: $command"
               return 1
               ;;
       esac
   }
   
   health_check() {
       echo "=== Citadel AI Health Check ==="
       echo ""
       
       # Check main target
       if systemctl is-active --quiet citadel-ai.target; then
           echo "✅ Citadel AI System: Active"
       else
           echo "❌ Citadel AI System: Inactive"
       fi
       
       # Check individual services
       services=("storage" "gpu" "models" "monitor")
       for service in "${services[@]}"; do
           service_name=$(get_service_name "$service")
           if systemctl is-active --quiet "$service_name"; then
               echo "✅ $service: Active"
           else
               echo "❌ $service: Inactive"
           fi
       done
       
       echo ""
       echo "Model Services:"
       models=("mixtral" "yi34b" "hermes" "openchat" "phi3" "coder" "vision")
       for model in "${models[@]}"; do
           service_name=$(get_service_name "$model")
           if systemctl is-active --quiet "$service_name"; then
               echo "  ✅ $model: Active"
           else
               echo "  ❌ $model: Inactive"
           fi
       done
   }
   
   # Main execution
   command="${1:-}"
   service="${2:-all}"
   
   if [ -z "$command" ]; then
       show_usage
       exit 1
   fi
   
   case "$command" in
       health)
           health_check
           ;;
       help|--help|-h)
           show_usage
           ;;
       *)
           service_command "$command" "$service"
           ;;
   esac
   EOF
   
   chmod +x /opt/citadel/scripts/citadel-service.sh
   
   # Create convenient alias
   sudo ln -sf /opt/citadel/scripts/citadel-service.sh /usr/local/bin/citadel
   ```

## Service Installation and Configuration

### Step 1: Install and Enable Services

1. **Reload Systemd and Enable Services**
   ```bash
   # Reload systemd daemon
   sudo systemctl daemon-reload
   
   # Enable core services
   sudo systemctl enable citadel-storage.service
   sudo systemctl enable citadel-gpu.service
   sudo systemctl enable citadel-monitor.service
   
   # Enable model services
   models=("mixtral" "yi34b" "hermes" "openchat" "phi3" "coder" "vision")
   for model in "${models[@]}"; do
       sudo systemctl enable "citadel-$model.service"
   done
   
   # Enable main target
   sudo systemctl enable citadel-ai.target
   
   echo "All services enabled for auto-start"
   ```

2. **Create Service Logs Directory**
   ```bash
   # Create logs directory structure
   mkdir -p /opt/citadel/logs/{services,models,monitoring}
   
   # Set up log rotation
   sudo tee /etc/logrotate.d/citadel-ai << 'EOF'
   /opt/citadel/logs/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 agent0 agent0
   }
   
   /opt/citadel/logs/*/*.log {
       daily
       rotate 30
       compress
       delaycompress
       missingok
       notifempty
       create 644 agent0 agent0
   }
   EOF
   ```

## Validation Steps

### Step 1: Service Installation Verification

```bash
# Verify service installation
echo "=== Service Installation Verification ==="

# Check service files
echo "Service files:"
ls -la /etc/systemd/system/citadel-*.service /etc/systemd/system/citadel-*.target

# Check service status
echo ""
echo "Service status:"
systemctl list-unit-files | grep citadel

# Verify dependencies
echo ""
echo "Service dependencies:"
systemctl list-dependencies citadel-ai.target
```

### Step 2: Service Functionality Testing

```bash
# Test service management
echo "=== Service Management Testing ==="

# Test service control script
/opt/citadel/scripts/citadel-service.sh health

# Test individual service start/stop
echo ""
echo "Testing service start/stop..."
sudo systemctl start citadel-storage.service
sudo systemctl status citadel-storage.service --no-pager
sudo systemctl stop citadel-storage.service
```

### Step 3: Complete System Test

```bash
# Full system test (with models present)
echo "=== Complete System Test ==="

# Start all services
echo "Starting all Citadel AI services..."
citadel start

# Wait for startup
sleep 30

# Check health
citadel health

# Check logs
echo ""
echo "Recent service logs:"
sudo journalctl -u citadel-ai.target --since "5 minutes ago" --no-pager
```

## Troubleshooting

### Issue: Services Won't Start
**Symptoms**: Service start failures, dependency errors
**Solutions**:
- Check service dependencies: `systemctl list-dependencies citadel-ai.target`
- Check service logs: `journalctl -u service-name -f`
- Verify environment file: `cat /etc/systemd/system/citadel-ai.env`
- Check permissions: `ls -la /opt/citadel/services/`

### Issue: Models Won't Load
**Symptoms**: Model services fail to start, port binding errors
**Solutions**:
- Check model paths: `ls -la /opt/citadel/models/`
- Verify GPU availability: `nvidia-smi`
- Check port conflicts: `netstat -tlnp | grep :1140`
- Check vLLM installation: `source /opt/citadel/vllm-env/bin/activate && python -c "import vllm"`

### Issue: Health Monitor Not Working
**Symptoms**: No health monitoring, services not restarting
**Solutions**:
- Check monitor service: `systemctl status citadel-monitor.service`
- Check monitor logs: `journalctl -u citadel-monitor.service -f`
- Verify network connectivity: `curl http://localhost:11400/health`
- Check script permissions: `ls -la /opt/citadel/services/scripts/`

## Configuration Summary

### Services Created
- ✅ **citadel-ai.target**: Main service target
- ✅ **citadel-storage.service**: Storage verification
- ✅ **citadel-gpu.service**: GPU optimization
- ✅ **citadel-models.target**: Model services target
- ✅ **Model Services**: 7 individual model services
- ✅ **citadel-monitor.service**: Health monitoring

### Management Tools
- **citadel-service.sh**: Comprehensive service management
- **start-model.sh/stop-model.sh**: Individual model control
- **health-monitor.sh**: Continuous health monitoring
- **citadel** command: Convenient service management alias

### Auto-start Configuration
- All services enabled for automatic startup
- Proper dependency chain configured
- Health monitoring with automatic restart
- Log rotation configured

## Next Steps

Continue to **[PLANB-08-Backup-Monitoring.md](PLANB-08-Backup-Monitoring.md)** for backup strategy implementation and comprehensive monitoring setup.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 45-60 minutes  
**Complexity**: High  
**Prerequisites**: All previous tasks completed, vLLM working, symlinks configured