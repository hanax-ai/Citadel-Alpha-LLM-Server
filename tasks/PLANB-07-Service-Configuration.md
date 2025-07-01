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

## Prerequisites Validation

Before starting service configuration, validate all dependencies and prerequisites:

### Step 0: Validate System Prerequisites

1. **Validate Core Dependencies**
   ```bash
   # Create prerequisite validation script
   tee /opt/citadel/scripts/validate-prerequisites.sh << 'EOF'
   #!/bin/bash
   # validate-prerequisites.sh - Validate all prerequisites before service setup
   
   set -euo pipefail
   
   echo "=== Citadel AI Prerequisites Validation ==="
   
   # Track validation status
   VALIDATION_PASSED=true
   
   # Function to check and report status
   check_requirement() {
       local description="$1"
       local command="$2"
       local required="${3:-true}"
       
       if eval "$command" > /dev/null 2>&1; then
           echo "✅ $description"
           return 0
       else
           if [ "$required" = "true" ]; then
               echo "❌ $description (REQUIRED)"
               VALIDATION_PASSED=false
           else
               echo "⚠️  $description (OPTIONAL)"
           fi
           return 1
       fi
   }
   
   echo ""
   echo "System Dependencies:"
   check_requirement "Ubuntu 24.04 LTS" "grep -q 'Ubuntu 24.04' /etc/os-release"
   check_requirement "Systemd available" "systemctl --version"
   check_requirement "NVIDIA drivers installed" "nvidia-smi"
   check_requirement "NVIDIA persistence daemon" "systemctl status nvidia-persistenced --no-pager"
   check_requirement "Python 3.12 available" "python3.12 --version"
   
   echo ""
   echo "Storage Requirements:"
   check_requirement "Models storage mounted" "mountpoint -q /mnt/citadel-models"
   check_requirement "Backup storage mounted" "mountpoint -q /mnt/citadel-backup"
   check_requirement "Models symlink exists" "[ -L /opt/citadel/models ]"
   check_requirement "Sufficient storage space (>500GB)" "[ $(df /mnt/citadel-models --output=avail | tail -1) -gt 524288000 ]"
   
   echo ""
   echo "Python Environment:"
   check_requirement "vLLM virtual environment" "[ -d /opt/citadel/vllm-env ]"
   check_requirement "vLLM installed" "source /opt/citadel/vllm-env/bin/activate && python -c 'import vllm'"
   check_requirement "Required Python packages" "source /opt/citadel/vllm-env/bin/activate && python -c 'import torch, transformers, huggingface_hub'"
   
   echo ""
   echo "Network Configuration:"
   check_requirement "Network interface available" "ip addr show | grep -q '192.168.10.35'"
   check_requirement "Required ports available" "! netstat -tuln | grep -E ':(11400|11401|11402|11403|11404|11405|11500)'"
   
   echo ""
   echo "Permissions and Security:"
   check_requirement "Agent0 user exists" "id agent0"
   check_requirement "Citadel directories writable" "[ -w /opt/citadel ]"
   check_requirement "Systemd user permissions" "systemctl --user status > /dev/null 2>&1" false
   
   echo ""
   if [ "$VALIDATION_PASSED" = "true" ]; then
       echo "🎉 All prerequisites validated successfully!"
       echo "System is ready for service configuration."
       exit 0
   else
       echo "❌ Prerequisites validation failed!"
       echo "Please resolve the above issues before proceeding."
       exit 1
   fi
   EOF
   
   chmod +x /opt/citadel/scripts/validate-prerequisites.sh
   
   # Run validation
   echo "Running prerequisites validation..."
   /opt/citadel/scripts/validate-prerequisites.sh
   ```

