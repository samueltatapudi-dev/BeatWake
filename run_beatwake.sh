#!/bin/bash

# Check if running in a display environment
if [ -z "$DISPLAY" ]; then
    echo "No display detected. Starting with virtual display (Xvfb)..."
    
    # Check if xvfb is installed
    if ! command -v xvfb-run &> /dev/null; then
        echo "Installing Xvfb..."
        sudo apt-get update && sudo apt-get install -y xvfb
    fi
    
    # Run with virtual display
    xvfb-run -a python /workspaces/BeatWake/BeatWake-SourceCode.py
else
    echo "Display detected: $DISPLAY"
    python /workspaces/BeatWake/BeatWake-SourceCode.py
fi
