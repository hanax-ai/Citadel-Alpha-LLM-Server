#!/usr/bin/env python3
"""
Test suite for enhanced backup models functionality
"""

import pytest
import os
import tempfile
import shutil
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from dataclasses import asdict

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))

from backup_models import (
    EnhancedBackupManager, 
    EnhancedBackupResult, 
    DependencyValidator
)
from storage_settings import StorageSettings


class TestDependencyValidator:
    """Test dependency validation functionality"""
    
    def test_validate_dependencies_success(self):
        """Test successful dependency validation"""
        with patch('subprocess.run') as mock_run:
            # Mock successful command checks
            mock_run.return_value.returncode = 0
            
            validator = DependencyValidator()
            valid, errors = validator.validate_dependencies()
            
            assert valid is True
            assert len(errors) == 0
    
    def test_validate_dependencies_missing_commands(self):
        """Test dependency validation with missing commands"""
        with patch('subprocess.run') as mock_run:
            # Mock missing commands
            mock_run.return_value.returncode = 1
            
            validator = DependencyValidator()
            valid, errors = validator.validate_dependencies()
            
            assert valid is False
            assert len(errors) > 0
            assert any("not found" in error for error in errors)
    
    def test_validate_dependencies_missing_packages(self):
        """Test dependency validation with missing Python packages"""
        with patch('subprocess.run') as mock_run:
            # Mock successful command checks
            mock_run.return_value.returncode = 0
            
            # Mock missing Python package
            with patch('builtins.__import__', side_effect=ImportError):
                validator = DependencyValidator()
                valid, errors = validator.validate_dependencies()
                
                assert valid is False
                assert any("package not found" in error for error in errors)


