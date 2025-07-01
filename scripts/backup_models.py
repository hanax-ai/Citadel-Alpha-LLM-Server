#!/usr/bin/env python3
"""
Enhanced Model Backup Manager
Extends existing backup_manager.py with comprehensive backup strategy
"""

import os
import sys
import time
import json
import hashlib
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from contextlib import contextmanager

# Add configs directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from storage_settings import StorageSettings, load_storage_settings
    from backup_manager import BackupManager, BackupJob, VerificationResult
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    print("Please ensure configs/storage_settings.py and scripts/backup_manager.py exist.")
    sys.exit(1)


@dataclass
class EnhancedBackupResult:
    """Enhanced backup operation result"""
    success: bool
    message: str
    backup_type: str
    model_name: Optional[str]
    backup_path: Optional[str]
    duration_seconds: float
    files_processed: int
    bytes_processed: int
    compression_ratio: Optional[float]
    errors: List[str]
    rollback_info: Optional[Dict[str, Any]] = None


class DependencyValidator:
    """Validates backup dependencies before operations"""
    
    @staticmethod
    def validate_dependencies() -> Tuple[bool, List[str]]:
        """Validate required dependencies for backup operations"""
        errors = []
        
        # Check required commands
        required_commands = ["rsync", "zstd", "tar", "sha256sum"]
        for cmd in required_commands:
            if not subprocess.run(["which", cmd], capture_output=True).returncode == 0:
                errors.append(f"Required command not found: {cmd}")
        
        # Check Python packages
        required_packages = ["psutil"]
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                errors.append(f"Required Python package not found: {package}")
        
        return len(errors) == 0, errors


