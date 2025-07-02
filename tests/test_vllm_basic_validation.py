#!/usr/bin/env python3
"""
PLANB-05-D1: Basic vLLM Functionality Test
Simplified vLLM validation test using configuration management
"""

import os
import sys
import time
import torch
from pathlib import Path
from typing import Optional, Tuple
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from configs.vllm_settings import (
    load_vllm_settings,
    VLLMInstallationSettings,
    VLLMTestSettings
)

console = Console()


class BasicVLLMValidator:
    """Basic vLLM functionality validator with configuration management"""
    
    def __init__(self):
        """Initialize validator with configuration settings"""
        try:
            self.install_settings, _, self.test_settings = load_vllm_settings()
            console.print("✅ Configuration loaded successfully")
        except Exception as e:
            console.print(f"❌ Failed to load configuration: {e}")
            console.print("Please ensure .env file exists with required variables")
            sys.exit(1)
    
    def test_vllm_import(self) -> bool:
        """Test basic vLLM import functionality"""
        try:
            import vllm
            console.print(f"✅ vLLM imported successfully: {vllm.__version__}")
            return True
        except ImportError as e:
            console.print(f"❌ vLLM import failed: {e}")
            return False
    
    def test_cuda_availability(self) -> bool:
        """Test CUDA availability for GPU acceleration"""
        if torch.cuda.is_available():
            cuda_version = torch.version.cuda
            gpu_count = torch.cuda.device_count()
            console.print(f"✅ CUDA available: {cuda_version}")
            console.print(f"✅ GPU count: {gpu_count}")
            
            # Display GPU information
            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                console.print(f"  GPU {i}: {gpu_name}")
            
            return True
        else:
            console.print("❌ CUDA not available")
            return False
    
    def test_vllm_engine_basic(self) -> bool:
        """Test basic vLLM engine initialization with configured test model"""
        try:
            from vllm import LLM, SamplingParams
            
            console.print("🧪 Testing vLLM engine with configured test model...")
            
            # Use configured test model and settings
            model_name = self.test_settings.test_model
            cache_dir = self.test_settings.test_cache_dir
            
            # Create cache directory if it doesn't exist
            Path(cache_dir).mkdir(parents=True, exist_ok=True)
            
            # Initialize LLM with minimal configuration for basic test
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Initializing vLLM engine...", total=None)
                
                llm = LLM(
                    model=model_name,
                    tensor_parallel_size=1,  # Single GPU for basic test
                    gpu_memory_utilization=0.3,  # Conservative memory usage
                    download_dir=cache_dir
                )
                
                progress.update(task, description="Running inference test...")
                
                # Test generation with simple prompt
                prompts = ["Hello, how are you?"]
                sampling_params = SamplingParams(
                    temperature=0.8, 
                    top_p=0.95, 
                    max_tokens=50
                )
                
                outputs = llm.generate(prompts, sampling_params)
                progress.remove_task(task)
            
            # Display results
            for output in outputs:
                prompt = output.prompt
                generated_text = output.outputs[0].text.strip()
                console.print(f"✅ Basic generation test successful:")
                console.print(f"  Prompt: {prompt}")
                console.print(f"  Generated: {generated_text}")
            
            return True
            
        except Exception as e:
            console.print(f"❌ vLLM engine test failed: {e}")
            return False
    
    def run_basic_tests(self) -> Tuple[int, int]:
        """Run basic validation tests"""
        console.print("🚀 Basic vLLM Functionality Test Suite")
        console.print("=" * 50)
        
        tests = [
            ("vLLM Import", self.test_vllm_import),
            ("CUDA Availability", self.test_cuda_availability),
            ("vLLM Engine Basic", self.test_vllm_engine_basic)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            console.print(f"\n📋 Running {test_name} test...")
            
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                console.print(f"❌ {test_name} test failed with exception: {e}")
                results.append((test_name, False))
        
        # Display results summary
        console.print(f"\n📊 Test Results Summary:")
        console.print("-" * 30)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            console.print(f"  {test_name}: {status}")
            if result:
                passed += 1
        
        total_tests = len(tests)
        console.print(f"\nOverall: {passed}/{total_tests} tests passed")
        
        if passed == total_tests:
            console.print("🎉 Basic vLLM functionality verified successfully!")
        else:
            console.print("⚠️ Some basic tests failed. Check installation.")
        
        return passed, total_tests


def main() -> int:
    """Main entry point for basic vLLM validation"""
    try:
        validator = BasicVLLMValidator()
        passed, total = validator.run_basic_tests()
        
        # Return appropriate exit code
        return 0 if passed == total else 1
        
    except KeyboardInterrupt:
        console.print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        console.print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())