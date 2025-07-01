"""
GPU Configuration Settings for NVIDIA Driver Setup
Centralized configuration management for PLANB-03 implementation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path


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
    ubuntu_version: str = "2404"
    architecture: str = "x86_64"


@dataclass
class DetectedSpecs:
    """Runtime-detected GPU specifications"""
    gpu_count: int = 0
    gpu_name: str = ""
    max_power_watts: int = 320
    max_memory_clock_mhz: int = 9501
    max_graphics_clock_mhz: int = 2610


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
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        return cls(
            driver_version=data.get("driver_version", "570"),
            cuda_version=data.get("cuda_version", "12-4"),
            target_gpus=data.get("target_gpus", 2),
            gpu_model=data.get("gpu_model", "RTX 4070 Ti SUPER"),
            auto_detect_clocks=data.get("auto_detect_clocks", True),
            performance_settings=GPUPerformanceSettings(**data.get("performance_settings", {})),
            repository=RepositorySettings(**data.get("repository", {})),
            detected_specs=DetectedSpecs(**data["detected_specs"]) if "detected_specs" in data else None
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
        return f"https://developer.download.nvidia.com/compute/cuda/repos/ubuntu{self.repository.ubuntu_version}/{self.repository.architecture}/cuda-keyring_1.1-1_all.deb"


# Default configuration paths
DEFAULT_CONFIG_PATH = Path("/opt/citadel/configs/gpu-config.json")
BACKUP_DIR_BASE = Path("/opt/citadel/backups")
SCRIPTS_DIR = Path("/opt/citadel/scripts")