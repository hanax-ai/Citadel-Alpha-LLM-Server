#!/usr/bin/env python3
"""
GPU Detection and Optimization Manager
Handles GPU specification detection and performance optimization
"""

import subprocess
import logging
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sys
import os

# Add configs to path for imports
sys.path.append(str(Path(__file__).parent.parent / "configs"))
from gpu_settings import GPUSettings, DetectedSpecs


class GPUDetectionManager:
    """Manages GPU hardware detection and specification gathering"""

    def __init__(self):
        """Initialize GPU detection manager"""
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for GPU operations"""
        logger = logging.getLogger("gpu_detection")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

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
            
        except Exception as e:
            self.logger.error(f"Failed to detect GPU specifications: {e}")
            return None

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
            return len(result.stdout.strip().split('\n'))
        except subprocess.CalledProcessError:
            return 0

    def _get_gpu_name(self) -> str:
        """Get GPU model name"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip().split('\n')[0]
        except subprocess.CalledProcessError:
            return "Unknown GPU"

    def _get_max_power(self) -> int:
        """Get maximum power limit"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=power.max_limit", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            power_str = result.stdout.strip().split('\n')[0].replace(' W', '')
            return int(float(power_str))
        except (subprocess.CalledProcessError, ValueError):
            return 320  # Default for RTX 4070 Ti SUPER

    def _get_max_clocks(self) -> Tuple[int, int]:
        """Get maximum memory and graphics clock speeds"""
        try:
            # Memory clock
            mem_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=clocks.max.memory", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            mem_clock_str = mem_result.stdout.strip().split('\n')[0].replace(' MHz', '')
            max_mem_clock = int(float(mem_clock_str))
            
            # Graphics clock
            gr_result = subprocess.run(
                ["nvidia-smi", "--query-gpu=clocks.max.graphics", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, check=True
            )
            gr_clock_str = gr_result.stdout.strip().split('\n')[0].replace(' MHz', '')
            max_gr_clock = int(float(gr_clock_str))
            
            return max_mem_clock, max_gr_clock
            
        except (subprocess.CalledProcessError, ValueError):
            return 9501, 2610  # Defaults for RTX 4070 Ti SUPER

    def _log_detected_specs(self, specs: DetectedSpecs) -> None:
        """Log detected GPU specifications"""
        self.logger.info("Detected GPU specifications:")
        self.logger.info(f"  Count: {specs.gpu_count}")
        self.logger.info(f"  Model: {specs.gpu_name}")
        self.logger.info(f"  Max Power: {specs.max_power_watts}W")
        self.logger.info(f"  Max Memory Clock: {specs.max_memory_clock_mhz}MHz")
        self.logger.info(f"  Max Graphics Clock: {specs.max_graphics_clock_mhz}MHz")


class GPUOptimizationManager:
    """Manages GPU performance optimization settings"""

    def __init__(self, settings: GPUSettings):
        """Initialize GPU optimization manager with settings"""
        self.settings = settings
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for GPU optimization"""
        logger = logging.getLogger("gpu_optimization")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger

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

    def _check_nvidia_smi(self) -> bool:
        """Check if nvidia-smi is available"""
        try:
            subprocess.run(
                ["nvidia-smi"], capture_output=True, check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
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
            max_power = 320
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

    def _get_gpu_count(self) -> int:
        """Get number of GPUs"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "-L"], 
                capture_output=True, text=True, check=True
            )
            return len(result.stdout.strip().split('\n'))
        except subprocess.CalledProcessError:
            return 1

    def get_current_status(self) -> Dict[str, any]:
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
                "timestamp": subprocess.run(["date"], capture_output=True, text=True).stdout.strip(),
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
            settings = GPUSettings.load_from_file(Path("/opt/citadel/configs/gpu-config.json"))
            optimizer = GPUOptimizationManager(settings)
            success = optimizer.apply_optimizations()
            print(f"Optimization {'successful' if success else 'failed'}")
        except Exception as e:
            print(f"Failed to load settings: {e}")
        
    elif action == "status":
        # Show current GPU status
        try:
            settings = GPUSettings.load_from_file(Path("/opt/citadel/configs/gpu-config.json"))
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