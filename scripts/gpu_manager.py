#!/usr/bin/env python3
"""
GPU Detection and Optimization Manager
Handles GPU specification detection and performance optimization

Usage:
    # Direct script execution (from project root):
    python3 scripts/gpu_manager.py {detect|optimize|status}
    
    # As module (from project root):
    python3 -m scripts.gpu_manager {detect|optimize|status}
    
    # With PYTHONPATH (recommended for production):
    PYTHONPATH=/path/to/Citadel-Alpha-LLM-Server-1 python3 scripts/gpu_manager.py {detect|optimize|status}
"""

import subprocess
import logging
import json
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import sys
import os
from datetime import datetime

# Configuration
CONFIG_FILE = "/opt/citadel/configs/gpu-config.json"

# Import GPU settings with proper fallback handling
try:
    # Try relative import first (when run as part of package)
    from ..configs.gpu_settings import GPUSettings, DetectedSpecs, GPUDefaults
except (ImportError, ValueError):
    # Fallback for direct script execution
    try:
        # Try absolute import if configs is in PYTHONPATH
        from configs.gpu_settings import GPUSettings, DetectedSpecs, GPUDefaults
    except ImportError:
        # Last resort: direct path import (only for backward compatibility)
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        configs_path = os.path.join(project_root, 'configs')
        
        if configs_path not in sys.path:
            sys.path.insert(0, configs_path)
        
        from gpu_settings import GPUSettings, DetectedSpecs, GPUDefaults


