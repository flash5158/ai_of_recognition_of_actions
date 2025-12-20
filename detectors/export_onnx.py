"""Export MobileNetV2 backbone to ONNX for faster CPU inference.
Run inside the project venv or inside the container after deps are installed.
"""
import os
import torch
import torchvision

def main():
    cache_dir = os.path.join(os.path.dirname(__file__), '..', '.cache')
    os.makedirs(cache_dir, exist_ok=True)
    onnx_path = os.path.join(cache_dir, 'mobilenetv2.onnx')
    if os.path.exists(onnx_path):
        print('ONNX already exists at', onnx_path)
        return

    print('Exporting MobileNetV2 to', onnx_path)
    model = torchvision.models.mobilenet_v2(pretrained=True)
    model.classifier = torch.nn.Identity()
    model.eval()
    dummy = torch.randn(1, 3, 224, 224)
    try:
        torch.onnx.export(
            model,
            dummy,
            onnx_path,
            opset_version=11,
            input_names=['input'],
            output_names=['output'],
            dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
        )
        print('Export complete')
    except Exception as e:
        print('Export failed:', e)

if __name__ == '__main__':
    main()
