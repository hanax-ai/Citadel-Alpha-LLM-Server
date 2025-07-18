#!/usr/bin/env python3
"""
PLANB-05: vLLM Client Test Script
Test vLLM server with OpenAI-compatible client
"""


import sys
import requests
import json
import time
import argparse
from rich.console import Console

console = Console()

def test_server_health(base_url):
    """Test server health endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            console.print("✅ Server health check: PASSED")
            return True
        else:
            console.print(f"❌ Server health check failed: HTTP {response.status_code}")
            return False
    except Exception as e:
        console.print(f"❌ Server health check failed: {e}")
        return False

def test_completion(base_url, model_name="test"):
    """Test completion endpoint"""
    try:
        url = f"{base_url}/v1/chat/completions"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": "Hello! Please respond with a short greeting."}
            ],
            "max_tokens": 50,
            "temperature": 0.7
        }
        
        console.print("🧪 Testing completion endpoint...")
        start_time = time.time()
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            console.print(f"✅ Completion test: PASSED ({response_time:.2f}s)")
            console.print(f"   Response: {content}")
            return True
        else:
            console.print(f"❌ Completion test failed: HTTP {response.status_code}")
            console.print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        console.print(f"❌ Completion test failed: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test vLLM server")
    parser.add_argument("--url", default="http://localhost:8000", help="Server URL")
    parser.add_argument("--model", default="test", help="Model name")
    
    args = parser.parse_args()
    
    console.print("🧪 vLLM Server Test")
    console.print("=" * 30)
    
    tests = [
        ("Health Check", lambda: test_server_health(args.url)),
        ("Completion", lambda: test_completion(args.url, args.model))
    ]
    
    passed = 0
    for test_name, test_func in tests:
        console.print(f"\n📋 Running {test_name}...")
        if test_func():
            passed += 1
    
    console.print(f"\n📊 Results: {passed}/{len(tests)} tests passed")
    return passed == len(tests)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)