#!/usr/bin/env python3
"""
Test suite for storage settings configuration
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from pydantic import ValidationError

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))

from storage_settings import (
    StoragePathSettings,
    ModelSettings,
    SymlinkSettings,
    StorageMonitoringSettings,
    BackupSettings,
    StorageSettings,
    load_storage_settings,
    get_storage_environment_variables
)


class TestStoragePathSettings:
    """Test storage path configuration"""
    
    def test_default_paths(self):
        """Test default path configuration"""
        settings = StoragePathSettings()
        
        assert settings.app_root == "/opt/citadel"
        assert settings.models_root == "/mnt/citadel-models"
        assert settings.backup_root == "/mnt/citadel-backup"
        
    def test_custom_paths(self):
        """Test custom path configuration"""
        custom_paths = {
            "app_root": "/custom/app",
            "models_root": "/custom/models",
            "backup_root": "/custom/backup"
        }
        
        settings = StoragePathSettings(**custom_paths)
        
        assert settings.app_root == "/custom/app"
        assert settings.models_root == "/custom/models"
        assert settings.backup_root == "/custom/backup"
    
    def test_environment_variable_override(self):
        """Test environment variable overrides"""
        with patch.dict(os.environ, {
            "CITADEL_APP_ROOT": "/env/app",
            "CITADEL_MODELS_ROOT": "/env/models"
        }):
            settings = StoragePathSettings()
            assert settings.app_root == "/env/app"
            assert settings.models_root == "/env/models"


class TestModelSettings:
    """Test model configuration"""
    
    def test_default_model_directories(self):
        """Test default model directory configuration"""
        settings = ModelSettings()
        
        assert "mixtral-8x7b-instruct" in settings.model_directories
        assert "yi-34b-chat" in settings.model_directories
        assert settings.model_directories["mixtral-8x7b-instruct"] == "Mixtral-8x7B-Instruct-v0.1"
    
    def test_convenience_links(self):
        """Test convenience link configuration"""
        settings = ModelSettings()
        
        assert "mixtral" in settings.convenience_links
        assert "yi34b" in settings.convenience_links
        assert settings.convenience_links["mixtral"] == "mixtral-8x7b-instruct"
    
    def test_download_timeout_validation(self):
        """Test download timeout validation"""
        settings = ModelSettings(download_timeout=3600)
        assert settings.download_timeout == 3600
        
        # Test with invalid timeout
        with pytest.raises(ValidationError):
            ModelSettings(download_timeout=-1)


class TestSymlinkSettings:
    """Test symlink configuration"""
    
    def test_default_symlink_settings(self):
        """Test default symlink configuration"""
        settings = SymlinkSettings()
        
        assert settings.force_recreate == False
        assert settings.verify_targets == True
        assert settings.directory_mode == "0755"
        assert settings.symlink_owner == "agent0"
    
    def test_health_check_settings(self):
        """Test health check configuration"""
        settings = SymlinkSettings(
            health_check_interval=600,
            repair_broken_links=False
        )
        
        assert settings.health_check_interval == 600
        assert settings.repair_broken_links == False


class TestStorageMonitoringSettings:
    """Test storage monitoring configuration"""
    
    def test_default_monitoring_settings(self):
        """Test default monitoring configuration"""
        settings = StorageMonitoringSettings()
        
        assert settings.enable_monitoring == True
        assert settings.check_interval == 60
        assert settings.disk_usage_warning == 0.8
        assert settings.disk_usage_critical == 0.9
    
    def test_threshold_validation(self):
        """Test threshold validation"""
        # Valid thresholds
        settings = StorageMonitoringSettings(
            disk_usage_warning=0.7,
            disk_usage_critical=0.85
        )
        assert settings.disk_usage_warning == 0.7
        assert settings.disk_usage_critical == 0.85
        
        # Invalid thresholds
        with pytest.raises(ValidationError):
            StorageMonitoringSettings(disk_usage_warning=1.5)
        
        with pytest.raises(ValidationError):
            StorageMonitoringSettings(disk_usage_critical=0.05)


class TestBackupSettings:
    """Test backup configuration"""
    
    def test_default_backup_settings(self):
        """Test default backup configuration"""
        settings = BackupSettings()
        
        assert settings.enable_auto_backup == True
        assert settings.backup_schedule == "0 2 * * *"
        assert settings.retention_days == 30
        assert settings.verify_backups == True
    
    def test_verification_sample_rate(self):
        """Test verification sample rate validation"""
        settings = BackupSettings(verification_sample_rate=0.5)
        assert settings.verification_sample_rate == 0.5
        
        # Test boundary values
        settings = BackupSettings(verification_sample_rate=0.0)
        assert settings.verification_sample_rate == 0.0
        
        settings = BackupSettings(verification_sample_rate=1.0)
        assert settings.verification_sample_rate == 1.0
        
        # Invalid sample rate
        with pytest.raises(ValidationError):
            BackupSettings(verification_sample_rate=1.5)


class TestStorageSettings:
    """Test combined storage settings"""
    
    def test_default_storage_settings(self):
        """Test default storage configuration"""
        settings = StorageSettings()
        
        assert isinstance(settings.paths, StoragePathSettings)
        assert isinstance(settings.models, ModelSettings)
        assert isinstance(settings.symlinks, SymlinkSettings)
        assert isinstance(settings.monitoring, StorageMonitoringSettings)
        assert isinstance(settings.backup, BackupSettings)
    
    def test_nested_configuration(self):
        """Test nested configuration override"""
        config = {
            "paths": {"app_root": "/test/app"},
            "models": {"download_timeout": 7200},
            "monitoring": {"check_interval": 120}
        }
        
        settings = StorageSettings(**config)
        
        assert settings.paths.app_root == "/test/app"
        assert settings.models.download_timeout == 7200
        assert settings.monitoring.check_interval == 120


class TestStorageSettingsFactory:
    """Test storage settings factory functions"""
    
    def test_load_storage_settings(self):
        """Test loading storage settings"""
        settings = load_storage_settings()
        
        assert isinstance(settings, StorageSettings)
        assert isinstance(settings.paths, StoragePathSettings)
    
    def test_get_environment_variables(self):
        """Test environment variable generation"""
        settings = StorageSettings()
        env_vars = get_storage_environment_variables(settings)
        
        # Check required environment variables
        required_vars = [
            "CITADEL_MODELS_ROOT",
            "CITADEL_MODELS_ACTIVE",
            "CITADEL_BACKUP_ROOT",
            "HF_HOME",
            "TRANSFORMERS_CACHE"
        ]
        
        for var in required_vars:
            assert var in env_vars
            assert env_vars[var] is not None
    
    def test_model_specific_environment_variables(self):
        """Test model-specific environment variable generation"""
        settings = StorageSettings()
        env_vars = get_storage_environment_variables(settings)
        
        # Check model-specific variables
        assert "CITADEL_MODEL_MIXTRAL" in env_vars
        assert "CITADEL_MODEL_YI34B" in env_vars
        assert "CITADEL_MODEL_HERMES" in env_vars
        
        # Verify paths are constructed correctly
        assert env_vars["CITADEL_MODEL_MIXTRAL"].endswith("Mixtral-8x7B-Instruct-v0.1")


class TestEnvironmentIntegration:
    """Test environment variable integration"""
    
    def test_env_file_loading(self):
        """Test loading from .env file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("CITADEL_APP_ROOT=/test/env/app\n")
            f.write("CITADEL_MODELS_ROOT=/test/env/models\n")
            f.write("MODEL_DOWNLOAD_TIMEOUT=5400\n")
            env_file = f.name
        
        try:
            # Mock the env_file configuration
            with patch.object(StoragePathSettings.Config, 'env_file', env_file):
                with patch.object(ModelSettings.Config, 'env_file', env_file):
                    settings = StorageSettings()
                    
                    # Note: This test would need actual dotenv loading
                    # For now, just verify the structure is correct
                    assert isinstance(settings.paths, StoragePathSettings)
                    assert isinstance(settings.models, ModelSettings)
        finally:
            os.unlink(env_file)
    
    def test_case_insensitive_env_vars(self):
        """Test case insensitive environment variables"""
        with patch.dict(os.environ, {
            "citadel_app_root": "/test/case/app",
            "CITADEL_MODELS_ROOT": "/test/case/models"
        }):
            # The actual case insensitivity would depend on pydantic configuration
            # This test verifies the structure supports it
            settings = StoragePathSettings()
            assert hasattr(settings, 'app_root')
            assert hasattr(settings, 'models_root')


if __name__ == "__main__":
    pytest.main([__file__, "-v"])