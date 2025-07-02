#!/usr/bin/env python3
"""
Test script for gpu_settings.py DetectedSpecs fix
Tests that extra fields in specs_data are properly handled
"""

import json
import tempfile
from pathlib import Path
import sys
import os

# Add the configs directory to Python path
sys.path.insert(0, '/home/agent0/Citadel-Alpha-LLM-Server-1/configs')

from gpu_settings import GPUSettings

def test_detected_specs_with_extra_fields():
    """Test that DetectedSpecs handles extra fields gracefully"""
    
    # Create a test configuration with extra fields in detected_specs
    test_config = {
        "driver_version": "570",
        "cuda_version": "12-4",
        "target_gpus": 2,
        "gpu_model": "RTX 4070 Ti SUPER",
        "auto_detect_clocks": True,
        "performance_settings": {
            "power_limit_percent": 95,
            "memory_clock_offset": 0,
            "graphics_clock_offset": 0,
            "compute_mode": "EXCLUSIVE_PROCESS"
        },
        "repository": {
            "ubuntu_version": "24.04",
            "architecture": "x86_64"
        },
        "detected_specs": {
            "gpu_count": 2,
            "gpu_name": "NVIDIA GeForce RTX 4070 Ti SUPER",
            "max_power_watts": 320,
            "max_memory_clock_mhz": 9501,
            "max_graphics_clock_mhz": 2610,
            # Extra fields that should be ignored
            "extra_field_1": "should_be_ignored",
            "extra_field_2": 12345,
            "extra_field_3": {"nested": "object"},
            "extra_field_4": [1, 2, 3]
        }
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        temp_config_path = Path(f.name)
    
    try:
        print("Testing DetectedSpecs with extra fields...")
        
        # This should work without throwing an error
        gpu_settings = GPUSettings.load_from_file(temp_config_path)
        
        print("✅ GPUSettings loaded successfully")
        
        # Verify that the detected_specs fields are correctly set
        assert gpu_settings.detected_specs is not None
        assert gpu_settings.detected_specs.gpu_count == 2
        assert gpu_settings.detected_specs.gpu_name == "NVIDIA GeForce RTX 4070 Ti SUPER"
        assert gpu_settings.detected_specs.max_power_watts == 320
        assert gpu_settings.detected_specs.max_memory_clock_mhz == 9501
        assert gpu_settings.detected_specs.max_graphics_clock_mhz == 2610
        
        print("✅ All DetectedSpecs fields are correctly set")
        
        # Verify that extra fields don't appear in the DetectedSpecs object
        specs_dict = gpu_settings.detected_specs.__dict__
        extra_fields = ["extra_field_1", "extra_field_2", "extra_field_3", "extra_field_4"]
        for field in extra_fields:
            assert field not in specs_dict, f"Extra field {field} should not be in DetectedSpecs"
        
        print("✅ Extra fields correctly excluded from DetectedSpecs")
        
        # Test saving and reloading to ensure consistency
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            save_path = Path(f.name)
        
        gpu_settings.save_to_file(save_path)
        gpu_settings_reloaded = GPUSettings.load_from_file(save_path)
        
        assert gpu_settings_reloaded.detected_specs.gpu_count == gpu_settings.detected_specs.gpu_count
        assert gpu_settings_reloaded.detected_specs.gpu_name == gpu_settings.detected_specs.gpu_name
        
        print("✅ Save/reload cycle works correctly")
        
        # Clean up
        os.unlink(save_path)
        
        print("\n🎉 All tests passed! Extra fields are properly handled.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        # Clean up temp file
        os.unlink(temp_config_path)

def test_detected_specs_without_extra_fields():
    """Test that normal operation still works without extra fields"""
    
    test_config = {
        "driver_version": "570",
        "cuda_version": "12-4",
        "target_gpus": 1,
        "gpu_model": "RTX 4070",
        "auto_detect_clocks": False,
        "performance_settings": {
            "power_limit_percent": 90,
            "memory_clock_offset": 100,
            "graphics_clock_offset": 50,
            "compute_mode": "DEFAULT"
        },
        "repository": {
            "ubuntu_version": "24.04",
            "architecture": "x86_64"
        },
        "detected_specs": {
            "gpu_count": 1,
            "gpu_name": "NVIDIA GeForce RTX 4070",
            "max_power_watts": 280,
            "max_memory_clock_mhz": 8000,
            "max_graphics_clock_mhz": 2400
        }
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        temp_config_path = Path(f.name)
    
    try:
        print("\nTesting DetectedSpecs without extra fields...")
        
        gpu_settings = GPUSettings.load_from_file(temp_config_path)
        
        print("✅ GPUSettings loaded successfully")
        
        assert gpu_settings.detected_specs is not None
        assert gpu_settings.detected_specs.gpu_count == 1
        assert gpu_settings.detected_specs.gpu_name == "NVIDIA GeForce RTX 4070"
        
        print("✅ Normal operation works correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise
    finally:
        os.unlink(temp_config_path)

if __name__ == "__main__":
    test_detected_specs_with_extra_fields()
    test_detected_specs_without_extra_fields()
    print("\n🎉 All tests completed successfully!")
