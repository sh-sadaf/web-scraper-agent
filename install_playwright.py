#!/usr/bin/env python3
"""
Script to install Playwright browsers manually if needed.
Run this script if the automatic installation in streamlit_app.py fails.
"""

import subprocess
import sys

def install_playwright_browsers():
    """Install Playwright browsers"""
    print("Installing Playwright browsers...")
    print("This may take a few minutes...")
    
    try:
        # Install chromium browser
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], check=True, capture_output=True, text=True)
        
        print("✅ Playwright browsers installed successfully!")
        print("You can now run your Streamlit app.")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        print(f"Error output: {e.stderr}")
        return False

if __name__ == "__main__":
    install_playwright_browsers()
