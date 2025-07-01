#!/usr/bin/env python3
"""
PLANB-05: vLLM Server Startup Script with Configuration Management
Enhanced vLLM server with centralized configuration and error handling
"""

import argparse
import subprocess
import sys
import time
import os
from pathlib import Path
from typing import Optional

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from configs.vllm_settings import load_vllm_settings, get_environment_variables

class VLLMServerManager:
    """vLLM server management with configuration integration"""
    
    def __init__(self):
        """Initialize server manager with configuration"""
        try:
            self.install_settings, self.model_settings, self.test_settings = load_vllm_settings()
            # Set environment variables from configuration
            env_vars = get_environment_variables(self.install_settings)
            for key, value in env_vars.items():
                os.environ[key] = value
            print("✅ Configuration loaded successfully")
        except Exception as e:
            print(f"❌ Configuration loading failed: {e}")
            print("Please ensure .env file exists with required variables")
            sys.exit(1)
    
    def validate_model_path(self, model_path: str) -> bool:
        """Validate model path or model name"""
        # Check if it's a local path
        if Path(model_path).exists():
            print(f"✅ Local model path validated: {model_path}")
            return True
        
        # Check if it's a HuggingFace model name
        if "/" in model_path:
            print(f"✅ HuggingFace model name detected: {model_path}")
            return True
        
        print(f"❌ Invalid model path/name: {model_path}")
        return False
    
    def start_vllm_server(
        self,
        model_path: str,
        port: Optional[int] = None,
        host: Optional[str] = None,
        tensor_parallel_size: Optional[int] = None,
        gpu_memory_utilization: Optional[float] = None
    ) -> bool:
        """Start vLLM OpenAI-compatible API server with configuration"""
        
        if not self.validate_model_path(model_path):
            return False
        
        # Use configuration defaults if not specified
        port = port or self.install_settings.default_port
        host = host or self.install_settings.default_host
        tensor_parallel_size = tensor_parallel_size or self.install_settings.tensor_parallel_size
        gpu_memory_utilization = gpu_memory_utilization or self.install_settings.gpu_memory_utilization
        
        cmd = [
            "python", "-m", "vllm.entrypoints.openai.api_server",
            "--model", model_path,
            "--host", host,
            "--port", str(port),
            "--tensor-parallel-size", str(tensor_parallel_size),
            "--gpu-memory-utilization", str(gpu_memory_utilization),
            "--trust-remote-code"
        ]
        
        print(f"🚀 Starting vLLM server with configuration...")
        print(f"   Model: {model_path}")
        print(f"   Host: {host}")
        print(f"   Port: {port}")
        print(f"   Tensor Parallel Size: {tensor_parallel_size}")
        print(f"   GPU Memory Utilization: {gpu_memory_utilization}")
        print(f"   Cache Directory: {self.install_settings.hf_cache_dir}")
        print(f"   Command: {' '.join(cmd)}")
        
        try:
            # Set additional environment variables for the server process
            server_env = os.environ.copy()
            server_env.update({
                'HF_HOME': self.install_settings.hf_cache_dir,
                'TRANSFORMERS_CACHE': self.install_settings.transformers_cache,
                'HF_TOKEN': self.install_settings.hf_token
            })
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=server_env
            )
            
            print(f"✅ Server started with PID: {process.pid}")
            print(f"🌐 API will be available at: http://{host}:{port}")
            print(f"📚 API docs at: http://{host}:{port}/docs")
            print(f"💾 Models cached in: {self.install_settings.hf_cache_dir}")
            print("\n--- Server Output ---")

            # Stream and print server output in real time
            try:
                while True:
                    output = process.stdout.readline()
                    if output:
                        print(f"[vLLM] {output.rstrip()}")
                    
                    err = process.stderr.readline()
                    if err:
                        print(f"[vLLM ERROR] {err.rstrip()}")
                    
                    if output == '' and err == '' and process.poll() is not None:
                        break
                        
            except KeyboardInterrupt:
                print("\n🛑 Server stopped by user")
                process.terminate()
                process.wait(timeout=10)
                return False

            rc = process.poll()
            if rc != 0:
                print(f"❌ Server exited with code {rc}")
                return False
            return True
            
        except Exception as e:
            print(f"❌ Server failed to start: {e}")
            return False

def main():
    """Main entry point with enhanced argument parsing"""
    
    def valid_port(value):
        try:
            port = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Port must be an integer, got '{value}'")
        if not (1024 <= port <= 65535):
            raise argparse.ArgumentTypeError(f"Port must be between 1024 and 65535, got {port}")
        return port
    
    def valid_memory_util(value):
        try:
            mem_util = float(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Memory utilization must be a float, got '{value}'")
        if not (0.1 <= mem_util <= 1.0):
            raise argparse.ArgumentTypeError(f"Memory utilization must be between 0.1 and 1.0, got {mem_util}")
        return mem_util

    parser = argparse.ArgumentParser(
        description="Start vLLM server with configuration management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s facebook/opt-125m                                    # Basic usage with small model
  %(prog)s /path/to/local/model --port 8001                   # Local model on custom port
  %(prog)s mistralai/Mixtral-8x7B-Instruct-v0.1 --gpu-mem 0.8 # Large model with custom GPU memory
        """
    )
    
    parser.add_argument(
        "model_path",
        help="Path to model directory or HuggingFace model name"
    )
    parser.add_argument(
        "--port",
        type=valid_port,
        help="Server port (1024-65535, default from configuration)"
    )
    parser.add_argument(
        "--host",
        help="Server host (default from configuration)"
    )
    parser.add_argument(
        "--tensor-parallel-size",
        type=int,
        help="Tensor parallel size for multi-GPU (default from configuration)"
    )
    parser.add_argument(
        "--gpu-memory-utilization",
        "--gpu-mem",
        type=valid_memory_util,
        help="GPU memory utilization (0.1-1.0, default from configuration)"
    )
    parser.add_argument(
        "--config-info",
        action="store_true",
        help="Show current configuration and exit"
    )

    args = parser.parse_args()
    
    # Initialize server manager
    server_manager = VLLMServerManager()
    
    # Show configuration info if requested
    if args.config_info:
        print("=== Current Configuration ===")
        print(f"Default Host: {server_manager.install_settings.default_host}")
        print(f"Default Port: {server_manager.install_settings.default_port}")
        print(f"Tensor Parallel Size: {server_manager.install_settings.tensor_parallel_size}")
        print(f"GPU Memory Utilization: {server_manager.install_settings.gpu_memory_utilization}")
        print(f"HF Cache Directory: {server_manager.install_settings.hf_cache_dir}")
        print(f"Model Storage Path: {server_manager.install_settings.model_storage_path}")
        print(f"Supported Models: {len(server_manager.model_settings.supported_models)}")
        return 0
    
    # Start server with configuration
    success = server_manager.start_vllm_server(
        model_path=args.model_path,
        port=args.port,
        host=args.host,
        tensor_parallel_size=args.tensor_parallel_size,
        gpu_memory_utilization=args.gpu_memory_utilization
    )
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())