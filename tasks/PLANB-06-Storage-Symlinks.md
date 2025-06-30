# PLANB-06: Model Storage Symlink Configuration and Integration

**Task:** Configure model storage symlinks and integrate with dedicated storage architecture  
**Duration:** 20-30 minutes  
**Prerequisites:** PLANB-01 through PLANB-05 completed, vLLM installed, storage configured  

## Overview

This task configures the symlink integration between the application directory structure and the dedicated model storage, ensuring seamless access to models while maintaining the optimized storage architecture.

## Storage Integration Architecture

### Current Storage State
```
Storage Configuration:
├── /opt/citadel/                   # Application directory (1TB LVM)
│   ├── models/                     # → Symlink to /mnt/citadel-models/active
│   ├── vllm-env/                   # Python virtual environment
│   ├── scripts/                    # Management scripts
│   └── configs/                    # Configuration files
├── /mnt/citadel-models/            # Dedicated model storage (3.6TB NVMe)
│   ├── active/                     # Active models (symlinked)
│   ├── archive/                    # Archived models
│   ├── downloads/                  # Download staging
│   └── cache/                      # Temporary cache
└── /mnt/citadel-backup/            # Backup storage (7.3TB HDD)
    ├── models/                     # Model backups
    └── system/                     # System backups
```

### Target Symlink Structure
```
/opt/citadel/models/                # Main symlink → /mnt/citadel-models/active
├── mixtral-8x7b-instruct/         # Individual model directories
├── yi-34b-chat/
├── nous-hermes-2-mixtral/
├── openchat-3.5/
├── phi-3-mini-128k/
├── deepcoder-14b-instruct/
└── mimo-vl-7b-rl/

/opt/citadel/model-links/           # Convenience symlinks
├── mixtral → /mnt/citadel-models/active/mixtral-8x7b-instruct
├── yi34b → /mnt/citadel-models/active/yi-34b-chat
├── hermes → /mnt/citadel-models/active/nous-hermes-2-mixtral
├── openchat → /mnt/citadel-models/active/openchat-3.5
├── phi3 → /mnt/citadel-models/active/phi-3-mini-128k
├── coder → /mnt/citadel-models/active/deepcoder-14b-instruct
└── vision → /mnt/citadel-models/active/mimo-vl-7b-rl
```

## Symlink Configuration Steps

### Step 1: Verify Storage Prerequisites

1. **Check Storage Mount Status**
   ```bash
   # Verify all storage is properly mounted
   echo "=== Storage Mount Verification ==="
   df -h | grep -E "(citadel|nvme|sda)"
   echo ""
   mount | grep citadel
   echo ""
   
   # Check directory structure
   ls -la /mnt/citadel-models/
   ls -la /mnt/citadel-backup/
   ls -la /opt/citadel/
   ```

2. **Verify Permissions**
   ```bash
   # Check ownership and permissions
   echo "=== Permission Verification ==="
   ls -la /opt/citadel/
   ls -la /mnt/citadel-models/
   ls -la /mnt/citadel-backup/
   
   # Ensure agent0 owns directories
   sudo chown -R agent0:agent0 /opt/citadel
   sudo chown -R agent0:agent0 /mnt/citadel-models
   sudo chown -R agent0:agent0 /mnt/citadel-backup
   ```

### Step 2: Create Model Directory Structure

1. **Create Individual Model Directories**
   ```bash
   # Create directories for each model on dedicated storage
   echo "=== Creating Model Directory Structure ==="
   
   # Model names and their storage directories
   declare -A MODELS=(
       ["mixtral-8x7b-instruct"]="Mixtral-8x7B-Instruct-v0.1"
       ["yi-34b-chat"]="Yi-34B-Chat"
       ["nous-hermes-2-mixtral"]="Nous-Hermes-2-Mixtral-8x7B-DPO"
       ["openchat-3.5"]="openchat-3.5-1210"
       ["phi-3-mini-128k"]="Phi-3-mini-128k-instruct"
       ["deepcoder-14b-instruct"]="deepseek-coder-14b-instruct-v1.5"
       ["mimo-vl-7b-rl"]="imp-v1_5-7b"
   )
   
   # Create model directories
   for model_dir in "${!MODELS[@]}"; do
       echo "Creating directory: $model_dir"
       mkdir -p "/mnt/citadel-models/active/$model_dir"
       chmod 755 "/mnt/citadel-models/active/$model_dir"
   done
   
   # Verify creation
   ls -la /mnt/citadel-models/active/
   ```

