#!/usr/bin/env python
"""
Enterprise AI Security Red Teaming Platform
Cross-platform startup script
"""
import os
import sys
import subprocess

def main():
    print("========================================")
    print("Enterprise AI Security Red Teaming Platform")
    print("Starting Backend Server...")
    print("========================================")
    
    # Get the backend directory
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Running as script
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    backend_dir = os.path.join(os.path.dirname(base_dir), 'backend')
    
    print(f"\nBackend directory: {backend_dir}")
    print("\nInstalling dependencies...")
    
    # Install dependencies
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                  cwd=backend_dir, capture_output=True)
    
    print("\nStarting server on port 8080...")
    print("Open http://localhost:8080 in your browser")
    print("========================================\n")
    
    # Start the server
    os.chdir(backend_dir)
    subprocess.run([sys.executable, '-m', 'uvicorn', 'app.main:app', 
                   '--host', '127.0.0.1', '--port', '8080'])

if __name__ == '__main__':
    main()
