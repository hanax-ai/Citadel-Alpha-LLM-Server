# Set compilation environment variables
export CC=gcc-11
export CXX=g++-11
export CUDA_HOME=/usr/local/cuda
export NVCC_PREPEND_FLAGS='-ccbin /usr/bin/gcc-11'
export TORCH_CUDA_ARCH_LIST="8.9"  # For RTX 4070 Ti SUPER
export MAX_JOBS=8  # Limit parallel compilation to prevent OOM

# Add to shell profile for persistence
tee -a ~/.bashrc << 'EOF'

# vLLM Compilation Environment
export CC=gcc-11
export CXX=g++-11
export NVCC_PREPEND_FLAGS='-ccbin /usr/bin/gcc-11'
export TORCH_CUDA_ARCH_LIST="8.9"
export MAX_JOBS=8
EOF

source ~/.bashrc