2. **Create Archive and Cache Directories**
   ```bash
   # Create additional storage directories
   mkdir -p /mnt/citadel-models/{archive,downloads,cache,staging}
   mkdir -p /mnt/citadel-models/archive/{monthly,weekly,daily}
   mkdir -p /mnt/citadel-models/cache/{tokenizers,compiled,temporary}
   
   # Set appropriate permissions
   chmod 755 /mnt/citadel-models/archive
   chmod 775 /mnt/citadel-models/downloads
   chmod 775 /mnt/citadel-models/cache
   chmod 775 /mnt/citadel-models/staging
   
   echo "Storage directory structure created"
   ```

### Step 3: Create Primary Symlinks

1. **Create Main Models Symlink**
   ```bash
   # Remove existing models directory if it exists
   if [ -e "/opt/citadel/models" ]; then
       echo "Removing existing models directory/symlink..."
       rm -rf /opt/citadel/models
   fi
   
   # Create primary symlink
   echo "Creating primary models symlink..."
   ln -sf /mnt/citadel-models/active /opt/citadel/models
   
   # Verify symlink
   ls -la /opt/citadel/models
   echo "Primary symlink created: /opt/citadel/models → /mnt/citadel-models/active"
   ```

2. **Create Convenience Symlinks**
   ```bash
   # Create convenience symlink directory
   mkdir -p /opt/citadel/model-links
   
   # Create short-name symlinks for easy access
   declare -A SHORT_NAMES=(
       ["mixtral"]="mixtral-8x7b-instruct"
       ["yi34b"]="yi-34b-chat"
       ["hermes"]="nous-hermes-2-mixtral"
       ["openchat"]="openchat-3.5"
       ["phi3"]="phi-3-mini-128k"
       ["coder"]="deepcoder-14b-instruct"
       ["vision"]="mimo-vl-7b-rl"
   )
   
   # Create convenience symlinks
   for short_name in "${!SHORT_NAMES[@]}"; do
       full_name="${SHORT_NAMES[$short_name]}"
       echo "Creating convenience symlink: $short_name → $full_name"
       ln -sf "/mnt/citadel-models/active/$full_name" "/opt/citadel/model-links/$short_name"
   done
   
   # Verify convenience symlinks
   ls -la /opt/citadel/model-links/
   ```

### Step 4: Create Cache and Download Symlinks

1. **Create Cache Symlinks**
   ```bash
   # Create symlinks for cache directories
   echo "Creating cache symlinks..."
   
   # Hugging Face cache
   mkdir -p /home/agent0/.cache
   if [ -e "/home/agent0/.cache/huggingface" ]; then
       rm -rf /home/agent0/.cache/huggingface
   fi
   ln -sf /mnt/citadel-models/cache /home/agent0/.cache/huggingface
   
   # PyTorch cache
   if [ -e "/home/agent0/.cache/torch" ]; then
       rm -rf /home/agent0/.cache/torch
   fi
   ln -sf /mnt/citadel-models/cache/torch /home/agent0/.cache/torch
   mkdir -p /mnt/citadel-models/cache/torch
   
   # vLLM cache
   mkdir -p /mnt/citadel-models/cache/vllm
   export VLLM_CACHE_ROOT="/mnt/citadel-models/cache/vllm"
   
   echo "Cache symlinks created"
   ```

2. **Create Download Staging Links**
   ```bash
   # Create download staging symlinks
   echo "Creating download staging symlinks..."
   
   # Create staging symlink in application directory
   ln -sf /mnt/citadel-models/downloads /opt/citadel/downloads
   ln -sf /mnt/citadel-models/staging /opt/citadel/staging
   
   # Verify download symlinks
   ls -la /opt/citadel/ | grep -E "(downloads|staging)"
   ```

### Step 5: Configure Environment Variables