class EnhancedBackupManager(BackupManager):
    """Enhanced backup manager with comprehensive strategy and error handling"""
    
    def __init__(self, settings: Optional[StorageSettings] = None):
        """Initialize enhanced backup manager"""
        super().__init__(settings)
        self.validator = DependencyValidator()
        
        # Validate dependencies on initialization
        deps_valid, deps_errors = self.validator.validate_dependencies()
        if not deps_valid:
            self.logger.error(f"Dependency validation failed: {deps_errors}")
            raise RuntimeError(f"Backup dependencies not met: {deps_errors}")
    
    @contextmanager
    def backup_transaction(self, operation_name: str):
        """Context manager for backup operations with comprehensive rollback"""
        rollback_actions = []
        start_time = time.time()
        
        try:
            self.logger.info(f"Starting backup operation: {operation_name}")
            yield rollback_actions
            duration = time.time() - start_time
            self.logger.info(f"Completed backup operation: {operation_name} in {duration:.2f}s")
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Backup operation failed: {operation_name} after {duration:.2f}s - {e}")
            
            # Execute rollback actions in reverse order
            for action in reversed(rollback_actions):
                try:
                    action()
                    self.logger.info("Rollback action completed")
                except Exception as rollback_error:
                    self.logger.error(f"Rollback failed: {rollback_error}")
            raise
    
    def create_model_backup(
        self, 
        model_name: str, 
        backup_type: str = "daily",
        test_mode: bool = False
    ) -> EnhancedBackupResult:
        """Create backup for specific model with enhanced error handling"""
        
        start_time = time.time()
        
        try:
            with self.backup_transaction(f"backup_{model_name}_{backup_type}") as rollback_actions:
                
                # Determine model path
                model_path = self._get_model_path(model_name)
                if not model_path:
                    raise ValueError(f"Model path not found for: {model_name}")
                
                if not Path(model_path).exists():
                    raise FileNotFoundError(f"Model directory does not exist: {model_path}")
                
                # Create backup with retry logic
                backup_job = self._create_backup_with_retry(
                    model_name, model_path, backup_type, rollback_actions, test_mode
                )
                
                # Calculate compression ratio if compressed
                compression_ratio = None
                if self.settings.backup.compress_backups and backup_job.destination_path:
                    compression_ratio = self._calculate_compression_ratio(
                        model_path, backup_job.destination_path
                    )
                
                duration = time.time() - start_time
                
                return EnhancedBackupResult(
                    success=True,
                    message=f"Backup completed for {model_name}",
                    backup_type=backup_type,
                    model_name=model_name,
                    backup_path=backup_job.destination_path,
                    duration_seconds=duration,
                    files_processed=backup_job.files_processed,
                    bytes_processed=backup_job.bytes_processed,
                    compression_ratio=compression_ratio,
                    errors=backup_job.errors
                )
                
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Model backup failed for {model_name}: {e}")
            
            return EnhancedBackupResult(
                success=False,
                message=f"Backup failed for {model_name}: {e}",
                backup_type=backup_type,
                model_name=model_name,
                backup_path=None,
                duration_seconds=duration,
                files_processed=0,
                bytes_processed=0,
                compression_ratio=None,
                errors=[str(e)]
            )
    
    def _get_model_path(self, model_name: str) -> Optional[str]:
        """Get model path from configuration"""
        # Map model names to actual paths
        model_mapping = {
            "phi3": "phi-3-mini-128k",
            "mixtral": "mixtral-8x7b-instruct", 
            "yi34b": "yi-34b-chat",
            "hermes": "nous-hermes-2-mixtral",
            "openchat": "openchat-3.5",
            "coder": "deepcoder-14b-instruct",
            "vision": "mimo-vl-7b-rl"
        }
        
        config_key = model_mapping.get(model_name, model_name)
        if config_key in self.settings.models.model_directories:
            full_name = self.settings.models.model_directories[config_key]
            return f"{self.settings.paths.models_active}/{full_name}"
        
        return None
    
    def _create_backup_with_retry(
        self, 
        model_name: str, 
        model_path: str, 
        backup_type: str,
        rollback_actions: List,
        test_mode: bool = False
    ) -> BackupJob:
        """Create backup with retry logic"""
        
        max_attempts = self.settings.backup.max_retry_attempts
        retry_delay = self.settings.backup.retry_delay_seconds
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Backup attempt {attempt}/{max_attempts} for {model_name}")
                
                # Create backup job
                if test_mode:
                    # For test mode, create smaller backup for validation
                    source_path = self._create_test_subset(model_path, rollback_actions)
                else:
                    source_path = model_path
                
                backup_job = self.create_backup(source_path, backup_type)
                
                # Wait for completion and verify
                self._wait_for_backup_completion(backup_job, timeout=1800)  # 30 min timeout
                
                if backup_job.status == "completed":
                    self.logger.info(f"Backup successful for {model_name} on attempt {attempt}")
                    return backup_job
                else:
                    raise Exception(f"Backup job failed with status: {backup_job.status}")
                    
            except Exception as e:
                self.logger.warning(f"Backup attempt {attempt} failed for {model_name}: {e}")
                
                if attempt < max_attempts:
                    self.logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise Exception(f"All {max_attempts} backup attempts failed: {e}")
        
        raise Exception("Backup retry logic exhausted")
    
    def _create_test_subset(self, model_path: str, rollback_actions: List) -> str:
        """Create a small subset of model for testing purposes"""
        test_dir = f"{self.settings.paths.models_staging}/test_backup_{int(time.time())}"
        Path(test_dir).mkdir(parents=True, exist_ok=True)
        
        # Add cleanup to rollback actions
        rollback_actions.append(lambda: self._cleanup_directory(test_dir))
        
        # Copy a small subset of files for testing
        source = Path(model_path)
        target = Path(test_dir)
        
        # Copy essential files for testing (config.json, tokenizer files, small sample)
        essential_files = ["config.json", "tokenizer.json", "tokenizer_config.json"]
        copied_files = 0
        
        for file_name in essential_files:
            src_file = source / file_name
            if src_file.exists() and copied_files < 5:  # Limit test size
                subprocess.run(["cp", str(src_file), str(target)], check=True)
                copied_files += 1
        
        self.logger.info(f"Created test subset with {copied_files} files: {test_dir}")
        return test_dir
    
    def _cleanup_directory(self, directory: str) -> None:
        """Safely cleanup directory"""
        try:
            if Path(directory).exists():
                subprocess.run(["rm", "-rf", directory], check=True)
                self.logger.info(f"Cleaned up directory: {directory}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup directory {directory}: {e}")
    
    def _wait_for_backup_completion(self, backup_job: BackupJob, timeout: int = 1800) -> None:
        """Wait for backup job completion with timeout"""
        start_time = time.time()
        
        while backup_job.status in ["pending", "running"]:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Backup job timed out after {timeout} seconds")
            
            time.sleep(10)  # Check every 10 seconds
            
            # Job status is updated by the background thread in parent class
            # This is a simplified check - in practice you'd query job status
        
        if backup_job.status == "failed":
            raise Exception(f"Backup job failed: {backup_job.errors}")
    
    def _calculate_compression_ratio(self, source_path: str, backup_path: str) -> Optional[float]:
        """Calculate compression ratio"""
        try:
            if not Path(backup_path).exists():
                return None
                
            # Get source size
            source_size = subprocess.run(
                ["du", "-sb", source_path], 
                capture_output=True, text=True, check=True
            ).stdout.split()[0]
            
            # Get compressed size
            compressed_size = Path(backup_path).stat().st_size
            
            if int(source_size) > 0:
                return compressed_size / int(source_size)
            
        except Exception as e:
            self.logger.warning(f"Could not calculate compression ratio: {e}")
        
        return None


