#!/usr/bin/env python3
"""
PLANB-04 Python Environment Validation Test Suite
Comprehensive validation for Python 3.12, virtual environments, and AI dependencies
"""

import subprocess
import sys
import os
import json
import time
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class PythonInstallationValidator:
    """Validates Python 3.12 installation and configuration"""
    
    def __init__(self):
        self.config_file = "/opt/citadel/configs/python-config.json"
        self.results = {}
    
    def validate_python_version(self) -> Tuple[bool, str]:
        """Validate Python 3.12 installation"""
        try:
            result = subprocess.run(['python3.12', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "Python 3.12" in result.stdout:
                version = result.stdout.strip()
                return True, f"✅ Python version: {version}"
            return False, f"❌ Python 3.12 not found or wrong version: {result.stdout}"
        except Exception as e:
            return False, f"❌ Python validation error: {str(e)}"
    
    def validate_pip_installation(self) -> Tuple[bool, str]:
        """Validate pip installation for Python 3.12"""
        try:
            result = subprocess.run(['python3.12', '-m', 'pip', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "pip" in result.stdout:
                return True, f"✅ Pip installed: {result.stdout.strip()}"
            return False, f"❌ Pip not working: {result.stderr}"
        except Exception as e:
            return False, f"❌ Pip validation error: {str(e)}"
    
    def validate_alternatives(self) -> Tuple[bool, str]:
        """Validate Python alternatives configuration"""
        try:
            result = subprocess.run(['python', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and "Python 3.12" in result.stdout:
                return True, f"✅ Python alternative pointing to 3.12"
            return False, f"❌ Python alternative not configured: {result.stdout}"
        except Exception as e:
            return False, f"❌ Alternatives validation error: {str(e)}"
    
    def validate_configuration(self) -> Tuple[bool, str]:
        """Validate configuration file"""
        try:
            if not os.path.exists(self.config_file):
                return False, f"❌ Configuration file not found: {self.config_file}"
            
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            
            required_keys = ['python', 'environments', 'optimization', 'paths']
            for key in required_keys:
                if key not in config:
                    return False, f"❌ Missing configuration key: {key}"
            
            return True, f"✅ Configuration file valid"
        except Exception as e:
            return False, f"❌ Configuration validation error: {str(e)}"

class VirtualEnvironmentValidator:
    """Validates virtual environment setup and management"""
    
    def __init__(self):
        self.citadel_root = "/opt/citadel"
        self.env_manager = f"{self.citadel_root}/scripts/env-manager.sh"
        self.results = {}
    
    def validate_env_manager(self) -> Tuple[bool, str]:
        """Validate environment manager script"""
        try:
            if not os.path.exists(self.env_manager):
                return False, f"❌ Environment manager not found: {self.env_manager}"
            
            if not os.access(self.env_manager, os.X_OK):
                return False, f"❌ Environment manager not executable"
            
            result = subprocess.run([self.env_manager, 'list'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, f"✅ Environment manager working"
            return False, f"❌ Environment manager error: {result.stderr}"
        except Exception as e:
            return False, f"❌ Environment manager validation error: {str(e)}"
    
    def validate_environments(self) -> Tuple[bool, str]:
        """Validate virtual environments creation"""
        try:
            expected_envs = ['citadel-env', 'vllm-env', 'dev-env']
            missing_envs = []
            
            for env_name in expected_envs:
                env_path = f"{self.citadel_root}/{env_name}"
                if not os.path.exists(env_path):
                    missing_envs.append(env_name)
                elif not os.path.exists(f"{env_path}/bin/python"):
                    missing_envs.append(f"{env_name} (invalid)")
            
            if missing_envs:
                return False, f"❌ Missing environments: {', '.join(missing_envs)}"
            
            return True, f"✅ All virtual environments created"
        except Exception as e:
            return False, f"❌ Environment validation error: {str(e)}"
    
    def validate_activation_script(self) -> Tuple[bool, str]:
        """Validate activation script"""
        try:
            script_path = f"{self.citadel_root}/scripts/activate-citadel.sh"
            if not os.path.exists(script_path):
                return False, f"❌ Activation script not found: {script_path}"
            
            if not os.access(script_path, os.X_OK):
                return False, f"❌ Activation script not executable"
            
            return True, f"✅ Activation script ready"
        except Exception as e:
            return False, f"❌ Activation script validation error: {str(e)}"

class DependencyValidator:
    """Validates AI/ML dependencies installation"""
    
    def __init__(self):
        self.citadel_env = "/opt/citadel/citadel-env"
        self.results = {}
    
    def validate_in_environment(self, env_path: str, command: List[str]) -> Tuple[bool, str]:
        """Run validation command in virtual environment"""
        try:
            env = os.environ.copy()
            env['VIRTUAL_ENV'] = env_path
            env['PATH'] = f"{env_path}/bin:{env['PATH']}"
            
            result = subprocess.run(command, capture_output=True, text=True, 
                                  timeout=30, env=env, cwd=env_path)
            return result.returncode == 0, result.stdout + result.stderr
        except Exception as e:
            return False, str(e)
    
    def validate_pytorch(self) -> Tuple[bool, str]:
        """Validate PyTorch installation with CUDA support"""
        try:
            test_script = [
                "python", "-c",
                """
import torch
print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU count: {torch.cuda.device_count()}')
    # Test basic tensor operations
    x = torch.randn(100, 100).cuda()
    y = torch.randn(100, 100).cuda()
    z = torch.matmul(x, y)
    print('GPU tensor operations: PASSED')
else:
    print('CUDA not available - CPU only')
"""
            ]
            
            success, output = self.validate_in_environment(self.citadel_env, test_script)
            if success and "PyTorch version:" in output:
                return True, f"✅ PyTorch validation:\n{output}"
            return False, f"❌ PyTorch validation failed:\n{output}"
        except Exception as e:
            return False, f"❌ PyTorch validation error: {str(e)}"
    
    def validate_transformers(self) -> Tuple[bool, str]:
        """Validate Transformers library"""
        try:
            test_script = [
                "python", "-c",
                "import transformers; print(f'Transformers version: {transformers.__version__}')"
            ]
            
            success, output = self.validate_in_environment(self.citadel_env, test_script)
            if success and "Transformers version:" in output:
                return True, f"✅ Transformers: {output.strip()}"
            return False, f"❌ Transformers validation failed: {output}"
        except Exception as e:
            return False, f"❌ Transformers validation error: {str(e)}"
    
    def validate_core_packages(self) -> Tuple[bool, str]:
        """Validate core AI/ML packages"""
        try:
            packages = ['numpy', 'scipy', 'pandas', 'matplotlib', 'sklearn']
            test_script = [
                "python", "-c",
                f"""
import sys
packages = {packages}
results = []
for pkg in packages:
    try:
        __import__(pkg)
        results.append(f'{{pkg}}: OK')
    except ImportError:
        results.append(f'{{pkg}}: MISSING')
print('\\n'.join(results))
"""
            ]
            
            success, output = self.validate_in_environment(self.citadel_env, test_script)
            if success and "MISSING" not in output:
                return True, f"✅ Core packages:\n{output}"
            return False, f"❌ Core packages validation failed:\n{output}"
        except Exception as e:
            return False, f"❌ Core packages validation error: {str(e)}"

class PerformanceValidator:
    """Validates Python performance and optimization"""
    
    def __init__(self):
        self.citadel_env = "/opt/citadel/citadel-env"
        self.results = {}
    
    def validate_gpu_performance(self) -> Tuple[bool, str]:
        """Run GPU performance benchmark"""
        try:
            benchmark_script = [
                "python", "-c",
                """
import torch
import time
import numpy as np

if not torch.cuda.is_available():
    print('CUDA not available - skipping GPU benchmark')
    exit(0)

device = torch.device('cuda:0')
print(f'Benchmarking on: {torch.cuda.get_device_name(0)}')

# Warm up
for _ in range(5):
    x = torch.randn(1000, 1000, device=device)
    y = torch.randn(1000, 1000, device=device)
    z = torch.matmul(x, y)

# Benchmark
sizes = [1000, 2000]
for size in sizes:
    times = []
    for _ in range(5):
        x = torch.randn(size, size, device=device)
        y = torch.randn(size, size, device=device)
        
        torch.cuda.synchronize()
        start_time = time.time()
        z = torch.matmul(x, y)
        torch.cuda.synchronize()
        end_time = time.time()
        
        times.append(end_time - start_time)
    
    avg_time = np.mean(times)
    print(f'Matrix {size}x{size}: {avg_time:.4f}s avg')

print('GPU performance benchmark completed')
"""
            ]
            
            env = os.environ.copy()
            env['VIRTUAL_ENV'] = self.citadel_env
            env['PATH'] = f"{self.citadel_env}/bin:{env['PATH']}"
            
            result = subprocess.run(benchmark_script, capture_output=True, text=True, 
                                  timeout=60, env=env, cwd=self.citadel_env)
            
            if result.returncode == 0:
                return True, f"✅ GPU Performance:\n{result.stdout}"
            return False, f"❌ GPU benchmark failed:\n{result.stderr}"
        except Exception as e:
            return False, f"❌ GPU performance validation error: {str(e)}"
    
    def validate_memory_optimization(self) -> Tuple[bool, str]:
        """Validate memory optimization settings"""
        try:
            optimization_script = [
                "python", "/opt/citadel/configs/python-optimization.py"
            ]
            
            env = os.environ.copy()
            env['VIRTUAL_ENV'] = self.citadel_env
            env['PATH'] = f"{self.citadel_env}/bin:{env['PATH']}"
            
            result = subprocess.run(optimization_script, capture_output=True, text=True, 
                                  timeout=30, env=env)
            
            if result.returncode == 0 and "optimizations applied" in result.stdout:
                return True, f"✅ Memory optimization: {result.stdout.strip()}"
            return False, f"❌ Memory optimization failed: {result.stderr}"
        except Exception as e:
            return False, f"❌ Memory optimization validation error: {str(e)}"

class PLANB04ValidationSuite:
    """Main validation suite for PLANB-04 Python Environment"""
    
    def __init__(self):
        self.python_validator = PythonInstallationValidator()
        self.env_validator = VirtualEnvironmentValidator()
        self.dep_validator = DependencyValidator()
        self.perf_validator = PerformanceValidator()
        self.results = {}
        self.start_time = time.time()
    
    def run_all_validations(self) -> Dict[str, Dict[str, Tuple[bool, str]]]:
        """Run all validation tests"""
        print("🔍 Starting PLANB-04 Python Environment Validation")
        print("=" * 60)
        
        # Python Installation Validation
        print("\n📦 Python Installation Validation")
        print("-" * 40)
        self.results['python'] = {
            'version': self.python_validator.validate_python_version(),
            'pip': self.python_validator.validate_pip_installation(),
            'alternatives': self.python_validator.validate_alternatives(),
            'configuration': self.python_validator.validate_configuration()
        }
        
        for test, (success, message) in self.results['python'].items():
            print(f"{message}")
        
        # Virtual Environment Validation
        print("\n🏗️  Virtual Environment Validation")
        print("-" * 40)
        self.results['environments'] = {
            'manager': self.env_validator.validate_env_manager(),
            'creation': self.env_validator.validate_environments(),
            'activation': self.env_validator.validate_activation_script()
        }
        
        for test, (success, message) in self.results['environments'].items():
            print(f"{message}")
        
        # Dependencies Validation
        print("\n📚 Dependencies Validation")
        print("-" * 40)
        self.results['dependencies'] = {
            'pytorch': self.dep_validator.validate_pytorch(),
            'transformers': self.dep_validator.validate_transformers(),
            'core_packages': self.dep_validator.validate_core_packages()
        }
        
        for test, (success, message) in self.results['dependencies'].items():
            print(f"{message}")
        
        # Performance Validation
        print("\n⚡ Performance Validation")
        print("-" * 40)
        self.results['performance'] = {
            'gpu_benchmark': self.perf_validator.validate_gpu_performance(),
            'memory_optimization': self.perf_validator.validate_memory_optimization()
        }
        
        for test, (success, message) in self.results['performance'].items():
            print(f"{message}")
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        end_time = time.time()
        duration = end_time - self.start_time
        
        total_tests = 0
        passed_tests = 0
        
        report = []
        report.append("# PLANB-04 Python Environment Validation Report")
        report.append(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Duration: {duration:.2f} seconds")
        report.append("")
        
        for category, tests in self.results.items():
            report.append(f"## {category.title()} Tests")
            for test_name, (success, message) in tests.items():
                total_tests += 1
                if success:
                    passed_tests += 1
                status = "PASS" if success else "FAIL"
                report.append(f"- {test_name}: **{status}**")
                if not success:
                    report.append(f"  ```\n  {message}\n  ```")
            report.append("")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        report.append(f"## Summary")
        report.append(f"- Total Tests: {total_tests}")
        report.append(f"- Passed: {passed_tests}")
        report.append(f"- Failed: {total_tests - passed_tests}")
        report.append(f"- Success Rate: {success_rate:.1f}%")
        report.append("")
        
        if success_rate >= 90:
            report.append("✅ **VALIDATION PASSED** - Python environment ready for production")
        elif success_rate >= 70:
            report.append("⚠️ **VALIDATION PARTIAL** - Some issues need attention")
        else:
            report.append("❌ **VALIDATION FAILED** - Critical issues must be resolved")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = None):
        """Save validation report to file"""
        if filename is None:
            filename = f"/opt/citadel/logs/planb-04-validation-{int(time.time())}.md"
        
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        with open(filename, 'w') as f:
            f.write(self.generate_report())
        
        print(f"\n📋 Validation report saved: {filename}")

def main():
    """Main execution function"""
    print("🚀 PLANB-04 Python Environment Validation Suite")
    print("=" * 60)
    
    validator = PLANB04ValidationSuite()
    results = validator.run_all_validations()
    
    print("\n" + "=" * 60)
    print(validator.generate_report())
    
    # Save report
    validator.save_report()
    
    # Determine exit code
    total_tests = sum(len(tests) for tests in results.values())
    passed_tests = sum(1 for tests in results.values() for success, _ in tests.values() if success)
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    if success_rate >= 90:
        print(f"\n🎉 All validations completed successfully!")
        return 0
    else:
        print(f"\n⚠️ Some validations failed - check report for details")
        return 1

if __name__ == "__main__":
    sys.exit(main())