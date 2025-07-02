#!/usr/bin/env python3
"""
Test validation for simple vLLM server script
PLANB-05-D3: Create Simple vLLM Server Script - Validation
"""

import unittest
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestSimpleVLLMServerScript(unittest.TestCase):
    """Test suite for simple vLLM server script validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.script_path = "/opt/citadel/scripts/start-vllm-server.py"
        self.test_model = "facebook/opt-125m"
    
    def test_script_exists_and_executable(self):
        """Test that the script exists and is executable"""
        script = Path(self.script_path)
        self.assertTrue(script.exists(), f"Script not found at {self.script_path}")
        self.assertTrue(os.access(self.script_path, os.X_OK), "Script is not executable")
    
    def test_script_syntax_validation(self):
        """Test script has valid Python syntax"""
        result = subprocess.run(
            ["python3", "-m", "py_compile", self.script_path],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Syntax error in script: {result.stderr}")
    
    def test_script_help_output(self):
        """Test script provides help output"""
        result = subprocess.run(
            ["python3", self.script_path, "--help"],
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, "Help command failed")
        self.assertIn("Start vLLM server", result.stdout)
        self.assertIn("model_path", result.stdout)
    
    def test_script_imports_successfully(self):
        """Test script can import required modules"""
        # Test by importing the script module
        import importlib.util
        spec = importlib.util.spec_from_file_location("start_vllm_server", self.script_path)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
            self.assertTrue(hasattr(module, 'main'), "Script missing main function")
            self.assertTrue(hasattr(module, 'start_vllm_server'), "Script missing start_vllm_server function")
        except ImportError as e:
            self.fail(f"Script imports failed: {e}")
    
    def test_configuration_loading(self):
        """Test configuration loading functionality"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("start_vllm_server", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test configuration loading function
        config = module.load_configuration()
        self.assertIsInstance(config, dict, "Configuration should return dictionary")
        
        # Check required configuration keys
        required_keys = ['host', 'port', 'tensor_parallel_size', 'gpu_memory_utilization']
        for key in required_keys:
            self.assertIn(key, config, f"Missing required configuration key: {key}")
    
    @patch('subprocess.Popen')
    def test_server_startup_command_construction(self, mock_popen):
        """Test that server startup command is constructed correctly"""
        # Mock process
        mock_process = MagicMock()
        mock_process.pid = 12345
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("start_vllm_server", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test start_vllm_server function
        result = module.start_vllm_server(self.test_model, port=8001, host="127.0.0.1")
        
        # Verify subprocess.Popen was called
        mock_popen.assert_called_once()
        call_args = mock_popen.call_args[0][0]  # Get the command arguments
        
        # Verify command structure
        self.assertIn("python", call_args[0])
        self.assertIn("vllm.entrypoints.openai.api_server", call_args)
        self.assertIn("--model", call_args)
        self.assertIn(self.test_model, call_args)
        self.assertIn("--port", call_args)
        self.assertIn("8001", call_args)
        self.assertIn("--host", call_args)
        self.assertIn("127.0.0.1", call_args)
    
    def test_error_handling_invalid_arguments(self):
        """Test script handles invalid arguments gracefully"""
        # Test with missing model argument
        result = subprocess.run(
            ["python3", self.script_path],
            capture_output=True,
            text=True
        )
        self.assertNotEqual(result.returncode, 0, "Script should fail with missing arguments")
        self.assertIn("required", result.stderr.lower())


def run_validation_tests():
    """Run all validation tests and return results"""
    print("🧪 Running Simple vLLM Server Script Validation Tests...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSimpleVLLMServerScript)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    
    print(f"\n{'='*50}")
    print(f"📊 Test Summary:")
    print(f"   Tests Run: {tests_run}")
    print(f"   Failures: {failures}")
    print(f"   Errors: {errors}")
    print(f"   Success Rate: {((tests_run - failures - errors) / tests_run * 100):.1f}%")
    
    if failures == 0 and errors == 0:
        print("✅ All validation tests passed!")
        return True
    else:
        print("❌ Some validation tests failed!")
        return False


if __name__ == "__main__":
    success = run_validation_tests()
    sys.exit(0 if success else 1)