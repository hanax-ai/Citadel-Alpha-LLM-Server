#!/usr/bin/env python3
"""
GPU Benchmark Module for PLANB-04 Validation
Provides GPU performance testing functionality for PyTorch with CUDA
"""

import torch
import time
import numpy as np
from typing import Optional, Dict, Any


def run_gpu_benchmark() -> str:
    """
    Run GPU performance benchmark using PyTorch
    
    Returns:
        str: Formatted benchmark results
    """
    try:
        if not torch.cuda.is_available():
            return 'CUDA not available - skipping GPU benchmark'
        
        device = torch.device('cuda:0')
        results = []
        results.append(f'Benchmarking on: {torch.cuda.get_device_name(0)}')
        
        # Warm up GPU
        _warmup_gpu(device)
        
        # Run benchmark tests
        benchmark_results = _run_matrix_benchmark(device)
        results.extend(benchmark_results)
        
        results.append('GPU performance benchmark completed')
        return '\n'.join(results)
        
    except Exception as e:
        return f'GPU benchmark error: {str(e)}'


def _warmup_gpu(device: torch.device, iterations: int = 5) -> None:
    """
    Warm up GPU with small matrix operations
    
    Args:
        device: PyTorch CUDA device
        iterations: Number of warmup iterations
    """
    for _ in range(iterations):
        x = torch.randn(1000, 1000, device=device)
        y = torch.randn(1000, 1000, device=device)
        z = torch.matmul(x, y)
        del x, y, z  # Explicit cleanup


def _run_matrix_benchmark(device: torch.device) -> list:
    """
    Run matrix multiplication benchmarks
    
    Args:
        device: PyTorch CUDA device
        
    Returns:
        list: List of benchmark result strings
    """
    results = []
    sizes = [1000, 2000]
    iterations = 5
    
    for size in sizes:
        times = []
        
        for _ in range(iterations):
            x = torch.randn(size, size, device=device)
            y = torch.randn(size, size, device=device)
            
            # Synchronize before timing
            torch.cuda.synchronize()
            start_time = time.time()
            
            z = torch.matmul(x, y)
            
            # Synchronize after computation
            torch.cuda.synchronize()
            end_time = time.time()
            
            times.append(end_time - start_time)
            
            # Cleanup
            del x, y, z
        
        avg_time = np.mean(times)
        results.append(f'Matrix {size}x{size}: {avg_time:.4f}s avg')
    
    return results


def get_gpu_info() -> Dict[str, Any]:
    """
    Get GPU information for diagnostics
    
    Returns:
        dict: GPU information including device count, names, memory, etc.
    """
    if not torch.cuda.is_available():
        return {'cuda_available': False, 'message': 'CUDA not available'}
    
    gpu_info = {
        'cuda_available': True,
        'device_count': torch.cuda.device_count(),
        'current_device': torch.cuda.current_device(),
        'devices': []
    }
    
    for i in range(torch.cuda.device_count()):
        device_info = {
            'id': i,
            'name': torch.cuda.get_device_name(i),
            'memory_total': torch.cuda.get_device_properties(i).total_memory,
            'memory_reserved': torch.cuda.memory_reserved(i),
            'memory_allocated': torch.cuda.memory_allocated(i)
        }
        gpu_info['devices'].append(device_info)
    
    return gpu_info


if __name__ == "__main__":
    # Allow running as standalone script for testing
    print(run_gpu_benchmark())
