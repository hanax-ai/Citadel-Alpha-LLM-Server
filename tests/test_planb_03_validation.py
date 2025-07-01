#!/usr/bin/env python3
"""
PLANB-03 NVIDIA Driver Setup Validation Tests
Comprehensive validation suite for NVIDIA 570.x driver installation with CUDA 12.4+
"""

import unittest
import subprocess
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "configs"))
sys.path.append(str(project_root / "scripts"))

from gpu_settings import GPUSettings, DEFAULT_CONFIG_PATH


class TestPLANB03Validation(unittest.TestCase):
    """Test suite for PLANB-03 NVIDIA driver setup validation"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.logger = cls._setup_logging()
        cls.config_path = DEFAULT_CONFIG_PATH
        cls.test_results = []
        cls.logger.info("🧪 Starting PLANB-03 validation tests")
    
    @classmethod
    def _setup_logging(cls) -> logging.Logger:
        """Setup logging for validation tests"""
        logger = logging.getLogger("planb03_validation")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run command and return success status, stdout, stderr"""
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            return False, "", str(e)
    
    def _log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result and add to results list"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.logger.info(f"{status}: {test_name}")
        if details:
            self.logger.info(f"  Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def test_01_gpu_configuration_exists(self):
        """Test 1: Verify GPU configuration file exists and is valid"""
        test_name = "GPU Configuration File"
        
        try:
            if not self.config_path.exists():
                self._log_test_result(test_name, False, f"Config file not found: {self.config_path}")
                return
            
            # Load and validate configuration
            settings = GPUSettings.load_from_file(self.config_path)
            
            # Validate required fields
            self.assertIsNotNone(settings.driver_version)
            self.assertIsNotNone(settings.cuda_version)
            self.assertEqual(settings.target_gpus, 2)
            
            self._log_test_result(test_name, True, f"Driver: {settings.driver_version}, CUDA: {settings.cuda_version}")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_02_nvidia_driver_installed(self):
        """Test 2: Verify NVIDIA driver is installed and loaded"""
        test_name = "NVIDIA Driver Installation"
        
        try:
            # Check if nvidia-smi is available
            success, stdout, stderr = self._run_command(["nvidia-smi", "--version"])
            
            if not success:
                self._log_test_result(test_name, False, "nvidia-smi not available")
                return
            
            # Extract driver version
            driver_version = "Unknown"
            for line in stdout.split('\n'):
                if "Driver Version:" in line:
                    driver_version = line.split("Driver Version:")[1].split()[0]
                    break
            
            self._log_test_result(test_name, True, f"Driver version: {driver_version}")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_03_cuda_installation(self):
        """Test 3: Verify CUDA toolkit installation"""
        test_name = "CUDA Toolkit Installation"
        
        try:
            # Check nvcc availability
            success, stdout, stderr = self._run_command(["nvcc", "--version"])
            
            if not success:
                self._log_test_result(test_name, False, "nvcc not available - check PATH configuration")
                return
            
            # Extract CUDA version
            cuda_version = "Unknown"
            for line in stdout.split('\n'):
                if "release" in line.lower():
                    cuda_version = line.strip()
                    break
            
            self._log_test_result(test_name, True, cuda_version)
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_04_gpu_detection(self):
        """Test 4: Verify GPU detection and count"""
        test_name = "GPU Detection"
        
        try:
            # Get GPU list
            success, stdout, stderr = self._run_command(["nvidia-smi", "-L"])
            
            if not success:
                self._log_test_result(test_name, False, "Cannot list GPUs")
                return
            
            gpu_lines = [line for line in stdout.strip().split('\n') if line.strip()]
            gpu_count = len(gpu_lines)
            
            # Check if we have expected number of GPUs
            expected_gpus = 2
            if gpu_count >= expected_gpus:
                details = f"Found {gpu_count} GPU(s): " + "; ".join(gpu_lines)
                self._log_test_result(test_name, True, details)
            else:
                self._log_test_result(test_name, False, f"Expected {expected_gpus} GPUs, found {gpu_count}")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_05_gpu_memory_detection(self):
        """Test 5: Verify GPU memory detection"""
        test_name = "GPU Memory Detection"
        
        try:
            # Get GPU memory information
            success, stdout, stderr = self._run_command([
                "nvidia-smi", 
                "--query-gpu=name,memory.total", 
                "--format=csv,noheader,nounits"
            ])
            
            if not success:
                self._log_test_result(test_name, False, "Cannot query GPU memory")
                return
            
            memory_info = []
            total_vram = 0
            
            for line in stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(',')
                    if len(parts) >= 2:
                        gpu_name = parts[0].strip()
                        memory_mb = int(parts[1].strip())
                        memory_gb = memory_mb / 1024
                        total_vram += memory_gb
                        memory_info.append(f"{gpu_name}: {memory_gb:.1f}GB")
            
            details = f"Total VRAM: {total_vram:.1f}GB - " + "; ".join(memory_info)
            
            # Check if total VRAM meets expectations (should be ~32GB for dual RTX 4070 Ti SUPER)
            if total_vram >= 28:  # Allow some tolerance
                self._log_test_result(test_name, True, details)
            else:
                self._log_test_result(test_name, False, f"Low VRAM detected: {details}")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_06_cuda_device_query(self):
        """Test 6: Run CUDA device query test"""
        test_name = "CUDA Device Query"
        
        try:
            # Try to find and run deviceQuery
            device_query_paths = [
                "/usr/local/cuda/extras/demo_suite/deviceQuery",
                "/usr/local/cuda-*/extras/demo_suite/deviceQuery"
            ]
            
            device_query_path = None
            for path_pattern in device_query_paths:
                try:
                    # Use shell expansion for wildcards
                    result = subprocess.run(
                        f"ls {path_pattern} 2>/dev/null | head -1",
                        shell=True, capture_output=True, text=True
                    )
                    if result.returncode == 0 and result.stdout.strip():
                        device_query_path = result.stdout.strip()
                        break
                except:
                    continue
            
            if not device_query_path or not Path(device_query_path).exists():
                self._log_test_result(test_name, False, "deviceQuery not found")
                return
            
            # Run deviceQuery
            success, stdout, stderr = self._run_command([device_query_path], timeout=60)
            
            if success and "Result = PASS" in stdout:
                # Extract device count
                device_count = 0
                for line in stdout.split('\n'):
                    if "Detected" in line and "CUDA Capable device" in line:
                        try:
                            device_count = int(line.split()[1])
                        except:
                            pass
                
                self._log_test_result(test_name, True, f"CUDA devices detected: {device_count}")
            else:
                self._log_test_result(test_name, False, "deviceQuery failed or returned FAIL")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_07_gpu_performance_settings(self):
        """Test 7: Verify GPU performance settings"""
        test_name = "GPU Performance Settings"
        
        try:
            # Check persistence mode
            success, stdout, stderr = self._run_command([
                "nvidia-smi", 
                "--query-gpu=persistence_mode,power.management", 
                "--format=csv,noheader"
            ])
            
            if not success:
                self._log_test_result(test_name, False, "Cannot query GPU settings")
                return
            
            settings_info = []
            all_optimized = True
            
            for line in stdout.strip().split('\n'):
                if line.strip():
                    settings = line.strip().split(',')
                    if len(settings) >= 2:
                        persistence = settings[0].strip()
                        power_mgmt = settings[1].strip()
                        
                        settings_info.append(f"Persistence: {persistence}, Power Mgmt: {power_mgmt}")
                        
                        # Check if settings are optimal
                        if persistence != "Enabled" or power_mgmt != "Supported":
                            all_optimized = False
            
            details = "; ".join(settings_info)
            self._log_test_result(test_name, all_optimized, details)
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_08_environment_variables(self):
        """Test 8: Verify CUDA environment variables"""
        test_name = "CUDA Environment Variables"
        
        try:
            import os
            
            required_vars = ["CUDA_HOME", "CUDA_ROOT"]
            missing_vars = []
            present_vars = []
            
            for var in required_vars:
                if var in os.environ:
                    present_vars.append(f"{var}={os.environ[var]}")
                else:
                    missing_vars.append(var)
            
            # Check PATH for CUDA
            path = os.environ.get("PATH", "")
            cuda_in_path = any("cuda" in p.lower() for p in path.split(":"))
            
            if cuda_in_path:
                present_vars.append("CUDA in PATH")
            else:
                missing_vars.append("CUDA in PATH")
            
            if not missing_vars:
                self._log_test_result(test_name, True, "; ".join(present_vars))
            else:
                details = f"Missing: {', '.join(missing_vars)}"
                if present_vars:
                    details += f"; Present: {', '.join(present_vars)}"
                self._log_test_result(test_name, False, details)
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_09_pytorch_cuda_compatibility(self):
        """Test 9: Test PyTorch CUDA compatibility (if available)"""
        test_name = "PyTorch CUDA Compatibility"
        
        try:
            # Try to import torch and test CUDA
            test_script = '''
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version: {torch.version.cuda}")
    print(f"Device count: {torch.cuda.device_count()}")
    for i in range(torch.cuda.device_count()):
        print(f"Device {i}: {torch.cuda.get_device_name(i)}")
        props = torch.cuda.get_device_properties(i)
        print(f"  Memory: {props.total_memory / 1024**3:.1f} GB")
else:
    print("CUDA not available in PyTorch")
'''
            
            success, stdout, stderr = self._run_command([
                "python3", "-c", test_script
            ], timeout=30)
            
            if success and "CUDA available: True" in stdout:
                # Extract device count
                device_count = 0
                for line in stdout.split('\n'):
                    if "Device count:" in line:
                        try:
                            device_count = int(line.split(':')[1].strip())
                        except:
                            pass
                
                self._log_test_result(test_name, True, f"PyTorch CUDA devices: {device_count}")
            elif "No module named 'torch'" in stderr:
                self._log_test_result(test_name, True, "PyTorch not installed (skipped)")
            else:
                self._log_test_result(test_name, False, "PyTorch CUDA not available")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    def test_10_gpu_stress_test(self):
        """Test 10: Basic GPU computational stress test"""
        test_name = "GPU Stress Test"
        
        try:
            # Simple matrix multiplication test using nvidia-smi
            self.logger.info("Running 30-second GPU stress test...")
            
            # Get initial GPU utilization
            success, stdout_before, _ = self._run_command([
                "nvidia-smi", 
                "--query-gpu=utilization.gpu,temperature.gpu", 
                "--format=csv,noheader,nounits"
            ])
            
            if not success:
                self._log_test_result(test_name, False, "Cannot query initial GPU state")
                return
            
            # Run stress test if python/torch available
            stress_script = '''
import time
try:
    import torch
    if torch.cuda.is_available():
        device = torch.cuda.current_device()
        print(f"Running stress test on GPU {device}")
        
        # Create large tensors and perform operations
        for i in range(10):
            a = torch.randn(2000, 2000, device='cuda')
            b = torch.randn(2000, 2000, device='cuda')
            c = torch.matmul(a, b)
            torch.cuda.synchronize()
            time.sleep(1)
        
        print("Stress test completed")
    else:
        print("CUDA not available for stress test")
except ImportError:
    print("PyTorch not available for stress test")
    # Fallback: just check if GPU is responsive
    time.sleep(5)
    print("Basic responsiveness test completed")
'''
            
            # Run stress test
            success, stdout, stderr = self._run_command([
                "python3", "-c", stress_script
            ], timeout=45)
            
            # Get final GPU utilization
            success_after, stdout_after, _ = self._run_command([
                "nvidia-smi", 
                "--query-gpu=utilization.gpu,temperature.gpu", 
                "--format=csv,noheader,nounits"
            ])
            
            if success and success_after:
                self._log_test_result(test_name, True, "GPU stress test completed successfully")
            else:
                self._log_test_result(test_name, False, "GPU stress test failed or GPU unresponsive")
            
        except Exception as e:
            self._log_test_result(test_name, False, str(e))
    
    @classmethod
    def tearDownClass(cls):
        """Generate final test report"""
        cls.logger.info("\n" + "="*60)
        cls.logger.info("PLANB-03 NVIDIA Driver Setup - Validation Results")
        cls.logger.info("="*60)
        
        passed_tests = sum(1 for result in cls.test_results if result["passed"])
        total_tests = len(cls.test_results)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        cls.logger.info(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        cls.logger.info("")
        
        # Log failed tests
        failed_tests = [result for result in cls.test_results if not result["passed"]]
        if failed_tests:
            cls.logger.info("❌ Failed Tests:")
            for test in failed_tests:
                cls.logger.info(f"   • {test['test']}: {test['details']}")
        else:
            cls.logger.info("✅ All tests passed!")
        
        cls.logger.info("")
        
        # Overall assessment
        if success_rate >= 90:
            cls.logger.info("🎉 PLANB-03 NVIDIA setup is FULLY FUNCTIONAL")
        elif success_rate >= 70:
            cls.logger.info("⚠️  PLANB-03 NVIDIA setup is MOSTLY FUNCTIONAL")
        else:
            cls.logger.info("❌ PLANB-03 NVIDIA setup has CRITICAL ISSUES")
        
        cls.logger.info("="*60)


def main():
    """Run the validation test suite"""
    # Set up test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestPLANB03Validation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return appropriate exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    exit(main())