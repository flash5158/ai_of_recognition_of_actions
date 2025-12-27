import time
import sys
import os

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# Ensure we can import from current dir
sys.path.append(os.getcwd())

from orchestrator import Orchestrator

def main():
    print("--- CHALAS AI: FULL SYSTEM VERIFICATION ---")
    
    orch = Orchestrator(source=0)
    
    # Check Compatibility
    print(f"Settings Check: {orch.settings}")
    
    orch.start()
    print("Engines Started.")
    
    try:
        start_time = time.time()
        frames = 0
        
        print("Running 5s stress test...")
        while time.time() - start_time < 5:
            frame_bytes = orch.get_frame()
            if frame_bytes:
                frames += 1
                
            tel = orch.get_telemetry()
            # print(f"Telemetry FPS: {tel['fps']}")
            
            # Simulate 30Hz poll
            time.sleep(0.01)
            
        duration = time.time() - start_time
        fps = frames / duration
        print(f"RESULT: Processed {frames} frames in {duration:.2f}s => {fps:.2f} FPS (Output)")
        
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback; traceback.print_exc()
        
    orch.stop()
    print("System Stopped.")

if __name__ == "__main__":
    main()
