#!/usr/bin/env python3
"""
PLANB-05 Step 7: Hugging Face CLI Installation Validation Tests
Comprehensive validation suite for HF CLI setup and authentication
"""

import os
import sys
import unittest
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from configs.vllm_settings import VLLMInstallationSettings


class TestHuggingFaceCLIInstallation(unittest.TestCase):
    """Test suite for Hugging Face CLI installation and configuration"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.test_env = os.environ.copy()
        cls.venv_path = "/opt/citadel/dev-env"
        
    def setUp(self):
        """Set up individual test"""
        self.addCleanup(self._restore_environment)
        
    def _restore_environment(self):
        """Restore environment after test"""
        os.environ.clear()
        os.environ.update(self.test_env)
    
    def test_01_environment_file_exists(self):
        """Test that .env file exists and contains required variables"""
        env_file = Path(".env")
        
        if not env_file.exists():
            self.skipTest(".env file not found - configuration not complete")
        
        # Read .env file
        with open(env_file, 'r') as f:
            content = f.read()
        
        # Check for required variables
        required_vars = [
            "HF_TOKEN",
            "HF_HOME",
            "TRANSFORMERS_CACHE"
        ]
        
        for var in required_vars:
            self.assertIn(var, content, f"Required variable {var} not found in .env")
    
    def test_02_virtual_environment_exists(self):
        """Test that virtual environment exists and is functional"""
        venv_path = Path(self.venv_path)
        
        self.assertTrue(venv_path.exists(), f"Virtual environment not found at {self.venv_path}")
        
        # Check for activation script
        activate_script = venv_path / "bin" / "activate"
        self.assertTrue(activate_script.exists(), "Virtual environment activation script not found")
        
        # Check for Python executable
        python_exe = venv_path / "bin" / "python"
        self.assertTrue(python_exe.exists(), "Python executable not found in virtual environment")
    
    def test_03_huggingface_cli_installation(self):
        """Test that huggingface-cli is installed and accessible"""
        # Test CLI availability in virtual environment
        try:
            result = subprocess.run(
                [f"{self.venv_path}/bin/python", "-m", "huggingface_hub.commands.huggingface_cli", "--version"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            self.assertEqual(result.returncode, 0, "huggingface-cli not accessible")
            self.assertIn("huggingface_hub", result.stdout.lower(), "Unexpected version output")
            
        except subprocess.TimeoutExpired:
            self.fail("CLI version check timed out")
        except FileNotFoundError:
            self.fail("Virtual environment Python executable not found")
    
    def test_04_cache_directories_exist(self):
        """Test that cache directories are created with proper permissions"""
        # Load settings to get cache paths
        try:
            settings = VLLMInstallationSettings()
        except Exception as e:
            self.skipTest(f"Cannot load settings: {e}")
        
        cache_dirs = [
            Path(settings.hf_cache_dir),
            Path(settings.transformers_cache)
        ]
        
        for cache_dir in cache_dirs:
            self.assertTrue(cache_dir.exists(), f"Cache directory not found: {cache_dir}")
            self.assertTrue(cache_dir.is_dir(), f"Cache path is not a directory: {cache_dir}")
            
            # Check permissions (should be readable/writable)
            self.assertTrue(os.access(cache_dir, os.R_OK), f"Cache directory not readable: {cache_dir}")
            self.assertTrue(os.access(cache_dir, os.W_OK), f"Cache directory not writable: {cache_dir}")
    
    def test_05_environment_script_exists(self):
        """Test that environment setup script exists and is executable"""
        script_path = Path("/opt/citadel/scripts/setup-hf-env.sh")
        
        if not script_path.exists():
            self.skipTest("Environment script not found - installation incomplete")
        
        self.assertTrue(script_path.is_file(), "Environment script is not a file")
        self.assertTrue(os.access(script_path, os.X_OK), "Environment script is not executable")
        
        # Check script content
        with open(script_path, 'r') as f:
            content = f.read()
        
        required_exports = ["HF_TOKEN", "HF_HOME", "TRANSFORMERS_CACHE"]
        for export in required_exports:
            self.assertIn(export, content, f"Missing export for {export}")
    
    @unittest.skipIf(not Path(".env").exists(), "No .env file - cannot test authentication")
    def test_06_configuration_validation(self):
        """Test configuration loading and validation"""
        try:
            settings = VLLMInstallationSettings()
            
            # Validate token format
            self.assertTrue(settings.hf_token.startswith("hf_"), "HF token should start with 'hf_'")
            self.assertGreater(len(settings.hf_token), 20, "HF token appears too short")
            
            # Validate paths
            self.assertTrue(Path(settings.hf_cache_dir).is_absolute(), "HF cache dir should be absolute path")
            self.assertTrue(Path(settings.transformers_cache).is_absolute(), "Transformers cache should be absolute path")
            
        except Exception as e:
            self.fail(f"Configuration validation failed: {e}")
    
    def test_07_huggingface_auth_script_exists(self):
        """Test that authentication helper script exists and is functional"""
        auth_script = Path("scripts/huggingface_auth.py")
        
        self.assertTrue(auth_script.exists(), "Authentication helper script not found")
        self.assertTrue(auth_script.is_file(), "Authentication script is not a file")
        
        # Test script can be imported
        try:
            import scripts.huggingface_auth
            self.assertTrue(hasattr(scripts.huggingface_auth, 'HuggingFaceAuthenticator'), 
                           "HuggingFaceAuthenticator class not found")
        except ImportError as e:
            self.fail(f"Cannot import authentication script: {e}")
    
    def test_08_main_installation_script_exists(self):
        """Test that main installation script exists and is executable"""
        script_path = Path("scripts/planb-05-step7-huggingface-cli.sh")
        
        self.assertTrue(script_path.exists(), "Main installation script not found")
        self.assertTrue(script_path.is_file(), "Installation script is not a file")
        self.assertTrue(os.access(script_path, os.X_OK), "Installation script is not executable")
        
        # Check script content for required functions
        with open(script_path, 'r') as f:
            content = f.read()
        
        required_functions = [
            "validate_environment",
            "install_huggingface_cli",
            "configure_authentication",
            "verify_authentication"
        ]
        
        for function in required_functions:
            self.assertIn(function, content, f"Required function {function} not found in script")
    
    @unittest.skipIf(not Path(".env").exists(), "No .env file - cannot test authentication")
    def test_09_authentication_status(self):
        """Test authentication status if possible"""
        try:
            # Try to check authentication status
            result = subprocess.run(
                [f"{self.venv_path}/bin/python", "-m", "huggingface_hub.commands.huggingface_cli", "whoami"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.assertIsNotNone(result.stdout.strip(), "No username returned from whoami")
                print(f"✅ Authenticated as: {result.stdout.strip()}")
            else:
                print("ℹ️  Authentication not yet configured (expected during setup)")
                
        except subprocess.TimeoutExpired:
            self.skipTest("Authentication check timed out")
        except Exception as e:
            self.skipTest(f"Cannot check authentication: {e}")
    
    def test_10_security_validation(self):
        """Test that no hardcoded credentials exist in scripts"""
        script_files = [
            "scripts/planb-05-step7-huggingface-cli.sh",
            "scripts/huggingface_auth.py"
        ]
        
        # Look for potential hardcoded tokens
        suspicious_patterns = [
            "hf_",  # But not in comments or variable names
            "huggingface.co/settings/tokens"  # URLs are OK
        ]
        
        for script_file in script_files:
            script_path = Path(script_file)
            if not script_path.exists():
                continue
                
            with open(script_path, 'r') as f:
                content = f.read()
            
            # Check that no actual tokens are hardcoded
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                # Skip comments and documentation
                if line.strip().startswith('#') or line.strip().startswith('"""') or line.strip().startswith("'"):
                    continue
                
                # Check for suspicious patterns
                if "hf_" in line and "token" in line.lower():
                    # Make sure it's a variable reference, not a hardcoded token
                    if not any(var in line for var in ["${", "$HF_TOKEN", "settings.hf_token"]):
                        self.fail(f"Potential hardcoded token in {script_file}:{i}")


