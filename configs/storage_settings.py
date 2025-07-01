#!/usr/bin/env python3
"""
PLANB-06: Storage Configuration Management
Pydantic-based settings for storage, symlinks, and model management
"""

from typing import Optional, Dict, List, Union
from pathlib import Path
from pydantic import BaseSettings, Field, validator
import os


class StoragePathSettings(BaseSettings):
    """Storage path configuration settings"""
    
    # Application Paths
    app_root: str = Field(
        default="/opt/citadel",
        description="Application root directory"
    )
    app_models: str = Field(
        default="/opt/citadel/models",
        description="Application models symlink path"
    )
    app_scripts: str = Field(
        default="/opt/citadel/scripts",
        description="Application scripts directory"
    )
    app_configs: str = Field(
        default="/opt/citadel/configs",
        description="Application configuration directory"
    )
    app_logs: str = Field(
        default="/opt/citadel/logs",
        description="Application logs directory"
    )
    
    # Storage Paths
    models_root: str = Field(
        default="/mnt/citadel-models",
        description="Model storage root directory"
    )
    models_active: str = Field(
        default="/mnt/citadel-models/active",
        description="Active models directory"
    )
    models_archive: str = Field(
        default="/mnt/citadel-models/archive",
        description="Archived models directory"
    )
    models_cache: str = Field(
        default="/mnt/citadel-models/cache",
        description="Model cache directory"
    )
    models_downloads: str = Field(
        default="/mnt/citadel-models/downloads",
        description="Model download staging directory"
    )
    models_staging: str = Field(
        default="/mnt/citadel-models/staging",
        description="Model staging directory"
    )
    
    # Backup Paths
    backup_root: str = Field(
        default="/mnt/citadel-backup",
        description="Backup storage root directory"
    )
    backup_models: str = Field(
        default="/mnt/citadel-backup/models",
        description="Model backup directory"
    )
    backup_system: str = Field(
        default="/mnt/citadel-backup/system",
        description="System backup directory"
    )
    
    # Cache Paths
    hf_cache: str = Field(
        default="/mnt/citadel-models/cache",
        description="Hugging Face cache directory"
    )
    torch_cache: str = Field(
        default="/mnt/citadel-models/cache/torch",
        description="PyTorch cache directory"
    )
    vllm_cache: str = Field(
        default="/mnt/citadel-models/cache/vllm",
        description="vLLM cache directory"
    )
    transformers_cache: str = Field(
        default="/mnt/citadel-models/cache/transformers",
        description="Transformers cache directory"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "CITADEL_"
        case_sensitive = False


class ModelSettings(BaseSettings):
    """Model configuration settings"""
    
    # Model Directory Names
    model_directories: Dict[str, str] = Field(
        default={
            "mixtral-8x7b-instruct": "Mixtral-8x7B-Instruct-v0.1",
            "yi-34b-chat": "Yi-34B-Chat", 
            "nous-hermes-2-mixtral": "Nous-Hermes-2-Mixtral-8x7B-DPO",
            "openchat-3.5": "openchat-3.5-1210",
            "phi-3-mini-128k": "Phi-3-mini-128k-instruct",
            "deepcoder-14b-instruct": "deepseek-coder-14b-instruct-v1.5",
            "mimo-vl-7b-rl": "imp-v1_5-7b"
        },
        description="Model directory mapping (short_name -> full_directory_name)"
    )
    
    # Convenience Symlink Names
    convenience_links: Dict[str, str] = Field(
        default={
            "mixtral": "mixtral-8x7b-instruct",
            "yi34b": "yi-34b-chat",
            "hermes": "nous-hermes-2-mixtral", 
            "openchat": "openchat-3.5",
            "phi3": "phi-3-mini-128k",
            "coder": "deepcoder-14b-instruct",
            "vision": "mimo-vl-7b-rl"
        },
        description="Convenience symlink mapping (short_name -> model_directory_key)"
    )
    
    # Model Management Settings
    download_timeout: int = Field(
        default=1800,
        description="Model download timeout in seconds"
    )
    verification_enabled: bool = Field(
        default=True,
        description="Enable model file verification"
    )
    auto_backup: bool = Field(
        default=True,
        description="Enable automatic model backup"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "MODEL_"
        case_sensitive = False


class SymlinkSettings(BaseSettings):
    """Symlink configuration and management settings"""
    
    # Symlink Behavior
    force_recreate: bool = Field(
        default=False,
        description="Force recreation of existing symlinks"
    )
    verify_targets: bool = Field(
        default=True,
        description="Verify symlink targets exist before creation"
    )
    create_missing_targets: bool = Field(
        default=True,
        description="Create missing target directories"
    )
    
    # Permissions
    directory_mode: str = Field(
        default="0755",
        description="Default directory permissions (octal)"
    )
    symlink_owner: str = Field(
        default="agent0",
        description="Default symlink owner"
    )
    symlink_group: str = Field(
        default="agent0", 
        description="Default symlink group"
    )
    
    # Validation Settings
    health_check_interval: int = Field(
        default=300,
        description="Symlink health check interval in seconds"
    )
    repair_broken_links: bool = Field(
        default=True,
        description="Automatically repair broken symlinks"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "SYMLINK_"
        case_sensitive = False


class StorageMonitoringSettings(BaseSettings):
    """Storage monitoring and health check settings"""
    
    # Monitoring Configuration
    enable_monitoring: bool = Field(
        default=True,
        description="Enable storage monitoring"
    )
    check_interval: int = Field(
        default=60,
        description="Monitoring check interval in seconds"
    )
    
    # Remote Monitoring Integration
    enable_remote_monitoring: bool = Field(
        default=True,
        description="Enable remote monitoring to dev-ops server"
    )
    dev_ops_server: str = Field(
        default="192.168.10.36",
        description="Dev-ops server IP address"
    )
    prometheus_port: int = Field(
        default=9090,
        description="Prometheus server port"
    )
    grafana_port: int = Field(
        default=3000,
        description="Grafana server port"
    )
    alertmanager_port: int = Field(
        default=9093,
        description="AlertManager server port"
    )
    
    # Local Metrics Export
    metrics_port: int = Field(
        default=8000,
        description="Local metrics export port"
    )
    health_check_port: int = Field(
        default=8001,
        description="Local health check port"
    )
    
    # Model Service Monitoring
    model_ports: Dict[str, int] = Field(
        default={
            "mixtral": 11400,
            "hermes": 11401,
            "openchat": 11402,
            "phi3": 11403,
            "yi34b": 11404,
            "coder": 11405,
            "vision": 11500
        },
        description="Model service port mapping"
    )
    
    # Thresholds
    disk_usage_warning: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="Disk usage warning threshold (0.0-1.0)"
    )
    disk_usage_critical: float = Field(
        default=0.9,
        ge=0.1,
        le=1.0,
        description="Disk usage critical threshold (0.0-1.0)"
    )
    inode_usage_warning: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="Inode usage warning threshold (0.0-1.0)"
    )
    cpu_usage_warning: float = Field(
        default=0.8,
        ge=0.1,
        le=1.0,
        description="CPU usage warning threshold (0.0-1.0)"
    )
    memory_usage_warning: float = Field(
        default=0.85,
        ge=0.1,
        le=1.0,
        description="Memory usage warning threshold (0.0-1.0)"
    )
    gpu_memory_warning: float = Field(
        default=0.9,
        ge=0.1,
        le=1.0,
        description="GPU memory warning threshold (0.0-1.0)"
    )
    gpu_temperature_critical: float = Field(
        default=80.0,
        description="GPU temperature critical threshold (Celsius)"
    )
    
    # Performance Monitoring
    io_latency_threshold: float = Field(
        default=100.0,
        description="I/O latency threshold in milliseconds"
    )
    throughput_threshold: float = Field(
        default=100.0,
        description="Minimum throughput in MB/s"
    )
    
    # Health Check Settings
    enable_smart_checks: bool = Field(
        default=True,
        description="Enable SMART disk health checks"
    )
    smart_check_interval: int = Field(
        default=3600,
        description="SMART check interval in seconds"
    )
    
    # Data Retention
    metrics_retention_days: int = Field(
        default=30,
        description="Metrics retention period in days"
    )
    alerts_retention_days: int = Field(
        default=7,
        description="Alerts retention period in days"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "STORAGE_MONITOR_"
        case_sensitive = False


class BackupSettings(BaseSettings):
    """Backup configuration and verification settings"""
    
    # Backup Configuration
    enable_auto_backup: bool = Field(
        default=True,
        description="Enable automatic backups"
    )
    backup_schedule: str = Field(
        default="0 2 * * *",  # Daily at 2 AM
        description="Backup schedule (cron format)"
    )
    retention_days: int = Field(
        default=30,
        description="Backup retention period in days"
    )
    
    # Backup Types
    incremental_backup: bool = Field(
        default=True,
        description="Use incremental backups"
    )
    compress_backups: bool = Field(
        default=True,
        description="Compress backup files"
    )
    compression_algorithm: str = Field(
        default="zstd",
        description="Compression algorithm (zstd, gzip, lz4)"
    )
    compression_level: int = Field(
        default=3,
        ge=1,
        le=22,
        description="Compression level (1-22)"
    )
    
    # Enhanced Backup Strategy
    backup_types: Dict[str, str] = Field(
        default={
            "daily": "0 2 * * *",
            "weekly": "0 3 * * 0",
            "monthly": "0 4 1 * *"
        },
        description="Backup type schedules"
    )
    deduplication_enabled: bool = Field(
        default=True,
        description="Enable backup deduplication"
    )
    parallel_jobs: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Number of parallel backup jobs"
    )
    
    # Verification Settings
    verify_backups: bool = Field(
        default=True,
        description="Verify backup integrity"
    )
    verification_sample_rate: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Percentage of files to verify (0.0-1.0)"
    )
    checksum_algorithm: str = Field(
        default="sha256",
        description="Checksum algorithm for verification"
    )
    test_restore_enabled: bool = Field(
        default=True,
        description="Enable periodic test restores"
    )
    
    # Error Handling
    max_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum backup retry attempts"
    )
    retry_delay_seconds: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Delay between retry attempts"
    )
    
    class Config:
        env_file = ".env"
        env_prefix = "BACKUP_"
        case_sensitive = False


