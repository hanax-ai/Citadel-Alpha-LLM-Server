#!/usr/bin/env python3
"""
Test suite for storage monitoring functionality
"""

import pytest
import os
import tempfile
import shutil
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from dataclasses import asdict
from datetime import datetime

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "scripts"))
sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))

from storage_monitor import (
    StorageMonitor, 
    StorageHealth, 
    PerformanceMetrics, 
    SymlinkStatus
)
from storage_settings import StorageSettings


class TestStorageHealth:
    """Test StorageHealth data class"""
    
    def test_storage_health_creation(self):
        """Test StorageHealth creation"""
        health = StorageHealth(
            path="/test/path",
            total_space=1000000,
            used_space=500000,
            free_space=500000,
            usage_percent=50.0,
            inode_total=1000,
            inode_used=500,
            inode_free=500,
            inode_usage_percent=50.0,
            mount_point="/",
            filesystem="ext4",
            is_healthy=True,
            warnings=[],
            timestamp=datetime.now()
        )
        
        assert health.path == "/test/path"
        assert health.usage_percent == 50.0
        assert health.is_healthy is True
        assert len(health.warnings) == 0
    
    def test_storage_health_with_warnings(self):
        """Test StorageHealth with warnings"""
        health = StorageHealth(
            path="/test/path",
            total_space=1000000,
            used_space=900000,
            free_space=100000,
            usage_percent=90.0,
            inode_total=1000,
            inode_used=500,
            inode_free=500,
            inode_usage_percent=50.0,
            mount_point="/",
            filesystem="ext4",
            is_healthy=False,
            warnings=["High disk usage: 90.0%"],
            timestamp=datetime.now()
        )
        
        assert health.is_healthy is False
        assert len(health.warnings) == 1
        assert "High disk usage" in health.warnings[0]


class TestPerformanceMetrics:
    """Test PerformanceMetrics data class"""
    
    def test_performance_metrics_creation(self):
        """Test PerformanceMetrics creation"""
        metrics = PerformanceMetrics(
            path="/test/path",
            read_latency_ms=10.5,
            write_latency_ms=15.2,
            read_throughput_mbps=100.0,
            write_throughput_mbps=80.0,
            iops_read=1000.0,
            iops_write=800.0,
            timestamp=datetime.now()
        )
        
        assert metrics.path == "/test/path"
        assert metrics.read_latency_ms == 10.5
        assert metrics.write_throughput_mbps == 80.0
        assert metrics.iops_read == 1000.0


class TestSymlinkStatus:
    """Test SymlinkStatus data class"""
    
    def test_symlink_status_valid(self):
        """Test valid symlink status"""
        status = SymlinkStatus(
            path="/test/symlink",
            target="/test/target",
            exists=True,
            is_valid=True,
            is_broken=False,
            error_message=None,
            timestamp=datetime.now()
        )
        
        assert status.is_valid is True
        assert status.is_broken is False
        assert status.error_message is None
    
    def test_symlink_status_broken(self):
        """Test broken symlink status"""
        status = SymlinkStatus(
            path="/test/broken",
            target="/nonexistent",
            exists=True,
            is_valid=False,
            is_broken=True,
            error_message="Target does not exist",
            timestamp=datetime.now()
        )
        
        assert status.is_valid is False
        assert status.is_broken is True
        assert status.error_message == "Target does not exist"


