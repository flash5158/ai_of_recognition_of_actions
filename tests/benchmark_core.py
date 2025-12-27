import time
import sys
import os

# Ensure we can import from current dir
sys.path.append(os.getcwd())

from core.vision_thread import VisionThread
from core.inference_engine import InferenceEngine
from core.shared_state import SharedState

def main():
    print("--- CHALAS AI: M2 BENCHMARK START ---")
    
    shared = SharedState()
    
    # Start Vision
    vision = VisionThread(source=0)
    vision.start()
    
    # Start Brain
    brain = InferenceEngine(model_path="yolo11n-pose.pt")
    brain.start()
    
    print("Threads started. Warming up (5s)...")
    time.sleep(5)
    
    print("\nStarting Measurement Loop (10s)...")
    start_measure = time.time()
    frames_seen_start = shared.frame_id
    
    try:
        for i in range(10):
            time.sleep(1.0)
            
            # Reads
            current_frame_id = shared.frame_id
            video_fps = current_frame_id - frames_seen_start
            frames_seen_start = current_frame_id
            
            ai_fps = shared.inference_fps
            
            print(f"[{i+1}/10] VIDEO: {video_fps} FPS | AI: {ai_fps:.2f} FPS | Status: {shared.system_status}")
            
    except KeyboardInterrupt:
        pass
        
    print("\nStopping threads...")
    vision.stop()
    brain.stop()
    print("Benchmark Complete.")

if __name__ == "__main__":
    main()
