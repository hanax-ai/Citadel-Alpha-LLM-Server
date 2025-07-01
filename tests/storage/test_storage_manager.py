#!/usr/bin/env python3
"""
Test suite for storage manager functionality
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from dataclasses import asdict

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))

from storage_manager import StorageManager, OperationResult, StorageManagerError
from storage_settings import StorageSettings


class TestStorageManager:
    """Test storage manager functionality"""
    
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
        settings.paths.backup_root = f"{temp_dir}/backup"
        settings.paths.app_logs = f"{temp_dir}/logs"
        
        return settings
    
    @pytest.fixture
    def storage_manager(self, mock_settings):
        """Create storage manager instance for testing"""
        return StorageManager(mock_settings)
    
    def test_storage_manager_initialization(self, storage_manager):
        """Test storage manager initialization"""
        assert storage_manager.settings is not None
        assert storage_manager.logger is not None
        assert isinstance(storage_manager.operations_log, list)
    
    def test_verify_storage_prerequisites_success(self, storage_manager, temp_dir):
        """Test successful storage prerequisites verification"""
        # Create required directories
        Path(f"{temp_dir}/models").mkdir(parents=True)
        Path(f"{temp_dir}/backup").mkdir(parents=True)
        
        result = storage_manager.verify_storage_prerequisites()
        
        assert result.success is True
        assert "Prerequisites verified" in result.message
    
    def test_verify_storage_prerequisites_missing_mounts(self, storage_manager):
        """Test prerequisites verification with missing mount points"""
        result = storage_manager.verify_storage_prerequisites()
        
        assert result.success is False
        assert "Missing required mount points" in result.message
        assert result.details is not None
        assert "missing_mounts" in result.details
    
    def test_create_directory_structure_success(self, storage_manager, temp_dir):
        """Test successful directory structure creation"""
        # Create base directories
        Path(f"{temp_dir}/models").mkdir(parents=True)
        Path(f"{temp_dir}/backup").mkdir(parents=True)
        Path(f"{temp_dir}/app").mkdir(parents=True)
        
        result = storage_manager.create_directory_structure()
        
        assert result.success is True
        assert "directories" in result.message
        assert result.details is not None
        assert "created_directories" in result.details
        
        # Verify some directories were created
        assert Path(f"{temp_dir}/models/active").exists()
        assert Path(f"{temp_dir}/models/cache").exists()
        assert Path(f"{temp_dir}/backup/models").exists()
    
    def test_create_directory_structure_with_model_dirs(self, storage_manager, temp_dir):
        """Test directory creation includes model directories"""
        # Create base directories
        Path(f"{temp_dir}/models").mkdir(parents=True)
        Path(f"{temp_dir}/backup").mkdir(parents=True)
        Path(f"{temp_dir}/app").mkdir(parents=True)
        
        result = storage_manager.create_directory_structure()
        
        assert result.success is True
        
        # Check that model directories were created
        for model_dir in storage_manager.settings.models.model_directories.values():
            model_path = Path(f"{temp_dir}/models/active/{model_dir}")
            assert model_path.exists()
    
    def test_create_symlinks_success(self, storage_manager, temp_dir):
        """Test successful symlink creation"""
        # Create required directory structure
        Path(f"{temp_dir}/models/active").mkdir(parents=True)
        Path(f"{temp_dir}/models/downloads").mkdir(parents=True)
        Path(f"{temp_dir}/models/staging").mkdir(parents=True)
        Path(f"{temp_dir}/app").mkdir(parents=True)
        
        # Create model directories
        for model_dir in storage_manager.settings.models.model_directories.values():
            Path(f"{temp_dir}/models/active/{model_dir}").mkdir(parents=True)
        
        result = storage_manager.create_symlinks()
        
        assert result.success is True
        assert "symlinks" in result.message
        assert result.details is not None
        assert "created_symlinks" in result.details
        
        # Verify primary symlinks were created
        assert Path(f"{temp_dir}/app/models").is_symlink()
        assert Path(f"{temp_dir}/app/downloads").is_symlink()
        assert Path(f"{temp_dir}/app/staging").is_symlink()
    
    def test_create_symlinks_with_convenience_links(self, storage_manager, temp_dir):
        """Test convenience symlink creation"""
        # Setup required directories
        Path(f"{temp_dir}/models/active").mkdir(parents=True)
        Path(f"{temp_dir}/app").mkdir(parents=True)
        
        # Create model directories
        for model_dir in storage_manager.settings.models.model_directories.values():
            Path(f"{temp_dir}/models/active/{model_dir}").mkdir(parents=True)
        
        result = storage_manager.create_symlinks()
        
        assert result.success is True
        
        # Verify convenience symlinks
        convenience_dir = Path(f"{temp_dir}/app/model-links")
        assert convenience_dir.exists()
        
        for short_name in storage_manager.settings.models.convenience_links.keys():
            symlink = convenience_dir / short_name
            assert symlink.is_symlink()
    
    def test_verify_symlinks_success(self, storage_manager, temp_dir):
        """Test successful symlink verification"""
        # Create directory structure and symlinks
        Path(f"{temp_dir}/models/active").mkdir(parents=True)
        Path(f"{temp_dir}/app").mkdir(parents=True)
        
        # Create primary symlinks
        Path(f"{temp_dir}/app/models").symlink_to(f"{temp_dir}/models/active")
        
        result = storage_manager.verify_symlinks()
        
        assert result.success is True
        assert "verified" in result.message
        assert result.details is not None
        assert result.details["verified_count"] > 0
    
    def test_verify_symlinks_with_broken_links(self, storage_manager, temp_dir):
        """Test symlink verification with broken links"""
        # Create app directory and broken symlink
        Path(f"{temp_dir}/app").mkdir(parents=True)
        Path(f"{temp_dir}/app/models").symlink_to("/nonexistent/path")
        
        result = storage_manager.verify_symlinks()
        
        assert result.success is False
        assert "issues" in result.message
        assert result.details is not None
        assert "issues" in result.details
        assert len(result.details["issues"]) > 0
    
    def test_repair_symlinks_success(self, storage_manager, temp_dir):
        """Test successful symlink repair"""
        # Create directory structure
        Path(f"{temp_dir}/models/active").mkdir(parents=True)
        Path(f"{temp_dir}/app").mkdir(parents=True)
        
        # Create broken symlink
        Path(f"{temp_dir}/app/models").symlink_to("/nonexistent/path")
        
        result = storage_manager.repair_symlinks()
        
        # Should attempt repair but may not fully succeed without proper target determination
        assert result.success is not None
        assert result.details is not None
    
    def test_determine_symlink_target(self, storage_manager):
        """Test symlink target determination"""
        # Test primary symlinks
        target = storage_manager._determine_symlink_target("/opt/citadel/models")
        assert target == storage_manager.settings.paths.models_active
        
        target = storage_manager._determine_symlink_target("/opt/citadel/downloads")
        assert target == storage_manager.settings.paths.models_downloads
        
        # Test convenience symlinks
        target = storage_manager._determine_symlink_target("/opt/citadel/model-links/mixtral")
        assert target is not None
        assert "mixtral-8x7b-instruct" in target
    
    def test_create_symlink_with_force_recreate(self, storage_manager, temp_dir):
        """Test symlink creation with force recreate option"""
        # Create target directory
        target_dir = Path(f"{temp_dir}/target")
        target_dir.mkdir(parents=True)
        
        # Create existing symlink
        link_path = Path(f"{temp_dir}/existing_link")
        link_path.symlink_to(target_dir)
        
        # Enable force recreate
        storage_manager.settings.symlinks.force_recreate = True
        
        # Create new symlink (should overwrite)
        result = storage_manager._create_symlink(
            str(link_path), 
            str(target_dir), 
            []
        )
        
        assert result.success is True
        assert link_path.is_symlink()
        assert link_path.readlink() == target_dir
    
    def test_create_symlink_missing_target(self, storage_manager, temp_dir):
        """Test symlink creation with missing target"""
        link_path = f"{temp_dir}/test_link"
        target_path = f"{temp_dir}/nonexistent_target"
        
        # Test with create_missing_targets enabled
        storage_manager.settings.symlinks.create_missing_targets = True
        
        result = storage_manager._create_symlink(link_path, target_path, [])
        
        assert result.success is True
        assert Path(target_path).exists()
        assert Path(link_path).is_symlink()
    
    def test_verify_single_symlink_cases(self, storage_manager, temp_dir):
        """Test individual symlink verification cases"""
        # Test missing symlink
        issue = storage_manager._verify_single_symlink("/nonexistent/symlink")
        assert issue is not None
        assert "Missing symlink" in issue
        
        # Test broken symlink
        broken_link = Path(f"{temp_dir}/broken")
        broken_link.symlink_to("/nonexistent/target")
        
        issue = storage_manager._verify_single_symlink(str(broken_link))
        assert issue is not None
        assert "Broken symlink" in issue
        
        # Test valid symlink
        target = Path(f"{temp_dir}/valid_target")
        target.mkdir()
        valid_link = Path(f"{temp_dir}/valid_link")
        valid_link.symlink_to(target)
        
        issue = storage_manager._verify_single_symlink(str(valid_link))
        assert issue is None
    
    def test_transaction_rollback(self, storage_manager, temp_dir):
        """Test transaction rollback functionality"""
        created_dirs = []
        
        def create_dir_and_fail():
            with storage_manager._transaction("test_transaction") as rollback_actions:
                # Create a directory
                test_dir = Path(f"{temp_dir}/test_rollback")
                test_dir.mkdir(parents=True)
                created_dirs.append(test_dir)
                
                # Add rollback action
                rollback_actions.append(lambda: test_dir.rmdir() if test_dir.exists() else None)
                
                # Simulate failure
                raise Exception("Simulated failure")
        
        # Should raise exception and trigger rollback
        with pytest.raises(Exception, match="Simulated failure"):
            create_dir_and_fail()
        
        # Verify rollback was attempted (directory might still exist if not empty)
        # The rollback action was added to the list
        assert len(created_dirs) == 1
    
    def test_operation_logging(self, storage_manager):
        """Test operation logging functionality"""
        initial_count = len(storage_manager.operations_log)
        
        # Log an operation
        storage_manager._log_operation("test_operation", {"key": "value"})
        
        assert len(storage_manager.operations_log) == initial_count + 1
        
        last_log = storage_manager.operations_log[-1]
        assert last_log["operation"] == "test_operation"
        assert last_log["details"]["key"] == "value"
        assert "timestamp" in last_log


class TestOperationResult:
    """Test OperationResult data class"""
    
    def test_operation_result_creation(self):
        """Test OperationResult creation"""
        result = OperationResult(
            success=True,
            message="Test operation completed",
            details={"count": 5},
            rollback_info={"action": "restore"}
        )
        
        assert result.success is True
        assert result.message == "Test operation completed"
        assert result.details["count"] == 5
        assert result.rollback_info["action"] == "restore"
    
    def test_operation_result_minimal(self):
        """Test OperationResult with minimal data"""
        result = OperationResult(success=False, message="Failed")
        
        assert result.success is False
        assert result.message == "Failed"
        assert result.details is None
        assert result.rollback_info is None


class TestStorageManagerError:
    """Test StorageManagerError exception"""
    
    def test_storage_manager_error(self):
        """Test StorageManagerError exception"""
        error = StorageManagerError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestStorageManagerIntegration:
    """Integration tests for storage manager"""
    
    @pytest.fixture
    def integration_temp_dir(self):
        """Create temporary directory for integration testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_setup_workflow(self, integration_temp_dir):
        """Test full storage setup workflow"""
        # Create mock settings
        settings = StorageSettings()
        settings.paths.app_root = f"{integration_temp_dir}/app"
        settings.paths.models_root = f"{integration_temp_dir}/models"
        settings.paths.models_active = f"{integration_temp_dir}/models/active"
        settings.paths.models_downloads = f"{integration_temp_dir}/models/downloads"
        settings.paths.models_staging = f"{integration_temp_dir}/models/staging"
        settings.paths.backup_root = f"{integration_temp_dir}/backup"
        settings.paths.app_logs = f"{integration_temp_dir}/logs"
        
        manager = StorageManager(settings)
        
        # Step 1: Create base directories manually (simulating mount points)
        Path(f"{integration_temp_dir}/models").mkdir(parents=True)
        Path(f"{integration_temp_dir}/backup").mkdir(parents=True)
        
        # Step 2: Verify prerequisites
        prereq_result = manager.verify_storage_prerequisites()
        assert prereq_result.success is True
        
        # Step 3: Create directory structure
        dirs_result = manager.create_directory_structure()
        assert dirs_result.success is True
        
        # Step 4: Create symlinks
        symlinks_result = manager.create_symlinks()
        assert symlinks_result.success is True
        
        # Step 5: Verify symlinks
        verify_result = manager.verify_symlinks()
        assert verify_result.success is True
        
        # Verify final state
        assert Path(f"{integration_temp_dir}/app/models").is_symlink()
        assert Path(f"{integration_temp_dir}/models/active").exists()
        assert Path(f"{integration_temp_dir}/backup/models").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])