1. **Create Environment Configuration**
   ```bash
   # Create environment configuration for symlinks
   tee /opt/citadel/configs/storage-env.sh << 'EOF'
   #!/bin/bash
   # storage-env.sh - Storage environment configuration
   
   # Model storage paths
   export CITADEL_MODELS_ROOT="/mnt/citadel-models"
   export CITADEL_MODELS_ACTIVE="/mnt/citadel-models/active"
   export CITADEL_MODELS_ARCHIVE="/mnt/citadel-models/archive"
   export CITADEL_MODELS_CACHE="/mnt/citadel-models/cache"
   export CITADEL_MODELS_DOWNLOADS="/mnt/citadel-models/downloads"
   
   # Backup storage paths
   export CITADEL_BACKUP_ROOT="/mnt/citadel-backup"
   export CITADEL_BACKUP_MODELS="/mnt/citadel-backup/models"
   export CITADEL_BACKUP_SYSTEM="/mnt/citadel-backup/system"
   
   # Application paths
   export CITADEL_APP_ROOT="/opt/citadel"
   export CITADEL_APP_MODELS="/opt/citadel/models"
   export CITADEL_APP_CONFIGS="/opt/citadel/configs"
   export CITADEL_APP_SCRIPTS="/opt/citadel/scripts"
   export CITADEL_APP_LOGS="/opt/citadel/logs"
   
   # Cache configuration
   export HF_HOME="/mnt/citadel-models/cache"
   export HUGGINGFACE_HUB_CACHE="/mnt/citadel-models/cache"
   export TRANSFORMERS_CACHE="/mnt/citadel-models/cache/transformers"
   export TORCH_HOME="/mnt/citadel-models/cache/torch"
   export VLLM_CACHE_ROOT="/mnt/citadel-models/cache/vllm"
   
   # Model-specific paths
   export CITADEL_MODEL_MIXTRAL="$CITADEL_MODELS_ACTIVE/mixtral-8x7b-instruct"
   export CITADEL_MODEL_YI34B="$CITADEL_MODELS_ACTIVE/yi-34b-chat"
   export CITADEL_MODEL_HERMES="$CITADEL_MODELS_ACTIVE/nous-hermes-2-mixtral"
   export CITADEL_MODEL_OPENCHAT="$CITADEL_MODELS_ACTIVE/openchat-3.5"
   export CITADEL_MODEL_PHI3="$CITADEL_MODELS_ACTIVE/phi-3-mini-128k"
   export CITADEL_MODEL_CODER="$CITADEL_MODELS_ACTIVE/deepcoder-14b-instruct"
   export CITADEL_MODEL_VISION="$CITADEL_MODELS_ACTIVE/mimo-vl-7b-rl"
   
   echo "Storage environment variables loaded"
   EOF
   
   chmod +x /opt/citadel/configs/storage-env.sh
   ```

2. **Update Shell Profile**
   ```bash
   # Add storage environment to shell profile
   if ! grep -q "storage-env.sh" ~/.bashrc; then
       echo "" >> ~/.bashrc
       echo "# Citadel AI Storage Environment" >> ~/.bashrc
       echo "source /opt/citadel/configs/storage-env.sh" >> ~/.bashrc
   fi
   
   # Source the environment
   source /opt/citadel/configs/storage-env.sh
   ```

### Step 6: Create Storage Management Scripts