2. **Validate Model Availability**
   ```bash
   # Create model validation script
   tee /opt/citadel/scripts/validate-models.sh << 'EOF'
   #!/bin/bash
   # validate-models.sh - Validate model availability and readiness
   
   set -euo pipefail
   
   echo "=== Model Validation ==="
   
   # Model paths to validate
   declare -A MODELS=(
       ["mixtral"]="/opt/citadel/models/mixtral-8x7b-instruct"
       ["yi34b"]="/opt/citadel/models/yi-34b-chat"
       ["hermes"]="/opt/citadel/models/nous-hermes-2-mixtral"
       ["openchat"]="/opt/citadel/models/openchat-3.5"
       ["phi3"]="/opt/citadel/models/phi-3-mini-128k"
       ["coder"]="/opt/citadel/models/deepcoder-14b-instruct"
       ["vision"]="/opt/citadel/models/mimo-vl-7b-rl"
   )
   
   MODELS_AVAILABLE=0
   MODELS_TOTAL=${#MODELS[@]}
   
   for model_name in "${!MODELS[@]}"; do
       model_path="${MODELS[$model_name]}"
       
       if [ -d "$model_path" ] && [ -f "$model_path/config.json" ]; then
           echo "✅ $model_name: Available at $model_path"
           ((MODELS_AVAILABLE++))
       else
           echo "❌ $model_name: Not found at $model_path"
       fi
   done
   
   echo ""
   echo "Models Summary: $MODELS_AVAILABLE/$MODELS_TOTAL available"
   
   if [ $MODELS_AVAILABLE -eq 0 ]; then
       echo "❌ No models available! Services cannot be started."
       exit 1
   elif [ $MODELS_AVAILABLE -lt $MODELS_TOTAL ]; then
       echo "⚠️  Some models unavailable. Services will be created for available models only."
   else
       echo "🎉 All models validated successfully!"
   fi
   EOF
   
   chmod +x /opt/citadel/scripts/validate-models.sh
   ```

## Service Configuration Steps

### Step 1: Create Base Service Infrastructure (with Prerequisites)

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
## Incremental Testing Strategy

### Step 1: Phased Service Deployment

