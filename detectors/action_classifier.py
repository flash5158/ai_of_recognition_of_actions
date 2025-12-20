import numpy as np
import time

class ActionClassifier:
    """
    Clasificador de acciones basado en reglas geométricas simples sobre landmarks de Pose.
    Acciones soportadas: PARADO, SENTADO, SALUDANDO, CAMINANDO, INACTIVO.
    """
    def __init__(self):
        self.history = {} # Para suavizado temporal si fuera necesario

    def classify(self, lm_list):
        """
        Recibe una lista de landmarks [id, x, y, z, visibility] y retorna una etiqueta de acción en español.
        """
        if not lm_list or len(lm_list) < 33:
            return "DESCONOCIDO"

        # Extraer puntos clave (indices de MediaPipe Pose)
        # 11: left_shoulder, 12: right_shoulder
        # 23: left_hip, 24: right_hip
        # 25: left_knee, 26: right_knee
        # 27: left_ankle, 28: right_ankle
        # 15: left_wrist, 16: right_wrist
        # 0: nose

        # Helper para obtener coordenadas (x, y)
        def get_pt(idx):
            return np.array([lm_list[idx][1], lm_list[idx][2]])

        l_shoulder = get_pt(11)
        r_shoulder = get_pt(12)
        l_hip = get_pt(23)
        r_hip = get_pt(24)
        l_knee = get_pt(25)
        r_knee = get_pt(26)
        l_ankle = get_pt(27)
        r_ankle = get_pt(28)
        l_wrist = get_pt(15)
        r_wrist = get_pt(16)
        nose = get_pt(0)

        # 1. Detectar "SALUDANDO" (Waving)
        # Si la muñeca está significativamente por encima del hombro y se mueve (opcional, por ahora solo posición)
        is_waving = False
        if l_wrist[1] < l_shoulder[1] or r_wrist[1] < r_shoulder[1]:
            # Verificar si está realmente arriba (y < y_shoulder) - recordamos y=0 es arriba
            # Chequear que esté cerca de la cabeza horizontalmente para evitar falsos positivos
            if (l_wrist[1] < nose[1]) or (r_wrist[1] < nose[1]):
                return "SALUDANDO"

        # 2. Detectar "SENTADO" vs "PARADO"
        # Usamos el ángulo de la rodilla o la relación vertical entre cadera y rodilla
        # En "SENTADO", la distancia vertical entre cadera y rodilla es pequeña comparada con el muslo
        
        # Altura vertical del muslo (hip.y - knee.y) (Nota: y aumenta hacia abajo)
        # Si la persona está parada, knee.y es mucho mayor que hip.y
        # Si está sentada, knee.y es similar a hip.y (muslo horizontal)
        
        # Calculamos distancias verticales
        l_thigh_vert = abs(l_knee[1] - l_hip[1])
        r_thigh_vert = abs(r_knee[1] - r_hip[1])
        
        # Referencia: altura del torso (shoulder a hip)
        torso_h = abs(l_shoulder[1] - l_hip[1]) + abs(r_shoulder[1] - r_hip[1])
        
        # Si la proyección vertical del muslo es pequeña (comparada con torso), el muslo está horizontal -> SENTADO
        if (l_thigh_vert < 0.5 * torso_h) or (r_thigh_vert < 0.5 * torso_h):
             return "SENTADO"

        # 3. Detectar "CAMINANDO" vs "PARADO"
        # Esto requiere análisis temporal o verificar apertura de piernas (stride)
        # Usamos stride (distancia entre tobillos)
        ankle_dist = np.linalg.norm(l_ankle - r_ankle)
        # Normalizamos con ancho de hombros
        shoulder_width = np.linalg.norm(l_shoulder - r_shoulder)
        
        if ankle_dist > 1.2 * shoulder_width:
             return "CAMINANDO"

        return "PARADO"