class TestStorageMonitor:
    """Test storage monitor functionality"""
    
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
        settings.paths.backup_root = f"{temp_dir}/backup"
        settings.paths.app_logs = f"{temp_dir}/logs"
        
        # Set monitoring settings for testing
        settings.monitoring.check_interval = 1  # 1 second for fast testing
        settings.monitoring.disk_usage_warning = 0.8
        settings.monitoring.disk_usage_critical = 0.9
        
        return settings
    
    @pytest.fixture
    def storage_monitor(self, mock_settings):
        """Create storage monitor instance for testing"""
        return StorageMonitor(mock_settings)
    
    def test_storage_monitor_initialization(self, storage_monitor):
        """Test storage monitor initialization"""
        assert storage_monitor.settings is not None
        assert storage_monitor.logger is not None
        assert storage_monitor.monitoring is False
        assert storage_monitor.monitor_thread is None
        assert len(storage_monitor.monitored_paths) > 0
    
    @patch('psutil.disk_usage')
    def test_get_storage_health_success(self, mock_disk_usage, storage_monitor, temp_dir):
        """Test successful storage health retrieval"""
        # Create test path
        test_path = Path(f"{temp_dir}/test_storage")
        test_path.mkdir(parents=True)
        
        # Mock disk usage
        mock_usage = MagicMock()
        mock_usage.total = 1000000
        mock_usage.used = 500000
        mock_usage.free = 500000
        mock_disk_usage.return_value = mock_usage
        
        # Mock other methods
        with patch.object(storage_monitor, '_get_mount_info') as mock_mount:
            mock_mount.return_value = {
                "mount_point": "/",
                "filesystem": "ext4",
                "device": "/dev/sda1"
            }
            
            with patch.object(storage_monitor, '_get_inode_info') as mock_inode:
                mock_inode.return_value = {
                    "total": 1000,
                    "used": 500,
                    "free": 500,
                    "usage_percent": 50.0
                }
                
                health = storage_monitor.get_storage_health(str(test_path))
                
                assert health.path == str(test_path)
                assert health.total_space == 1000000
                assert health.used_space == 500000
                assert health.usage_percent == 50.0
                assert health.is_healthy is True
    
    def test_get_storage_health_nonexistent_path(self, storage_monitor):
        """Test storage health for nonexistent path"""
        health = storage_monitor.get_storage_health("/nonexistent/path")
        
        assert health.path == "/nonexistent/path"
        assert health.is_healthy is False
        assert len(health.warnings) > 0
        assert "Path does not exist" in health.warnings[0]
    
    @patch('psutil.disk_usage')
    def test_get_storage_health_high_usage(self, mock_disk_usage, storage_monitor, temp_dir):
        """Test storage health with high disk usage"""
        # Create test path
        test_path = Path(f"{temp_dir}/test_storage")
        test_path.mkdir(parents=True)
        
        # Mock high disk usage (90%)
        mock_usage = MagicMock()
        mock_usage.total = 1000000
        mock_usage.used = 900000
        mock_usage.free = 100000
        mock_disk_usage.return_value = mock_usage
        
        with patch.object(storage_monitor, '_get_mount_info') as mock_mount:
            mock_mount.return_value = {"mount_point": "/", "filesystem": "ext4", "device": "/dev/sda1"}
            
            with patch.object(storage_monitor, '_get_inode_info') as mock_inode:
                mock_inode.return_value = {"total": 1000, "used": 500, "free": 500, "usage_percent": 50.0}
                
                health = storage_monitor.get_storage_health(str(test_path))
                
                assert health.usage_percent == 90.0
                assert health.is_healthy is False
                assert len(health.warnings) > 0
                assert "Critical disk usage" in health.warnings[0]
    
    @patch('psutil.disk_partitions')
    def test_get_mount_info(self, mock_partitions, storage_monitor):
        """Test mount info retrieval"""
        mock_partition = MagicMock()
        mock_partition.mountpoint = "/"
        mock_partition.fstype = "ext4"
        mock_partition.device = "/dev/sda1"
        mock_partitions.return_value = [mock_partition]
        
        mount_info = storage_monitor._get_mount_info("/test/path")
        
        assert mount_info["mount_point"] == "/"
        assert mount_info["filesystem"] == "ext4"
        assert mount_info["device"] == "/dev/sda1"
    
    @patch('subprocess.run')
    def test_get_inode_info_success(self, mock_run, storage_monitor):
        """Test successful inode info retrieval"""
        mock_result = MagicMock()
        mock_result.stdout = "Filesystem      Inodes   IUsed   IFree IUse% Mounted on\n/dev/sda1         1000     500     500   50% /"
        mock_run.return_value = mock_result
        
        inode_info = storage_monitor._get_inode_info("/test/path")
        
        assert inode_info is not None
        assert inode_info["total"] == 1000
        assert inode_info["used"] == 500
        assert inode_info["free"] == 500
        assert inode_info["usage_percent"] == 50.0
    
    @patch('subprocess.run')
    def test_get_inode_info_failure(self, mock_run, storage_monitor):
        """Test inode info retrieval failure"""
        mock_run.side_effect = Exception("Command failed")
        
        inode_info = storage_monitor._get_inode_info("/test/path")
        
        assert inode_info is None
    
    def test_get_performance_metrics(self, storage_monitor, temp_dir):
        """Test performance metrics measurement"""
        test_path = Path(f"{temp_dir}/perf_test")
        test_path.mkdir(parents=True)
        
        metrics = storage_monitor.get_performance_metrics(str(test_path), test_size_mb=1)
        
        assert metrics.path == str(test_path)
        assert metrics.read_latency_ms >= 0
        assert metrics.write_latency_ms >= 0
        assert metrics.read_throughput_mbps >= 0
        assert metrics.write_throughput_mbps >= 0
    
    def test_check_single_symlink_valid(self, storage_monitor, temp_dir):
        """Test checking valid symlink"""
        # Create target and symlink
        target = Path(f"{temp_dir}/target")
        target.mkdir()
        
        link = Path(f"{temp_dir}/symlink")
        link.symlink_to(target)
        
        status = storage_monitor._check_single_symlink(str(link))
        
        assert status.exists is True
        assert status.is_valid is True
        assert status.is_broken is False
        assert status.error_message is None
    
    def test_check_single_symlink_broken(self, storage_monitor, temp_dir):
        """Test checking broken symlink"""
        # Create broken symlink
        link = Path(f"{temp_dir}/broken_link")
        link.symlink_to("/nonexistent/target")
        
        status = storage_monitor._check_single_symlink(str(link))
        
        assert status.exists is True
        assert status.is_valid is False
        assert status.is_broken is True
        assert status.error_message == "Target does not exist"
    
    def test_check_single_symlink_missing(self, storage_monitor):
        """Test checking missing symlink"""
        status = storage_monitor._check_single_symlink("/nonexistent/symlink")
        
        assert status.exists is False
        assert status.is_valid is False
        assert status.is_broken is True
        assert "does not exist" in status.error_message
    
    def test_check_symlinks(self, storage_monitor, temp_dir):
        """Test checking multiple symlinks"""
        # Create app directory structure
        app_dir = Path(f"{temp_dir}/app")
        app_dir.mkdir(parents=True)
        
        # Create some test symlinks
        target = Path(f"{temp_dir}/target")
        target.mkdir()
        
        link1 = app_dir / "models"
        link1.symlink_to(target)
        
        statuses = storage_monitor.check_symlinks()
        
        # Should return a list of symlink statuses
        assert isinstance(statuses, list)
        # Exact count depends on what symlinks exist in the test environment
    
    @patch('subprocess.run')
    def test_check_smart_health_enabled(self, mock_run, storage_monitor):
        """Test SMART health check when enabled"""
        storage_monitor.settings.monitoring.enable_smart_checks = True
        
        # Mock successful SMART check
        mock_result = MagicMock()
        mock_result.stdout = "SMART overall-health self-assessment test result: PASSED"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        with patch.object(storage_monitor, '_get_storage_devices') as mock_devices:
            mock_devices.return_value = ["/dev/sda"]
            
            smart_health = storage_monitor.check_smart_health()
            
            assert smart_health["enabled"] is True
            assert "devices" in smart_health
            assert "/dev/sda" in smart_health["devices"]
            assert smart_health["devices"]["/dev/sda"]["healthy"] is True
    
    def test_check_smart_health_disabled(self, storage_monitor):
        """Test SMART health check when disabled"""
        storage_monitor.settings.monitoring.enable_smart_checks = False
        
        smart_health = storage_monitor.check_smart_health()
        
        assert smart_health["enabled"] is False
        assert "SMART checks disabled" in smart_health["message"]
    
    @patch('os.listdir')
    def test_get_storage_devices(self, mock_listdir, storage_monitor):
        """Test storage device enumeration"""
        # Mock /dev directory listing
        mock_listdir.return_value = [
            "nvme0n1", "nvme1n1", "sda", "sdb", "loop0", "tty0"
        ]
        
        devices = storage_monitor._get_storage_devices()
        
        expected_devices = ["/dev/nvme0n1", "/dev/nvme1n1", "/dev/sda", "/dev/sdb"]
        assert all(device in devices for device in expected_devices)
        assert "/dev/loop0" not in devices  # Should be filtered out
        assert "/dev/tty0" not in devices   # Should be filtered out
    
    def test_generate_health_report(self, storage_monitor, temp_dir):
        """Test health report generation"""
        # Create test directories
        for path in storage_monitor.monitored_paths:
            Path(path).mkdir(parents=True, exist_ok=True)
        
        with patch.object(storage_monitor, 'get_storage_health') as mock_health:
            mock_health.return_value = StorageHealth(
                path="/test", total_space=1000, used_space=500, free_space=500,
                usage_percent=50.0, inode_total=1000, inode_used=500, 
                inode_free=500, inode_usage_percent=50.0, mount_point="/",
                filesystem="ext4", is_healthy=True, warnings=[], 
                timestamp=datetime.now()
            )
            
            with patch.object(storage_monitor, 'check_symlinks') as mock_symlinks:
                mock_symlinks.return_value = [
                    SymlinkStatus("/test/link", "/test/target", True, True, False, None, datetime.now())
                ]
                
                report = storage_monitor.generate_health_report()
                
                assert "timestamp" in report
                assert "storage_health" in report
                assert "symlink_status" in report
                assert "summary" in report
                
                summary = report["summary"]
                assert "healthy_storage" in summary
                assert "total_storage" in summary
                assert "healthy_symlinks" in summary
                assert "total_symlinks" in summary
                assert "overall_healthy" in summary
    
    def test_start_stop_monitoring(self, storage_monitor):
        """Test starting and stopping monitoring"""
        # Start monitoring
        storage_monitor.start_monitoring()
        
        assert storage_monitor.monitoring is True
        assert storage_monitor.monitor_thread is not None
        assert storage_monitor.monitor_thread.is_alive()
        
        # Stop monitoring
        storage_monitor.stop_monitoring()
        
        assert storage_monitor.monitoring is False
        # Thread should stop within timeout
        time.sleep(0.1)  # Give it a moment to stop
    
    def test_get_status_summary(self, storage_monitor, temp_dir):
        """Test status summary generation"""
        # Create test directories
        for path in storage_monitor.monitored_paths:
            Path(path).mkdir(parents=True, exist_ok=True)
        
        with patch.object(storage_monitor, 'generate_health_report') as mock_report:
            mock_report.return_value = {
                "summary": {
                    "healthy_storage": 2,
                    "total_storage": 3,
                    "healthy_symlinks": 5,
                    "total_symlinks": 6,
                    "overall_healthy": False,
                    "errors": ["Test error 1", "Test error 2"]
                }
            }
            
            summary = storage_monitor.get_status_summary()
            
            assert "Storage Health: 2/3 healthy" in summary
            assert "Symlink Health: 5/6 healthy" in summary
            assert "❌ Issues Detected" in summary
            assert "Errors: 2" in summary
            assert "Test error 1" in summary


