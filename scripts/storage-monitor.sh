#!/bin/bash
# storage-monitor.sh - Monitor storage performance and usage

# Dynamically detect storage devices from mount points
NVME_MODEL_DEVICE=""
BACKUP_DEVICE=""

# Detect model storage device
if mountpoint -q /mnt/citadel-models 2>/dev/null; then
    MODEL_DEVICE_PATH=$(df --output=source /mnt/citadel-models | tail -n1)
    # Strip partition numbers to get base device (e.g., /dev/nvme1n1p1 -> /dev/nvme1n1)
    NVME_MODEL_DEVICE=$(echo "$MODEL_DEVICE_PATH" | sed 's/p[0-9]*$//' | sed 's/[0-9]*$//')
fi

# Detect backup storage device
if mountpoint -q /mnt/citadel-backup 2>/dev/null; then
    BACKUP_DEVICE_PATH=$(df --output=source /mnt/citadel-backup | tail -n1)
    # Strip partition numbers to get base device (e.g., /dev/sda1 -> /dev/sda)
    BACKUP_DEVICE=$(echo "$BACKUP_DEVICE_PATH" | sed 's/p[0-9]*$//' | sed 's/[0-9]*$//')
fi

echo "=== Storage Status Report $(date) ==="
echo ""

echo "Detected Storage Devices:"
echo "Model device: ${NVME_MODEL_DEVICE:-"Not detected"}"
echo "Backup device: ${BACKUP_DEVICE:-"Not detected"}"
echo ""

echo "Storage Usage:"
if [[ -n "$NVME_MODEL_DEVICE" || -n "$BACKUP_DEVICE" ]]; then
    # Create dynamic pattern for devices
    DEVICE_PATTERN="(citadel|Filesystem"
    [[ -n "$NVME_MODEL_DEVICE" ]] && DEVICE_PATTERN="${DEVICE_PATTERN}|$(basename "$NVME_MODEL_DEVICE")"
    [[ -n "$BACKUP_DEVICE" ]] && DEVICE_PATTERN="${DEVICE_PATTERN}|$(basename "$BACKUP_DEVICE")"
    DEVICE_PATTERN="${DEVICE_PATTERN})"
    df -h | grep -E "$DEVICE_PATTERN"
else
    # Fallback to showing citadel mounts only
    df -h | grep -E "(citadel|Filesystem)"
fi
echo ""

echo "Mount Status:"
mount | grep citadel
echo ""

echo "I/O Statistics:"
if command -v iostat >/dev/null 2>&1; then
    if [[ -n "$NVME_MODEL_DEVICE" || -n "$BACKUP_DEVICE" ]]; then
        # Create dynamic pattern for iostat
        IOSTAT_PATTERN="(Device"
        [[ -n "$NVME_MODEL_DEVICE" ]] && IOSTAT_PATTERN="${IOSTAT_PATTERN}|$(basename "$NVME_MODEL_DEVICE")"
        [[ -n "$BACKUP_DEVICE" ]] && IOSTAT_PATTERN="${IOSTAT_PATTERN}|$(basename "$BACKUP_DEVICE")"
        IOSTAT_PATTERN="${IOSTAT_PATTERN})"
        iostat -x 1 1 | grep -E "$IOSTAT_PATTERN" || echo "I/O statistics unavailable for detected devices"
    else
        echo "No storage devices detected for I/O monitoring"
    fi
else
    echo "iostat not available"
fi
echo ""

echo "Storage Temperature (if available):"
if command -v smartctl >/dev/null 2>&1; then
    if [[ -n "$NVME_MODEL_DEVICE" ]]; then
        sudo smartctl -A "$NVME_MODEL_DEVICE" | grep -i temperature || echo "Temperature monitoring not available for $NVME_MODEL_DEVICE"
    else
        echo "No NVMe device detected for temperature monitoring"
    fi
else
    echo "smartctl not available"
fi
echo ""

echo "Recent I/O Errors:"
dmesg | tail -20 | grep -i "error\|fail" || echo "No recent I/O errors"