1. **Create Incremental Deployment Script**
   ```bash
   # Create phased deployment script
   tee /opt/citadel/scripts/deploy-services.sh << 'EOF'
   #!/bin/bash
   # deploy-services.sh - Incremental service deployment with testing
   
   set -euo pipefail
   
   show_usage() {
       cat << 'USAGE'
   Incremental Service Deployment
   
   Usage: deploy-services.sh <phase> [options]
   
   Phases:
     validate     - Run prerequisites validation
     phase1       - Deploy infrastructure services (storage, gpu)
     phase2       - Deploy single test model service
     phase3       - Deploy remaining model services
     phase4       - Deploy monitoring services
     rollback     - Rollback all services
     status       - Show deployment status
   
   Options:
     --force      - Skip confirmation prompts
     --test-model - Specify test model for phase2 (default: phi3)
   USAGE
   }
   
   validate_phase() {
       echo "=== Phase Validation ==="
       /opt/citadel/scripts/validate-prerequisites.sh
       /opt/citadel/scripts/validate-models.sh
   }
   
   deploy_phase1() {
       echo "=== Phase 1: Infrastructure Services ==="
       
       # Reload systemd
       sudo systemctl daemon-reload
       
       # Deploy infrastructure services
       echo "Deploying storage service..."
       sudo systemctl enable citadel-storage.service
       sudo systemctl start citadel-storage.service
       
       echo "Waiting for storage service..."
       sleep 10
       
       if ! systemctl is-active --quiet citadel-storage.service; then
           echo "❌ Storage service failed to start"
           exit 1
       fi
       
       echo "Deploying GPU service..."
       sudo systemctl enable citadel-gpu.service
       sudo systemctl start citadel-gpu.service
       
       echo "Waiting for GPU service..."
       sleep 5
       
       if ! systemctl is-active --quiet citadel-gpu.service; then
           echo "❌ GPU service failed to start"
           exit 1
       fi
       
       echo "✅ Phase 1 completed successfully"
   }
   
   deploy_phase2() {
       local test_model="${1:-phi3}"
       
       echo "=== Phase 2: Test Model Service ==="
       echo "Deploying test model: $test_model"
       
       # Deploy single model for testing
       sudo systemctl enable "citadel-$test_model.service"
       sudo systemctl start "citadel-$test_model.service"
       
       echo "Waiting for model service to start..."
       sleep 30
       
       if ! systemctl is-active --quiet "citadel-$test_model.service"; then
           echo "❌ Test model service failed to start"
           exit 1
       fi
       
       # Test model endpoint
       local port
       case "$test_model" in
           phi3) port=11403 ;;
           openchat) port=11402 ;;
           *) port=11400 ;;
       esac
       
       echo "Testing model endpoint..."
       if curl -s "http://localhost:$port/health" > /dev/null; then
           echo "✅ Phase 2 completed successfully"
       else
           echo "❌ Model endpoint test failed"
           exit 1
       fi
   }
   
   deploy_phase3() {
       echo "=== Phase 3: Remaining Model Services ==="
       
       # Deploy models target
       sudo systemctl enable citadel-models.target
       
       # Deploy remaining model services
       models=("mixtral" "yi34b" "hermes" "openchat" "coder" "vision")
       for model in "${models[@]}"; do
           if systemctl is-active --quiet "citadel-$model.service"; then
               echo "Skipping $model (already active)"
               continue
           fi
           
           echo "Deploying $model service..."
           sudo systemctl enable "citadel-$model.service"
           sudo systemctl start "citadel-$model.service"
           
           echo "Waiting for $model to start..."
           sleep 20
           
           if ! systemctl is-active --quiet "citadel-$model.service"; then
               echo "⚠️  $model service failed to start (continuing)"
           else
               echo "✅ $model service started"
           fi
       done
       
       echo "✅ Phase 3 completed"
   }
   
   deploy_phase4() {
       echo "=== Phase 4: Monitoring Services ==="
       
       # Deploy monitoring service
       sudo systemctl enable citadel-monitor.service
       sudo systemctl start citadel-monitor.service
       
       echo "Waiting for monitor service..."
       sleep 10
       
       if ! systemctl is-active --quiet citadel-monitor.service; then
           echo "❌ Monitor service failed to start"
           exit 1
       fi
       
       # Deploy main target
       sudo systemctl enable citadel-ai.target
       sudo systemctl start citadel-ai.target
       
       echo "✅ Phase 4 completed successfully"
       echo "🎉 Full deployment completed!"
   }
   
   rollback_services() {
       echo "=== Rolling Back Services ==="
       
       # Stop and disable all services
       services=("citadel-ai.target" "citadel-monitor.service" "citadel-models.target")
       models=("mixtral" "yi34b" "hermes" "openchat" "phi3" "coder" "vision")
       
       for model in "${models[@]}"; do
           services+=("citadel-$model.service")
       done
       
       services+=("citadel-gpu.service" "citadel-storage.service")
       
       for service in "${services[@]}"; do
           echo "Stopping $service..."
           sudo systemctl stop "$service" 2>/dev/null || true
           sudo systemctl disable "$service" 2>/dev/null || true
       done
       
       echo "✅ Rollback completed"
   }
   
   show_status() {
       echo "=== Deployment Status ==="
       /opt/citadel/scripts/citadel-service.sh health
   }
   
   # Main execution
   phase="${1:-}"
   
   if [ -z "$phase" ]; then
       show_usage
       exit 1
   fi
   
   case "$phase" in
       validate)
           validate_phase
           ;;
       phase1)
           validate_phase
           deploy_phase1
           ;;
       phase2)
           deploy_phase2 "${2:-phi3}"
           ;;
       phase3)
           deploy_phase3
           ;;
       phase4)
           deploy_phase4
           ;;
       rollback)
           rollback_services
           ;;
       status)
           show_status
           ;;
       help|--help|-h)
           show_usage
           ;;
       *)
           echo "Unknown phase: $phase"
           show_usage
           exit 1
           ;;
   esac
   EOF
   
   chmod +x /opt/citadel/scripts/deploy-services.sh
   
   # Create convenient alias
   sudo ln -sf /opt/citadel/scripts/deploy-services.sh /usr/local/bin/citadel-deploy
   ```

## Rollback Strategy

### Step 1: Create Rollback Infrastructure

