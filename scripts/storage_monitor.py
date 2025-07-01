#!/usr/bin/env python3
"""
PLANB-06: Storage Monitoring and Health Checks 
Real-time monitoring of storage health, performance, and symlinks
"""

import os
import sys
import time
import json
import psutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
import signal

# Add configs directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from storage_settings import StorageSettings, load_storage_settings
except ImportError:
    print("❌ Could not import storage_settings. Please ensure configs/storage_settings.py exists.")
    sys.exit(1)


@dataclass
class StorageHealth:
    """Storage health information"""
    path: str
    total_space: int
    used_space: int
    free_space: int
    usage_percent: float
    inode_total: int
    inode_used: int
    inode_free: int
    inode_usage_percent: float
    mount_point: str
    filesystem: str
    is_healthy: bool
    warnings: List[str]
    timestamp: datetime


@dataclass
class PerformanceMetrics:
    """Storage performance metrics"""
    path: str
    read_latency_ms: float
    write_latency_ms: float
    read_throughput_mbps: float
    write_throughput_mbps: float
    iops_read: float
    iops_write: float
    timestamp: datetime


@dataclass
class SymlinkStatus:
    """Symlink health status"""
    path: str
    target: str
    exists: bool
    is_valid: bool
    is_broken: bool
    error_message: Optional[str]
    timestamp: datetime


