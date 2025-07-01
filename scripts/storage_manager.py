#!/usr/bin/env python3
"""
PLANB-06: Storage Management System
Modular storage management with error handling and rollback capabilities
"""

import os
import sys
import subprocess
import logging
import shutil
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from contextlib import contextmanager
import json

# Add configs directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from storage_settings import StorageSettings, load_storage_settings
except ImportError:
    print("❌ Could not import storage_settings. Please ensure configs/storage_settings.py exists.")
    sys.exit(1)


@dataclass
class OperationResult:
    """Result of a storage operation"""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    rollback_info: Optional[Dict[str, Any]] = None


class StorageManagerError(Exception):
    """Custom exception for storage management errors"""
    pass


class StorageManager:
    """Main storage management class with error handling and rollback capabilities"""
    
    def __init__(self, settings: Optional[StorageSettings] = None):
        """Initialize storage manager with configuration"""
        self.settings = settings or load_storage_settings()
        self.logger = self._setup_logging()
        self.operations_log: List[Dict[str, Any]] = []
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("StorageManager")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.settings.paths.app_logs)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        log_file = log_dir / "storage_manager.log"
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
    
    def _log_operation(self, operation: str, details: Dict[str, Any]) -> None:
        """Log operation for potential rollback"""
        self.operations_log.append({
            "timestamp": time.time(),
            "operation": operation,
            "details": details
        })
    
    @contextmanager
    def _transaction(self, operation_name: str):
        """Context manager for transactional operations with rollback"""
        rollback_actions = []
        try:
            self.logger.info(f"Starting operation: {operation_name}")
            yield rollback_actions
            self.logger.info(f"Completed operation: {operation_name}")
        except Exception as e:
            self.logger.error(f"Operation failed: {operation_name} - {e}")
            # Execute rollback actions in reverse order
            for action in reversed(rollback_actions):
                try:
                    action()
                    self.logger.info(f"Rollback action completed: {action.__name__}")
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
            raise
    
    def verify_storage_prerequisites(self) -> OperationResult:
        """Verify storage prerequisites are met"""
        try:
            self.logger.info("Verifying storage prerequisites...")
            
            # Check if required mount points exist
            required_mounts = [
                self.settings.paths.models_root,
                self.settings.paths.backup_root
            ]
            
            missing_mounts = []
            for mount_point in required_mounts:
                if not Path(mount_point).exists():
                    missing_mounts.append(mount_point)
            
            if missing_mounts:
                return OperationResult(
                    success=False,
                    message="Missing required mount points",
                    details={"missing_mounts": missing_mounts}
                )
            
            # Check permissions
            permission_issues = []
            for path_str in [self.settings.paths.app_root, self.settings.paths.models_root]:
                path = Path(path_str)
                if path.exists() and not os.access(path, os.R_OK | os.W_OK):
                    permission_issues.append(path_str)
            
            if permission_issues:
                return OperationResult(
                    success=False,
                    message="Permission issues detected",
                    details={"permission_issues": permission_issues}
                )
            
            self.logger.info("✅ Storage prerequisites verified")
            return OperationResult(success=True, message="Prerequisites verified")
            
        except Exception as e:
            self.logger.error(f"Prerequisites verification failed: {e}")
            return OperationResult(success=False, message=str(e))
    
    def create_directory_structure(self) -> OperationResult:
        """Create required directory structure with rollback capability"""
        try:
            with self._transaction("create_directory_structure") as rollback_actions:
                created_dirs = []
                
                # Define directories to create
                directories = [
                    self.settings.paths.models_active,
                    self.settings.paths.models_archive,
                    self.settings.paths.models_cache,
                    self.settings.paths.models_downloads,
                    self.settings.paths.models_staging,
                    f"{self.settings.paths.models_archive}/monthly",
                    f"{self.settings.paths.models_archive}/weekly", 
                    f"{self.settings.paths.models_archive}/daily",
                    f"{self.settings.paths.models_cache}/tokenizers",
                    f"{self.settings.paths.models_cache}/compiled",
                    f"{self.settings.paths.models_cache}/temporary",
                    self.settings.paths.backup_models,
                    self.settings.paths.backup_system,
                    self.settings.paths.app_scripts,
                    self.settings.paths.app_configs,
                    self.settings.paths.app_logs
                ]
                
                # Create model directories
                for model_key, model_dir in self.settings.models.model_directories.items():
                    model_path = f"{self.settings.paths.models_active}/{model_dir}"
                    directories.append(model_path)
                
                # Create directories
                for dir_path in directories:
                    path = Path(dir_path)
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        created_dirs.append(dir_path)
                        
                        # Add rollback action
                        rollback_actions.append(lambda p=path: p.rmdir() if p.exists() and not any(p.iterdir()) else None)
                        
                        self.logger.info(f"Created directory: {dir_path}")
                
                # Set permissions
                mode = int(self.settings.symlinks.directory_mode, 8)
                for dir_path in created_dirs:
                    os.chmod(dir_path, mode)
                
                self._log_operation("create_directories", {"created": created_dirs})
                
                return OperationResult(
                    success=True,
                    message=f"Created {len(created_dirs)} directories",
                    details={"created_directories": created_dirs}
                )
                
        except Exception as e:
            self.logger.error(f"Directory creation failed: {e}")
            return OperationResult(success=False, message=str(e))
    
    def create_symlinks(self) -> OperationResult:
        """Create symlinks with error handling and rollback"""
        try:
            with self._transaction("create_symlinks") as rollback_actions:
                created_symlinks = []
                
                # Primary symlinks
                primary_symlinks = [
                    (self.settings.paths.app_models, self.settings.paths.models_active),
                    (f"{self.settings.paths.app_root}/downloads", self.settings.paths.models_downloads),
                    (f"{self.settings.paths.app_root}/staging", self.settings.paths.models_staging)
                ]
                
                for link_path, target_path in primary_symlinks:
                    result = self._create_symlink(link_path, target_path, rollback_actions)
                    if result.success:
                        created_symlinks.append(link_path)
                    else:
                        raise StorageManagerError(f"Failed to create symlink: {result.message}")
                
                # Convenience symlinks
                convenience_dir = f"{self.settings.paths.app_root}/model-links"
                Path(convenience_dir).mkdir(exist_ok=True)
                
                for short_name, model_key in self.settings.models.convenience_links.items():
                    if model_key in self.settings.models.model_directories:
                        full_name = self.settings.models.model_directories[model_key]
                        link_path = f"{convenience_dir}/{short_name}"
                        target_path = f"{self.settings.paths.models_active}/{full_name}"
                        
                        result = self._create_symlink(link_path, target_path, rollback_actions)
                        if result.success:
                            created_symlinks.append(link_path)
                
                # Cache symlinks
                cache_symlinks = [
                    (f"{os.path.expanduser('~')}/.cache/huggingface", self.settings.paths.hf_cache),
                    (f"{os.path.expanduser('~')}/.cache/torch", self.settings.paths.torch_cache)
                ]
                
                for link_path, target_path in cache_symlinks:
                    result = self._create_symlink(link_path, target_path, rollback_actions)
                    if result.success:
                        created_symlinks.append(link_path)
                
                self._log_operation("create_symlinks", {"created": created_symlinks})
                
                return OperationResult(
                    success=True,
                    message=f"Created {len(created_symlinks)} symlinks",
                    details={"created_symlinks": created_symlinks}
                )
                
        except Exception as e:
            self.logger.error(f"Symlink creation failed: {e}")
            return OperationResult(success=False, message=str(e))
    
    def _create_symlink(self, link_path: str, target_path: str, rollback_actions: List) -> OperationResult:
        """Create individual symlink with proper error handling"""
        try:
            link = Path(link_path)
            target = Path(target_path)
            
            # Verify target exists if required
            if self.settings.symlinks.verify_targets and not target.exists():
                if self.settings.symlinks.create_missing_targets:
                    target.mkdir(parents=True, exist_ok=True)
                    self.logger.info(f"Created missing target: {target_path}")
                else:
                    return OperationResult(success=False, message=f"Target does not exist: {target_path}")
            
            # Remove existing link if force recreation is enabled
            if link.exists() or link.is_symlink():
                if self.settings.symlinks.force_recreate:
                    if link.is_symlink():
                        old_target = link.readlink()
                        rollback_actions.append(lambda: link.symlink_to(old_target))
                    link.unlink()
                else:
                    return OperationResult(success=True, message=f"Symlink already exists: {link_path}")
            
            # Create parent directory if needed
            link.parent.mkdir(parents=True, exist_ok=True)
            
            # Create symlink
            link.symlink_to(target)
            
            # Add rollback action
            rollback_actions.append(lambda l=link: l.unlink() if l.is_symlink() else None)
            
            self.logger.info(f"Created symlink: {link_path} → {target_path}")
            return OperationResult(success=True, message=f"Symlink created: {link_path}")
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to create symlink {link_path}: {e}")
    
    def verify_symlinks(self) -> OperationResult:
        """Verify all symlinks are working correctly"""
        try:
            self.logger.info("Verifying symlinks...")
            
            issues = []
            verified_count = 0
            
            # Check primary symlinks
            primary_symlinks = [
                self.settings.paths.app_models,
                f"{self.settings.paths.app_root}/downloads",
                f"{self.settings.paths.app_root}/staging"
            ]
            
            for link_path in primary_symlinks:
                issue = self._verify_single_symlink(link_path)
                if issue:
                    issues.append(issue)
                else:
                    verified_count += 1
            
            # Check convenience symlinks
            convenience_dir = f"{self.settings.paths.app_root}/model-links"
            if Path(convenience_dir).exists():
                for item in Path(convenience_dir).iterdir():
                    if item.is_symlink():
                        issue = self._verify_single_symlink(str(item))
                        if issue:
                            issues.append(issue)
                        else:
                            verified_count += 1
            
            if issues:
                return OperationResult(
                    success=False,
                    message=f"Found {len(issues)} symlink issues",
                    details={"issues": issues, "verified_count": verified_count}
                )
            
            self.logger.info(f"✅ Verified {verified_count} symlinks")
            return OperationResult(
                success=True,
                message=f"All {verified_count} symlinks verified",
                details={"verified_count": verified_count}
            )
            
        except Exception as e:
            self.logger.error(f"Symlink verification failed: {e}")
            return OperationResult(success=False, message=str(e))
    
    def _verify_single_symlink(self, link_path: str) -> Optional[str]:
        """Verify a single symlink, return issue description if any"""
        link = Path(link_path)
        
        if not link.exists() and not link.is_symlink():
            return f"Missing symlink: {link_path}"
        
        if not link.is_symlink():
            return f"Not a symlink: {link_path}"
        
        try:
            target = link.readlink()
            if not target.exists():
                return f"Broken symlink: {link_path} → {target}"
        except Exception as e:
            return f"Cannot read symlink: {link_path} ({e})"
        
        return None
    
    def repair_symlinks(self) -> OperationResult:
        """Repair broken symlinks"""
        try:
            self.logger.info("Repairing broken symlinks...")
            
            verification_result = self.verify_symlinks()
            if verification_result.success:
                return OperationResult(success=True, message="No repairs needed")
            
            issues = verification_result.details.get("issues", [])
            repaired = []
            failed = []
            
            for issue in issues:
                if "broken symlink" in issue.lower() or "missing symlink" in issue.lower():
                    # Extract link path from issue description
                    link_path = issue.split(":")[1].split("→")[0].strip()
                    
                    # Attempt repair
                    repair_result = self._repair_single_symlink(link_path)
                    if repair_result.success:
                        repaired.append(link_path)
                    else:
                        failed.append({"path": link_path, "error": repair_result.message})
            
            message = f"Repaired {len(repaired)} symlinks"
            if failed:
                message += f", {len(failed)} failed"
            
            return OperationResult(
                success=len(failed) == 0,
                message=message,
                details={"repaired": repaired, "failed": failed}
            )
            
        except Exception as e:
            self.logger.error(f"Symlink repair failed: {e}")
            return OperationResult(success=False, message=str(e))
    
    def _repair_single_symlink(self, link_path: str) -> OperationResult:
        """Repair a single broken symlink"""
        try:
            # Determine what the target should be based on the link path
            target_path = self._determine_symlink_target(link_path)
            if not target_path:
                return OperationResult(success=False, message=f"Cannot determine target for {link_path}")
            
            # Remove broken symlink
            link = Path(link_path)
            if link.exists() or link.is_symlink():
                link.unlink()
            
            # Recreate symlink
            result = self._create_symlink(link_path, target_path, [])
            return result
            
        except Exception as e:
            return OperationResult(success=False, message=str(e))
    
    def _determine_symlink_target(self, link_path: str) -> Optional[str]:
        """Determine what the target should be for a given symlink path"""
        link_path = str(Path(link_path).resolve())
        
        # Primary symlinks
        if link_path.endswith("/models"):
            return self.settings.paths.models_active
        elif link_path.endswith("/downloads"):
            return self.settings.paths.models_downloads
        elif link_path.endswith("/staging"):
            return self.settings.paths.models_staging
        elif "/.cache/huggingface" in link_path:
            return self.settings.paths.hf_cache
        elif "/.cache/torch" in link_path:
            return self.settings.paths.torch_cache
        
        # Convenience symlinks
        link_name = Path(link_path).name
        if link_name in self.settings.models.convenience_links:
            model_key = self.settings.models.convenience_links[link_name]
            if model_key in self.settings.models.model_directories:
                full_name = self.settings.models.model_directories[model_key]
                return f"{self.settings.paths.models_active}/{full_name}"
        
        return None


def main():
    """Main entry point for storage management"""
    if len(sys.argv) < 2:
        print("Usage: storage_manager.py <command>")
        print("Commands: verify-prereq, create-dirs, create-symlinks, verify-symlinks, repair-symlinks")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        manager = StorageManager()
        
        if command == "verify-prereq":
            result = manager.verify_storage_prerequisites()
        elif command == "create-dirs":
            result = manager.create_directory_structure()
        elif command == "create-symlinks":
            result = manager.create_symlinks()
        elif command == "verify-symlinks":
            result = manager.verify_symlinks()
        elif command == "repair-symlinks":
            result = manager.repair_symlinks()
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
        
        if result.success:
            print(f"✅ {result.message}")
            if result.details:
                print(f"Details: {json.dumps(result.details, indent=2)}")
        else:
            print(f"❌ {result.message}")
            if result.details:
                print(f"Details: {json.dumps(result.details, indent=2)}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()