class TestEnhancedBackupManager:
    """Test enhanced backup manager functionality"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Create mock storage settings for testing"""
        settings = StorageSettings()
        
        # Override paths to use temp directory
        settings.paths.app_root = f"{temp_dir}/app"
        settings.paths.models_root = f"{temp_dir}/models"
        settings.paths.models_active = f"{temp_dir}/models/active"
        settings.paths.models_staging = f"{temp_dir}/models/staging"
        settings.paths.backup_root = f"{temp_dir}/backup"
        settings.paths.backup_models = f"{temp_dir}/backup/models"
        settings.paths.app_logs = f"{temp_dir}/logs"
        
        # Configure backup settings
        settings.backup.max_retry_attempts = 2
        settings.backup.retry_delay_seconds = 1
        settings.backup.compress_backups = True
        
        return settings
    
    @pytest.fixture
    def backup_manager(self, mock_settings):
        """Create enhanced backup manager instance for testing"""
        with patch.object(DependencyValidator, 'validate_dependencies', return_value=(True, [])):
            return EnhancedBackupManager(mock_settings)
    
    def test_enhanced_backup_manager_initialization(self, backup_manager):
        """Test enhanced backup manager initialization"""
        assert backup_manager.settings is not None
        assert backup_manager.logger is not None
        assert isinstance(backup_manager.validator, DependencyValidator)
    
    def test_initialization_fails_with_missing_dependencies(self, mock_settings):
        """Test initialization fails when dependencies are missing"""
        with patch.object(DependencyValidator, 'validate_dependencies', 
                         return_value=(False, ["missing rsync"])):
            with pytest.raises(RuntimeError, match="Backup dependencies not met"):
                EnhancedBackupManager(mock_settings)
    
    def test_get_model_path_success(self, backup_manager):
        """Test successful model path resolution"""
        path = backup_manager._get_model_path("phi3")
        assert path is not None
        assert "phi-3-mini-128k" in path
        
        path = backup_manager._get_model_path("mixtral")
        assert path is not None
        assert "mixtral-8x7b-instruct" in path
    
    def test_get_model_path_unknown_model(self, backup_manager):
        """Test model path resolution for unknown model"""
        path = backup_manager._get_model_path("unknown_model")
        assert path is None
    
    def test_create_test_subset(self, backup_manager, temp_dir):
        """Test creation of model subset for testing"""
        # Create source model directory with test files
        source_dir = Path(f"{temp_dir}/test_model")
        source_dir.mkdir(parents=True)
        
        # Create test files
        (source_dir / "config.json").write_text('{"test": "config"}')
        (source_dir / "tokenizer.json").write_text('{"test": "tokenizer"}')
        (source_dir / "large_file.bin").write_text("large model data")
        
        rollback_actions = []
        
        # Create test subset
        test_subset = backup_manager._create_test_subset(str(source_dir), rollback_actions)
        
        assert Path(test_subset).exists()
        assert (Path(test_subset) / "config.json").exists()
        assert (Path(test_subset) / "tokenizer.json").exists()
        assert not (Path(test_subset) / "large_file.bin").exists()  # Should not copy large files
        
        # Test cleanup
        assert len(rollback_actions) > 0
        rollback_actions[0]()  # Execute cleanup
        assert not Path(test_subset).exists()
    
    def test_calculate_compression_ratio(self, backup_manager, temp_dir):
        """Test compression ratio calculation"""
        # Create test source directory
        source_dir = Path(f"{temp_dir}/source")
        source_dir.mkdir(parents=True)
        (source_dir / "test.txt").write_text("test data" * 100)
        
        # Create mock compressed file
        compressed_file = Path(f"{temp_dir}/backup.tar.zst")
        compressed_file.write_text("compressed")
        
        with patch('subprocess.run') as mock_run:
            # Mock du command output
            mock_run.return_value.stdout = "1000\t/path/to/source"
            mock_run.return_value.check = True
            
            ratio = backup_manager._calculate_compression_ratio(
                str(source_dir), str(compressed_file)
            )
            
            assert ratio is not None
            assert 0 < ratio < 1  # Should be compressed
    
    def test_backup_transaction_success(self, backup_manager):
        """Test successful backup transaction"""
        rollback_actions = []
        
        with backup_manager.backup_transaction("test_operation") as actions:
            actions.extend(rollback_actions)
            # Simulate successful operation
            pass
        
        # Should complete without issues
        assert True
    
    def test_backup_transaction_rollback(self, backup_manager):
        """Test backup transaction rollback on failure"""
        rollback_executed = []
        
        def mock_rollback():
            rollback_executed.append(True)
        
        with pytest.raises(ValueError, match="test error"):
            with backup_manager.backup_transaction("test_operation") as rollback_actions:
                rollback_actions.append(mock_rollback)
                raise ValueError("test error")
        
        # Verify rollback was executed
        assert len(rollback_executed) == 1
    
    def test_create_model_backup_success(self, backup_manager, temp_dir):
        """Test successful model backup creation"""
        # Create test model directory
        model_dir = Path(f"{temp_dir}/models/active/Phi-3-mini-128k-instruct")
        model_dir.mkdir(parents=True)
        (model_dir / "config.json").write_text('{"model": "phi3"}')
        (model_dir / "tokenizer.json").write_text('{"tokenizer": "data"}')
        
        # Mock backup creation methods
        with patch.object(backup_manager, 'create_backup') as mock_create:
            with patch.object(backup_manager, '_wait_for_backup_completion'):
                # Create mock backup job
                from backup_manager import BackupJob
                from datetime import datetime
                
                mock_job = BackupJob(
                    job_id="test_job",
                    source_path=str(model_dir),
                    destination_path=f"{temp_dir}/backup/test_backup",
                    backup_type="daily",
                    status="completed",
                    start_time=datetime.now(),
                    end_time=datetime.now(),
                    files_processed=2,
                    bytes_processed=1000,
                    errors=[],
                    checksum="abc123"
                )
                
                mock_create.return_value = mock_job
                
                # Test backup creation
                result = backup_manager.create_model_backup("phi3", "daily", test_mode=True)
                
                assert result.success is True
                assert result.model_name == "phi3"
                assert result.backup_type == "daily"
                assert result.files_processed == 2
                assert result.bytes_processed == 1000
    
    def test_create_model_backup_model_not_found(self, backup_manager):
        """Test backup creation with model not found"""
        result = backup_manager.create_model_backup("nonexistent_model", "daily")
        
        assert result.success is False
        assert "not found" in result.message.lower()
        assert result.model_name == "nonexistent_model"
    
    def test_create_model_backup_directory_missing(self, backup_manager, temp_dir):
        """Test backup creation with missing model directory"""
        # Model path exists in config but directory doesn't exist
        result = backup_manager.create_model_backup("phi3", "daily")
        
        assert result.success is False
        assert "does not exist" in result.message
        assert result.model_name == "phi3"


