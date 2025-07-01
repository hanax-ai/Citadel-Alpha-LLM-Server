#!/usr/bin/env python3 
"""
PLANB-05: vLLM Configuration Management
Pydantic-based settings for centralized configuration management
"""

from typing import Optional, Dict, List
from pathlib import Path
from pydantic import BaseSettings, Field, validator
import os


class VLLMInstallationSettings(BaseSettings):
    """vLLM Installation Configuration Settings"""
    
    # Environment Configuration
    dev_env_path: str = Field(
        default="/opt/citadel/dev-env",
        description="Path to Python virtual environment"
    )
    
    # Hugging Face Configuration
    hf_token: str = Field(
        ...,
        description="Hugging Face authentication token"
    )
    hf_cache_dir: str = Field(
        default="/mnt/citadel-models/cache",
        description="Hugging Face model cache directory"
    )
    transformers_cache: str = Field(
        default="/mnt/citadel-models/cache/transformers",
        description="Transformers library cache directory"
    )
    
    # Compilation Configuration
    max_jobs: int = Field(
        default=8,
        description="Maximum parallel compilation jobs"
    )
    cuda_arch: str = Field(
        default="8.9",
        description="CUDA architecture for RTX 4070 Ti SUPER"
    )
    gcc_version: str = Field(
        default="gcc-11",
        description="GCC compiler version"
    )
    
    # vLLM Configuration
    gpu_memory_utilization: float = Field(
        default=0.7,
        ge=0.1,
        le=1.0,
        description="GPU memory utilization ratio"
    )
    tensor_parallel_size: int = Field(
        default=1,
        ge=1,
        description="Tensor parallel size for multi-GPU"
    )
    
    # Server Configuration
    default_host: str = Field(
        default="0.0.0.0",
        description="Default server host"
    )
    default_port: int = Field(
        default=8000,
        ge=1024,
        le=65535,
        description="Default server port"
    )
    
    # Storage Configuration
    model_storage_path: str = Field(
        default="/mnt/citadel-models",
        description="Model storage directory"
    )
    
    @validator("dev_env_path", "hf_cache_dir", "model_storage_path")
    def validate_paths_exist(cls, v):
        """Validate that critical paths exist"""
        path = Path(v)
        if not path.exists():
            # Create directory if it doesn't exist
            path.mkdir(parents=True, exist_ok=True)
        return str(path.absolute())
    
    @validator("hf_token")
    def validate_hf_token(cls, v):
        """Validate HF token format"""
        if not v.startswith("hf_"):
            raise ValueError("Hugging Face token must start with 'hf_'")
        if len(v) < 20:
            raise ValueError("Hugging Face token appears to be invalid (too short)")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Allow extra fields for extensibility
        extra = "allow"


class VLLMModelSettings(BaseSettings):
    """Model-specific configuration settings"""
    
    # Supported Models
    supported_models: List[str] = Field(
        default=[
            "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "01-ai/Yi-34B-Chat",
            "NousResearch/Nous-Hermes-2-Mixtral-8x7B-DPO",
            "openchat/openchat-3.5-0106",
            "microsoft/Phi-3-mini-4k-instruct",
            "deepseek-ai/deepseek-coder-14b-instruct-v1.5",
            "MILVLG/imp-v1-3b"
        ]
    )
    
    # Model Loading Configuration
    download_timeout: int = Field(
        default=1800,  # 30 minutes
        description="Model download timeout in seconds"
    )
    
    # Performance Settings
    max_context_length: int = Field(
        default=4096,
        description="Maximum context length for models"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


class VLLMTestSettings(BaseSettings):
    """Testing and validation configuration"""
    
    # Test Configuration
    test_model: str = Field(
        default="facebook/opt-125m",
        description="Small model used for testing"
    )
    test_timeout: int = Field(
        default=300,  # 5 minutes
        description="Test timeout in seconds"
    )
    test_cache_dir: str = Field(
        default="/tmp/vllm_test_cache",
        description="Temporary cache for testing"
    )
    
    # Validation Settings
    enable_performance_tests: bool = Field(
        default=True,
        description="Enable performance validation tests"
    )
    min_throughput: float = Field(
        default=1.0,
        description="Minimum acceptable throughput (requests/second)"
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Configuration Factory
def load_vllm_settings() -> tuple[VLLMInstallationSettings, VLLMModelSettings, VLLMTestSettings]:
    """Load all vLLM configuration settings"""
    
    installation_settings = VLLMInstallationSettings()
    model_settings = VLLMModelSettings()
    test_settings = VLLMTestSettings()
    
    return installation_settings, model_settings, test_settings


def get_environment_variables(settings: VLLMInstallationSettings) -> Dict[str, str]:
    """Generate environment variables from settings"""
    
    return {
        "HF_TOKEN": settings.hf_token,
        "HF_HOME": settings.hf_cache_dir,
        "TRANSFORMERS_CACHE": settings.transformers_cache,
        "HUGGINGFACE_HUB_TOKEN": settings.hf_token,
        "CC": settings.gcc_version,
        "CXX": settings.gcc_version.replace("gcc", "g++"),
        "NVCC_PREPEND_FLAGS": f"-ccbin /usr/bin/{settings.gcc_version}",
        "TORCH_CUDA_ARCH_LIST": settings.cuda_arch,
        "MAX_JOBS": str(settings.max_jobs),
        "CUDA_HOME": "/usr/local/cuda"
    }


if __name__ == "__main__":
    # Example usage and validation
    try:
        install_settings, model_settings, test_settings = load_vllm_settings()
        print("✅ Configuration loaded successfully")
        print(f"Environment path: {install_settings.dev_env_path}")
        print(f"Supported models: {len(model_settings.supported_models)}")
        print(f"Test model: {test_settings.test_model}")
        
        # Generate environment variables
        env_vars = get_environment_variables(install_settings)
        print(f"Generated {len(env_vars)} environment variables")
        
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")