# Combined Settings Class
class StorageSettings(BaseSettings):
    """Complete storage configuration settings"""
    
    paths: StoragePathSettings = StoragePathSettings()
    models: ModelSettings = ModelSettings()
    symlinks: SymlinkSettings = SymlinkSettings()
    monitoring: StorageMonitoringSettings = StorageMonitoringSettings()
    backup: BackupSettings = BackupSettings()
    
    @validator("paths", pre=True, always=True)
    def validate_paths(cls, v):
        """Validate and create storage paths if needed"""
        if isinstance(v, dict):
            v = StoragePathSettings(**v)
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


def load_storage_settings() -> StorageSettings:
    """Load storage configuration settings"""
    return StorageSettings()


def get_storage_environment_variables(settings: StorageSettings) -> Dict[str, str]:
    """Generate environment variables from storage settings"""
    
    env_vars = {}
    
    # Storage paths
    env_vars.update({
        "CITADEL_MODELS_ROOT": settings.paths.models_root,
        "CITADEL_MODELS_ACTIVE": settings.paths.models_active,
        "CITADEL_MODELS_ARCHIVE": settings.paths.models_archive,
        "CITADEL_MODELS_CACHE": settings.paths.models_cache,
        "CITADEL_MODELS_DOWNLOADS": settings.paths.models_downloads,
        "CITADEL_BACKUP_ROOT": settings.paths.backup_root,
        "CITADEL_BACKUP_MODELS": settings.paths.backup_models,
        "CITADEL_BACKUP_SYSTEM": settings.paths.backup_system,
        "CITADEL_APP_ROOT": settings.paths.app_root,
        "CITADEL_APP_MODELS": settings.paths.app_models,
        "CITADEL_APP_CONFIGS": settings.paths.app_configs,
        "CITADEL_APP_SCRIPTS": settings.paths.app_scripts,
        "CITADEL_APP_LOGS": settings.paths.app_logs,
    })
    
    # Cache configuration
    env_vars.update({
        "HF_HOME": settings.paths.hf_cache,
        "HUGGINGFACE_HUB_CACHE": settings.paths.hf_cache,
        "TRANSFORMERS_CACHE": settings.paths.transformers_cache,
        "TORCH_HOME": settings.paths.torch_cache,
        "VLLM_CACHE_ROOT": settings.paths.vllm_cache,
    })
    
    # Model-specific paths
    for short_name, model_key in settings.models.convenience_links.items():
        if model_key in settings.models.model_directories:
            full_name = settings.models.model_directories[model_key]
            env_var_name = f"CITADEL_MODEL_{short_name.upper()}"
            env_vars[env_var_name] = f"{settings.paths.models_active}/{full_name}"
    
    return env_vars


if __name__ == "__main__":
    # Example usage and validation
    try:
        settings = load_storage_settings()
        print("✅ Storage configuration loaded successfully")
        print(f"Models root: {settings.paths.models_root}")
        print(f"Active models: {settings.paths.models_active}")
        print(f"Model count: {len(settings.models.model_directories)}")
        print(f"Convenience links: {len(settings.models.convenience_links)}")
        print(f"Monitoring enabled: {settings.monitoring.enable_monitoring}")
        print(f"Auto backup enabled: {settings.backup.enable_auto_backup}")
        
        # Generate environment variables
        env_vars = get_storage_environment_variables(settings)
        print(f"Generated {len(env_vars)} environment variables")
        
    except Exception as e:
        print(f"❌ Storage configuration validation failed: {e}")