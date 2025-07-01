#!/usr/bin/env python3
"""
PLANB-06: Backup Management and Verification
Automated backup verification and integrity checking
"""

import os
import sys
import hashlib
import json
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import threading
import time
import random

# Add configs directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from storage_settings import StorageSettings, load_storage_settings
except ImportError:
    print("❌ Could not import storage_settings. Please ensure configs/storage_settings.py exists.")
    sys.exit(1)


@dataclass
class BackupJob:
    """Backup job information"""
    job_id: str
    source_path: str
    destination_path: str
    backup_type: str  # full, incremental
    status: str  # pending, running, completed, failed
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    files_processed: int
    bytes_processed: int
    errors: List[str]
    checksum: Optional[str]


@dataclass
class VerificationResult:
    """Backup verification result"""
    backup_path: str
    is_valid: bool
    files_checked: int
    files_failed: int
    checksum_matches: bool
    errors: List[str]
    verification_time: datetime
    duration_seconds: float


class BackupManager:
    """Backup management and verification system"""
    
    def __init__(self, settings: Optional[StorageSettings] = None):
        """Initialize backup manager"""
        self.settings = settings or load_storage_settings()
        self.logger = self._setup_logging()
        self.backup_jobs: Dict[str, BackupJob] = {}
        self.metadata_file = Path(self.settings.paths.backup_root) / "backup_metadata.json"
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("BackupManager")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.settings.paths.app_logs)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        log_file = log_dir / "backup_manager.log"
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
    
    def create_backup(self, source_path: str, backup_type: str = "incremental") -> BackupJob:
        """Create a backup of the specified source path"""
        job_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
        
        # Determine destination path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{Path(source_path).name}_{backup_type}_{timestamp}"
        destination_path = str(Path(self.settings.paths.backup_models) / backup_name)
        
        job = BackupJob(
            job_id=job_id,
            source_path=source_path,
            destination_path=destination_path,
            backup_type=backup_type,
            status="pending",
            start_time=None,
            end_time=None,
            files_processed=0,
            bytes_processed=0,
            errors=[],
            checksum=None
        )
        
        self.backup_jobs[job_id] = job
        
        # Start backup in background thread
        backup_thread = threading.Thread(target=self._execute_backup, args=(job,), daemon=True)
        backup_thread.start()
        
        return job
    
    def _execute_backup(self, job: BackupJob) -> None:
        """Execute backup job"""
        try:
            self.logger.info(f"Starting backup job {job.job_id}: {job.source_path}")
            job.status = "running"
            job.start_time = datetime.now()
            
            source = Path(job.source_path)
            destination = Path(job.destination_path)
            
            if not source.exists():
                raise FileNotFoundError(f"Source path does not exist: {job.source_path}")
            
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Perform backup based on type
            if job.backup_type == "full":
                self._perform_full_backup(job, source, destination)
            else:
                self._perform_incremental_backup(job, source, destination)
            
            # Calculate checksum
            job.checksum = self._calculate_directory_checksum(str(destination))
            
            job.status = "completed"
            job.end_time = datetime.now()
            
            # Save metadata
            self._save_backup_metadata(job)
            
            self.logger.info(f"Backup job {job.job_id} completed successfully")
            
        except Exception as e:
            job.status = "failed"
            job.end_time = datetime.now()
            job.errors.append(str(e))
            self.logger.error(f"Backup job {job.job_id} failed: {e}")
    
    def _perform_full_backup(self, job: BackupJob, source: Path, destination: Path) -> None:
        """Perform full backup using rsync"""
        try:
            cmd = [
                "rsync", "-av", "--progress", "--stats",
                str(source) + "/",
                str(destination) + "/"
            ]
            
            if self.settings.backup.compress_backups:
                cmd.append("--compress")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse rsync stats
            self._parse_rsync_stats(job, result.stderr)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Rsync failed: {e.stderr}")
    
    def _perform_incremental_backup(self, job: BackupJob, source: Path, destination: Path) -> None:
        """Perform incremental backup"""
        # For incremental backup, we need to compare with the last backup
        last_backup = self._find_last_backup(job.source_path)
        
        if not last_backup:
            # No previous backup, perform full backup
            self._perform_full_backup(job, source, destination)
            return
        
        try:
            cmd = [
                "rsync", "-av", "--progress", "--stats",
                f"--link-dest={last_backup}",
                str(source) + "/",
                str(destination) + "/"
            ]
            
            if self.settings.backup.compress_backups:
                cmd.append("--compress")
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Parse rsync stats
            self._parse_rsync_stats(job, result.stderr)
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Incremental backup failed: {e.stderr}")
    
    def _parse_rsync_stats(self, job: BackupJob, rsync_output: str) -> None:
        """Parse rsync statistics"""
        lines = rsync_output.split('\n')
        for line in lines:
            if "Number of files:" in line:
                # Extract file count
                parts = line.split()
                if len(parts) >= 4:
                    job.files_processed = int(parts[3].replace(',', ''))
            elif "Total file size:" in line:
                # Extract bytes processed
                parts = line.split()
                if len(parts) >= 4:
                    job.bytes_processed = int(parts[3].replace(',', ''))
    
    def _find_last_backup(self, source_path: str) -> Optional[str]:
        """Find the most recent backup of the source path"""
        backup_dir = Path(self.settings.paths.backup_models)
        if not backup_dir.exists():
            return None
        
        source_name = Path(source_path).name
        matching_backups = []
        
        for item in backup_dir.iterdir():
            if item.is_dir() and item.name.startswith(source_name):
                matching_backups.append(item)
        
        if not matching_backups:
            return None
        
        # Sort by modification time and return the most recent
        matching_backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        return str(matching_backups[0])
    
    def _calculate_directory_checksum(self, directory_path: str) -> str:
        """Calculate MD5 checksum of directory contents"""
        hash_md5 = hashlib.md5()
        
        for root, dirs, files in os.walk(directory_path):
            # Sort to ensure consistent ordering
            dirs.sort()
            files.sort()
            
            for filename in files:
                filepath = os.path.join(root, filename)
                try:
                    with open(filepath, 'rb') as f:
                        # Read file in chunks to handle large files
                        for chunk in iter(lambda: f.read(4096), b""):
                            hash_md5.update(chunk)
                    
                    # Also include file path in hash for uniqueness
                    rel_path = os.path.relpath(filepath, directory_path)
                    hash_md5.update(rel_path.encode('utf-8'))
                    
                except (IOError, OSError) as e:
                    self.logger.warning(f"Could not read file for checksum: {filepath} - {e}")
        
        return hash_md5.hexdigest()
    
    def verify_backup(self, backup_path: str, sample_rate: Optional[float] = None) -> VerificationResult:
        """Verify backup integrity"""
        start_time = time.time()
        
        if sample_rate is None:
            sample_rate = self.settings.backup.verification_sample_rate
        
        self.logger.info(f"Verifying backup: {backup_path} (sample rate: {sample_rate})")
        
        backup_dir = Path(backup_path)
        if not backup_dir.exists():
            return VerificationResult(
                backup_path=backup_path,
                is_valid=False,
                files_checked=0,
                files_failed=0,
                checksum_matches=False,
                errors=[f"Backup directory does not exist: {backup_path}"],
                verification_time=datetime.now(),
                duration_seconds=time.time() - start_time
            )
        
        errors = []
        files_checked = 0
        files_failed = 0
        
        try:
            # Get all files in backup
            all_files = []
            for root, dirs, files in os.walk(backup_path):
                for filename in files:
                    filepath = os.path.join(root, filename)
                    all_files.append(filepath)
            
            # Sample files for verification
            if sample_rate < 1.0:
                sample_size = max(1, int(len(all_files) * sample_rate))
                files_to_check = random.sample(all_files, min(sample_size, len(all_files)))
            else:
                files_to_check = all_files
            
            # Verify each selected file
            for filepath in files_to_check:
                files_checked += 1
                try:
                    # Basic file integrity checks
                    if not os.path.exists(filepath):
                        files_failed += 1
                        errors.append(f"Missing file: {filepath}")
                        continue
                    
                    if not os.access(filepath, os.R_OK):
                        files_failed += 1
                        errors.append(f"Cannot read file: {filepath}")
                        continue
                    
                    # Try to read file to ensure it's not corrupted
                    try:
                        with open(filepath, 'rb') as f:
                            # Read in chunks to avoid memory issues
                            while f.read(8192):
                                pass
                    except (IOError, OSError) as e:
                        files_failed += 1
                        errors.append(f"Corrupted file: {filepath} - {e}")
                        continue
                    
                except Exception as e:
                    files_failed += 1
                    errors.append(f"Error checking file {filepath}: {e}")
            
            # Check backup metadata if it exists
            checksum_matches = self._verify_backup_checksum(backup_path)
            
            is_valid = files_failed == 0 and checksum_matches
            
            return VerificationResult(
                backup_path=backup_path,
                is_valid=is_valid,
                files_checked=files_checked,
                files_failed=files_failed,
                checksum_matches=checksum_matches,
                errors=errors,
                verification_time=datetime.now(),
                duration_seconds=time.time() - start_time
            )
            
        except Exception as e:
            return VerificationResult(
                backup_path=backup_path,
                is_valid=False,
                files_checked=files_checked,
                files_failed=files_failed,
                checksum_matches=False,
                errors=[f"Verification failed: {e}"],
                verification_time=datetime.now(),
                duration_seconds=time.time() - start_time
            )
    
    def _verify_backup_checksum(self, backup_path: str) -> bool:
        """Verify backup checksum against metadata"""
        try:
            # Find metadata for this backup
            metadata = self._load_backup_metadata()
            
            backup_name = Path(backup_path).name
            matching_jobs = [job for job in metadata.get("jobs", []) 
                           if Path(job.get("destination_path", "")).name == backup_name]
            
            if not matching_jobs:
                self.logger.warning(f"No metadata found for backup: {backup_name}")
                return True  # Can't verify, assume OK
            
            job_data = matching_jobs[0]
            expected_checksum = job_data.get("checksum")
            
            if not expected_checksum:
                self.logger.warning(f"No checksum in metadata for backup: {backup_name}")
                return True  # Can't verify, assume OK
            
            # Calculate current checksum
            current_checksum = self._calculate_directory_checksum(backup_path)
            
            return current_checksum == expected_checksum
            
        except Exception as e:
            self.logger.error(f"Checksum verification failed: {e}")
            return False
    
    def _save_backup_metadata(self, job: BackupJob) -> None:
        """Save backup job metadata"""
        try:
            metadata = self._load_backup_metadata()
            
            # Add current job
            job_dict = asdict(job)
            # Convert datetime objects to strings
            if job_dict["start_time"]:
                job_dict["start_time"] = job.start_time.isoformat()
            if job_dict["end_time"]:
                job_dict["end_time"] = job.end_time.isoformat()
            
            metadata.setdefault("jobs", []).append(job_dict)
            
            # Save to file
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save backup metadata: {e}")
    
    def _load_backup_metadata(self) -> Dict[str, Any]:
        """Load backup metadata"""
        if not self.metadata_file.exists():
            return {"jobs": [], "created": datetime.now().isoformat()}
        
        try:
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load backup metadata: {e}")
            return {"jobs": [], "created": datetime.now().isoformat()}
    
    def cleanup_old_backups(self, retention_days: Optional[int] = None) -> List[str]:
        """Clean up old backups based on retention policy"""
        if retention_days is None:
            retention_days = self.settings.backup.retention_days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        removed_backups = []
        
        try:
            backup_dir = Path(self.settings.paths.backup_models)
            if not backup_dir.exists():
                return removed_backups
            
            for item in backup_dir.iterdir():
                if item.is_dir():
                    # Check modification time
                    mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                    if mod_time < cutoff_date:
                        try:
                            shutil.rmtree(item)
                            removed_backups.append(str(item))
                            self.logger.info(f"Removed old backup: {item}")
                        except Exception as e:
                            self.logger.error(f"Failed to remove backup {item}: {e}")
            
            return removed_backups
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {e}")
            return removed_backups
    
    def get_backup_status(self) -> Dict[str, Any]:
        """Get status of all backup jobs"""
        return {
            "active_jobs": len([j for j in self.backup_jobs.values() if j.status == "running"]),
            "completed_jobs": len([j for j in self.backup_jobs.values() if j.status == "completed"]),
            "failed_jobs": len([j for j in self.backup_jobs.values() if j.status == "failed"]),
            "jobs": {job_id: asdict(job) for job_id, job in self.backup_jobs.items()}
        }


