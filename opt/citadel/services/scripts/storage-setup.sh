#!/bin/bash
# storage-setup.sh - Citadel AI Storage Verification and Setup
set -euo pipefail

echo "[storage-setup] Starting Citadel storage setup..."

# Ensure mount points exist
for dir in /mnt/citadel-models /mnt/citadel-backup; do
    if ! mountpoint -q "$dir"; then
        echo "[storage-setup] ERROR: $dir is not mounted."
        exit 1
    fi
    echo "[storage-setup] Verified mount: $dir"
done

# Ensure symlink exists
if [ ! -L /opt/citadel/models ] || [ ! -d /opt/citadel/models ]; then
    ln -sf /mnt/citadel-models/active /opt/citadel/models
    echo "[storage-setup] Created symlink: /opt/citadel/models -> /mnt/citadel-models/active"
else
    echo "[storage-setup] Symlink already exists: /opt/citadel/models"
fi

# Create required directories
for d in /mnt/citadel-models/cache /mnt/citadel-models/downloads /mnt/citadel-models/archive; do
    mkdir -p "$d"
    echo "[storage-setup] Ensured directory: $d"
done

# Set permissions
chown -R agent0:agent0 /mnt/citadel-models /mnt/citadel-backup || true
chmod -R 755 /mnt/citadel-models /mnt/citadel-backup || true

echo "[storage-setup] Storage setup complete."