1. **Create Symlink Verification Script**
   ```bash
   # Create symlink verification script
   tee /opt/citadel/scripts/verify-symlinks.sh << 'EOF'
   #!/bin/bash
   # verify-symlinks.sh - Verify symlink integrity
   
   echo "=== Citadel AI Storage Symlink Verification ==="
   echo ""
   
   # Check primary symlinks
   echo "Primary Symlinks:"
   check_symlink() {
       local link_path="$1"
       local description="$2"
       
       if [ -L "$link_path" ]; then
           local target=$(readlink "$link_path")
           if [ -e "$target" ]; then
               echo "  ✅ $description: $link_path → $target"
           else
               echo "  ❌ $description: $link_path → $target (target missing)"
           fi
       else
           echo "  ❌ $description: $link_path (not a symlink)"
       fi
   }
   
   check_symlink "/opt/citadel/models" "Main models directory"
   check_symlink "/opt/citadel/downloads" "Downloads directory"
   check_symlink "/opt/citadel/staging" "Staging directory"
   
   echo ""
   echo "Convenience Symlinks:"
   for link in /opt/citadel/model-links/*; do
       if [ -L "$link" ]; then
           name=$(basename "$link")
           target=$(readlink "$link")
           if [ -e "$target" ]; then
               echo "  ✅ $name → $target"
           else
               echo "  ❌ $name → $target (target missing)"
           fi
       fi
   done
   
   echo ""
   echo "Cache Symlinks:"
   check_symlink "/home/agent0/.cache/huggingface" "Hugging Face cache"
   check_symlink "/home/agent0/.cache/torch" "PyTorch cache"
   
   echo ""
   echo "Storage Usage:"
   df -h | grep -E "(citadel|nvme|sda)" | while read line; do
       echo "  $line"
   done
   
   echo ""
   echo "Symlink verification completed"
   EOF
   
   chmod +x /opt/citadel/scripts/verify-symlinks.sh
   ```

2. **Create Symlink Repair Script**
   ```bash
   # Create symlink repair script
   tee /opt/citadel/scripts/repair-symlinks.sh << 'EOF'
   #!/bin/bash
   # repair-symlinks.sh - Repair broken symlinks
   
   echo "=== Citadel AI Storage Symlink Repair ==="
   echo ""
   
   # Function to create or repair symlink
   repair_symlink() {
       local link_path="$1"
       local target_path="$2"
       local description="$3"
       
       echo "Repairing: $description"
       
       # Remove existing link if it exists
       if [ -e "$link_path" ] || [ -L "$link_path" ]; then
           rm -f "$link_path"
       fi
       
       # Create target directory if it doesn't exist
       mkdir -p "$(dirname "$target_path")"
       
       # Create symlink
       ln -sf "$target_path" "$link_path"
       
       if [ -L "$link_path" ]; then
           echo "  ✅ $description repaired: $link_path → $target_path"
       else
           echo "  ❌ Failed to repair: $description"
       fi
   }
   
   # Repair primary symlinks
   echo "Repairing primary symlinks..."
   repair_symlink "/opt/citadel/models" "/mnt/citadel-models/active" "Main models directory"
   repair_symlink "/opt/citadel/downloads" "/mnt/citadel-models/downloads" "Downloads directory"
   repair_symlink "/opt/citadel/staging" "/mnt/citadel-models/staging" "Staging directory"
   
   echo ""
   echo "Repairing convenience symlinks..."
   
   # Recreate convenience symlinks
   mkdir -p /opt/citadel/model-links
   
   declare -A SHORT_NAMES=(
       ["mixtral"]="mixtral-8x7b-instruct"
       ["yi34b"]="yi-34b-chat"
       ["hermes"]="nous-hermes-2-mixtral"
       ["openchat"]="openchat-3.5"
       ["phi3"]="phi-3-mini-128k"
       ["coder"]="deepcoder-14b-instruct"
       ["vision"]="mimo-vl-7b-rl"
   )
   
   for short_name in "${!SHORT_NAMES[@]}"; do
       full_name="${SHORT_NAMES[$short_name]}"
       repair_symlink "/opt/citadel/model-links/$short_name" "/mnt/citadel-models/active/$full_name" "Convenience link: $short_name"
   done
   
   echo ""
   echo "Repairing cache symlinks..."
   mkdir -p /home/agent0/.cache
   repair_symlink "/home/agent0/.cache/huggingface" "/mnt/citadel-models/cache" "Hugging Face cache"
   repair_symlink "/home/agent0/.cache/torch" "/mnt/citadel-models/cache/torch" "PyTorch cache"
   
   echo ""
   echo "Setting proper permissions..."
   chown -R agent0:agent0 /opt/citadel
   chown -R agent0:agent0 /mnt/citadel-models
   chown -R agent0:agent0 /home/agent0/.cache
   
   echo ""
   echo "Symlink repair completed"
   EOF
   
   chmod +x /opt/citadel/scripts/repair-symlinks.sh
   ```

