#!/bin/bash
# verify-models.sh - Verify model integrity and storage health

set -euo pipefail

MODELS_DIR="/mnt/citadel-models/active"
LOG_FILE="/opt/citadel/logs/verify.log"

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

echo "=== Model Verification Report $(date) ===" | tee -a "$LOG_FILE"

# Check model directory accessibility
if [ ! -d "$MODELS_DIR" ]; then
    echo "ERROR: Models directory not accessible: $MODELS_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Check available space using more robust approach
AVAILABLE_SPACE=$(df --output=avail -B1 "$MODELS_DIR" | tail -n1)
SPACE_GB=$((AVAILABLE_SPACE / 1024 / 1024 / 1024))

echo "Available space: ${SPACE_GB}GB" | tee -a "$LOG_FILE"

if [ "$SPACE_GB" -lt 100 ]; then
    echo "WARNING: Low disk space on model storage" | tee -a "$LOG_FILE"
fi

# Check model directories
MODEL_COUNT=0
# Enable nullglob to handle empty directories correctly
shopt -s nullglob
for model_dir in "$MODELS_DIR"/*; do
    if [ -d "$model_dir" ]; then
        MODEL_NAME=$(basename "$model_dir")
        MODEL_SIZE=$(du -sh "$model_dir" 2>/dev/null | cut -f1 || echo "Unknown")
        echo "Model: $MODEL_NAME - Size: $MODEL_SIZE" | tee -a "$LOG_FILE"
        ((MODEL_COUNT++))
    fi
done
# Restore default globbing behavior
shopt -u nullglob

echo "Total models found: $MODEL_COUNT" | tee -a "$LOG_FILE"

# Check storage health (if smartctl available)
if command -v smartctl >/dev/null 2>&1; then
    # Get the device path more robustly
    DEVICE_PATH=$(df --output=source "$MODELS_DIR" | tail -n1)
    # Extract base device by removing partition numbers
    NVME_DEVICE=$(echo "$DEVICE_PATH" | sed 's/p[0-9]*$//')
    if [ -b "$NVME_DEVICE" ]; then
        echo "Storage health check for $NVME_DEVICE:" | tee -a "$LOG_FILE"
        # Use -n flag to prevent password prompts in non-interactive environments
        sudo -n smartctl -H "$NVME_DEVICE" 2>/dev/null | grep -E "(SMART|Health)" | tee -a "$LOG_FILE" || echo "Health check unavailable (requires sudo privileges)" | tee -a "$LOG_FILE"
    fi
fi

echo "Verification completed: $(date)" | tee -a "$LOG_FILE"
echo "======================================" | tee -a "$LOG_FILE"