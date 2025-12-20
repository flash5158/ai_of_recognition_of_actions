import numpy as np

class ActionClassifier:
    """
    Clasificador de acciones basado en reglas geométricas sobre landmarks de YOLO-Pose (COCO format).
    Acciones soportadas: PARADO, SENTADO, SALUDANDO, CAMINANDO, INACTIVO.
    """
    def __init__(self):
        self.history = {} 

    def classify(self, lm_list):
        """
        Recibe una lista de landmarks [id, x, y, conf] y retorna una etiqueta de acción.
        Usa índices COCO (17 puntos).
        """
        # COCO tiene 17 puntos. MediaPipe tenía 33.
        if not lm_list or len(lm_list) < 17:
            return "DESCONOCIDO"

        # Helper para obtener coordenadas (x, y)
        def get_pt(idx):
            # lm_list[i] = [id, x, y, conf]
            return np.array([lm_list[idx][1], lm_list[idx][2]])

        # COCO Indices Mapping
        # 0: Nose
        # 5: Left Shoulder, 6: Right Shoulder
        # 11: Left Hip, 12: Right Hip
        # 13: Left Knee, 14: Right Knee
        # 15: Left Ankle, 16: Right Ankle
        # 9: Left Wrist, 10: Right Wrist

        nose = get_pt(0)
        l_shoulder = get_pt(5)
        r_shoulder = get_pt(6)
        l_hip = get_pt(11)
        r_hip = get_pt(12)
        l_knee = get_pt(13)
        r_knee = get_pt(14)
        l_ankle = get_pt(15)
        r_ankle = get_pt(16)
        l_wrist = get_pt(9)
        r_wrist = get_pt(10)

        # 1. Detectar "SALUDANDO" (Waving)
        # Si la muñeca está por encima del hombro (y menor, coords de pixel)
        # COCO keypoints are usually pixel coords (0,0 is top-left)
        if l_wrist[1] < l_shoulder[1] or r_wrist[1] < r_shoulder[1]:
            # Chequear que esté cerca de la cabeza/nariz para filtrar falsos positivos
            if (l_wrist[1] < nose[1] + 20) or (r_wrist[1] < nose[1] + 20):
                return "SALUDANDO"

        # 2. Detectar "SENTADO" vs "PARADO"
        # Altura vertical del muslo abs(knee.y - hip.y)
        l_thigh_vert = abs(l_knee[1] - l_hip[1])
        r_thigh_vert = abs(r_knee[1] - r_hip[1])
        
        # Referencia: altura del torso (shoulder a hip)
        torso_h = abs(l_shoulder[1] - l_hip[1]) + abs(r_shoulder[1] - r_hip[1])
        
        # Si el muslo está "corto" verticalmente, probablemente está horizontal (hacia la cámara o de lado sentado)
        # Factor ajustado para YOLO
        if torso_h > 0:
            if (l_thigh_vert < 0.6 * (torso_h / 2)) or (r_thigh_vert < 0.6 * (torso_h / 2)):
                 return "SENTADO"

        # 3. Detectar "CAMINANDO" vs "PARADO"
        ankle_dist = np.linalg.norm(l_ankle - r_ankle)
        shoulder_width = np.linalg.norm(l_shoulder - r_shoulder)
        
        if shoulder_width > 0 and ankle_dist > 1.3 * shoulder_width:
             return "CAMINANDO"

        return "PARADO"
