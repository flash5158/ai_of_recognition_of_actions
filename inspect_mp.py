import mediapipe
import os

path = os.path.dirname(mediapipe.__file__)
print(f"Path: {path}")
try:
    print("Contents (top level):")
    for item in os.listdir(path):
        print(f" - {item}")
        
    print("\nCheck if 'python' exists:")
    if os.path.exists(os.path.join(path, 'python')):
        print("Found 'python' directory.")
        print(os.listdir(os.path.join(path, 'python')))
    else:
        print("'python' directory NOT found.")

    print("\nCheck if 'tasks' exists:")
    if os.path.exists(os.path.join(path, 'tasks')):
        print("Found 'tasks' directory.")
        print(os.listdir(os.path.join(path, 'tasks')))
except Exception as e:
    print(f"Error: {e}")