class StorageMonitor:
    """Storage monitoring and health check system"""
    
    def __init__(self, settings: Optional[StorageSettings] = None):
        """Initialize storage monitor"""
        self.settings = settings or load_storage_settings()
        self.logger = self._setup_logging()
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Storage paths to monitor
        self.monitored_paths = [
            self.settings.paths.models_root,
            self.settings.paths.backup_root,
            self.settings.paths.app_root
        ]
        
        # Health history for trend analysis
        self.health_history: List[StorageHealth] = []
        self.performance_history: List[PerformanceMetrics] = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("StorageMonitor")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.settings.paths.app_logs)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        log_file = log_dir / "storage_monitor.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def get_storage_health(self, path: str) -> StorageHealth:
        """Get comprehensive storage health information"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                return StorageHealth(
                    path=path,
                    total_space=0,
                    used_space=0,
                    free_space=0,
                    usage_percent=0.0,
                    inode_total=0,
                    inode_used=0,
                    inode_free=0,
                    inode_usage_percent=0.0,
                    mount_point="",
                    filesystem="",
                    is_healthy=False,
                    warnings=["Path does not exist"],
                    timestamp=datetime.now()
                )
            
            # Get disk usage statistics
            disk_usage = psutil.disk_usage(path)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Get filesystem information
            mount_info = self._get_mount_info(path)
            
            # Get inode information
            inode_info = self._get_inode_info(path)
            
            # Determine health status and warnings
            warnings = []
            is_healthy = True
            
            if usage_percent > self.settings.monitoring.disk_usage_critical * 100:
                warnings.append(f"Critical disk usage: {usage_percent:.1f}%")
                is_healthy = False
            elif usage_percent > self.settings.monitoring.disk_usage_warning * 100:
                warnings.append(f"High disk usage: {usage_percent:.1f}%")
            
            if inode_info and inode_info["usage_percent"] > self.settings.monitoring.inode_usage_warning * 100:
                warnings.append(f"High inode usage: {inode_info['usage_percent']:.1f}%")
                if inode_info["usage_percent"] > 95.0:
                    is_healthy = False
            
            return StorageHealth(
                path=path,
                total_space=disk_usage.total,
                used_space=disk_usage.used,
                free_space=disk_usage.free,
                usage_percent=usage_percent,
                inode_total=inode_info["total"] if inode_info else 0,
                inode_used=inode_info["used"] if inode_info else 0,
                inode_free=inode_info["free"] if inode_info else 0,
                inode_usage_percent=inode_info["usage_percent"] if inode_info else 0.0,
                mount_point=mount_info["mount_point"],
                filesystem=mount_info["filesystem"],
                is_healthy=is_healthy,
                warnings=warnings,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get storage health for {path}: {e}")
            return StorageHealth(
                path=path,
                total_space=0,
                used_space=0,
                free_space=0,
                usage_percent=0.0,
                inode_total=0,
                inode_used=0,
                inode_free=0,
                inode_usage_percent=0.0,
                mount_point="",
                filesystem="",
                is_healthy=False,
                warnings=[f"Error getting health info: {e}"],
                timestamp=datetime.now()
            )
    
    def _get_mount_info(self, path: str) -> Dict[str, str]:
        """Get mount point and filesystem information"""
        try:
            # Find the mount point for this path
            path_obj = Path(path).resolve()
            for partition in psutil.disk_partitions():
                if str(path_obj).startswith(partition.mountpoint):
                    return {
                        "mount_point": partition.mountpoint,
                        "filesystem": partition.fstype,
                        "device": partition.device
                    }
            
            return {"mount_point": "/", "filesystem": "unknown", "device": "unknown"}
            
        except Exception:
            return {"mount_point": "unknown", "filesystem": "unknown", "device": "unknown"}
    
    def _get_inode_info(self, path: str) -> Optional[Dict[str, Any]]:
        """Get inode usage information"""
        try:
            result = subprocess.run(
                ["df", "-i", path],
                capture_output=True,
                text=True,
                check=True
            )
            
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                fields = lines[1].split()
                if len(fields) >= 4:
                    total = int(fields[1])
                    used = int(fields[2])
                    free = int(fields[3])
                    usage_percent = (used / total * 100) if total > 0 else 0.0
                    
                    return {
                        "total": total,
                        "used": used,
                        "free": free,
                        "usage_percent": usage_percent
                    }
            
        except Exception as e:
            self.logger.warning(f"Could not get inode info for {path}: {e}")
        
        return None
    
    def get_performance_metrics(self, path: str, test_size_mb: int = 10) -> PerformanceMetrics:
        """Measure storage performance metrics"""
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                path_obj.mkdir(parents=True, exist_ok=True)
            
            test_file = path_obj / ".storage_perf_test"
            test_data = b"0" * (1024 * 1024)  # 1MB of data
            
            # Measure write performance
            write_start = time.time()
            with open(test_file, "wb") as f:
                for _ in range(test_size_mb):
                    f.write(test_data)
                f.flush()
                os.fsync(f.fileno())
            write_time = time.time() - write_start
            
            # Measure read performance
            read_start = time.time()
            with open(test_file, "rb") as f:
                while f.read(1024 * 1024):
                    pass
            read_time = time.time() - read_start
            
            # Clean up test file
            test_file.unlink()
            
            # Calculate metrics
            data_size_mb = test_size_mb
            write_throughput = data_size_mb / write_time if write_time > 0 else 0
            read_throughput = data_size_mb / read_time if read_time > 0 else 0
            write_latency = (write_time / test_size_mb) * 1000 if test_size_mb > 0 else 0
            read_latency = (read_time / test_size_mb) * 1000 if test_size_mb > 0 else 0
            
            # Estimate IOPS (rough approximation)
            iops_write = (test_size_mb * 256) / write_time if write_time > 0 else 0  # Assuming 4KB blocks
            iops_read = (test_size_mb * 256) / read_time if read_time > 0 else 0
            
            return PerformanceMetrics(
                path=path,
                read_latency_ms=read_latency,
                write_latency_ms=write_latency,
                read_throughput_mbps=read_throughput,
                write_throughput_mbps=write_throughput,
                iops_read=iops_read,
                iops_write=iops_write,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Failed to measure performance for {path}: {e}")
            return PerformanceMetrics(
                path=path,
                read_latency_ms=0.0,
                write_latency_ms=0.0,
                read_throughput_mbps=0.0,
                write_throughput_mbps=0.0,
                iops_read=0.0,
                iops_write=0.0,
                timestamp=datetime.now()
            )
    
    def check_symlinks(self) -> List[SymlinkStatus]:
        """Check health of all symlinks"""
        symlink_statuses = []
        
        # Primary symlinks
        primary_symlinks = [
            self.settings.paths.app_models,
            f"{self.settings.paths.app_root}/downloads",
            f"{self.settings.paths.app_root}/staging"
        ]
        
        for link_path in primary_symlinks:
            status = self._check_single_symlink(link_path)
            symlink_statuses.append(status)
        
        # Convenience symlinks
        convenience_dir = Path(f"{self.settings.paths.app_root}/model-links")
        if convenience_dir.exists():
            for item in convenience_dir.iterdir():
                if item.is_symlink():
                    status = self._check_single_symlink(str(item))
                    symlink_statuses.append(status)
        
        # Cache symlinks
        cache_symlinks = [
            f"{os.path.expanduser('~')}/.cache/huggingface",
            f"{os.path.expanduser('~')}/.cache/torch"
        ]
        
        for link_path in cache_symlinks:
            if Path(link_path).exists():
                status = self._check_single_symlink(link_path)
                symlink_statuses.append(status)
        
        return symlink_statuses
    
    def _check_single_symlink(self, link_path: str) -> SymlinkStatus:
        """Check status of a single symlink"""
        try:
            link = Path(link_path)
            
            if not link.exists() and not link.is_symlink():
                return SymlinkStatus(
                    path=link_path,
                    target="",
                    exists=False,
                    is_valid=False,
                    is_broken=True,
                    error_message="Symlink does not exist",
                    timestamp=datetime.now()
                )
            
            if not link.is_symlink():
                return SymlinkStatus(
                    path=link_path,
                    target="",
                    exists=True,
                    is_valid=False,
                    is_broken=True,
                    error_message="Path exists but is not a symlink",
                    timestamp=datetime.now()
                )
            
            target = str(link.readlink())
            target_exists = Path(target).exists()
            
            return SymlinkStatus(
                path=link_path,
                target=target,
                exists=True,
                is_valid=target_exists,
                is_broken=not target_exists,
                error_message=None if target_exists else "Target does not exist",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            return SymlinkStatus(
                path=link_path,
                target="",
                exists=False,
                is_valid=False,
                is_broken=True,
                error_message=f"Error checking symlink: {e}",
                timestamp=datetime.now()
            )
    
    def check_smart_health(self) -> Dict[str, Any]:
        """Check SMART health status of storage devices"""
        if not self.settings.monitoring.enable_smart_checks:
            return {"enabled": False, "message": "SMART checks disabled"}
        
        try:
            smart_results = {}
            
            # Get list of storage devices
            devices = self._get_storage_devices()
            
            for device in devices:
                try:
                    result = subprocess.run(
                        ["sudo", "smartctl", "-H", device],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    smart_results[device] = {
                        "healthy": "PASSED" in result.stdout,
                        "output": result.stdout,
                        "error": result.stderr if result.returncode != 0 else None
                    }
                    
                except subprocess.TimeoutExpired:
                    smart_results[device] = {
                        "healthy": False,
                        "output": "",
                        "error": "SMART check timed out"
                    }
                except Exception as e:
                    smart_results[device] = {
                        "healthy": False,
                        "output": "",
                        "error": str(e)
                    }
            
            return {
                "enabled": True,
                "devices": smart_results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"SMART health check failed: {e}")
            return {
                "enabled": True,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _get_storage_devices(self) -> List[str]:
        """Get list of storage devices to monitor"""
        devices = []
        
        try:
            # Get NVMe devices
            nvme_devices = [f"/dev/{d}" for d in os.listdir("/dev") if d.startswith("nvme") and "n1" in d]
            devices.extend(nvme_devices)
            
            # Get SATA devices
            sata_devices = [f"/dev/{d}" for d in os.listdir("/dev") if d.startswith("sd") and len(d) == 3]
            devices.extend(sata_devices)
            
        except Exception as e:
            self.logger.warning(f"Could not enumerate storage devices: {e}")
        
        return devices
    
    def generate_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "storage_health": [],
            "symlink_status": [],
            "smart_health": {},
            "summary": {
                "healthy_storage": 0,
                "total_storage": 0,
                "healthy_symlinks": 0,
                "total_symlinks": 0,
                "overall_healthy": True,
                "warnings": [],
                "errors": []
            }
        }
        
        # Check storage health
        for path in self.monitored_paths:
            health = self.get_storage_health(path)
            report["storage_health"].append(asdict(health))
            
            report["summary"]["total_storage"] += 1
            if health.is_healthy:
                report["summary"]["healthy_storage"] += 1
            else:
                report["summary"]["overall_healthy"] = False
                report["summary"]["errors"].extend(health.warnings)
        
        # Check symlink status
        symlink_statuses = self.check_symlinks()
        for status in symlink_statuses:
            report["symlink_status"].append(asdict(status))
            
            report["summary"]["total_symlinks"] += 1
            if status.is_valid:
                report["summary"]["healthy_symlinks"] += 1
            else:
                report["summary"]["overall_healthy"] = False
                if status.error_message:
                    report["summary"]["errors"].append(f"Symlink {status.path}: {status.error_message}")
        
        # Check SMART health
        if self.settings.monitoring.enable_smart_checks:
            report["smart_health"] = self.check_smart_health()
            
            if report["smart_health"].get("devices"):
                for device, health in report["smart_health"]["devices"].items():
                    if not health.get("healthy", False):
                        report["summary"]["overall_healthy"] = False
                        error_msg = health.get("error", "SMART check failed")
                        report["summary"]["errors"].append(f"Device {device}: {error_msg}")
        
        return report
    
    def start_monitoring(self) -> None:
        """Start continuous monitoring"""
        if self.monitoring:
            self.logger.warning("Monitoring is already running")
            return
        
        self.monitoring = True
        self._stop_event.clear()
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        self.logger.info("Storage monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop continuous monitoring"""
        if not self.monitoring:
            return
        
        self.monitoring = False
        self._stop_event.set()
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        self.logger.info("Storage monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring and not self._stop_event.is_set():
            try:
                # Generate health report
                report = self.generate_health_report()
                
                # Log warnings and errors
                if not report["summary"]["overall_healthy"]:
                    for error in report["summary"]["errors"]:
                        self.logger.warning(f"Health issue: {error}")
                
                # Store health data for trending
                for health_data in report["storage_health"]:
                    health = StorageHealth(**health_data)
                    self.health_history.append(health)
                
                # Trim history to prevent memory growth
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-500:]
                
                # Save report to file
                report_file = Path(self.settings.paths.app_logs) / "storage_health_report.json"
                with open(report_file, "w") as f:
                    json.dump(report, f, indent=2, default=str)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
            
            # Wait for next check interval
            self._stop_event.wait(self.settings.monitoring.check_interval)
    
    def get_status_summary(self) -> str:
        """Get quick status summary as string"""
        report = self.generate_health_report()
        summary = report["summary"]
        
        status_lines = [
            f"Storage Health: {summary['healthy_storage']}/{summary['total_storage']} healthy",
            f"Symlink Health: {summary['healthy_symlinks']}/{summary['total_symlinks']} healthy",
            f"Overall Status: {'✅ Healthy' if summary['overall_healthy'] else '❌ Issues Detected'}"
        ]
        
        if summary["errors"]:
            status_lines.append(f"Errors: {len(summary['errors'])}")
            for error in summary["errors"][:5]:  # Show first 5 errors
                status_lines.append(f"  - {error}")
        
        return "\n".join(status_lines)


def main():
    """Main entry point for storage monitoring"""
    def signal_handler(signum, frame):
        print("\nShutting down storage monitor...")
        if 'monitor' in locals():
            monitor.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if len(sys.argv) < 2:
        print("Usage: storage_monitor.py <command>")
        print("Commands: status, health-report, start-monitor, performance")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        monitor = StorageMonitor()
        
        if command == "status":
            print(monitor.get_status_summary())
        elif command == "health-report":
            report = monitor.generate_health_report()
            print(json.dumps(report, indent=2, default=str))
        elif command == "start-monitor":
            print("Starting continuous storage monitoring...")
            print("Press Ctrl+C to stop")
            monitor.start_monitoring()
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                monitor.stop_monitoring()
                print("\nMonitoring stopped")
        elif command == "performance":
            path = sys.argv[2] if len(sys.argv) > 2 else monitor.settings.paths.models_root
            print(f"Testing performance for: {path}")
            metrics = monitor.get_performance_metrics(path)
            print(json.dumps(asdict(metrics), indent=2, default=str))
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()