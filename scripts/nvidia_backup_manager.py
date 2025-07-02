#!/usr/bin/env python3
"""
NVIDIA Backup and Rollback Manager
Handles backup creation and system rollback for NVIDIA driver installation
"""

import subprocess
import shutil
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import json


class NVIDIABackupManager:
    """Manages backup and rollback operations for NVIDIA driver installation"""

    def __init__(self, backup_base_dir: Path = Path("/opt/citadel/backups")):
        """Initialize backup manager with specified backup directory"""
        self.backup_base_dir = backup_base_dir
        self.current_backup_dir: Optional[Path] = None
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for backup operations"""
        logger = logging.getLogger("nvidia_backup")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

    def create_backup(self) -> Path:
        """Create comprehensive backup of current system state"""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.current_backup_dir = self.backup_base_dir / f"nvidia-{timestamp}"
        
        try:
            # Create backup directory
            self.current_backup_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Creating backup at {self.current_backup_dir}")

            # Backup package state
            self._backup_package_state()
            
            # Backup configuration files
            self._backup_configuration_files()
            
            # Backup systemd services
            self._backup_systemd_services()
            
            # Create backup metadata
            self._create_backup_metadata()
            
            self.logger.info("✅ Backup completed successfully")
            return self.current_backup_dir
            
        except Exception as e:
            self.logger.error(f"❌ Backup failed: {e}")
            raise

    def _backup_package_state(self) -> None:
        """Backup current package installation state"""
        try:
            # Get list of NVIDIA and CUDA packages
            cmd = ["dpkg", "-l"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            nvidia_packages = [
                line for line in result.stdout.split('\n')
                if any(pkg in line.lower() for pkg in ['nvidia', 'cuda'])
            ]
            
            packages_file = self.current_backup_dir / "packages.list"
            with open(packages_file, 'w') as f:
                f.write('\n'.join(nvidia_packages))
                
            self.logger.info("📦 Package state backed up")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to backup package state: {e}")

    def _backup_configuration_files(self) -> None:
        """Backup critical configuration files"""
        config_files = [
            "/etc/X11/xorg.conf",
            "/etc/environment",
            "~/.bashrc"
        ]
        
        modprobe_dir = Path("/etc/modprobe.d")
        
        for config_file in config_files:
            if config_file.startswith("~/"):
                src_path = Path(config_file).expanduser()
            else:
                src_path = Path(config_file)
            if src_path.exists():
                try:
                    dst_path = self.current_backup_dir / src_path.name
                    shutil.copy2(src_path, dst_path)
                    self.logger.info(f"📄 Backed up {src_path}")
                except Exception as e:
                    self.logger.warning(f"Failed to backup {src_path}: {e}")
        
        # Backup modprobe.d directory
        if modprobe_dir.exists():
            try:
                dst_modprobe = self.current_backup_dir / "modprobe.d"
                shutil.copytree(modprobe_dir, dst_modprobe, dirs_exist_ok=True)
                self.logger.info("📁 Backed up modprobe.d directory")
            except Exception as e:
                self.logger.warning(f"Failed to backup modprobe.d: {e}")

    def _backup_systemd_services(self) -> None:
        """Backup NVIDIA-related systemd services"""
        try:
            cmd = ["systemctl", "list-unit-files"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            nvidia_services = [
                line for line in result.stdout.split('\n')
                if 'nvidia' in line.lower()
            ]
            
            services_file = self.current_backup_dir / "services.list"
            with open(services_file, 'w') as f:
                f.write('\n'.join(nvidia_services))
                
            self.logger.info("🔧 Systemd services backed up")
            
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to backup systemd services: {e}")

    def _create_backup_metadata(self) -> None:
        """Create metadata file with backup information"""
        metadata = {
            "timestamp": datetime.now().isoformat(),
            "backup_dir": str(self.current_backup_dir),
            "system_info": self._get_system_info()
        }
        
        metadata_file = self.current_backup_dir / "backup_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        try:
            # Get kernel version
            kernel_result = subprocess.run(
                ["uname", "-r"], capture_output=True, text=True, check=True
            )
            
            # Get GPU information if available
            gpu_info = "Not available"
            try:
                lspci_result = subprocess.run(
                    ["lspci"], capture_output=True, text=True, check=True
                )
                gpu_lines = [
                    line for line in lspci_result.stdout.split('\n')
                    if 'nvidia' in line.lower()
                ]
                gpu_info = gpu_lines if gpu_lines else "No NVIDIA GPUs detected"
            except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
                self.logger.debug(f"Failed to get GPU info via lspci: {e}")
                gpu_info = "GPU detection failed"
                
            return {
                "kernel_version": kernel_result.stdout.strip(),
                "gpu_info": gpu_info
            }
        except Exception as e:
            self.logger.warning(f"Failed to get system info: {e}")
            return {}

    def rollback_changes(self, backup_dir: Optional[Path] = None) -> bool:
        """Rollback system to previous state"""
        if backup_dir:
            rollback_dir = backup_dir
        elif self.current_backup_dir:
            rollback_dir = self.current_backup_dir
        else:
            self.logger.error("No backup directory specified for rollback")
            return False

        if not rollback_dir.exists():
            self.logger.error(f"Backup directory not found: {rollback_dir}")
            return False

        try:
            self.logger.info(f"🔄 Rolling back from backup: {rollback_dir}")
            
            # Restore configuration files
            self._restore_configuration_files(rollback_dir)
            
            self.logger.info("✅ Rollback completed. System may require reboot.")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Rollback failed: {e}")
            return False

    def _restore_configuration_files(self, backup_dir: Path) -> None:
        """Restore configuration files from backup"""
        restore_mappings = {
            "xorg.conf": Path("/etc/X11/xorg.conf"),
            "environment": Path("/etc/environment"),
            "bashrc": Path.home() / ".bashrc"
        }
        
        for backup_name, target_path in restore_mappings.items():
            backup_file = backup_dir / backup_name
            if backup_file.exists():
                try:
                    # Ensure parent directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy the file with error handling
                    shutil.copy2(backup_file, target_path)
                    self.logger.info(f"📄 Restored {target_path}")
                except PermissionError as e:
                    self.logger.warning(f"Permission denied restoring {target_path}: {e}")
                except OSError as e:
                    self.logger.warning(f"OS error restoring {target_path}: {e}")
                except Exception as e:
                    self.logger.warning(f"Failed to restore {target_path}: {e}")
        
        # Restore modprobe.d directory
        backup_modprobe = backup_dir / "modprobe.d"
        if backup_modprobe.exists():
            try:
                target_modprobe = Path("/etc/modprobe.d")
                # Ensure target directory exists
                target_modprobe.mkdir(parents=True, exist_ok=True)
                
                # Copy each file from backup modprobe.d
                for item in backup_modprobe.iterdir():
                    if item.is_file():
                        target_file = target_modprobe / item.name
                        shutil.copy2(item, target_file)
                        
                self.logger.info("📁 Restored modprobe.d directory")
            except PermissionError as e:
                self.logger.warning(f"Permission denied restoring modprobe.d: {e}")
            except OSError as e:
                self.logger.warning(f"OS error restoring modprobe.d: {e}")
            except Exception as e:
                self.logger.warning(f"Failed to restore modprobe.d: {e}")

    def list_backups(self) -> List[Path]:
        """List available backup directories"""
        if not self.backup_base_dir.exists():
            return []
        
        backups = [
            path for path in self.backup_base_dir.iterdir()
            if path.is_dir() and path.name.startswith("nvidia-")
        ]
        
        return sorted(backups, key=lambda x: x.name, reverse=True)

    def get_latest_backup(self) -> Optional[Path]:
        """Get the most recent backup directory"""
        backups = self.list_backups()
        return backups[0] if backups else None


def main():
    """CLI interface for backup manager"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: nvidia_backup_manager.py {backup|rollback|list}")
        sys.exit(1)
    
    manager = NVIDIABackupManager()
    action = sys.argv[1]
    
    if action == "backup":
        backup_dir = manager.create_backup()
        print(f"Backup created: {backup_dir}")
        
    elif action == "rollback":
        latest_backup = manager.get_latest_backup()
        if latest_backup:
            success = manager.rollback_changes(latest_backup)
            print(f"Rollback {'successful' if success else 'failed'}")
        else:
            print("No backups available for rollback")
            
    elif action == "list":
        backups = manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                print(f"  {backup}")
        else:
            print("No backups found")
            
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()