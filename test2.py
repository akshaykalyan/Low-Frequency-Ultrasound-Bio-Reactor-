# touch_diagnostic.py
import subprocess
import os

print("=== Touch Diagnostic ===")

# Check input devices
print("\n1. Input devices:")
result = subprocess.run(['ls', '/dev/input/'], capture_output=True, text=True)
print(result.stdout)

# Check if devices are readable
print("2. Device permissions:")
devices = ['event0', 'event1', 'mouse0', 'mouse1']
for device in devices:
    path = f'/dev/input/{device}'
    if os.path.exists(path):
        print(f"{path}: exists - readable: {os.access(path, os.R_OK)}")

print("3. Kivy config path:")
print(f"Kivy config: {os.path.expanduser('~/.kivy/config.ini')}")