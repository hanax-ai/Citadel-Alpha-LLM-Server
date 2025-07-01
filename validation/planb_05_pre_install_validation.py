#!/usr/bin/env python3
"""
PLANB-05 Pre-Installation Validation Script

This script validates all prerequisites before vLLM installation begins.
Ensures environment readiness and script availability per task rules.

Usage:
    python validation/planb_05_pre_install_validation.py

Author: Citadel AI OS Plan B Implementation Team
Date: July 1, 2025
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Tuple, Optional


class PLANB05PreInstallValidator:
    """Pre-installation validation for PLANB-05 vLLM setup."""
    
    def __init__(self, base_dir: str = "/home/agent0/Citadel-Alpha-LLM-Server-1"):
        self.base_dir = Path(base_dir)
        self.scripts_dir = self.base_dir / "scripts"
        self.validation_results: Dict[str, bool] = {}
        self.required_scripts = {
            "vllm_latest_installation.sh": 500,  # Max lines per task rules
            "vllm_quick_install.sh": 500,
            "test_vllm_installation.py": 500,
            "start_vllm_server.py": 500,
            "test_vllm_client.py": 500
        }
    
    def validate_scripts_exist(self) -> bool:
        """Validate all required scripts exist and are executable."""
        print("🔍 Validating Script Availability...")
        
        missing_scripts = []
        non_executable = []
        oversized_scripts = []
        
        for script_name, max_lines in self.required_scripts.items():
            script_path = self.scripts_dir / script_name
            
            # Check existence
            if not script_path.exists():
                missing_scripts.append(script_name)
                continue
            
            # Check executable permissions
            if not os.access(script_path, os.X_OK):
                non_executable.append(script_name)
            
            # Check file size compliance (task rules: under 500 lines)
            try:
                with open(script_path, 'r') as f:
                    line_count = sum(1 for _ in f)
                    if line_count > max_lines:
                        oversized_scripts.append(f"{script_name} ({line_count} lines)")
            except Exception as e:
                print(f"⚠️  Could not check line count for {script_name}: {e}")
        
        # Report results
        if missing_scripts:
            print(f"❌ Missing scripts: {', '.join(missing_scripts)}")
            return False
        
        if non_executable:
            print(f"⚠️  Non-executable scripts: {', '.join(non_executable)}")
            print("   Run: chmod +x scripts/*.sh scripts/*.py")
            return False
        
        if oversized_scripts:
            print(f"⚠️  Scripts exceeding 500-line limit: {', '.join(oversized_scripts)}")
            return False
        
        print("✅ All required scripts available and compliant")
        return True
    
    def validate_python_environment(self) -> bool:
        """Validate Python 3.12 and virtual environment setup."""
        print("🐍 Validating Python Environment...")
        
        # Check Python version
        if sys.version_info < (3, 12):
            print(f"❌ Python 3.12+ required, found {sys.version}")
            return False
        
        # Check if in virtual environment
        if not hasattr(sys, 'real_prefix') and not (
            hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
        ):
            print("⚠️  Not in virtual environment")
            print("   Activate: source /opt/citadel/dev-env/bin/activate")
            return False
        
        # Check critical packages
        required_packages = ['torch', 'transformers', 'fastapi', 'uvicorn']
        missing_packages = []
        
        for package in required_packages:
            if importlib.util.find_spec(package) is None:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Missing packages: {', '.join(missing_packages)}")
            return False
        
        print("✅ Python environment validated")
        return True
    
    def validate_cuda_environment(self) -> bool:
        """Validate CUDA and GPU availability."""
        print("🔥 Validating CUDA Environment...")
        
        try:
            import torch
            
            if not torch.cuda.is_available():
                print("❌ CUDA not available")
                return False
            
            gpu_count = torch.cuda.device_count()
            if gpu_count == 0:
                print("❌ No CUDA devices found")
                return False
            
            # Check GPU details
            for i in range(gpu_count):
                gpu_props = torch.cuda.get_device_properties(i)
                print(f"   GPU {i}: {gpu_props.name} ({gpu_props.total_memory // 1024**3}GB)")
            
            print(f"✅ CUDA validated with {gpu_count} GPU(s)")
            return True
            
        except ImportError:
            print("❌ PyTorch not available for CUDA validation")
            return False
        except Exception as e:
            print(f"❌ CUDA validation failed: {e}")
            return False
    
    def validate_system_dependencies(self) -> bool:
        """Validate system-level dependencies."""
        print("🔧 Validating System Dependencies...")
        
        # Check nvidia-smi availability
        try:
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ nvidia-smi not available")
                return False
        except FileNotFoundError:
            print("❌ nvidia-smi command not found")
            return False
        
        # Check available disk space (minimum 5GB recommended)
        try:
            statvfs = os.statvfs(self.base_dir)
            free_bytes = statvfs.f_frsize * statvfs.f_bavail
            free_gb = free_bytes / (1024**3)
            
            if free_gb < 5:
                print(f"⚠️  Low disk space: {free_gb:.1f}GB available (5GB recommended)")
                return False
            
            print(f"✅ System dependencies validated ({free_gb:.1f}GB available)")
            return True
            
        except Exception as e:
            print(f"⚠️  Could not check disk space: {e}")
            return True  # Non-critical, allow to continue
    
    def validate_environment_paths(self) -> bool:
        """Validate required directory structure and paths."""
        print("📁 Validating Environment Paths...")
        
        required_paths = [
            self.base_dir / "scripts",
            self.base_dir / "validation", 
            self.base_dir / "tasks",
            self.base_dir / "tasks" / "task-results",
            self.base_dir / "configs"
        ]
        
        missing_paths = []
        for path in required_paths:
            if not path.exists():
                missing_paths.append(str(path))
        
        if missing_paths:
            print(f"❌ Missing paths: {', '.join(missing_paths)}")
            return False
        
        print("✅ Environment paths validated")
        return True
    
    def run_validation(self) -> bool:
        """Run complete pre-installation validation suite."""
        print("🛡️  PLANB-05 Pre-Installation Validation")
        print("=" * 50)
        
        validations = [
            ("Scripts", self.validate_scripts_exist),
            ("Python Environment", self.validate_python_environment), 
            ("CUDA Environment", self.validate_cuda_environment),
            ("System Dependencies", self.validate_system_dependencies),
            ("Environment Paths", self.validate_environment_paths)
        ]
        
        all_passed = True
        for name, validator in validations:
            try:
                result = validator()
                self.validation_results[name] = result
                if not result:
                    all_passed = False
            except Exception as e:
                print(f"❌ {name} validation failed with error: {e}")
                self.validation_results[name] = False
                all_passed = False
            print()
        
        # Summary
        print("📊 Validation Summary:")
        print("=" * 30)
        for name, result in self.validation_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{name}: {status}")
        
        if all_passed:
            print("\n🎯 All validations passed - Ready for PLANB-05 implementation!")
            return True
        else:
            print("\n⚠️  Some validations failed - Address issues before proceeding")
            return False


def main():
    """Main validation entry point."""
    validator = PLANB05PreInstallValidator()
    
    # Check if running from correct directory
    if not os.getcwd().endswith("Citadel-Alpha-LLM-Server-1"):
        print("⚠️  Run from project root: /home/agent0/Citadel-Alpha-LLM-Server-1")
        sys.exit(1)
    
    success = validator.run_validation()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()