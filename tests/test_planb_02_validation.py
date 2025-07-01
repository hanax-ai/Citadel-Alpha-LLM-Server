#!/usr/bin/env python3
"""
PLANB-02 Storage Configuration Validation
Tests storage optimization, directory structure, symlinks, and backup integration
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class StorageValidator:
    """Validates PLANB-02 storage configuration implementation"""
    
    def __init__(self):
        self.results: Dict[str, bool] = {}
        self.errors: List[str] = []
        
    def run_command(self, cmd: List[str]) -> Tuple[bool, str]:
        """Run command and return success status and output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.returncode == 0, result.stdout.strip()
        except Exception as e:
            return False, str(e)

    def test_required_tools(self) -> bool:
        """Test if required tools are installed"""
        tools = ['iostat', 'smartctl', 'tree', 'rsync']
        all_installed = True
        
        for tool in tools:
            success, _ = self.run_command(['which', tool])
            if not success:
                self.errors.append(f"Required tool missing: {tool}")
                all_installed = False
                
        return all_installed

    def test_storage_mounts(self) -> bool:
        """Test if storage devices are properly mounted"""
        required_mounts = [
            '/mnt/citadel-models',
            '/mnt/citadel-backup'
        ]
        
        success, output = self.run_command(['df', '-h'])
        if not success:
            self.errors.append("Failed to check storage mounts")
            return False
            
        all_mounted = True
        for mount in required_mounts:
            if mount not in output:
                self.errors.append(f"Storage not mounted: {mount}")
                all_mounted = False
                
        return all_mounted

    def test_mount_options(self) -> bool:
        """Test if mount options are optimized"""
        success, output = self.run_command(['mount'])
        if not success:
            self.errors.append("Failed to check mount options")
            return False
            
        # Check for optimized mount options
        optimized = True
        if 'citadel-models' in output:
            if 'noatime' not in output or 'writeback' not in output:
                self.errors.append("Model storage mount options not optimized")
                optimized = False
                
        if 'citadel-backup' in output:
            if 'noatime' not in output or 'ordered' not in output:
                self.errors.append("Backup storage mount options not optimized")
                optimized = False
                
        return optimized

    def test_directory_structure(self) -> bool:
        """Test if directory structure is created correctly"""
        required_dirs = [
            # Model storage directories
            '/mnt/citadel-models/active',
            '/mnt/citadel-models/archive',
            '/mnt/citadel-models/downloads',
            '/mnt/citadel-models/cache',
            # Backup storage directories
            '/mnt/citadel-backup/models',
            '/mnt/citadel-backup/configs',
            '/mnt/citadel-backup/system',
            '/mnt/citadel-backup/logs',
            # Application directories
            '/opt/citadel/scripts',
            '/opt/citadel/configs',
            '/opt/citadel/logs',
            '/opt/citadel/tmp',
        ]
        
        all_exist = True
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                self.errors.append(f"Required directory missing: {dir_path}")
                all_exist = False
                
        return all_exist

    def test_model_directories(self) -> bool:
        """Test if individual model directories are created"""
        models = [
            'mixtral-8x7b', 'yi-34b', 'nous-hermes-2', 
            'openchat-3.5', 'phi-3-mini', 'deepcoder-14b', 'mimo-vl-7b'
        ]
        
        all_exist = True
        for model in models:
            model_path = Path(f'/mnt/citadel-models/active/{model}')
            if not model_path.exists():
                self.errors.append(f"Model directory missing: {model}")
                all_exist = False
                
        return all_exist

    def test_symlinks(self) -> bool:
        """Test if symlinks are created correctly"""
        # Test main models symlink
        models_link = Path('/opt/citadel/models')
        if not models_link.is_symlink():
            self.errors.append("Main models symlink missing: /opt/citadel/models")
            return False
            
        if not models_link.exists():
            self.errors.append("Main models symlink broken: /opt/citadel/models")
            return False
            
        # Test individual model symlinks
        model_links_dir = Path('/opt/citadel/model-links')
        if not model_links_dir.exists():
            self.errors.append("Model links directory missing: /opt/citadel/model-links")
            return False
            
        return True

    def test_scripts_exist(self) -> bool:
        """Test if backup and monitoring scripts are created"""
        required_scripts = [
            '/opt/citadel/scripts/backup-config.sh',
            'scripts/verify-models.sh',
            'scripts/storage-monitor.sh',
            'scripts/planb-02-storage-configuration.sh'
        ]
        
        all_exist = True
        for script in required_scripts:
            script_path = Path(script)
            if not script_path.exists():
                self.errors.append(f"Required script missing: {script}")
                all_exist = False
            elif not os.access(script_path, os.X_OK):
                self.errors.append(f"Script not executable: {script}")
                all_exist = False
                
        return all_exist

    def test_io_schedulers(self) -> bool:
        """Test if I/O schedulers are configured"""
        # Check NVMe scheduler
        nvme_scheduler = Path('/sys/block/nvme1n1/queue/scheduler')
        if nvme_scheduler.exists():
            try:
                with open(nvme_scheduler, 'r') as f:
                    content = f.read()
                    if '[none]' not in content:
                        self.errors.append("NVMe I/O scheduler not set to 'none'")
                        return False
            except Exception as e:
                self.errors.append(f"Could not check NVMe scheduler: {e}")
                return False
                
        # Check udev rules
        udev_rules = Path('/etc/udev/rules.d/60-ssd-scheduler.rules')
        if not udev_rules.exists():
            self.errors.append("I/O scheduler udev rules not configured")
            return False
            
        return True

    def test_trim_service(self) -> bool:
        """Test if TRIM service is enabled"""
        success, output = self.run_command(['systemctl', 'is-enabled', 'fstrim.timer'])
        if not success or 'enabled' not in output:
            self.errors.append("TRIM service not enabled")
            return False
            
        return True

    def test_backup_cron(self) -> bool:
        """Test if backup cron job is configured"""
        success, output = self.run_command(['crontab', '-l'])
        if not success:
            self.errors.append("Could not check cron jobs")
            return False
            
        if 'backup-config.sh' not in output:
            self.errors.append("Backup cron job not configured")
            return False
            
        return True

    def run_all_tests(self) -> Dict[str, bool]:
        """Run all validation tests"""
        tests = [
            ('Required Tools', self.test_required_tools),
            ('Storage Mounts', self.test_storage_mounts),
            ('Mount Options', self.test_mount_options),
            ('Directory Structure', self.test_directory_structure),
            ('Model Directories', self.test_model_directories),
            ('Symlinks', self.test_symlinks),
            ('Scripts Exist', self.test_scripts_exist),
            ('I/O Schedulers', self.test_io_schedulers),
            ('TRIM Service', self.test_trim_service),
            ('Backup Cron', self.test_backup_cron),
        ]
        
        print("=== PLANB-02 Storage Configuration Validation ===\n")
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                self.results[test_name] = result
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} - {test_name}")
                if result:
                    passed += 1
            except Exception as e:
                self.results[test_name] = False
                print(f"❌ FAIL - {test_name}: {e}")
                self.errors.append(f"{test_name}: {e}")
        
        print(f"\n=== Validation Summary ===")
        print(f"Tests Passed: {passed}/{total} ({passed/total*100:.1f}%)")
        
        if self.errors:
            print(f"\n=== Issues Found ===")
            for error in self.errors:
                print(f"- {error}")
        
        return self.results


def main():
    """Main validation function"""
    validator = StorageValidator()
    results = validator.run_all_tests()
    
    # Return appropriate exit code
    all_passed = all(results.values())
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()