#!/bin/bash
# storage-monitor.sh - Monitor storage performance and usage

# Storage devices (detected from current mounts)
NVME_MODEL_DEVICE="/dev/nvme1n1"
BACKUP_DEVICE="/dev/sda"

echo "=== Storage Status Report $(date) ==="
echo ""

echo "Storage Usage:"
df -h | grep -E "(citadel|nvme|sda|Filesystem)"
echo ""

echo "Mount Status:"
mount | grep citadel
echo ""

echo "I/O Statistics:"
if command -v iostat >/dev/null 2>&1; then
    iostat -x 1 1 | grep -E "($(basename "$NVME_MODEL_DEVICE")|$(basename "$BACKUP_DEVICE")|Device)" || echo "I/O statistics unavailable"
else
    echo "iostat not available"
fi
echo ""

echo "Storage Temperature (if available):"
if command -v smartctl >/dev/null 2>&1; then
    sudo smartctl -A "$NVME_MODEL_DEVICE" | grep -i temperature || echo "Temperature monitoring not available"
else
    echo "smartctl not available"
fi
echo ""

echo "Recent I/O Errors:"
dmesg | tail -20 | grep -i "error\|fail" || echo "No recent I/O errors"