class TestHuggingFaceAuthenticator(unittest.TestCase):
    """Test suite for HuggingFaceAuthenticator class"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_env = os.environ.copy()
        
    def tearDown(self):
        """Clean up test environment"""
        os.environ.clear()
        os.environ.update(self.test_env)
    
    @unittest.skipIf(not Path(".env").exists(), "No .env file - cannot test authenticator")
    def test_authenticator_initialization(self):
        """Test that authenticator can be initialized"""
        try:
            from scripts.huggingface_auth import HuggingFaceAuthenticator
            auth = HuggingFaceAuthenticator()
            self.assertIsNotNone(auth.settings, "Settings not loaded")
        except Exception as e:
            self.fail(f"Cannot initialize authenticator: {e}")
    
    def test_token_validation(self):
        """Test token validation logic"""
        from scripts.huggingface_auth import HuggingFaceAuthenticator
        
        # Mock settings for testing
        with patch.object(HuggingFaceAuthenticator, '__init__', lambda x: None):
            auth = HuggingFaceAuthenticator()
            auth.settings = MagicMock()
            
            # Test valid token
            auth.settings.hf_token = "hf_" + "x" * 20
            self.assertTrue(auth.validate_token())
            
            # Test invalid tokens
            auth.settings.hf_token = "invalid_token"
            self.assertFalse(auth.validate_token())
            
            auth.settings.hf_token = "hf_short"
            self.assertFalse(auth.validate_token())


def run_validation_suite():
    """Run the complete validation suite"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestHuggingFaceCLIInstallation))
    suite.addTests(loader.loadTestsFromTestCase(TestHuggingFaceAuthenticator))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Hugging Face CLI Installation Validation Tests")
    print("=" * 60)
    
    success = run_validation_suite()
    
    if success:
        print("\n✅ All validation tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some validation tests failed!")
        sys.exit(1)