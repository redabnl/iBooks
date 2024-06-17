import torch

print("CUDA available: ", torch.cuda.is_available())
if torch.cuda.is_available():
    print("CUDA version: ", torch.version.cuda)
    print("Device name: ", torch.cuda.get_device_name(0))
