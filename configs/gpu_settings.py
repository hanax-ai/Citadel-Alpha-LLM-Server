"""
GPU Configuration Settings for NVIDIA Driver Setup
Centralized configuration management for PLANB-03 implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path


# Default GPU hardware constants
class GPUDefaults:
    """Default GPU hardware values for RTX 4070 Ti SUPER"""
    DEFAULT_MAX_POWER = 320  # Watts
    DEFAULT_MAX_MEMORY_CLOCK = 9501  # MHz
    DEFAULT_MAX_GRAPHICS_CLOCK = 2610  # MHz


@dataclass
class GPUPerformanceSettings:
    """GPU performance optimization settings"""
    power_limit_percent: int = 95
    memory_clock_offset: int = 0
    graphics_clock_offset: int = 0
    compute_mode: str = "EXCLUSIVE_PROCESS"


@dataclass
class RepositorySettings:
    """NVIDIA repository configuration"""
    ubuntu_version: str = "24.04"
    architecture: str = "x86_64"


@dataclass
class DetectedSpecs:
    """Runtime-detected GPU specifications"""
    gpu_count: int = 0
    gpu_name: str = ""
    max_power_watts: int = GPUDefaults.DEFAULT_MAX_POWER
    max_memory_clock_mhz: int = GPUDefaults.DEFAULT_MAX_MEMORY_CLOCK
    max_graphics_clock_mhz: int = GPUDefaults.DEFAULT_MAX_GRAPHICS_CLOCK


@dataclass
class GPUSettings:
    """Complete GPU configuration settings"""
    driver_version: str = "570"
    cuda_version: str = "12-4"
    target_gpus: int = 2
    gpu_model: str = "RTX 4070 Ti SUPER"
    auto_detect_clocks: bool = True
    performance_settings: GPUPerformanceSettings = field(default_factory=GPUPerformanceSettings)
    repository: RepositorySettings = field(default_factory=RepositorySettings)
    detected_specs: Optional[DetectedSpecs] = None

    @classmethod
    def load_from_file(cls, config_path: Path) -> "GPUSettings":
        """Load GPU settings from JSON configuration file"""
        if not config_path.exists():
            raise FileNotFoundError(f"GPU configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file {config_path}: {e}")
        
        # Validate required fields and types
        if not isinstance(data, dict):
            raise ValueError("Configuration file must contain a JSON object")
        
        # Validate driver_version
        driver_version = data.get("driver_version", "570")
        if not isinstance(driver_version, str) or not driver_version:
            raise ValueError("driver_version must be a non-empty string")
        
        # Validate cuda_version
        cuda_version = data.get("cuda_version", "12-4")
        if not isinstance(cuda_version, str) or not cuda_version:
            raise ValueError("cuda_version must be a non-empty string")
        
        # Validate target_gpus
        target_gpus = data.get("target_gpus", 2)
        if not isinstance(target_gpus, int) or target_gpus < 1 or target_gpus > 8:
            raise ValueError("target_gpus must be an integer between 1 and 8")
        
        # Validate gpu_model
        gpu_model = data.get("gpu_model", "RTX 4070 Ti SUPER")
        if not isinstance(gpu_model, str) or not gpu_model:
            raise ValueError("gpu_model must be a non-empty string")
        
        # Validate auto_detect_clocks
        auto_detect_clocks = data.get("auto_detect_clocks", True)
        if not isinstance(auto_detect_clocks, bool):
            raise ValueError("auto_detect_clocks must be a boolean")
        
        # Validate performance_settings
        perf_data = data.get("performance_settings", {})
        if not isinstance(perf_data, dict):
            raise ValueError("performance_settings must be an object")
        
        # Validate performance settings fields
        power_limit = perf_data.get("power_limit_percent", 95)
        if not isinstance(power_limit, int) or power_limit < 50 or power_limit > 120:
            raise ValueError("power_limit_percent must be an integer between 50 and 120")
        
        memory_offset = perf_data.get("memory_clock_offset", 0)
        if not isinstance(memory_offset, int) or memory_offset < -2000 or memory_offset > 2000:
            raise ValueError("memory_clock_offset must be an integer between -2000 and 2000")
        
        graphics_offset = perf_data.get("graphics_clock_offset", 0)
        if not isinstance(graphics_offset, int) or graphics_offset < -500 or graphics_offset > 500:
            raise ValueError("graphics_clock_offset must be an integer between -500 and 500")
        
        compute_mode = perf_data.get("compute_mode", "EXCLUSIVE_PROCESS")
        valid_compute_modes = ["DEFAULT", "EXCLUSIVE_THREAD", "EXCLUSIVE_PROCESS", "PROHIBITED"]
        if not isinstance(compute_mode, str) or compute_mode not in valid_compute_modes:
            raise ValueError(f"compute_mode must be one of: {', '.join(valid_compute_modes)}")
        
        # Validate repository settings
        repo_data = data.get("repository", {})
        if not isinstance(repo_data, dict):
            raise ValueError("repository must be an object")
        
        ubuntu_version = repo_data.get("ubuntu_version", "24.04")
        if not isinstance(ubuntu_version, str) or not ubuntu_version:
            raise ValueError("ubuntu_version must be a non-empty string")
        
        architecture = repo_data.get("architecture", "x86_64")
        valid_architectures = ["x86_64", "aarch64", "ppc64le"]
        if not isinstance(architecture, str) or architecture not in valid_architectures:
            raise ValueError(f"architecture must be one of: {', '.join(valid_architectures)}")
        
        # Validate detected_specs if present
        detected_specs = None
        if "detected_specs" in data:
            specs_data = data["detected_specs"]
            if not isinstance(specs_data, dict):
                raise ValueError("detected_specs must be an object")
            
            gpu_count = specs_data.get("gpu_count", 0)
            if not isinstance(gpu_count, int) or gpu_count < 0:
                raise ValueError("gpu_count must be a non-negative integer")
            
            gpu_name = specs_data.get("gpu_name", "")
            if not isinstance(gpu_name, str):
                raise ValueError("gpu_name must be a string")
            
            max_power = specs_data.get("max_power_watts", GPUDefaults.DEFAULT_MAX_POWER)
            if not isinstance(max_power, int) or max_power < 50 or max_power > 1000:
                raise ValueError("max_power_watts must be an integer between 50 and 1000")
            
            max_memory_clock = specs_data.get("max_memory_clock_mhz", GPUDefaults.DEFAULT_MAX_MEMORY_CLOCK)
            if not isinstance(max_memory_clock, int) or max_memory_clock < 1000 or max_memory_clock > 50000:
                raise ValueError("max_memory_clock_mhz must be an integer between 1000 and 50000")
            
            max_graphics_clock = specs_data.get("max_graphics_clock_mhz", GPUDefaults.DEFAULT_MAX_GRAPHICS_CLOCK)
            if not isinstance(max_graphics_clock, int) or max_graphics_clock < 500 or max_graphics_clock > 5000:
                raise ValueError("max_graphics_clock_mhz must be an integer between 500 and 5000")
            
            # Extract only the fields expected by DetectedSpecs to avoid errors from extra fields
            detected_specs_kwargs = {
                "gpu_count": gpu_count,
                "gpu_name": gpu_name,
                "max_power_watts": max_power,
                "max_memory_clock_mhz": max_memory_clock,
                "max_graphics_clock_mhz": max_graphics_clock
            }
            detected_specs = DetectedSpecs(**detected_specs_kwargs)
        
        return cls(
            driver_version=driver_version,
            cuda_version=cuda_version,
            target_gpus=target_gpus,
            gpu_model=gpu_model,
            auto_detect_clocks=auto_detect_clocks,
            performance_settings=GPUPerformanceSettings(**perf_data),
            repository=RepositorySettings(**repo_data),
            detected_specs=detected_specs
        )

    def save_to_file(self, config_path: Path) -> None:
        """Save GPU settings to JSON configuration file"""
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "driver_version": self.driver_version,
            "cuda_version": self.cuda_version,
            "target_gpus": self.target_gpus,
            "gpu_model": self.gpu_model,
            "auto_detect_clocks": self.auto_detect_clocks,
            "performance_settings": {
                "power_limit_percent": self.performance_settings.power_limit_percent,
                "memory_clock_offset": self.performance_settings.memory_clock_offset,
                "graphics_clock_offset": self.performance_settings.graphics_clock_offset,
                "compute_mode": self.performance_settings.compute_mode
            },
            "repository": {
                "ubuntu_version": self.repository.ubuntu_version,
                "architecture": self.repository.architecture
            }
        }
        
        if self.detected_specs:
            data["detected_specs"] = {
                "gpu_count": self.detected_specs.gpu_count,
                "gpu_name": self.detected_specs.gpu_name,
                "max_power_watts": self.detected_specs.max_power_watts,
                "max_memory_clock_mhz": self.detected_specs.max_memory_clock_mhz,
                "max_graphics_clock_mhz": self.detected_specs.max_graphics_clock_mhz
            }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_repository_url(self) -> str:
        """Generate NVIDIA repository URL based on settings"""
        # Convert Ubuntu version format from "24.04" to "2404" for URL
        ubuntu_version_url = self.repository.ubuntu_version.replace(".", "")
        return f"https://developer.download.nvidia.com/compute/cuda/repos/ubuntu{ubuntu_version_url}/{self.repository.architecture}/cuda-keyring_1.1-1_all.deb"


# Default configuration paths
DEFAULT_CONFIG_PATH = Path("/opt/citadel/configs/gpu-config.json")
BACKUP_DIR_BASE = Path("/opt/citadel/backups")
SCRIPTS_DIR = Path("/opt/citadel/scripts")