def main():
    """Main entry point for backup management"""
    if len(sys.argv) < 2:
        print("Usage: backup_manager.py <command>")
        print("Commands: create, verify, cleanup, status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        manager = BackupManager()
        
        if command == "create":
            if len(sys.argv) < 3:
                print("Usage: backup_manager.py create <source_path> [backup_type]")
                sys.exit(1)
            
            source_path = sys.argv[2]
            backup_type = sys.argv[3] if len(sys.argv) > 3 else "incremental"
            
            job = manager.create_backup(source_path, backup_type)
            print(f"✅ Backup job created: {job.job_id}")
            print(f"Source: {job.source_path}")
            print(f"Destination: {job.destination_path}")
            print(f"Type: {job.backup_type}")
            
        elif command == "verify":
            if len(sys.argv) < 3:
                print("Usage: backup_manager.py verify <backup_path> [sample_rate]")
                sys.exit(1)
            
            backup_path = sys.argv[2]
            sample_rate = float(sys.argv[3]) if len(sys.argv) > 3 else None
            
            result = manager.verify_backup(backup_path, sample_rate)
            print(json.dumps(asdict(result), indent=2, default=str))
            
            if result.is_valid:
                print("✅ Backup verification passed")
            else:
                print("❌ Backup verification failed")
                sys.exit(1)
                
        elif command == "cleanup":
            retention_days = int(sys.argv[2]) if len(sys.argv) > 2 else None
            removed = manager.cleanup_old_backups(retention_days)
            print(f"✅ Cleaned up {len(removed)} old backups")
            for backup in removed:
                print(f"  - {backup}")
                
        elif command == "status":
            status = manager.get_backup_status()
            print(json.dumps(status, indent=2, default=str))
            
        else:
            print(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()