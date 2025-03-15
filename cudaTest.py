import torch

# Check if CUDA is available
cuda_available = torch.cuda.is_available()

if cuda_available:
    print("CUDA is available.")
    # Print the CUDA device name
    print("CUDA device name:", torch.cuda.get_device_name(0))
else:
    print("CUDA is not available.")
