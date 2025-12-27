
# DEFINICIÓN DE COMPORTAMIENTOS ("Knowledge Graph")
# Este archivo actúa como la "memoria entrenada" de la IA.
# Define qué es cada acción basándose en características semánticas.

BEHAVIOR_DB = {
    "AGRESION": {
        "description": "Postura de combate, puños arriba",
        "policy": "PROHIBITED",
        "severity": "CRITICAL",
        "features": {
            "hands_up": True, # Manos sobre hombros
            "elbows_out": True,
            "guard_width": "narrow", # Puños cerca de la cara
        }
    },
    "MANOS_ARRIBA": {
        "description": "Rendición o estiramiento",
        "policy": "WARNING",
        "severity": "HIGH",
        "features": {
            "hands_above_head": True,
            "arms_straight": True
        }
    },
    "TOCANDO_CARA": {
        "description": "Ansiedad o pensamiento",
        "policy": "ALLOWED",
        "severity": "LOW",
        "features": {
            "hands_near_nose": True
        }
    },
    "USO_CELULAR": {
        "description": "Distracción con dispositivo",
        "policy": "RESTRICTED", # Depende del contexto laboral
        "severity": "MEDIUM",
        "features": {
            "hand_near_ear": True,
            "head_tilted": True
        }
    },
    "DURMIENDO": {
        "description": "Cabeza caída o postura recostada",
        "policy": "PROHIBITED",
        "severity": "CRITICAL",
        "features": {
            "head_low": True,
            "torso_horizontal": True
        }
    },
    "CAMINANDO": {
        "description": "Desplazamiento activo",
        "policy": "ALLOWED",
        "severity": "INFO",
        "features": {
            "legs_moving": True,
            "pose_vertical": True
        }
    },
    "SENTADO": {
        "description": "Reposo o trabajo en escritorio",
        "policy": "ALLOWED",
        "severity": "INFO",
        "features": {
            "legs_bent": True,
            "height_reduced": True
        }
    },
    "POSTURA_FIRME": {
        "description": "Parado estático",
        "policy": "ALLOWED",
        "severity": "INFO",
        "features": {
            "legs_straight": True,
            "motion_low": True
        }
    }
}

def get_policy(action):
    if action in BEHAVIOR_DB:
        return BEHAVIOR_DB[action]["policy"]
    return "UNKNOWN"
