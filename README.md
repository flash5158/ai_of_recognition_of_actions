# CHALAS AI RECOGNITION

Plataforma de Inteligencia Conductual y Vigilancia Cuántica.

## Requisitos previos

- Python 3.10+
- Node.js 18+ (para el dashboard)
- Docker (opcional, para base de datos vectorial Milvus)
- Webcam conectada

## Instalación

1.  **Backend (Python)**
    ```bash
    # Crear entorno virtual
    python -m venv .venv
    source .venv/bin/activate  # o .venv\Scripts\activate en Windows

    # Instalar dependencias
    pip install -r requirements.txt
    ```

2.  **Dashboard (Next.js)**
    ```bash
    cd dashboard
    npm install
    ```

3.  **Base de Datos (Opcional)**
    Si deseas persistencia de vectores a largo plazo:
    ```bash
    docker-compose up -d
    ```
    *El sistema funcionará en "Modo Volátil" si no se detecta la base de datos.*

## Ejecución

1.  **Iniciar Backend**
    ```bash
    # En la carpeta raíz
    python server.py
    ```
    El servidor iniciará en `http://localhost:8000`.

2.  **Iniciar Dashboard**
    ```bash
    # En otra terminal, carpeta ./dashboard
    npm run dev
    ```
    Accede a `http://localhost:3000`.

## PANOPTES: Chalas AI Recognition V2 (M2 Optimized)

> **Status**: 🚀 PRODUCTION READY (Apple Silicon Native)
> **Performance**: 46+ FPS on M2 Air
> **Engine**: YOLOv11-Pose + MPS Metal Acceleration

Sistema de vigilancia proactiva con arquitectura asíncrona de alto rendimiento.

## ⚡ Características M2
- **Core Asíncrono**: Video a 60FPS independientemente de la carga de IA.
- **Metal Performance Shaders (MPS)**: Aceleración por hardware real.
- **Cyberpunk HUD**: Visualización cinemática con corrección de coordenadas.
- **Anti-Jitter**: Suavizado de movimiento y estados con decaimiento automático. (YOLOv11 + MediaPipe).
- **Bóveda**: Historial de sujetos detectados (requiere Milvus).
- **Config**: Ajuste de sensibilidad y renderizado.

## Créditos

Desarrollado con Arquitectura de Agentes Avanzados.
```
