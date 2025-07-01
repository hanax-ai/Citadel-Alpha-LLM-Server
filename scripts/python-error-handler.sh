#!/bin/bash
# python-error-handler.sh - Error handling and rollback for Python setup

set -euo pipefail

BACKUP_DIR="/opt/citadel/backups/python-$(date +%Y%m%d-%H%M%S)"
LOG_FILE="/opt/citadel/logs/python-setup.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create backup
create_backup() {
    log "Creating backup at $BACKUP_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Backup existing Python installations
    if command -v python3 >/dev/null 2>&1; then
        python3 --version > "$BACKUP_DIR/python_version.txt" 2>&1 || true
    fi
    
    # Backup existing virtual environments
    if [ -d "/opt/citadel" ]; then
        find /opt/citadel -name "*-env" -type d > "$BACKUP_DIR/existing_envs.txt" 2>/dev/null || true
    fi
    
    # Backup package lists
    dpkg -l | grep python > "$BACKUP_DIR/python_packages.txt" 2>/dev/null || true
    
    # Backup environment variables
    env | grep -E "(PYTHON|PATH)" > "$BACKUP_DIR/environment.txt" 2>/dev/null || true
    
    log "✅ Backup created: $BACKUP_DIR"
}

# Rollback function
rollback_changes() {
    if [ -z "${BACKUP_DIR:-}" ] || [ ! -d "$BACKUP_DIR" ]; then
        log "ERROR: No backup directory found for rollback"
        return 1
    fi
    
    log "Rolling back changes from backup: $BACKUP_DIR"
    
    # Remove failed virtual environments
    for env in citadel-env vllm-env dev-env; do
        if [ -d "/opt/citadel/$env" ]; then
            log "Removing failed environment: $env"
            rm -rf "/opt/citadel/$env" || true
        fi
    done
    
    # Remove Python alternatives if they were added
    if update-alternatives --list python3 2>/dev/null | grep -q "python3.12"; then
        log "Removing Python alternatives"
        sudo update-alternatives --remove python3 /usr/bin/python3.12 2>/dev/null || true
        sudo update-alternatives --remove python /usr/bin/python3.12 2>/dev/null || true
    fi
    
    log "✅ Rollback completed"
}

# Validate step completion
validate_step() {
    local step_name="$1"
    local validation_command="$2"
    
    log "Validating step: $step_name"
    
    if eval "$validation_command"; then
        log "✅ Step validated: $step_name"
        return 0
    else
        log "❌ Step validation failed: $step_name"
        return 1
    fi
}

# Execute step with error handling
execute_step() {
    local step_name="$1"
    local step_command="$2"
    local validation_command="$3"
    
    log "Executing step: $step_name"
    
    if eval "$step_command"; then
        if validate_step "$step_name" "$validation_command"; then
            log "✅ Step completed successfully: $step_name"
            return 0
        else
            log "❌ Step validation failed: $step_name"
            return 1
        fi
    else
        log "❌ Step execution failed: $step_name"
        return 1
    fi
}

case "${1:-}" in
    backup)
        create_backup
        ;;
    rollback)
        rollback_changes
        ;;
    validate)
        validate_step "$2" "$3"
        ;;
    execute)
        execute_step "$2" "$3" "$4"
        ;;
    *)
        echo "Usage: $0 {backup|rollback|validate|execute}"
        echo "  backup                    - Create system backup"
        echo "  rollback                  - Rollback changes"
        echo "  validate <name> <cmd>     - Validate step completion"
        echo "  execute <name> <cmd> <val> - Execute step with validation"
        exit 1
        ;;
esac