def main():
    """Enhanced main entry point with gradual rollout support"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Model Backup Manager")
    parser.add_argument("--type", default="daily", choices=["daily", "weekly", "monthly"],
                       help="Backup type")
    parser.add_argument("--model", help="Specific model to backup")
    parser.add_argument("--test-mode", action="store_true", 
                       help="Run in test mode with small subset")
    parser.add_argument("--gradual-rollout", action="store_true",
                       help="Perform gradual rollout starting with phi3")
    
    args = parser.parse_args()
    
    try:
        # Initialize enhanced backup manager
        manager = EnhancedBackupManager()
        
        if args.gradual_rollout:
            # Gradual rollout: start with phi3, then expand
            models = ["phi3", "openchat", "mixtral", "hermes", "yi34b", "coder", "vision"]
            
            print("=== Gradual Backup Rollout ===")
            
            for i, model in enumerate(models):
                print(f"\nStep {i+1}/{len(models)}: Backing up {model}")
                
                result = manager.create_model_backup(
                    model, args.type, test_mode=(i == 0 and args.test_mode)
                )
                
                if result.success:
                    print(f"✅ {model}: {result.message}")
                    print(f"   Duration: {result.duration_seconds:.2f}s")
                    print(f"   Files: {result.files_processed}, Bytes: {result.bytes_processed}")
                    if result.compression_ratio:
                        print(f"   Compression: {result.compression_ratio:.2%}")
                else:
                    print(f"❌ {model}: {result.message}")
                    if i == 0:  # If first model fails, stop rollout
                        print("❌ Stopping rollout due to initial failure")
                        sys.exit(1)
                    print("⚠️ Continuing with remaining models")
                
                # Brief pause between models to avoid overwhelming system
                if i < len(models) - 1:
                    time.sleep(5)
            
            print("\n✅ Gradual backup rollout completed")
            
        elif args.model:
            # Single model backup
            result = manager.create_model_backup(args.model, args.type, args.test_mode)
            
            if result.success:
                print(f"✅ {result.message}")
                print(json.dumps(asdict(result), indent=2, default=str))
            else:
                print(f"❌ {result.message}")
                sys.exit(1)
        else:
            print("Error: Either --model or --gradual-rollout must be specified")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Backup operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()