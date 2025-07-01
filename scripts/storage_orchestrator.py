#!/usr/bin/env python3
"""
PLANB-06: Storage System Orchestrator
Main orchestration script for complete storage setup and management
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import asdict

# Add configs directory to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from storage_settings import StorageSettings, load_storage_settings, get_storage_environment_variables
    from storage_manager import StorageManager
    from storage_monitor import StorageMonitor
    from backup_manager import BackupManager
except ImportError as e:
    print(f"❌ Could not import required modules: {e}")
    print("Please ensure all dependencies are installed and paths are correct.")
    sys.exit(1)


class StorageOrchestrator:
    """Main orchestrator for storage system operations"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize storage orchestrator"""
        self.settings = load_storage_settings()
        self.logger = self._setup_logging()
        
        # Initialize component managers
        self.storage_manager = StorageManager(self.settings)
        self.storage_monitor = StorageMonitor(self.settings)
        self.backup_manager = BackupManager(self.settings)
        
        self.logger.info("Storage orchestrator initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration"""
        logger = logging.getLogger("StorageOrchestrator")
        logger.setLevel(logging.INFO)
        
        # Create logs directory if it doesn't exist
        log_dir = Path(self.settings.paths.app_logs)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # File handler
        log_file = log_dir / "storage_orchestrator.log"
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
    
    def setup_complete_storage_system(self) -> Dict[str, Any]:
        """Complete storage system setup workflow"""
        self.logger.info("Starting complete storage system setup...")
        
        results = {
            "setup_started": True,
            "steps_completed": [],
            "steps_failed": [],
            "overall_success": False,
            "summary": {}
        }
        
        try:
            # Step 1: Verify prerequisites
            self.logger.info("Step 1: Verifying storage prerequisites...")
            prereq_result = self.storage_manager.verify_storage_prerequisites()
            
            if prereq_result.success:
                results["steps_completed"].append("prerequisites_verified")
                self.logger.info("✅ Prerequisites verified")
            else:
                results["steps_failed"].append({
                    "step": "prerequisites_verification",
                    "error": prereq_result.message,
                    "details": prereq_result.details
                })
                self.logger.error(f"❌ Prerequisites verification failed: {prereq_result.message}")
                return results
            
            # Step 2: Create directory structure
            self.logger.info("Step 2: Creating directory structure...")
            dirs_result = self.storage_manager.create_directory_structure()
            
            if dirs_result.success:
                results["steps_completed"].append("directories_created")
                results["summary"]["directories_created"] = len(dirs_result.details.get("created_directories", []))
                self.logger.info(f"✅ Created {results['summary']['directories_created']} directories")
            else:
                results["steps_failed"].append({
                    "step": "directory_creation",
                    "error": dirs_result.message
                })
                self.logger.error(f"❌ Directory creation failed: {dirs_result.message}")
                return results
            
            # Step 3: Create symlinks
            self.logger.info("Step 3: Creating symlinks...")
            symlinks_result = self.storage_manager.create_symlinks()
            
            if symlinks_result.success:
                results["steps_completed"].append("symlinks_created")
                results["summary"]["symlinks_created"] = len(symlinks_result.details.get("created_symlinks", []))
                self.logger.info(f"✅ Created {results['summary']['symlinks_created']} symlinks")
            else:
                results["steps_failed"].append({
                    "step": "symlink_creation",
                    "error": symlinks_result.message
                })
                self.logger.error(f"❌ Symlink creation failed: {symlinks_result.message}")
                return results
            
            # Step 4: Verify symlinks
            self.logger.info("Step 4: Verifying symlinks...")
            verify_result = self.storage_manager.verify_symlinks()
            
            if verify_result.success:
                results["steps_completed"].append("symlinks_verified")
                results["summary"]["symlinks_verified"] = verify_result.details.get("verified_count", 0)
                self.logger.info(f"✅ Verified {results['summary']['symlinks_verified']} symlinks")
            else:
                # Attempt repair
                self.logger.info("Attempting symlink repair...")
                repair_result = self.storage_manager.repair_symlinks()
                
                if repair_result.success:
                    results["steps_completed"].append("symlinks_repaired")
                    results["summary"]["symlinks_repaired"] = len(repair_result.details.get("repaired", []))
                    self.logger.info(f"✅ Repaired {results['summary']['symlinks_repaired']} symlinks")
                else:
                    results["steps_failed"].append({
                        "step": "symlink_verification",
                        "error": verify_result.message,
                        "repair_attempted": True,
                        "repair_result": repair_result.message
                    })
                    self.logger.error(f"❌ Symlink verification and repair failed")
            
            # Step 5: Generate environment configuration
            self.logger.info("Step 5: Generating environment configuration...")
            env_vars = get_storage_environment_variables(self.settings)
            
            # Save environment configuration
            env_file_path = Path(self.settings.paths.app_configs) / "storage-env.sh"
            self._generate_environment_script(env_vars, env_file_path)
            
            results["steps_completed"].append("environment_configured")
            results["summary"]["environment_variables"] = len(env_vars)
            self.logger.info(f"✅ Generated {len(env_vars)} environment variables")
            
            # Step 6: Initial health check
            self.logger.info("Step 6: Performing initial health check...")
            health_report = self.storage_monitor.generate_health_report()
            
            results["steps_completed"].append("health_check_completed")
            results["summary"]["health_status"] = health_report["summary"]["overall_healthy"]
            
            if health_report["summary"]["overall_healthy"]:
                self.logger.info("✅ Initial health check passed")
            else:
                self.logger.warning(f"⚠️ Health check identified {len(health_report['summary']['errors'])} issues")
                results["summary"]["health_issues"] = health_report["summary"]["errors"]
            
            # Success!
            results["overall_success"] = True
            results["summary"]["total_steps"] = len(results["steps_completed"])
            results["summary"]["failed_steps"] = len(results["steps_failed"])
            
            self.logger.info("🎉 Complete storage system setup successful!")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Storage setup failed with exception: {e}")
            results["steps_failed"].append({
                "step": "orchestrator_exception",
                "error": str(e)
            })
            return results
    
    def _generate_environment_script(self, env_vars: Dict[str, str], output_path: Path) -> None:
        """Generate shell script with environment variables"""
        script_content = [
            "#!/bin/bash",
            "# Storage environment configuration",
            "# Generated by Storage Orchestrator",
            "",
            "# Storage Paths"
        ]
        
        # Group environment variables by category
        storage_vars = {k: v for k, v in env_vars.items() if k.startswith("CITADEL_")}
        cache_vars = {k: v for k, v in env_vars.items() if k.startswith(("HF_", "TRANSFORMERS_", "TORCH_", "VLLM_"))}
        model_vars = {k: v for k, v in env_vars.items() if "MODEL_" in k}
        
        # Add storage variables
        for key, value in storage_vars.items():
            script_content.append(f'export {key}="{value}"')
        
        script_content.extend(["", "# Cache Configuration"])
        for key, value in cache_vars.items():
            script_content.append(f'export {key}="{value}"')
        
        script_content.extend(["", "# Model-Specific Paths"])
        for key, value in model_vars.items():
            script_content.append(f'export {key}="{value}"')
        
        script_content.extend([
            "",
            'echo "Storage environment variables loaded"'
        ])
        
        # Write script
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write('\n'.join(script_content))
        
        # Make executable
        output_path.chmod(0o755)
        
        self.logger.info(f"Environment script generated: {output_path}")
    
    def status_check(self) -> Dict[str, Any]:
        """Comprehensive status check of storage system"""
        self.logger.info("Performing comprehensive status check...")
        
        status = {
            "timestamp": str(Path.ctime(Path())),
            "storage_health": {},
            "symlink_status": {},
            "backup_status": {},
            "monitoring_status": {},
            "overall_status": "unknown"
        }
        
        try:
            # Storage health
            health_report = self.storage_monitor.generate_health_report()
            status["storage_health"] = health_report["summary"]
            
            # Symlink verification
            symlink_verify = self.storage_manager.verify_symlinks()
            status["symlink_status"] = {
                "healthy": symlink_verify.success,
                "details": symlink_verify.details
            }
            
            # Backup status
            backup_status = self.backup_manager.get_backup_status()
            status["backup_status"] = backup_status
            
            # Monitoring status
            status["monitoring_status"] = {
                "enabled": self.settings.monitoring.enable_monitoring,
                "running": self.storage_monitor.monitoring
            }
            
            # Overall status
            all_healthy = (
                health_report["summary"]["overall_healthy"] and
                symlink_verify.success
            )
            
            status["overall_status"] = "healthy" if all_healthy else "issues_detected"
            
            return status
            
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            status["error"] = str(e)
            status["overall_status"] = "error"
            return status
    
    def start_monitoring(self) -> Dict[str, Any]:
        """Start storage monitoring"""
        try:
            self.storage_monitor.start_monitoring()
            return {
                "success": True,
                "message": "Storage monitoring started",
                "monitoring_enabled": True
            }
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return {
                "success": False,
                "message": str(e),
                "monitoring_enabled": False
            }
    
    def stop_monitoring(self) -> Dict[str, Any]:
        """Stop storage monitoring"""
        try:
            self.storage_monitor.stop_monitoring()
            return {
                "success": True,
                "message": "Storage monitoring stopped",
                "monitoring_enabled": False
            }
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring: {e}")
            return {
                "success": False,
                "message": str(e),
                "monitoring_enabled": self.storage_monitor.monitoring
            }
    
    def create_backup(self, source_path: str, backup_type: str = "incremental") -> Dict[str, Any]:
        """Create backup using backup manager"""
        try:
            job = self.backup_manager.create_backup(source_path, backup_type)
            return {
                "success": True,
                "message": f"Backup job created: {job.job_id}",
                "job_id": job.job_id,
                "job_details": asdict(job)
            }
        except Exception as e:
            self.logger.error(f"Failed to create backup: {e}")
            return {
                "success": False,
                "message": str(e)
            }


def main():
    """Main entry point for storage orchestrator"""
    parser = argparse.ArgumentParser(description="Storage System Orchestrator")
    parser.add_argument("command", choices=[
        "setup", "status", "start-monitor", "stop-monitor", 
        "backup", "repair", "health-check"
    ], help="Command to execute")
    parser.add_argument("--source", help="Source path for backup operations")
    parser.add_argument("--type", default="incremental", choices=["full", "incremental"], 
                       help="Backup type")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    
    args = parser.parse_args()
    
    try:
        orchestrator = StorageOrchestrator()
        
        if args.command == "setup":
            result = orchestrator.setup_complete_storage_system()
        elif args.command == "status":
            result = orchestrator.status_check()
        elif args.command == "start-monitor":
            result = orchestrator.start_monitoring()
        elif args.command == "stop-monitor":
            result = orchestrator.stop_monitoring()
        elif args.command == "backup":
            if not args.source:
                print("❌ --source is required for backup operations")
                sys.exit(1)
            result = orchestrator.create_backup(args.source, args.type)
        elif args.command == "repair":
            result = orchestrator.storage_manager.repair_symlinks()
            result = asdict(result)
        elif args.command == "health-check":
            result = orchestrator.storage_monitor.generate_health_report()
        else:
            print(f"Unknown command: {args.command}")
            sys.exit(1)
        
        # Output result
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if isinstance(result, dict) and result.get("overall_success") is True:
                print("✅ Operation completed successfully")
                if "summary" in result:
                    for key, value in result["summary"].items():
                        print(f"  {key}: {value}")
            elif isinstance(result, dict) and result.get("success") is True:
                print(f"✅ {result.get('message', 'Operation completed')}")
            else:
                print("❌ Operation encountered issues")
                if isinstance(result, dict):
                    if "steps_failed" in result and result["steps_failed"]:
                        print("Failed steps:")
                        for step in result["steps_failed"]:
                            print(f"  - {step}")
                    if "message" in result:
                        print(f"Message: {result['message']}")
        
    except Exception as e:
        if args.json:
            print(json.dumps({"error": str(e), "success": False}, indent=2))
        else:
            print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()