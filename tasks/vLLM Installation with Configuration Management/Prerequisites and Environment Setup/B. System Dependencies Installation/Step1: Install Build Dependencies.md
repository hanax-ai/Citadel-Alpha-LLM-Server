# Install system packages required for vLLM compilation
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  ninja-build \
  python3.12-dev \
  libopenmpi-dev \
  libaio-dev \
  libcurl4-openssl-dev \
  libssl-dev \
  libffi-dev \
  libnuma-dev \
  pkg-config

# Install additional compilation tools
sudo apt install -y \
  gcc-11 \
  g++-11 \
  libc6-dev \
  libc-dev-bin \
  linux-libc-dev

# Set GCC version for compilation
sudo update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100
sudo update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100