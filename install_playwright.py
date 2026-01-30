import subprocess
import sys

print("Installing Playwright browsers...")
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
print("Playwright Chromium installed successfully!")