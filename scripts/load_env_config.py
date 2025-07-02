#!/usr/bin/env python3
"""
Helper script to load configuration and export environment variables.

This script reads the JSON configuration file and outputs shell-compatible
environment variable assignments. It replaces inline Python JSON parsing
in shell scripts with a more maintainable approach.

Usage:
    eval "$(python3 load_env_config.py /path/to/config.json)"
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional


def load_config(config_path: str) -> Optional[Dict[str, Any]]:
    """Load configuration from JSON file with error handling."""
    try:
        if not os.path.isfile(config_path):
            print(f"# Config file not found: {config_path}", file=sys.stderr)
            return None
        
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config
    except json.JSONDecodeError as e:
        print(f"# Error parsing JSON config: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"# Error loading config: {e}", file=sys.stderr)
        return None


def export_optimization_vars(config: Dict[str, Any]) -> None:
    """Export optimization-related environment variables."""
    optimization = config.get("optimization", {})
    
    # Memory optimizations
    memory = optimization.get("memory", {})
    malloc_arena_max = memory.get("malloc_arena_max", 4)
    print(f"export MALLOC_ARENA_MAX='{malloc_arena_max}'")
    
    # Threading optimizations
    threading = optimization.get("threading", {})
    max_threads = min(threading.get("max_threads", 8), 16)
    print(f"export OMP_NUM_THREADS='{max_threads}'")
    print(f"export MKL_NUM_THREADS='{max_threads}'")
    print(f"export NUMEXPR_NUM_THREADS='{max_threads}'")
    
    # CUDA optimizations
    cuda = optimization.get("cuda", {})
    launch_blocking = "1" if cuda.get("launch_blocking", False) else "0"
    cache_disable = "1" if cuda.get("cache_disable", False) else "0"
    print(f"export CUDA_LAUNCH_BLOCKING='{launch_blocking}'")
    print(f"export CUDA_CACHE_DISABLE='{cache_disable}'")


def export_default_vars() -> None:
    """Export default optimization variables when config is unavailable."""
    print("export MALLOC_ARENA_MAX='4'")
    print("export OMP_NUM_THREADS='8'")
    print("export MKL_NUM_THREADS='8'")
    print("export NUMEXPR_NUM_THREADS='8'")
    print("export CUDA_LAUNCH_BLOCKING='0'")
    print("export CUDA_CACHE_DISABLE='0'")


def main() -> None:
    """Main function to load config and export environment variables."""
    if len(sys.argv) != 2:
        print("# Usage: load_env_config.py <config_file>", file=sys.stderr)
        export_default_vars()
        return
    
    config_file = sys.argv[1]
    config = load_config(config_file)
    
    if config is None:
        print("# Using default optimization values", file=sys.stderr)
        export_default_vars()
        return
    
    export_optimization_vars(config)
    print("# Optimization variables exported successfully", file=sys.stderr)


if __name__ == "__main__":
    main()