class GPUBaseManager:
    """Base class for GPU management operations with common utilities"""
    
    def __init__(self):
        """Initialize base GPU manager"""
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for GPU operations"""
        logger = logging.getLogger(self.__class__.__name__.lower())
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available and working"""
        try:
            subprocess.run(
                ["nvidia-smi", "--version"], 
                capture_output=True, check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False
    
    def _get_gpu_count(self) -> int:
        """Get number of detected GPUs"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"], 
                capture_output=True, text=True, check=True
            )
            output = result.stdout.strip()
            if not output:
                return 0
            return len(output.split('\n'))
        except subprocess.CalledProcessError:
            return 0
        except FileNotFoundError:
            self.logger.error("nvidia-smi command not found")
            return 0


class GPUDetectionManager(GPUBaseManager):
    """Manages GPU hardware detection and specification gathering"""

    def __init__(self):
        """Initialize GPU detection manager"""
        super().__init__()

    def check_gpu_hardware(self) -> bool:
        """Check if NVIDIA GPUs are present in the system"""
        try:
            result = subprocess.run(
                ["lspci"], capture_output=True, text=True, check=True
            )
            nvidia_gpus = [
                line for line in result.stdout.split('\n')
                if 'nvidia' in line.lower()
            ]
            
            if nvidia_gpus:
                self.logger.info(f"Found {len(nvidia_gpus)} NVIDIA GPU(s)")
                for gpu in nvidia_gpus:
                    self.logger.info(f"  {gpu}")
                return True
            else:
                self.logger.warning("No NVIDIA GPUs detected")
                return False
                
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to check GPU hardware: {e}")
            return False

    def detect_gpu_specs(self) -> Optional[DetectedSpecs]:
        """Detect GPU specifications using nvidia-smi"""
        if not self._check_nvidia_smi():
            self.logger.warning("nvidia-smi not available - using default values")
            return None

        try:
            # Get GPU count
            gpu_count = self._get_gpu_count()
            
            # Get GPU name
            gpu_name = self._get_gpu_name()
            
            # Get power limits
            max_power = self._get_max_power()
            
            # Get clock speeds
            max_mem_clock, max_gr_clock = self._get_max_clocks()
            
            specs = DetectedSpecs(
                gpu_count=gpu_count,
                gpu_name=gpu_name,
                max_power_watts=max_power,
                max_memory_clock_mhz=max_mem_clock,
                max_graphics_clock_mhz=max_gr_clock
            )
            
            self.logger.info("✅ GPU specifications detected successfully")
            self._log_detected_specs(specs)
            
            return specs
            
        except (subprocess.CalledProcessError, ValueError, FileNotFoundError) as e:
            self.logger.error(f"Failed to detect GPU specifications: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during GPU specification detection: {e}")
            self.logger.error("This may indicate a bug or unsupported system configuration")
            return None

    def _get_gpu_name(self) -> str:
        """Get GPU model name"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            output_lines = result.stdout.strip().split('\n')
            if not output_lines or not output_lines[0]:
                return "Unknown GPU"
            return output_lines[0]
        except subprocess.CalledProcessError:
            return "Unknown GPU"

    def _get_max_power(self) -> int:
        """Get maximum power limit"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=power.max_limit", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            power_output_lines = result.stdout.strip().split('\n')
            if not power_output_lines or not power_output_lines[0]:
                raise ValueError("Empty power output")
            power_str = power_output_lines[0].replace(' W', '')
            return int(float(power_str))
        except (subprocess.CalledProcessError, ValueError):
            return GPUDefaults.DEFAULT_MAX_POWER  # Default for RTX 4070 Ti SUPER

    def _get_max_clocks(self) -> Tuple[int, int]:
        """Get maximum memory and graphics clock speeds"""
        try:
            # Memory clock
            mem_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=clocks.max.memory", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            mem_output_lines = mem_result.stdout.strip().split('\n')
            if not mem_output_lines or not mem_output_lines[0]:
                raise ValueError("Empty memory clock output")
            mem_clock_str = mem_output_lines[0].replace(' MHz', '')
            max_mem_clock = int(float(mem_clock_str))
            
            # Graphics clock
            gr_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=clocks.max.graphics", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            gr_output_lines = gr_result.stdout.strip().split('\n')
            if not gr_output_lines or not gr_output_lines[0]:
                raise ValueError("Empty graphics clock output")
            gr_clock_str = gr_output_lines[0].replace(' MHz', '')
            max_gr_clock = int(float(gr_clock_str))
            
            return max_mem_clock, max_gr_clock
            
        except (subprocess.CalledProcessError, ValueError):
            return GPUDefaults.DEFAULT_MAX_MEMORY_CLOCK, GPUDefaults.DEFAULT_MAX_GRAPHICS_CLOCK

    def _log_detected_specs(self, specs: DetectedSpecs) -> None:
        """Log detected GPU specifications"""
        self.logger.info("Detected GPU specifications:")
        self.logger.info(f"  Count: {specs.gpu_count}")
        self.logger.info(f"  Model: {specs.gpu_name}")
        self.logger.info(f"  Max Power: {specs.max_power_watts}W")
        self.logger.info(f"  Max Memory Clock: {specs.max_memory_clock_mhz}MHz")
        self.logger.info(f"  Max Graphics Clock: {specs.max_graphics_clock_mhz}MHz")


class GPUOptimizationManager(GPUBaseManager):
    """Manages GPU performance optimization settings"""

    def __init__(self, settings: GPUSettings):
        """Initialize GPU optimization manager with settings"""
        super().__init__()
        self.settings = settings

    def apply_optimizations(self) -> bool:
        """Apply GPU performance optimizations"""
        if not self._check_nvidia_smi():
            self.logger.error("nvidia-smi not available - cannot apply optimizations")
            return False

        try:
            self.logger.info("🚀 Applying GPU optimizations for AI workloads")
            
            # Enable persistence mode
            if not self._enable_persistence_mode():
                self.logger.warning("Failed to enable persistence mode")
            
            # Set power limits
            if not self._set_power_limits():
                self.logger.warning("Failed to set power limits")
            
            # Set application clocks
            if self.settings.auto_detect_clocks and self.settings.detected_specs:
                if not self._set_application_clocks():
                    self.logger.warning("Failed to set application clocks")
            
            # Set compute mode
            if not self._set_compute_mode():
                self.logger.warning("Failed to set compute mode")
            
            self.logger.info("✅ GPU optimizations applied successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ GPU optimization failed: {e}")
            return False

    def _enable_persistence_mode(self) -> bool:
        """Enable GPU persistence mode"""
        try:
            subprocess.run(
                ["nvidia-smi", "-pm", "1"], 
                capture_output=True, check=True
            )
            self.logger.info("🔄 Persistence mode enabled")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Could not enable persistence mode: {e}")
            return False

    def _set_power_limits(self) -> bool:
        """Set power limits for all GPUs"""
        if not self.settings.detected_specs:
            self.logger.warning("No detected specs - using default power limit")
            max_power = GPUDefaults.DEFAULT_MAX_POWER
        else:
            max_power = self.settings.detected_specs.max_power_watts
        
        power_limit = int(max_power * self.settings.performance_settings.power_limit_percent / 100)
        
        try:
            gpu_count = self._get_gpu_count()
            self.logger.info(f"⚡ Setting power limit to {power_limit}W on {gpu_count} GPU(s)")
            
            success = True
            for idx in range(gpu_count):
                try:
                    subprocess.run(
                        ["nvidia-smi", "-i", str(idx), "-pl", str(power_limit)],
                        capture_output=True, check=True
                    )
                    self.logger.info(f"  GPU {idx}: Power limit set to {power_limit}W")
                except subprocess.CalledProcessError:
                    self.logger.warning(f"  GPU {idx}: Failed to set power limit")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.warning(f"Failed to set power limits: {e}")
            return False

    def _set_application_clocks(self) -> bool:
        """Set application clocks for all GPUs"""
        if not self.settings.detected_specs:
            return False
        
        mem_clock = self.settings.detected_specs.max_memory_clock_mhz
        gr_clock = self.settings.detected_specs.max_graphics_clock_mhz
        
        try:
            gpu_count = self._get_gpu_count()
            self.logger.info(f"🔧 Setting clocks to {mem_clock},{gr_clock} MHz on {gpu_count} GPU(s)")
            
            success = True
            for idx in range(gpu_count):
                try:
                    subprocess.run(
                        ["nvidia-smi", "-i", str(idx), "-ac", f"{mem_clock},{gr_clock}"],
                        capture_output=True, check=True
                    )
                    self.logger.info(f"  GPU {idx}: Application clocks set")
                except subprocess.CalledProcessError:
                    self.logger.warning(f"  GPU {idx}: Failed to set application clocks")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.warning(f"Failed to set application clocks: {e}")
            return False

    def _set_compute_mode(self) -> bool:
        """Set compute mode for all GPUs"""
        compute_modes = {
            "DEFAULT": 0,
            "EXCLUSIVE_THREAD": 1,
            "PROHIBITED": 2,
            "EXCLUSIVE_PROCESS": 3
        }
        
        mode_name = self.settings.performance_settings.compute_mode
        mode_num = compute_modes.get(mode_name, 3)
        
        try:
            subprocess.run(
                ["nvidia-smi", "-c", str(mode_num)],
                capture_output=True, check=True
            )
            self.logger.info(f"🎯 Compute mode set to {mode_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.warning(f"Failed to set compute mode: {e}")
            return False

    def get_current_status(self) -> Dict[str, Any]:
        """Get current GPU status and performance metrics"""
        if not self._check_nvidia_smi():
            return {"error": "nvidia-smi not available"}
        
        try:
            # Get basic status
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,driver_version,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw,power.limit",
                 "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            
            status = {
                "timestamp": datetime.now().isoformat(),
                "gpu_data": result.stdout.strip(),
                "raw_output": subprocess.run(["nvidia-smi"], capture_output=True, text=True).stdout
            }
            
            return status
            
        except subprocess.CalledProcessError as e:
            return {"error": f"Failed to get GPU status: {e}"}


def main():
    """CLI interface for GPU manager"""
    if len(sys.argv) < 2:
        print("Usage: gpu_manager.py {detect|optimize|status}")
        sys.exit(1)
    
    action = sys.argv[1]
    
    if action == "detect":
        detector = GPUDetectionManager()
        if detector.check_gpu_hardware():
            specs = detector.detect_gpu_specs()
            if specs:
                print(f"GPU Count: {specs.gpu_count}")
                print(f"GPU Name: {specs.gpu_name}")
                print(f"Max Power: {specs.max_power_watts}W")
                print(f"Max Memory Clock: {specs.max_memory_clock_mhz}MHz")
                print(f"Max Graphics Clock: {specs.max_graphics_clock_mhz}MHz")
        
    elif action == "optimize":
        # Load settings and apply optimizations
        try:
            settings = GPUSettings.load_from_file(Path(CONFIG_FILE))
            optimizer = GPUOptimizationManager(settings)
            success = optimizer.apply_optimizations()
            print(f"Optimization {'successful' if success else 'failed'}")
        except Exception as e:
            print(f"Failed to load settings: {e}")
        
    elif action == "status":
        # Show current GPU status
        try:
            settings = GPUSettings.load_from_file(Path(CONFIG_FILE))
            optimizer = GPUOptimizationManager(settings)
            status = optimizer.get_current_status()
            print(json.dumps(status, indent=2))
        except Exception as e:
            print(f"Failed to get status: {e}")
        
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)


if __name__ == "__main__":
    main()