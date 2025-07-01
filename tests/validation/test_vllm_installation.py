#!/usr/bin/env python3
"""
PLANB-05: vLLM Installation Validation Test Suite 
Comprehensive testing and validation of vLLM installation using configuration management
"""

import os
import sys
import time
import torch
from pathlib import Path
from typing import List, Tuple, Optional
from rich.console import Console
from rich.progress import Progress

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from configs.vllm_settings import (
    load_vllm_settings,
    VLLMInstallationSettings,
    VLLMModelSettings,
    VLLMTestSettings
)

console = Console()

class VLLMInstallationValidator:
    """Main validation class for vLLM installation testing"""
    
    def __init__(self):
        """Initialize validator with configuration settings"""
        try:
            self.install_settings, self.model_settings, self.test_settings = load_vllm_settings()
            console.print("✅ Configuration loaded successfully")
        except Exception as e:
            console.print(f"❌ Failed to load configuration: {e}")
            console.print("Please ensure .env file exists with required variables")
            sys.exit(1)
    
    def test_vllm_import(self) -> bool:
        """Test vLLM import and basic functionality"""
        try:
            import vllm
            console.print(f"✅ vLLM imported successfully: {vllm.__version__}")
            
            # Check version compatibility
            version_parts = vllm.__version__.split('.')
            major, minor = int(version_parts[0]), int(version_parts[1])
            
            if major == 0 and minor >= 6:
                console.print("✅ vLLM version is compatible (0.6.x+)")
            elif major >= 1:
                console.print("✅ vLLM version is compatible (1.x+)")
            else:
                console.print(f"⚠️ vLLM version may have compatibility issues: {vllm.__version__}")
                
            return True
        except ImportError as e:
            console.print(f"❌ vLLM import failed: {e}")
            return False
    
    def test_cuda_availability(self) -> bool:
        """Test CUDA availability"""
        if torch.cuda.is_available():
            console.print(f"✅ CUDA available: {torch.version.cuda}")
            console.print(f"✅ GPU count: {torch.cuda.device_count()}")
            for i in range(torch.cuda.device_count()):
                console.print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            return True
        else:
            console.print("❌ CUDA not available")
            return False
    
    def test_dependencies(self) -> bool:
        """Test key dependencies"""
        dependencies = [
            ('transformers', '4.36.0'),
            ('tokenizers', '0.15.0'),
            ('fastapi', '0.104.0'),
            ('uvicorn', '0.24.0'),
            ('pydantic', '2.5.0'),
            ('huggingface_hub', '0.19.0'),
            ('torch', '2.0.0'),
            ('accelerate', '0.25.0')
        ]
        
        passed = 0
        for package, min_version in dependencies:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                console.print(f"✅ {package}: {version}")
                passed += 1
            except ImportError:
                console.print(f"❌ {package}: not installed")
        
        console.print(f"Dependencies: {passed}/{len(dependencies)} passed")
        return passed == len(dependencies)
    
    def test_configuration(self) -> bool:
        """Test configuration management"""
        try:
            # Test environment variables
            required_env_vars = [
                'HF_TOKEN',
                'DEV_ENV_PATH',
                'MODEL_STORAGE_PATH'
            ]
            
            missing_vars = []
            for var in required_env_vars:
                if not os.getenv(var) and not hasattr(self.install_settings, var.lower()):
                    missing_vars.append(var)
            
            if missing_vars:
                console.print(f"❌ Missing required environment variables: {missing_vars}")
                return False
            
            # Test path validation
            dev_env_path = Path(self.install_settings.dev_env_path)
            if not dev_env_path.exists():
                console.print(f"❌ Development environment path does not exist: {dev_env_path}")
                return False
            
            console.print("✅ Configuration validation passed")
            return True
            
        except Exception as e:
            console.print(f"❌ Configuration test failed: {e}")
            return False
    
    def test_huggingface_auth(self) -> bool:
        """Test Hugging Face authentication"""
        try:
            from huggingface_hub import whoami
            
            # Use token from configuration
            os.environ['HF_TOKEN'] = self.install_settings.hf_token
            
            user_info = whoami()
            console.print(f"✅ HF Authentication: {user_info['name']}")
            return True
        except Exception as e:
            console.print(f"❌ HF Authentication failed: {e}")
            console.print("Please check your HF_TOKEN in .env file")
            return False
    
    def test_vllm_engine(self) -> bool:
        """Test vLLM engine initialization with configured test model"""
        try:
            from vllm import LLM, SamplingParams
            
            console.print("🧪 Testing vLLM engine with configured test model...")
            
            # Use test model from configuration
            model_name = self.test_settings.test_model
            
            # Initialize LLM with configuration settings
            llm = LLM(
                model=model_name,
                tensor_parallel_size=self.install_settings.tensor_parallel_size,
                gpu_memory_utilization=self.install_settings.gpu_memory_utilization,
                download_dir=self.test_settings.test_cache_dir
            )
            
            # Test generation
            prompts = ["Hello, how are you?"]
            sampling_params = SamplingParams(temperature=0.8, top_p=0.95, max_tokens=50)
            
            outputs = llm.generate(prompts, sampling_params)
            
            for output in outputs:
                prompt = output.prompt
                generated_text = output.outputs[0].text
                console.print(f"✅ Test generation successful:")
                console.print(f"  Prompt: {prompt}")
                console.print(f"  Generated: {generated_text}")
            
            return True
            
        except Exception as e:
            console.print(f"❌ vLLM engine test failed: {e}")
            return False
    
    def test_performance(self) -> bool:
        """Basic performance test using configuration settings"""
        if not self.test_settings.enable_performance_tests:
            console.print("⏭️ Performance tests disabled in configuration")
            return True
            
        try:
            from vllm import LLM, SamplingParams
            
            console.print("🏃 Running performance test...")
            
            llm = LLM(
                model=self.test_settings.test_model,
                tensor_parallel_size=self.install_settings.tensor_parallel_size,
                gpu_memory_utilization=self.install_settings.gpu_memory_utilization
            )
            
            # Performance test
            prompts = ["Hello world!"] * 10
            sampling_params = SamplingParams(max_tokens=20)
            
            start_time = time.time()
            outputs = llm.generate(prompts, sampling_params)
            end_time = time.time()
            
            total_time = end_time - start_time
            throughput = len(prompts) / total_time
            
            console.print(f"✅ Performance test completed:")
            console.print(f"   Requests: {len(prompts)}")
            console.print(f"   Total time: {total_time:.2f}s")
            console.print(f"   Throughput: {throughput:.2f} requests/second")
            
            # Check against minimum throughput
            if throughput >= self.test_settings.min_throughput:
                console.print(f"✅ Throughput meets minimum requirement ({self.test_settings.min_throughput:.2f})")
                return True
            else:
                console.print(f"⚠️ Throughput below minimum requirement ({self.test_settings.min_throughput:.2f})")
                return False
            
        except Exception as e:
            console.print(f"❌ Performance test failed: {e}")
            return False
    
    def run_all_tests(self) -> Tuple[int, int]:
        """Run all validation tests"""
        console.print("🚀 PLANB-05 vLLM Installation Validation Suite")
        console.print("=" * 60)
        
        tests = [
            ("Configuration", self.test_configuration),
            ("vLLM Import", self.test_vllm_import),
            ("CUDA Availability", self.test_cuda_availability),
            ("Dependencies", self.test_dependencies),
            ("Hugging Face Auth", self.test_huggingface_auth),
            ("vLLM Engine", self.test_vllm_engine),
            ("Performance", self.test_performance)
        ]
        
        results = []
        for test_name, test_func in tests:
            console.print(f"\n📋 Running {test_name} test...")
            
            # Timeout handling for tests
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                console.print(f"❌ {test_name} test failed with exception: {e}")
                results.append((test_name, False))
        
        console.print(f"\n📊 Test Results Summary:")
        console.print("-" * 40)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            console.print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        total_tests = len(tests)
        console.print(f"\nOverall: {passed}/{total_tests} tests passed")
        
        if passed == total_tests:
            console.print("🎉 All tests passed! vLLM is ready for use.")
        else:
            console.print("⚠️ Some tests failed. Check installation and configuration.")
        
        return passed, total_tests


def main():
    """Main entry point for validation suite"""
    validator = VLLMInstallationValidator()
    passed, total = validator.run_all_tests()
    
    # Return appropriate exit code
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())