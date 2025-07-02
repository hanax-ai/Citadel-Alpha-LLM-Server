#!/usr/bin/env python3
"""
PLANB-05-Step8: Monitoring and Utilities Validation Test
Comprehensive validation of monitoring and development tools installation
"""

import sys
import subprocess
import importlib
import os
import time
from pathlib import Path
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Validation test result"""
    test_name: str
    passed: bool
    message: str
    details: str = ""


class MonitoringUtilitiesValidator:
    """Comprehensive validator for monitoring and utilities installation"""
    
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.env_path = "/opt/citadel/dev-env"
        
    def log_result(self, test_name: str, passed: bool, message: str, details: str = "") -> None:
        """Log a validation result"""
        result = ValidationResult(test_name, passed, message, details)
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}: {message}")
        if details and not passed:
            print(f"    Details: {details}")
    
    def test_virtual_environment(self) -> None:
        """Test virtual environment availability"""
        test_name = "Virtual Environment"
        
        if not Path(self.env_path).exists():
            self.log_result(test_name, False, "Virtual environment directory not found", 
                          f"Expected: {self.env_path}")
            return
            
        python_path = Path(self.env_path) / "bin" / "python"
        if not python_path.exists():
            self.log_result(test_name, False, "Python executable not found in virtual environment")
            return
            
        try:
            result = subprocess.run([str(python_path), "--version"], 
                                 capture_output=True, text=True, timeout=10)
            if result.returncode == 0 and "3.12" in result.stdout:
                self.log_result(test_name, True, f"Python 3.12 available in virtual environment", 
                              result.stdout.strip())
            else:
                self.log_result(test_name, False, "Wrong Python version or execution failed",
                              result.stdout + result.stderr)
        except Exception as e:
            self.log_result(test_name, False, "Failed to execute Python", str(e))
    
    def test_monitoring_packages(self) -> None:
        """Test monitoring package imports"""
        monitoring_packages = [
            ("psutil", "System monitoring"),
            ("GPUtil", "GPU utilities"),
            ("py3nvml", "NVIDIA ML Python"),
            ("pynvml", "NVIDIA ML (alternative)"),
            ("rich", "Rich text formatting"),
            ("typer", "CLI framework"),
            ("tqdm", "Progress bars")
        ]
        
        for package_name, description in monitoring_packages:
            test_name = f"Monitoring Package: {package_name}"
            try:
                module = importlib.import_module(package_name)
                version = getattr(module, '__version__', 'Unknown')
                self.log_result(test_name, True, f"Imported successfully", 
                              f"Version: {version} - {description}")
            except ImportError as e:
                self.log_result(test_name, False, f"Import failed", str(e))
    
    def test_development_tools(self) -> None:
        """Test development tool imports"""
        dev_packages = [
            ("IPython", "Interactive Python"),
            ("jupyter", "Jupyter notebooks"),
            ("matplotlib", "Plotting library"),
            ("seaborn", "Statistical plotting"),
            ("tensorboard", "TensorBoard visualization")
        ]
        
        for package_name, description in dev_packages:
            test_name = f"Development Tool: {package_name}"
            try:
                module = importlib.import_module(package_name)
                version = getattr(module, '__version__', 'Unknown')
                self.log_result(test_name, True, f"Imported successfully", 
                              f"Version: {version} - {description}")
            except ImportError as e:
                self.log_result(test_name, False, f"Import failed", str(e))
    
    def test_gpu_monitoring_functionality(self) -> None:
        """Test GPU monitoring functionality"""
        test_name = "GPU Monitoring Functionality"
        
        try:
            import pynvml
            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()
            
            if device_count > 0:
                # Test first GPU
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                
                self.log_result(test_name, True, f"GPU monitoring operational", 
                              f"Detected {device_count} GPU(s), first GPU: {name}, temp: {temperature}°C")
            else:
                self.log_result(test_name, False, "No GPUs detected")
                
        except Exception as e:
            self.log_result(test_name, False, "GPU monitoring failed", str(e))
    
    def test_system_monitoring_functionality(self) -> None:
        """Test system monitoring functionality"""
        test_name = "System Monitoring Functionality"
        
        try:
            import psutil
            
            # Test CPU monitoring
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Test memory monitoring
            memory = psutil.virtual_memory()
            
            # Test disk monitoring
            disk = psutil.disk_usage('/')
            
            details = (f"CPU: {cpu_percent}%, "
                      f"Memory: {memory.percent}% used, "
                      f"Disk: {(disk.used/disk.total)*100:.1f}% used")
            
            self.log_result(test_name, True, "System monitoring operational", details)
            
        except Exception as e:
            self.log_result(test_name, False, "System monitoring failed", str(e))
    
    def test_monitoring_scripts(self) -> None:
        """Test monitoring utility scripts"""
        test_name = "Monitoring Scripts"
        
        script_path = "/opt/citadel/scripts/system-monitor.py"
        
        if not Path(script_path).exists():
            self.log_result(test_name, False, "System monitor script not found", script_path)
            return
        
        try:
            # Test script execution
            python_path = Path(self.env_path) / "bin" / "python"
            result = subprocess.run([str(python_path), script_path], 
                                 capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log_result(test_name, True, "System monitor script executed successfully",
                              "Script produces formatted output with system and GPU status")
            else:
                self.log_result(test_name, False, "Script execution failed",
                              result.stderr)
                
        except subprocess.TimeoutExpired:
            self.log_result(test_name, False, "Script execution timed out")
        except Exception as e:
            self.log_result(test_name, False, "Script test failed", str(e))
    
    def test_jupyter_availability(self) -> None:
        """Test Jupyter notebook availability"""
        test_name = "Jupyter Notebook Availability"
        
        try:
            python_path = Path(self.env_path) / "bin" / "python"
            result = subprocess.run([str(python_path), "-c", "import jupyter; print('OK')"],
                                 capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0 and "OK" in result.stdout:
                self.log_result(test_name, True, "Jupyter available for notebook development")
            else:
                self.log_result(test_name, False, "Jupyter import failed", result.stderr)
                
        except Exception as e:
            self.log_result(test_name, False, "Jupyter test failed", str(e))
    
    def test_ipython_availability(self) -> None:
        """Test IPython availability"""
        test_name = "IPython Availability"
        
        try:
            python_path = Path(self.env_path) / "bin" / "python"
            result = subprocess.run([str(python_path), "-c", "import IPython; print(IPython.__version__)"],
                                 capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.log_result(test_name, True, f"IPython available for interactive development",
                              f"Version: {version}")
            else:
                self.log_result(test_name, False, "IPython import failed", result.stderr)
                
        except Exception as e:
            self.log_result(test_name, False, "IPython test failed", str(e))
    
    def test_rich_formatting(self) -> None:
        """Test Rich text formatting functionality"""
        test_name = "Rich Text Formatting"
        
        try:
            from rich.console import Console
            from rich.table import Table
            
            console = Console()
            table = Table(title="Test Table")
            table.add_column("Test", style="cyan")
            table.add_column("Status", style="green")
            table.add_row("Rich Formatting", "✅ Working")
            
            # Capture output to test rendering
            with console.capture() as capture:
                console.print(table)
            
            output = capture.get()
            if "Test Table" in output and "Rich Formatting" in output:
                self.log_result(test_name, True, "Rich text formatting operational")
            else:
                self.log_result(test_name, False, "Rich formatting output unexpected")
                
        except Exception as e:
            self.log_result(test_name, False, "Rich formatting test failed", str(e))
    
    def test_integration_with_vllm(self) -> None:
        """Test integration with existing vLLM installation"""
        test_name = "vLLM Integration"
        
        try:
            python_path = Path(self.env_path) / "bin" / "python"
            test_code = """