class TestStorageMonitorIntegration:
    """Integration tests for storage monitor"""
    
    @pytest.fixture
    def integration_temp_dir(self):
        """Create temporary directory for integration testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_full_monitoring_cycle(self, integration_temp_dir):
        """Test full monitoring cycle"""
        # Create mock settings
        settings = StorageSettings()
        settings.paths.models_root = f"{integration_temp_dir}/models"
        settings.paths.backup_root = f"{integration_temp_dir}/backup"
        settings.paths.app_root = f"{integration_temp_dir}/app"
        settings.paths.app_logs = f"{integration_temp_dir}/logs"
        settings.monitoring.check_interval = 1  # Fast for testing
        
        monitor = StorageMonitor(settings)
        
        # Create test directories
        for path in monitor.monitored_paths:
            Path(path).mkdir(parents=True, exist_ok=True)
        
        # Generate health report
        report = monitor.generate_health_report()
        
        # Verify report structure
        assert "storage_health" in report
        assert "symlink_status" in report
        assert "summary" in report
        
        # Verify summary contains expected data
        summary = report["summary"]
        assert isinstance(summary["total_storage"], int)
        assert isinstance(summary["healthy_storage"], int)
        assert isinstance(summary["total_symlinks"], int)
        assert isinstance(summary["healthy_symlinks"], int)
        assert isinstance(summary["overall_healthy"], bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])