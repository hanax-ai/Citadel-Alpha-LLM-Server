#!/usr/bin/env python3
"""
PLANB-05 Step 7: Hugging Face Authentication Helper
Secure authentication configuration using pydantic settings
"""

import os
import sys
from pathlib import Path
from typing import Optional
import subprocess
import logging

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from configs.vllm_settings import VLLMInstallationSettings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class HuggingFaceAuthenticator:
    """Handles Hugging Face authentication configuration"""
    
    def __init__(self):
        """Initialize authenticator with settings"""
        try:
            self.settings = VLLMInstallationSettings()
            logger.info("Configuration loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def validate_token(self) -> bool:
        """Validate HF token format and accessibility"""
        token = self.settings.hf_token
        
        # Basic format validation
        if not token.startswith("hf_"):
            logger.error("Token must start with 'hf_'")
            return False
        
        if len(token) < 20:
            logger.error("Token appears to be too short")
            return False
        
        return True
    
    def setup_environment_variables(self) -> None:
        """Set up environment variables for current session"""
        env_vars = {
            "HF_TOKEN": self.settings.hf_token,
            "HF_HOME": self.settings.hf_cache_dir,
            "HUGGINGFACE_HUB_TOKEN": self.settings.hf_token,
            "TRANSFORMERS_CACHE": self.settings.transformers_cache
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            logger.info(f"Set environment variable: {key}")
    
    def login_via_cli(self) -> bool:
        """Login using huggingface-cli with token"""
        try:
            # Use token from stdin for security
            cmd = ["huggingface-cli", "login", "--token"]
            
            # Run with token input
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=self.settings.hf_token)
            
            if process.returncode == 0:
                logger.info("Successfully authenticated with Hugging Face")
                return True
            else:
                logger.error(f"Authentication failed: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"CLI authentication error: {e}")
            return False
    
    def verify_authentication(self) -> bool:
        """Verify authentication by checking user info"""
        try:
            result = subprocess.run(
                ["huggingface-cli", "whoami"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                username = result.stdout.strip()
                logger.info(f"Authenticated as: {username}")
                return True
            else:
                logger.error(f"Verification failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Authentication verification timed out")
            return False
        except Exception as e:
            logger.error(f"Verification error: {e}")
            return False
    
    def configure_authentication(self) -> bool:
        """Main authentication configuration process"""
        logger.info("Starting Hugging Face authentication configuration")
        
        # Step 1: Validate token
        if not self.validate_token():
            logger.error("Token validation failed")
            return False
        
        # Step 2: Setup environment variables
        self.setup_environment_variables()
        
        # Step 3: Authenticate via CLI
        if not self.login_via_cli():
            logger.error("CLI authentication failed")
            return False
        
        # Step 4: Verify authentication
        if not self.verify_authentication():
            logger.error("Authentication verification failed")
            return False
        
        logger.info("✅ Hugging Face authentication configured successfully")
        return True


def main():
    """Main execution function"""
    try:
        # Initialize authenticator
        auth = HuggingFaceAuthenticator()
        
        # Configure authentication
        success = auth.configure_authentication()
        
        if success:
            print("✅ Hugging Face authentication configured successfully")
            sys.exit(0)
        else:
            print("❌ Hugging Face authentication configuration failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Authentication cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()