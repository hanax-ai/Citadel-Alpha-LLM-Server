#!/usr/bin/env python3
"""
update_gpu_config.py - Update GPU configuration with detected specifications
"""

import sys
import argparse
from pathlib import Path


def main():
    """Main function to update GPU configuration with detected specs"""
    parser = argparse.ArgumentParser(description='Update GPU configuration with detected specifications')
    parser.add_argument('--project-root', required=True, help='Project root directory path')
    parser.add_argument('--config-file', required=True, help='GPU configuration file path')
    parser.add_argument('--script-dir', required=True, help='Scripts directory path')
    
    args = parser.parse_args()
    
    try:
        # Add paths to sys.path for imports
        sys.path.append(str(Path(args.project_root) / 'configs'))
        sys.path.append(args.script_dir)
        
        # Import required modules
        from gpu_settings import GPUSettings
        from gpu_manager import GPUDetectionManager
        
        # Load current settings
        config_path = Path(args.config_file)
        settings = GPUSettings.load_from_file(config_path)
        
        # Detect specifications
        detector = GPUDetectionManager()
        specs = detector.detect_gpu_specs()
        
        if specs:
            # Update settings with detected specs
            settings.detected_specs = specs
            settings.save_to_file(config_path)
            print('✅ GPU specifications updated')
            return 0
        else:
            print('⚠️  Using default specifications')
            return 1
            
    except ImportError as e:
        print(f'❌ Import error: {e}', file=sys.stderr)
        print('Required modules (gpu_settings, gpu_manager) not found', file=sys.stderr)
        return 2
    except FileNotFoundError as e:
        print(f'❌ File not found: {e}', file=sys.stderr)
        return 3
    except Exception as e:
        print(f'❌ Unexpected error: {e}', file=sys.stderr)
        return 4


if __name__ == '__main__':
    sys.exit(main())
