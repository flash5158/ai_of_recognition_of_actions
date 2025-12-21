import cv2
import mediapipe as mp
import numpy as np

class EmotionDetector:
    """
    Detector de emociones faciales ligero basado en geometría de landmarks (FaceMesh).
    Optimizado para rendimiento y privacidad (procesamiento geométrico local).
    """
    def __init__(self, refine_landmarks=False):
        self.mp_face_mesh = mp.solutions.face_mesh
        # Configuración "china-style": alta eficiencia
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=4, # Multiobjetivo
            refine_landmarks=refine_landmarks,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.last_results = None

    def detect(self, frame_bgr):
        """
        Procesa el frame y retorna lista de emociones por rostro detectado.
        Retorna: List[Dict] -> [{'bbox': [x,y,w,h], 'emotion': 'NEUTRAL', 'score': 0.9}, ...]
        """
        results = []
        h, w, _ = frame_bgr.shape
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        self.last_results = self.face_mesh.process(frame_rgb)
        
        if self.last_results.multi_face_landmarks:
            for face_landmarks in self.last_results.multi_face_landmarks:
                # 1. Bounding Box Estimada
                x_min, y_min = w, h
                x_max, y_max = 0, 0
                for lm in face_landmarks.landmark:
                    x, y = int(lm.x * w), int(lm.y * h)
                    if x < x_min: x_min = x
                    if x > x_max: x_max = x
                    if y < y_min: y_min = y
                    if y > y_max: y_max = y
                
                bbox = [x_min, y_min, x_max - x_min, y_max - y_min]
                
                # 2. Análisis Geométrico
                emotion, score = self._analyze_geometry(face_landmarks.landmark)
                
                results.append({
                    "box": bbox,
                    "emotion": emotion,
                    "conf": score
                })
        
        return results

    def _analyze_geometry(self, landmarks):
        """
        Analiza distancias clave entre puntos de referencia.
        """
        # Índices clave de MediaPipe FaceMesh
        # Labios: Superior 13, Inferior 14, Comisura Izq 61, Comisura Der 291
        # Cejas: Izq sup 105, Der sup 334
        # Ojos: Superiores (159, 386), Inferiores (145, 374)
        
        def dist(i1, i2):
            p1 = np.array([landmarks[i1].x, landmarks[i1].y])
            p2 = np.array([landmarks[i2].x, landmarks[i2].y])
            return np.linalg.norm(p1 - p2)

        # Normalización (ancho de la cara bi-zygomatic width aprox: 234 a 454)
        face_width = dist(234, 454)
        if face_width == 0: return "NEUTRAL", 0.0
        
        # Apertura de boca
        mouth_open = dist(13, 14) / face_width
        
        # Sonrisa (ancho de boca)
        mouth_wide = dist(61, 291) / face_width
        
        # Comisuras vs Centro (Sonrisa levanta comisuras? En 3D sí, en 2D a veces)
        # Usamos curvatura simple: Y de comisuras vs Y de labio inferior
        lips_y = (landmarks[61].y + landmarks[291].y) / 2
        center_y = landmarks[13].y
        smile_curve = center_y - lips_y # Si positivo, comisuras más altas (quizás) -> No siempre fiable en 2D directo
        
        # Heurísticas Simples & Rápidas
        emotion = "NEUTRAL"
        score = 0.5
        
        # SORPRESA: Boca muy abierta
        if mouth_open > 0.15: # Umbral ajustado
            emotion = "SORPRESA"
            score = 0.8
        
        # FELICIDAD: Boca ancha + "Sonrisa" (esto necesita calibración, usamos mouth_wide por simplicidad)
        # Un width > 0.45 suele ser sonrisa amplia
        elif mouth_wide > 0.45: 
            emotion = "FELIZ"
            score = 0.85
            
        # IRA: Cejas juntas y bajas (requiere medir la distancia entre cejas y ojos)
        # Distancia entre ceja(65) y ojo(159)
        # brow_eye = dist(65, 159) / face_width
        # if brow_eye < 0.05: ... (Complejo de tunear sin dataset)
        
        return emotion, score
