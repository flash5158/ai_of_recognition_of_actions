import numpy as np
import os


class EmbeddingExtractor:
    """
    Embedding extractor that attempts to use a lightweight PyTorch model
    (MobileNetV2) for image-based features. If PyTorch is not available or
    model load fails, falls back to a deterministic lightweight extractor
    based on bbox geometry and pose features.
    """
    def __init__(self, dim=128, device=None):
        self.dim = dim
        self.device = device
        self._use_torch = False
        self._torch_model = None
        try:
            import torch
            import torchvision
            from torchvision import transforms

            # small MobileNetV2 backbone without classifier
            model = torchvision.models.mobilenet_v2(pretrained=True)
            # use feature extractor by removing classifier
            model.classifier = torch.nn.Identity()
            model.eval()
            if device is None:
                device = torch.device('cpu')
            model.to(device)
            # CPU optimizations: limit threads and attempt compilation/tracing
            try:
                import os
                num_threads = max(1, (os.cpu_count() or 1) - 1)
                torch.set_num_threads(num_threads)
            except Exception:
                pass

            self._torch_model = model
            # Try to compile (torch>=2.0) for performance
            try:
                if hasattr(torch, 'compile'):
                    self._torch_model = torch.compile(self._torch_model)
            except Exception:
                pass

            # Try to trace/jit the model for faster CPU inference
            try:
                dummy = torch.randn(1, 3, 224, 224, device=device)
                self._torch_model = torch.jit.trace(self._torch_model, dummy)
            except Exception:
                # tracing failed; continue with compiled/regular model
                pass
            self._torch_transforms = transforms.Compose([
                transforms.ToPILImage(),
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            self._torch = torch
            self._use_torch = True
            # Try to enable ONNXRuntime backend for faster CPU inference if available
            try:
                import onnxruntime as ort
                cache_dir = os.path.join(os.path.dirname(__file__), '..', '.cache')
                os.makedirs(cache_dir, exist_ok=True)
                onnx_path = os.path.join(cache_dir, 'mobilenetv2.onnx')
                # Export ONNX if not present
                if not os.path.exists(onnx_path):
                    try:
                        export_model = torchvision.models.mobilenet_v2(pretrained=True)
                        export_model.classifier = torch.nn.Identity()
                        export_model.eval()
                        export_model.to('cpu')
                        dummy = torch.randn(1, 3, 224, 224)
                        torch.onnx.export(
                            export_model,
                            dummy,
                            onnx_path,
                            opset_version=11,
                            input_names=['input'],
                            output_names=['output'],
                            dynamic_axes={'input': {0: 'batch'}, 'output': {0: 'batch'}}
                        )
                    except Exception:
                        # If export fails, continue without ONNX
                        pass

                # If ONNX file exists, try to create a session
                if os.path.exists(onnx_path):
                    so = ort.SessionOptions()
                    try:
                        so.intra_op_num_threads = max(1, (os.cpu_count() or 1) - 1)
                    except Exception:
                        pass
                    try:
                        sess = ort.InferenceSession(onnx_path, sess_options=so, providers=['CPUExecutionProvider'])
                        self._ort_session = sess
                        self._use_onnx = True
                    except Exception:
                        self._use_onnx = False
                else:
                    self._use_onnx = False
            except Exception:
                self._use_onnx = False
        except Exception:
            # fallback to deterministic extractor
            self._use_torch = False

    def _normalize_box(self, box, frame_shape):
        h, w = frame_shape[:2]
        x1, y1, x2, y2 = box
        cx = (x1 + x2) / 2.0 / w
        cy = (y1 + y2) / 2.0 / h
        bw = (x2 - x1) / float(w)
        bh = (y2 - y1) / float(h)
        return [cx, cy, bw, bh]

    def _pose_to_features(self, lm_list):
        feats = []
        if not lm_list:
            return [0.0] * 8
        try:
            idx_map = {n: None for n in [11,12,15,16,23,24,27,28]}
            for item in lm_list:
                if item[0] in idx_map:
                    idx_map[item[0]] = (item[1], item[2])

            def dist(a,b):
                return float(np.linalg.norm(np.array(a)-np.array(b))) if a and b else 0.0

            feats.extend([
                dist(idx_map[11], idx_map[12]),
                dist(idx_map[23], idx_map[24]),
                dist(idx_map[15], idx_map[16]),
                dist(idx_map[27], idx_map[28]),
                dist(idx_map[11], idx_map[23]),
                dist(idx_map[12], idx_map[24]),
                dist(idx_map[15], idx_map[27]),
                dist(idx_map[16], idx_map[28])
            ])
        except Exception:
            return [0.0] * 8
        return [float(x) for x in feats[:8]] + [0.0] * max(0, 8 - len(feats))

    def _deterministic_embed(self, frame, box, lm_list=None):
        fshape = frame.shape if frame is not None else (720, 1280, 3)
        box_feats = self._normalize_box(box, fshape)
        pose_feats = self._pose_to_features(lm_list)
        base = np.array(box_feats + pose_feats, dtype=np.float32)
        vec = np.zeros(self.dim, dtype=np.float32)
        vec[:len(base)] = base
        seed = int(sum(base) * 1e6) & 0xFFFFFFFF
        rng = np.random.RandomState(seed)
        vec[len(base):] = rng.rand(self.dim - len(base)).astype(np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def _torch_embed(self, frame, box, lm_list=None):
        # Crop region and run through backbone to get features
        try:
            x1, y1, x2, y2 = map(int, box)
            h, w = frame.shape[:2]
            # Ensure coords inside frame
            x1 = max(0, min(x1, w-1))
            x2 = max(0, min(x2, w-1))
            y1 = max(0, min(y1, h-1))
            y2 = max(0, min(y2, h-1))
            crop = frame[y1:y2 if y2>y1 else y1+1, x1:x2 if x2>x1 else x1+1]
            if crop.size == 0:
                import cv2
                crop = cv2.resize(frame, (224,224))
            else:
                import cv2
                crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

            tensor = self._torch_transforms(crop).unsqueeze(0)
            # ensure model and tensor on CPU for CPU-optimized path
            device = next(self._torch_model.parameters()).device if any(True for _ in self._torch_model.parameters()) else None
            if device is not None:
                tensor = tensor.to(device)

            # Use inference_mode for best CPU perf
            with self._torch.inference_mode():
                feats = self._torch_model(tensor)
            feats = feats.squeeze().cpu().numpy().astype(np.float32)
            # reduce or expand to dim
            if feats.size >= self.dim:
                vec = feats[:self.dim]
            else:
                vec = np.zeros(self.dim, dtype=np.float32)
                vec[:feats.size] = feats
                # fill rest deterministically
                seed = int(vec.sum() * 1e6) & 0xFFFFFFFF
                rng = np.random.RandomState(seed)
                vec[feats.size:] = rng.rand(self.dim - feats.size).astype(np.float32)
            # normalize
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.tolist()
        except Exception:
            return self._deterministic_embed(frame, box, lm_list)

    def _onnx_embed(self, frame, box, lm_list=None):
        try:
            import cv2
            x1, y1, x2, y2 = map(int, box)
            h, w = frame.shape[:2]
            x1 = max(0, min(x1, w-1))
            x2 = max(0, min(x2, w-1))
            y1 = max(0, min(y1, h-1))
            y2 = max(0, min(y2, h-1))
            crop = frame[y1:y2 if y2>y1 else y1+1, x1:x2 if x2>x1 else x1+1]
            if crop.size == 0:
                crop = cv2.resize(frame, (224,224))
            else:
                crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

            img = cv2.resize(crop, (224,224)).astype(np.float32) / 255.0
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img = (img - mean) / std
            img = img.transpose(2,0,1)
            img = np.expand_dims(img, 0).astype(np.float32)

            input_name = self._ort_session.get_inputs()[0].name
            outputs = self._ort_session.run(None, {input_name: img})
            feats = np.array(outputs[0]).squeeze().astype(np.float32)

            if feats.size >= self.dim:
                vec = feats[:self.dim]
            else:
                vec = np.zeros(self.dim, dtype=np.float32)
                vec[:feats.size] = feats
                seed = int(vec.sum() * 1e6) & 0xFFFFFFFF
                rng = np.random.RandomState(seed)
                vec[feats.size:] = rng.rand(self.dim - feats.size).astype(np.float32)

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            return vec.tolist()
        except Exception:
            return self._deterministic_embed(frame, box, lm_list)

    def embed(self, frame, box, lm_list=None):
        # Prefer ONNXRuntime for CPU if available, then PyTorch, then deterministic
        if getattr(self, '_use_onnx', False) and getattr(self, '_ort_session', None) is not None:
            return self._onnx_embed(frame, box, lm_list)
        if self._use_torch and self._torch_model is not None:
            return self._torch_embed(frame, box, lm_list)
        return self._deterministic_embed(frame, box, lm_list)