1. **Create Service Rollback Script**
   ```bash
   # Create comprehensive rollback script
   tee /opt/citadel/scripts/rollback-services.sh << 'EOF'
   #!/bin/bash
   # rollback-services.sh - Emergency rollback for Citadel AI services
   
   set -euo pipefail
   
   show_usage() {
       cat << 'USAGE'
   Citadel AI Service Rollback
   
   Usage: rollback-services.sh <action> [options]
   
   Actions:
     emergency    - Immediate stop of all services
     graceful     - Graceful shutdown with health checks
     partial      - Rollback specific service group
     backup       - Create service configuration backup
     restore      - Restore from backup
     status       - Show rollback status
   
   Options:
     --group      - Service group (models, infrastructure, monitoring)
     --force      - Skip confirmation prompts
     --backup-id  - Backup identifier for restore
   USAGE
   }
   
   emergency_rollback() {
       echo "=== EMERGENCY ROLLBACK ==="
       echo "⚠️  Performing immediate service shutdown..."
       
       # Kill all vLLM processes immediately
       pkill -9 -f "vllm.entrypoints.openai.api_server" || true
       
       # Stop all Citadel services
       sudo systemctl stop citadel-ai.target || true
       
       # Stop individual services
       services=("citadel-monitor.service" "citadel-models.target")
       models=("mixtral" "yi34b" "hermes" "openchat" "phi3" "coder" "vision")
       
       for model in "${models[@]}"; do
           sudo systemctl stop "citadel-$model.service" || true
       done
       
       sudo systemctl stop citadel-gpu.service || true
       sudo systemctl stop citadel-storage.service || true
       
       echo "✅ Emergency rollback completed"
   }
   
   graceful_rollback() {
       echo "=== GRACEFUL ROLLBACK ==="
       
       # Gracefully stop services in reverse order
       echo "Stopping main target..."
       sudo systemctl stop citadel-ai.target || true
       
       echo "Stopping monitoring..."
       sudo systemctl stop citadel-monitor.service || true
       
       echo "Stopping model services..."
       models=("vision" "coder" "phi3" "openchat" "hermes" "yi34b" "mixtral")
       for model in "${models[@]}"; do
           if systemctl is-active --quiet "citadel-$model.service"; then
               echo "  Stopping $model..."
               sudo systemctl stop "citadel-$model.service"
               sleep 5
           fi
       done
       
       echo "Stopping models target..."
       sudo systemctl stop citadel-models.target || true
       
       echo "Stopping infrastructure services..."
       sudo systemctl stop citadel-gpu.service || true
       sudo systemctl stop citadel-storage.service || true
       
       echo "✅ Graceful rollback completed"
   }
   
   partial_rollback() {
       local group="$1"
       
       echo "=== PARTIAL ROLLBACK: $group ==="
       
       case "$group" in
           models)
               models=("mixtral" "yi34b" "hermes" "openchat" "phi3" "coder" "vision")
               for model in "${models[@]}"; do
                   echo "Stopping $model..."
                   sudo systemctl stop "citadel-$model.service" || true
               done
               sudo systemctl stop citadel-models.target || true
               ;;
           infrastructure)
               sudo systemctl stop citadel-gpu.service || true
               sudo systemctl stop citadel-storage.service || true
               ;;
           monitoring)
               sudo systemctl stop citadel-monitor.service || true
               ;;
           *)
               echo "Unknown group: $group"
               exit 1
               ;;
       esac
       
       echo "✅ Partial rollback completed"
   }
   
   backup_configuration() {
       local backup_id="backup-$(date +%Y%m%d-%H%M%S)"
       local backup_dir="/opt/citadel/backups/services/$backup_id"
       
       echo "=== CREATING CONFIGURATION BACKUP ==="
       echo "Backup ID: $backup_id"
       
       mkdir -p "$backup_dir"
       
       # Backup systemd service files
       cp -r /etc/systemd/system/citadel-*.service "$backup_dir/" 2>/dev/null || true
       cp -r /etc/systemd/system/citadel-*.target "$backup_dir/" 2>/dev/null || true
       cp /etc/systemd/system/citadel-ai.env "$backup_dir/" 2>/dev/null || true
       
       # Backup service scripts
       cp -r /opt/citadel/services "$backup_dir/" 2>/dev/null || true
       
       # Create backup manifest
       cat > "$backup_dir/manifest.txt" << EOF
   Citadel AI Service Configuration Backup
   Created: $(date)
   Backup ID: $backup_id
   
   Contents:
   - Systemd service files
   - Service scripts and configurations
   - Environment configuration
   EOF
       
       echo "✅ Backup created: $backup_dir"
       echo "$backup_id" > /opt/citadel/backups/services/latest-backup.txt
   }
   
   restore_configuration() {
       local backup_id="$1"
       local backup_dir="/opt/citadel/backups/services/$backup_id"
       
       if [ ! -d "$backup_dir" ]; then
           echo "❌ Backup not found: $backup_id"
           exit 1
       fi
       
       echo "=== RESTORING CONFIGURATION ==="
       echo "Restoring from: $backup_id"
       
       # Stop services first
       graceful_rollback
       
       # Restore files
       sudo cp "$backup_dir"/citadel-*.service /etc/systemd/system/ 2>/dev/null || true
       sudo cp "$backup_dir"/citadel-*.target /etc/systemd/system/ 2>/dev/null || true
       sudo cp "$backup_dir/citadel-ai.env" /etc/systemd/system/ 2>/dev/null || true
       
       # Restore service scripts
       cp -r "$backup_dir/services/"* /opt/citadel/services/ 2>/dev/null || true
       
       # Reload systemd
       sudo systemctl daemon-reload
       
       echo "✅ Configuration restored from backup"
   }
   
   # Main execution
   action="${1:-}"
   
   if [ -z "$action" ]; then
       show_usage
       exit 1
   fi
   
   case "$action" in
       emergency)
           emergency_rollback
           ;;
       graceful)
           graceful_rollback
           ;;
       partial)
           partial_rollback "${2:-models}"
           ;;
       backup)
           backup_configuration
           ;;
       restore)
           restore_configuration "${2:-}"
           ;;
       status)
           /opt/citadel/scripts/citadel-service.sh health
           ;;
       help|--help|-h)
           show_usage
           ;;
       *)
           echo "Unknown action: $action"
           show_usage
           exit 1
           ;;
   esac
   EOF
   
   chmod +x /opt/citadel/scripts/rollback-services.sh
   
   # Create convenient alias
   sudo ln -sf /opt/citadel/scripts/rollback-services.sh /usr/local/bin/citadel-rollback
   ```