## Validation Steps

### Step 1: Symlink Verification
```bash
# Comprehensive symlink verification
echo "=== Symlink Verification ==="
/opt/citadel/scripts/verify-symlinks.sh
```

### Step 2: Access Testing
```bash
# Test symlink access
echo "=== Access Testing ==="

# Test main models symlink
echo "Testing main models symlink:"
ls -la /opt/citadel/models
echo ""

# Test convenience symlinks
echo "Testing convenience symlinks:"
ls -la /opt/citadel/model-links/
echo ""

# Test write access through symlinks
echo "Testing write access:"
touch /opt/citadel/models/test-write.txt 2>/dev/null && echo "✅ Write test passed" || echo "❌ Write test failed"
ls -la /mnt/citadel-models/active/test-write.txt 2>/dev/null && rm -f /opt/citadel/models/test-write.txt
```

### Step 3: Environment Variable Testing
```bash
# Test environment variables
echo "=== Environment Variable Testing ==="
source /opt/citadel/configs/storage-env.sh

echo "Storage environment variables:"
env | grep CITADEL | sort
echo ""

echo "Cache environment variables:"
env | grep -E "(HF_|TRANSFORMERS_|TORCH_|VLLM_)" | sort
```

### Step 4: Performance Testing
```bash
# Test symlink performance
echo "=== Performance Testing ==="

# Test read performance through symlink
echo "Testing read performance..."
time ls -la /opt/citadel/models/ > /dev/null

# Test write performance through symlink
echo "Testing write performance..."
time dd if=/dev/zero of=/opt/citadel/models/test-perf bs=1M count=100 2>/dev/null
rm -f /opt/citadel/models/test-perf

echo "Performance test completed"
```

## Troubleshooting

### Issue: Broken Symlinks
**Symptoms**: Symlinks pointing to non-existent targets
**Solutions**:
- Run repair script: `/opt/citadel/scripts/repair-symlinks.sh`
- Check target directories: `ls -la /mnt/citadel-models/`
- Verify mount points: `mount | grep citadel`

### Issue: Permission Denied
**Symptoms**: Cannot access through symlinks
**Solutions**:
- Check ownership: `ls -la /opt/citadel/ /mnt/citadel-models/`
- Fix permissions: `sudo chown -R agent0:agent0 /opt/citadel /mnt/citadel-models`
- Verify user membership: `groups agent0`

### Issue: Performance Issues
**Symptoms**: Slow access through symlinks
**Solutions**:
- Check storage mount options: `mount | grep citadel`
- Verify storage health: `sudo smartctl -a /dev/nvme1n1`
- Check I/O statistics: `iostat -x 1`

### Issue: Environment Variables Not Set
**Symptoms**: Applications can't find models/cache
**Solutions**:
- Source environment: `source /opt/citadel/configs/storage-env.sh`
- Check shell profile: `grep storage-env ~/.bashrc`
- Restart shell session: `exec bash`

## Configuration Summary

### Symlinks Created
- ✅ **Main Models**: `/opt/citadel/models` → `/mnt/citadel-models/active`
- ✅ **Downloads**: `/opt/citadel/downloads` → `/mnt/citadel-models/downloads`
- ✅ **Staging**: `/opt/citadel/staging` → `/mnt/citadel-models/staging`
- ✅ **Convenience Links**: Short names for easy model access
- ✅ **Cache Links**: Hugging Face and PyTorch cache redirection

### Environment Variables
- Storage paths for all components
- Cache redirection for ML libraries
- Model-specific path variables
- Backup and archive paths

### Management Tools
- **verify-symlinks.sh**: Check symlink integrity
- **repair-symlinks.sh**: Repair broken symlinks
- **storage-env.sh**: Environment configuration

## Next Steps

Continue to **[PLANB-07-Service-Configuration.md](PLANB-07-Service-Configuration.md)** for systemd service configuration and automated startup procedures.

---

**Task Status**: ⚠️ **Ready for Implementation**  
**Estimated Time**: 20-30 minutes  
**Complexity**: Medium  
**Prerequisites**: Storage configured, vLLM installed, directories created