class TestEnhancedBackupResult:
    """Test enhanced backup result data structure"""
    
    def test_enhanced_backup_result_creation(self):
        """Test EnhancedBackupResult creation"""
        result = EnhancedBackupResult(
            success=True,
            message="Backup completed",
            backup_type="daily",
            model_name="phi3",
            backup_path="/path/to/backup",
            duration_seconds=120.5,
            files_processed=100,
            bytes_processed=1000000,
            compression_ratio=0.7,
            errors=[]
        )
        
        assert result.success is True
        assert result.message == "Backup completed"
        assert result.backup_type == "daily"
        assert result.model_name == "phi3"
        assert result.duration_seconds == 120.5
        assert result.compression_ratio == 0.7
    
    def test_enhanced_backup_result_serialization(self):
        """Test EnhancedBackupResult serialization"""
        result = EnhancedBackupResult(
            success=False,
            message="Backup failed",
            backup_type="weekly",
            model_name="mixtral",
            backup_path=None,
            duration_seconds=30.0,
            files_processed=0,
            bytes_processed=0,
            compression_ratio=None,
            errors=["Connection timeout", "Disk full"]
        )
        
        # Test conversion to dict
        result_dict = asdict(result)
        assert result_dict["success"] is False
        assert result_dict["errors"] == ["Connection timeout", "Disk full"]
        assert result_dict["compression_ratio"] is None
        
        # Test JSON serialization
        json_str = json.dumps(result_dict, default=str)
        assert "Backup failed" in json_str
        assert "mixtral" in json_str


class TestIntegration:
    """Integration tests for enhanced backup functionality"""
    
    @pytest.fixture
    def integration_temp_dir(self):
        """Create temporary directory for integration testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_gradual_rollout_simulation(self, integration_temp_dir):
        """Test gradual backup rollout simulation"""
        # Create mock settings
        settings = StorageSettings()
        settings.paths.models_active = f"{integration_temp_dir}/models/active"
        settings.paths.models_staging = f"{integration_temp_dir}/models/staging"
        settings.paths.backup_models = f"{integration_temp_dir}/backup/models"
        settings.paths.app_logs = f"{integration_temp_dir}/logs"
        settings.backup.max_retry_attempts = 1
        settings.backup.retry_delay_seconds = 1
        
        # Create model directories
        for model in ["Phi-3-mini-128k-instruct", "Mixtral-8x7B-Instruct-v0.1"]:
            model_dir = Path(f"{integration_temp_dir}/models/active/{model}")
            model_dir.mkdir(parents=True)
            (model_dir / "config.json").write_text(f'{{"model": "{model}"}}')
        
        Path(f"{integration_temp_dir}/models/staging").mkdir(parents=True)
        Path(f"{integration_temp_dir}/backup/models").mkdir(parents=True)
        Path(f"{integration_temp_dir}/logs").mkdir(parents=True)
        
        # Test with mocked dependencies and backup operations
        with patch.object(DependencyValidator, 'validate_dependencies', return_value=(True, [])):
            with patch('scripts.backup_models.BackupManager.create_backup') as mock_create:
                with patch('scripts.backup_models.EnhancedBackupManager._wait_for_backup_completion'):
                    # Create mock backup job
                    from backup_manager import BackupJob
                    from datetime import datetime
                    
                    mock_job = BackupJob(
                        job_id="test_job",
                        source_path="test_path",
                        destination_path="test_destination",
                        backup_type="daily",
                        status="completed",
                        start_time=datetime.now(),
                        end_time=datetime.now(),
                        files_processed=10,
                        bytes_processed=5000,
                        errors=[],
                        checksum="test_checksum"
                    )
                    
                    mock_create.return_value = mock_job
                    
                    manager = EnhancedBackupManager(settings)
                    
                    # Test phi3 backup (first in gradual rollout)
                    result = manager.create_model_backup("phi3", "daily", test_mode=True)
                    assert result.success is True
                    
                    # Test mixtral backup 
                    result = manager.create_model_backup("mixtral", "daily", test_mode=False)
                    assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])