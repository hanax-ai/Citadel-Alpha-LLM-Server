#!/bin/bash
# storage-cleanup.sh - Citadel AI Storage Cleanup
set -euo pipefail

echo "[storage-cleanup] Starting Citadel storage cleanup..."

# Remove symlink if it exists
if [ -L /opt/citadel/models ]; then
    rm -f /opt/citadel/models
    echo "[storage-cleanup] Removed symlink: /opt/citadel/models"
fi

# Optionally clean up cache or temp directories (customize as needed)
# rm -rf /mnt/citadel-models/cache/*
# echo "[storage-cleanup] Cleared model cache."

echo "[storage-cleanup] Storage cleanup complete."
