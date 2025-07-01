#!/usr/bin/env python3
"""
PLANB-05: vLLM Installation Test Suite
Comprehensive testing and validation of vLLM installation
"""

import os
import sys
import time
import torch
from rich.console import Console
from rich.progress import Progress

console = Console()

def test_vllm_import():
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

def test_cuda_availability():
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

def test_dependencies():
    """Test key dependencies"""
    dependencies = [
        ('transformers', '4.36.0'),
        ('tokenizers', '0.15.0'),
        ('fastapi', '0.104.0'),
        ('uvicorn', '0.24.0'),
        ('pydantic', '2.5.0'),
        ('huggingface_hub', '0.19.0')
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

def test_vllm_engine():
    """Test vLLM engine initialization with a small model"""
    try:
        from vllm import LLM, SamplingParams
        
        console.print("🧪 Testing vLLM engine with small model...")
        
        # Use a small model for testing, configurable via environment variable
        model_name = os.environ.get("VLLM_TEST_MODEL", "facebook/opt-125m")
        
        # Initialize LLM
        llm = LLM(
            model=model_name,
            tensor_parallel_size=1,
            gpu_memory_utilization=0.3,
            download_dir="/tmp/vllm_test_cache"
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

def test_huggingface_auth():
    """Test Hugging Face authentication"""
    try:
        from huggingface_hub import whoami
        
        user_info = whoami()
        console.print(f"✅ HF Authentication: {user_info['name']}")
        return True
    except Exception as e:
        console.print(f"❌ HF Authentication failed: {e}")
        return False

def test_performance():
    """Basic performance test"""
    try:
        import time
        from vllm import LLM, SamplingParams
        
        console.print("🏃 Running performance test...")
        
        llm = LLM(
            model="facebook/opt-125m",
            tensor_parallel_size=1,
            gpu_memory_utilization=0.3
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
        
        return True
        
    except Exception as e:
        console.print(f"❌ Performance test failed: {e}")
        return False

def main():
    console.print("🚀 PLANB-05 vLLM Installation Test Suite")
    console.print("=" * 50)
    
    tests = [
        ("vLLM Import", test_vllm_import),
        ("CUDA Availability", test_cuda_availability),
        ("Dependencies", test_dependencies),
        ("Hugging Face Auth", test_huggingface_auth),
        ("vLLM Engine", test_vllm_engine),
        ("Performance", test_performance)
    ]
    
    results = []
    for test_name, test_func in tests:
        console.print(f"\n📋 Running {test_name} test...")
        result = test_func()
        results.append((test_name, result))
    
    console.print(f"\n📊 Test Results Summary:")
    console.print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        console.print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    console.print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        console.print("🎉 All tests passed! vLLM is ready for use.")
        return 0
    else:
        console.print("⚠️ Some tests failed. Check installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())