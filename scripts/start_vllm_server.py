#!/usr/bin/env python3
"""
PLANB-05: vLLM Server Startup Script
Simple vLLM server for testing and development
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

def start_vllm_server(model_path, port=8000, host="0.0.0.0"):
    """Start vLLM OpenAI-compatible API server"""
    
    if not Path(model_path).exists():
        print(f"❌ Model path not found: {model_path}")
        return False
    
    cmd = [
        "python", "-m", "vllm.entrypoints.openai.api_server",
        "--model", model_path,
        "--host", host,
        "--port", str(port),
        "--tensor-parallel-size", "1",
        "--gpu-memory-utilization", "0.7",
        "--trust-remote-code"
    ]
    
    print(f"🚀 Starting vLLM server...")
    print(f"   Model: {model_path}")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Command: {' '.join(cmd)}")
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print(f"✅ Server started with PID: {process.pid}")
        print(f"🌐 API will be available at: http://{host}:{port}")
        print(f"📚 API docs at: http://localhost:{port}/docs")

        # Stream and print server output in real time
        try:
            while True:
                output = process.stdout.readline()
                if output:
                    print(f"[vLLM STDOUT] {output}", end="")
                err = process.stderr.readline()
                if err:
                    print(f"[vLLM STDERR] {err}", end="")
                if output == '' and err == '' and process.poll() is not None:
                    break
        except KeyboardInterrupt:
            print("\n🛑 Server stopped by user")
            process.terminate()
            return False

        rc = process.poll()
        if rc != 0:
            print(f"❌ Server exited with code {rc}")
            return False
        return True
    except Exception as e:
        print(f"❌ Server failed: {e}")
        return False

def main():
    def valid_port(value):
        try:
            port = int(value)
        except ValueError:
            raise argparse.ArgumentTypeError(f"Port must be an integer, got '{value}'")
        if not (1 <= port <= 65535):
            raise argparse.ArgumentTypeError(f"Port must be between 1 and 65535, got {port}")
        return port

    parser = argparse.ArgumentParser(description="Start vLLM server")
    parser.add_argument("model_path", help="Path to model directory")
    parser.add_argument("--port", type=valid_port, default=8000, help="Server port (1-65535)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")

    args = parser.parse_args()

    return start_vllm_server(args.model_path, args.port, args.host)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)