import vllm
import psutil
import GPUtil
print(f"vLLM: {vllm.__version__}")
print(f"Monitoring integration: OK")
"""
            
            result = subprocess.run([str(python_path), "-c", test_code],
                                 capture_output=True, text=True, timeout=15)
            
            if result.returncode == 0 and "Monitoring integration: OK" in result.stdout:
                self.log_result(test_name, True, "Monitoring tools integrate properly with vLLM",
                              result.stdout.strip())
            else:
                self.log_result(test_name, False, "Integration test failed", result.stderr)
                
        except Exception as e:
            self.log_result(test_name, False, "vLLM integration test failed", str(e))
    
    def run_all_tests(self) -> None:
        """Run all validation tests"""
        print("=" * 60)
        print("PLANB-05-Step8: Monitoring and Utilities Validation")
        print("=" * 60)
        print()
        
        # Run all test methods
        self.test_virtual_environment()
        self.test_monitoring_packages()
        self.test_development_tools()
        self.test_gpu_monitoring_functionality()
        self.test_system_monitoring_functionality()
        self.test_monitoring_scripts()
        self.test_jupyter_availability()
        self.test_ipython_availability()
        self.test_rich_formatting()
        self.test_integration_with_vllm()
        
        # Summary
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)
        
        passed_tests = [r for r in self.results if r.passed]
        failed_tests = [r for r in self.results if not r.passed]
        
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {(len(passed_tests)/len(self.results)*100):.1f}%")
        
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  ❌ {test.test_name}: {test.message}")
                if test.details:
                    print(f"     {test.details}")
        
        overall_success = len(failed_tests) == 0
        print(f"\nOVERALL STATUS: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
        
        return overall_success


def main():
    """Main validation entry point"""
    validator = MonitoringUtilitiesValidator()
    success = validator.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()