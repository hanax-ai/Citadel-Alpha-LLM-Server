#!/usr/bin/env python3
"""
Test validation for vLLM client test script
PLANB-05-D4: Create vLLM Client Test Script - Validation
"""

import unittest
import subprocess
import sys
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from unittest import mock

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestVLLMClientScript(unittest.TestCase):
    """Test suite for vLLM client test script validation"""
    
    def setUp(self):
        """Set up test environment"""
        self.script_path = "/opt/citadel/scripts/test-vllm-client.py"
        self.test_url = "http://localhost:8000"
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
        self.assertIn("Test vLLM server", result.stdout)
        self.assertIn("--url", result.stdout)
        self.assertIn("--model", result.stdout)
        self.assertIn("--verbose", result.stdout)
    
    def test_script_imports_successfully(self):
        """Test script can import required modules"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        
        try:
            spec.loader.exec_module(module)
            self.assertTrue(hasattr(module, 'main'), "Script missing main function")
            self.assertTrue(hasattr(module, 'VLLMClientTester'), "Script missing VLLMClientTester class")
        except ImportError as e:
            self.fail(f"Script imports failed: {e}")
    
    def test_vllm_client_tester_class(self):
        """Test VLLMClientTester class functionality"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test class initialization
        tester = module.VLLMClientTester(self.test_url, self.test_model)
        self.assertEqual(tester.base_url, self.test_url)
        self.assertEqual(tester.model_name, self.test_model)
        self.assertIsNotNone(tester.config)
        self.assertIsInstance(tester.config, dict)
    
    def test_configuration_loading(self):
        """Test configuration loading functionality"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        tester = module.VLLMClientTester(self.test_url, self.test_model)
        config = tester._load_configuration()
        
        # Check required configuration keys
        required_keys = ['timeout', 'default_host', 'default_port', 'test_model']
        for key in required_keys:
            self.assertIn(key, config, f"Missing required configuration key: {key}")
        
        # Check data types
        self.assertIsInstance(config['timeout'], int)
        self.assertIsInstance(config['default_host'], str)
        self.assertIsInstance(config['default_port'], int)
        self.assertIsInstance(config['test_model'], str)
    
    @patch('requests.Session.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        tester = module.VLLMClientTester(self.test_url, self.test_model)
        success, result = tester.test_server_health()
        
        self.assertTrue(success, "Health check should succeed")
        self.assertEqual(result['test'], 'health_check')
        self.assertEqual(result['status'], 'passed')
        self.assertIn('response_time', result['details'])
    
    @patch('requests.Session.get')
    def test_health_check_failure(self, mock_get):
        """Test failed health check"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        tester = module.VLLMClientTester(self.test_url, self.test_model)
        success, result = tester.test_server_health()
        
        self.assertFalse(success, "Health check should fail")
        self.assertEqual(result['status'], 'failed')
        self.assertIn('error', result['details'])
    
    @patch('requests.Session.get')
    def test_models_endpoint_success(self, mock_get):
        """Test successful models endpoint"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'data': [
                {'id': 'facebook/opt-125m'},
                {'id': 'microsoft/Phi-3-mini-4k-instruct'}
            ]
        }
        mock_get.return_value = mock_response
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        tester = module.VLLMClientTester(self.test_url, self.test_model)
        success, result = tester.test_models_endpoint()
        
        self.assertTrue(success, "Models endpoint should succeed")
        self.assertEqual(result['status'], 'passed')
        self.assertIn('available_models', result['details'])
        self.assertEqual(len(result['details']['available_models']), 2)
    
    @patch('requests.Session.post')
    def test_completion_success(self, mock_post):
        """Test successful completion"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'choices': [{
                'message': {'content': 'Test successful'},
                'finish_reason': 'stop'
            }],
            'usage': {'total_tokens': 10}
        }
        mock_post.return_value = mock_response
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_vllm_client", self.script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        tester = module.VLLMClientTester(self.test_url, self.test_model)
        success, result = tester.test_completion()
        
        self.assertTrue(success, "Completion should succeed")
        self.assertEqual(result['status'], 'passed')
        self.assertIn('response_content', result['details'])
        self.assertIn('usage', result['details'])
    
    def test_invalid_arguments_handling(self):
        """Test script handles invalid arguments gracefully"""
        # Test with invalid URL format
        result = subprocess.run(
            ["python3", self.script_path, "--url", "invalid-url"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should not crash, may fail but should exit gracefully
        self.assertIn(result.returncode, [0, 1], "Script should handle invalid URLs gracefully")


def run_validation_tests():
    """Run all validation tests and return results"""
    print("🧪 Running vLLM Client Test Script Validation...")
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestVLLMClientScript)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Print summary
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    
    print(f"\n{'='*60}")
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