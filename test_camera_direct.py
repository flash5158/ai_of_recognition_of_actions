#!/usr/bin/env python3
"""
Direct Camera Test - Diagnose OpenCV VideoCapture on macOS
"""
import cv2
import sys
import time

print("=" * 60)
print("DIAGNOSTIC: OpenCV Camera Test")
print("=" * 60)

# Test 1: Try to open camera 0
print("\n[TEST 1] Attempting cv2.VideoCapture(0)...")
cap = cv2.VideoCapture(0)
print(f"  Result: cap.isOpened() = {cap.isOpened()}")

if cap.isOpened():
    print("\n[TEST 2] Reading first frame...")
    ret, frame = cap.read()
    print(f"  Result: ret={ret}, frame shape={frame.shape if ret else 'N/A'}")
    
    if ret:
        print("\n[TEST 3] Encoding frame to JPEG...")
        ret_enc, buffer = cv2.imencode('.jpg', frame)
        print(f"  Result: Success={ret_enc}, Size={len(buffer) if ret_enc else 0} bytes")
    
    cap.release()
    print("\n✅ CAMERA WORKS - Issue is elsewhere (orchestrator loop or WS)")
else:
    print("\n❌ CAMERA FAILED - Testing alternatives...")
    for idx in [1, 2]:
        print(f"\n  Trying device {idx}...")
        cap_alt = cv2.VideoCapture(idx)
        if cap_alt.isOpened():
            print(f"  ✅ Device {idx} works!")
            cap_alt.release()
            sys.exit(0)
        cap_alt.release()
    
    print("\n❌ NO CAMERA ACCESSIBLE")
    print("  Possible causes:")
    print("  - Terminal lacks Camera permission (System Settings > Privacy)")
    print("  - Camera in use by another app")
    print("  - Camera hardware failure")

print("\n" + "=" * 60)
