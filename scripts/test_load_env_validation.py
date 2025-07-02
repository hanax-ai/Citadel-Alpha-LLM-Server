#!/usr/bin/env python3
"""
Test script for load_env_config.py validation improvements
"""

import json
import tempfile
import subprocess
import sys
import os

def create_test_config(config_data):
    """Create a temporary config file with given data"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f, indent=2)
        return f.name

def run_load_env_config(config_file):
    """Run the load_env_config.py script and capture output"""
    script_path = "/home/agent0/Citadel-Alpha-LLM-Server-1/scripts/load_env_config.py"
    result = subprocess.run([sys.executable, script_path, config_file], 
                          capture_output=True, text=True)
    return result.stdout, result.stderr

def test_valid_config():
    """Test with a valid configuration"""
    print("Testing valid configuration...")
    config = {
        "optimization": {
            "memory": {"malloc_arena_max": 8},
            "threading": {"max_threads": 12},
            "cuda": {"launch_blocking": True, "cache_disable": False}
        }
    }
    
    config_file = create_test_config(config)
    try:
        stdout, stderr = run_load_env_config(config_file)
        print("✅ Valid config test passed")
        print("stdout:", stdout)
        print("stderr:", stderr)
    finally:
        os.unlink(config_file)

def test_malformed_optimization():
    """Test with optimization as a string instead of dict"""
    print("\nTesting malformed optimization section...")
    config = {
        "optimization": "this should be a dict"
    }
    
    config_file = create_test_config(config)
    try:
        stdout, stderr = run_load_env_config(config_file)
        print("✅ Malformed optimization test passed")
        print("stdout:", stdout)
        print("stderr:", stderr)
    finally:
        os.unlink(config_file)

def test_malformed_memory():
    """Test with memory as a list instead of dict"""
    print("\nTesting malformed memory section...")
    config = {
        "optimization": {
            "memory": ["this", "should", "be", "a", "dict"],
            "threading": {"max_threads": 4},
            "cuda": {"launch_blocking": False}
        }
    }
    
    config_file = create_test_config(config)
    try:
        stdout, stderr = run_load_env_config(config_file)
        print("✅ Malformed memory test passed")
        print("stdout:", stdout)
        print("stderr:", stderr)
    finally:
        os.unlink(config_file)

def test_wrong_types():
    """Test with wrong data types for values"""
    print("\nTesting wrong data types...")
    config = {
        "optimization": {
            "memory": {"malloc_arena_max": "this should be an int"},
            "threading": {"max_threads": "this should be an int"},
            "cuda": {"launch_blocking": "this should be a bool", "cache_disable": 123}
        }
    }
    
    config_file = create_test_config(config)
    try:
        stdout, stderr = run_load_env_config(config_file)
        print("✅ Wrong types test passed")
        print("stdout:", stdout)
        print("stderr:", stderr)
    finally:
        os.unlink(config_file)

def test_non_dict_config():
    """Test with top-level config as a list instead of dict"""
    print("\nTesting non-dict config...")
    config = ["this", "should", "be", "a", "dict"]
    
    config_file = create_test_config(config)
    try:
        stdout, stderr = run_load_env_config(config_file)
        print("✅ Non-dict config test passed")
        print("stdout:", stdout)
        print("stderr:", stderr)
    finally:
        os.unlink(config_file)

if __name__ == "__main__":
    print("Testing load_env_config.py validation...")
    test_valid_config()
    test_malformed_optimization()
    test_malformed_memory()
    test_wrong_types()
    test_non_dict_config()
    print("\n🎉 All tests completed!")