2. **Create Backup Directory Structure**
   ```bash
   # Create backup directory structure
   mkdir -p /opt/citadel/backups/services
   mkdir -p /opt/citadel/backups/configs
   
   # Set permissions
   chmod 755 /opt/citadel/backups
   chown -R agent0:agent0 /opt/citadel/backups
   ```

## Monitoring Integration Preparation

### Step 1: Prepare for Prometheus/Grafana Integration

1. **Create Monitoring Endpoints**
   ```bash
   # Create monitoring preparation script
   tee /opt/citadel/scripts/prepare-monitoring.sh << 'EOF'
   #!/bin/bash
   # prepare-monitoring.sh - Prepare infrastructure for Prometheus/Grafana monitoring
   
   set -euo pipefail
   
   echo "=== Preparing Monitoring Infrastructure ==="
   
   # Create monitoring configuration directory
   mkdir -p /opt/citadel/monitoring/{prometheus,grafana,exporters}
   mkdir -p /opt/citadel/monitoring/configs
   
   # Create metrics endpoints configuration
   cat > /opt/citadel/monitoring/configs/endpoints.yaml << 'YAML'
   # Citadel AI Monitoring Endpoints Configuration
   # This file will be used by future monitoring tasks
   
   prometheus:
     scrape_configs:
       - job_name: 'citadel-models'
         static_configs:
           - targets:
             - 'localhost:11400'  # mixtral
             - 'localhost:11401'  # hermes
             - 'localhost:11402'  # openchat
             - 'localhost:11403'  # phi3
             - 'localhost:11404'  # yi34b
             - 'localhost:11405'  # coder
             - 'localhost:11500'  # vision
         metrics_path: '/metrics'
         scrape_interval: 15s
         
       - job_name: 'citadel-system'
         static_configs:
           - targets:
             - 'localhost:9100'  # node-exporter
             - 'localhost:9101'  # gpu-exporter
         scrape_interval: 15s
         
   grafana:
     dashboards:
       - name: 'citadel-overview'
         path: '/opt/citadel/monitoring/grafana/dashboards/overview.json'
       - name: 'citadel-models'
         path: '/opt/citadel/monitoring/grafana/dashboards/models.json'
       - name: 'citadel-system'
         path: '/opt/citadel/monitoring/grafana/dashboards/system.json'
   YAML
   
   # Create monitoring service integration hooks
   cat > /opt/citadel/scripts/monitoring-hooks.sh << 'HOOKS'
   #!/bin/bash
   # monitoring-hooks.sh - Integration hooks for monitoring services
   
   # Function to be called by model services to register metrics
   register_model_metrics() {
       local model_name="$1"
       local port="$2"
       
       echo "Registering metrics for $model_name on port $port"
       # This will be implemented in future monitoring tasks
   }
   
   # Function to be called by health monitor to expose metrics
   expose_health_metrics() {
       local status="$1"
       local model_name="$2"
       
       echo "Exposing health metrics: $model_name=$status"
       # This will be implemented in future monitoring tasks
   }
   
   # Function to prepare service discovery for Prometheus
   prepare_service_discovery() {
       echo "Preparing service discovery configuration"
       # This will be implemented in future monitoring tasks
   }
   HOOKS
   
   chmod +x /opt/citadel/scripts/monitoring-hooks.sh
   
   # Create placeholder for monitoring configuration
   cat > /opt/citadel/monitoring/README.md << 'README'
   # Citadel AI Monitoring Infrastructure
   
   This directory contains the monitoring infrastructure preparation for Citadel AI services.
   
   ## Directory Structure
   - `prometheus/` - Prometheus configuration and data
   - `grafana/` - Grafana dashboards and configuration
   - `exporters/` - Custom metrics exporters
   - `configs/` - Monitoring configuration files
   
   ## Integration Points
   - Model services expose metrics on `/metrics` endpoint
   - Health monitor integrates with monitoring system
   - System metrics collected via node-exporter and GPU-exporter
   
   ## Future Implementation
   This infrastructure will be fully implemented in future monitoring tasks (PLANB-08+).
   
   ## Prepared Endpoints
   - Model services: ports 11400-11405, 11500
   - System metrics: ports 9100-9101
   - Health status: integrated with systemd journal
   README
   
   # Set permissions
   chown -R agent0:agent0 /opt/citadel/monitoring
   chmod 755 /opt/citadel/monitoring
   
   echo "✅ Monitoring infrastructure prepared"
   echo "📊 Ready for Prometheus/Grafana integration in future tasks"
   EOF
   
   chmod +x /opt/citadel/scripts/prepare-monitoring.sh
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
## Service Installation and Configuration

### Step 1: Install and Enable Services (Updated for Incremental Deployment)

1. **Use Incremental Deployment Approach**
   ```bash
   # Create configuration backup first
   /opt/citadel/scripts/rollback-services.sh backup
   
   # Deploy services incrementally
   echo "=== Incremental Service Deployment ==="
   
   # Phase 1: Infrastructure
   citadel-deploy validate
   citadel-deploy phase1
   
   # Phase 2: Test single model
   citadel-deploy phase2 phi3
   
   # Phase 3: Deploy remaining models (if tests pass)
   citadel-deploy phase3
   
   # Phase 4: Enable monitoring
   citadel-deploy phase4
   
   echo "All services deployed incrementally"
   ```

2. **Prepare Monitoring Infrastructure**
   ```bash
   # Prepare monitoring integration
   /opt/citadel/scripts/prepare-monitoring.sh
   
   echo "Monitoring infrastructure prepared for future integration"
   ```

3. **Create Service Logs Directory**
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

## Enhanced Validation Steps

### Step 1: Prerequisites and Installation Verification

```bash
# Enhanced validation with prerequisites check
echo "=== Enhanced Service Validation ==="

