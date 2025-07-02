# Remove any existing vLLM installation
pip uninstall vllm -y
pip uninstall vllm-flash-attn -y
pip uninstall flash-attn -y

# Clear pip cache
pip cache purge

# Verify clean state
pip list | grep vllm || echo "vLLM successfully removed"
