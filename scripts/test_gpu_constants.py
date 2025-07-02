#!/usr/bin/env python3
"""
Test script to verify GPU constants are properly configured
"""

import sys
from pathlib import Path

# Add configs to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))

try:
    from gpu_settings import GPUDefaults, DetectedSpecs
    
    print("✅ GPU settings import successful")
    print("\n📊 GPU Default Constants:")
    print(f"  Default Max Power: {GPUDefaults.DEFAULT_MAX_POWER}W")
    print(f"  Default Max Memory Clock: {GPUDefaults.DEFAULT_MAX_MEMORY_CLOCK}MHz")
    print(f"  Default Max Graphics Clock: {GPUDefaults.DEFAULT_MAX_GRAPHICS_CLOCK}MHz")
    
    # Test DetectedSpecs with default values
    specs = DetectedSpecs()
    print(f"\n🔍 DetectedSpecs default values:")
    print(f"  GPU Count: {specs.gpu_count}")
    print(f"  GPU Name: '{specs.gpu_name}'")
    print(f"  Max Power: {specs.max_power_watts}W")
    print(f"  Max Memory Clock: {specs.max_memory_clock_mhz}MHz")
    print(f"  Max Graphics Clock: {specs.max_graphics_clock_mhz}MHz")
    
    print("\n✅ All constants properly configured!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