# Step 1: Validate prerequisites
echo "1. Validating prerequisites..."
/opt/citadel/scripts/validate-prerequisites.sh

# Step 2: Validate models
echo "2. Validating models..."
/opt/citadel/scripts/validate-models.sh

# Step 3: Verify service installation
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

### Step 3: Incremental Deployment Test

```bash
# Incremental deployment test
echo "=== Incremental Deployment Test ==="

# Phase 1: Infrastructure
echo "Phase 1: Infrastructure services..."
citadel-deploy phase1

# Phase 2: Test model
echo "Phase 2: Test model service..."
citadel-deploy phase2 phi3

# Phase 3: All models
echo "Phase 3: All model services..."
citadel-deploy phase3

# Phase 4: Monitoring
echo "Phase 4: Monitoring services..."
citadel-deploy phase4

# Final health check
citadel health

# Test rollback capability
echo ""
echo "Testing rollback capability..."
citadel-rollback backup
echo "Backup created for rollback testing"
```

### Step 4: Monitoring Preparation Test

```bash
# Test monitoring preparation
echo "=== Monitoring Preparation Test ==="

# Prepare monitoring infrastructure
/opt/citadel/scripts/prepare-monitoring.sh

# Verify monitoring endpoints configuration
echo "Monitoring endpoints configured:"
cat /opt/citadel/monitoring/configs/endpoints.yaml

# Verify integration hooks
echo "Integration hooks prepared:"
ls -la /opt/citadel/scripts/monitoring-hooks.sh

echo "✅ System ready for Prometheus/Grafana integration"
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

### Issue: Rollback Failures
**Symptoms**: Services won't stop, rollback script fails
**Solutions**:
- Use emergency rollback: `citadel-rollback emergency`
- Check for stuck processes: `ps aux | grep vllm`
- Manually kill processes: `pkill -f vllm`
- Verify backup integrity: `ls -la /opt/citadel/backups/services/`

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
- **citadel-deploy**: Incremental deployment management
- **citadel-rollback**: Emergency rollback and backup system

### Auto-start Configuration
- All services enabled for automatic startup
- Proper dependency chain configured
- Health monitoring with automatic restart
- Log rotation configured

### New Safety Features
- **Prerequisites validation**: Comprehensive system checks before deployment
- **Incremental deployment**: Phase-by-phase service rollout
- **Rollback system**: Emergency stop and configuration backup/restore
- **Monitoring preparation**: Infrastructure ready for Prometheus/Grafana

## Deployment Guide

### Recommended Deployment Sequence

1. **Prerequisites Validation**
   ```bash
   # Validate all prerequisites
   /opt/citadel/scripts/validate-prerequisites.sh
   /opt/citadel/scripts/validate-models.sh
   ```

2. **Incremental Deployment**
   ```bash
   # Create configuration backup
   citadel-rollback backup
   
   # Deploy incrementally
   citadel-deploy phase1    # Infrastructure
   citadel-deploy phase2    # Test model
   citadel-deploy phase3    # All models
   citadel-deploy phase4    # Monitoring
   ```

3. **Monitoring Preparation**
   ```bash
   # Prepare for future monitoring integration
   /opt/citadel/scripts/prepare-monitoring.sh
   ```

4. **Validation and Testing**
   ```bash
   # Verify deployment
   citadel health
   citadel-deploy status
   
   # Test rollback (optional)
   citadel-rollback graceful
   citadel-deploy phase1  # Re-deploy for testing
   ```

### Emergency Procedures

- **Emergency Stop**: `citadel-rollback emergency`
- **Graceful Rollback**: `citadel-rollback graceful`
- **Restore from Backup**: `citadel-rollback restore <backup-id>`

## Next Steps

### Immediate Next Tasks
- Continue to **[PLANB-08-Backup-Monitoring.md](PLANB-08-Backup-Monitoring.md)** for backup strategy implementation
- Monitoring infrastructure is prepared for Prometheus/Grafana integration

### Future Monitoring Integration
- Prometheus metrics collection from model endpoints
- Grafana dashboards for system visualization
- Alerting integration with health monitoring system

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 45-60 minutes (+ 15 minutes for new features)  
**Complexity**: High  
**Prerequisites**: All previous tasks completed, vLLM working, symlinks configured  
**New Features**: Prerequisites validation, incremental deployment, rollback strategy, monitoring preparation