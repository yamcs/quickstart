#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're on Linux or macOS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Check if gnome-terminal exists
    if command_exists gnome-terminal; then
        # Launch YAMCS in new tab
        gnome-terminal --tab --title="MCS_TAB" -- bash -c "cd MCS && ./mvnw yamcs:run; exec bash"
        
        # Wait a bit for YAMCS to start
        sleep 5
        
        # Launch simulator in new tab
        gnome-terminal --tab --title="SIM_TAB" -- bash -c "cd SIM && python3 simulator_runtime.py; exec bash"
    else
        echo "gnome-terminal not found. Please install it or modify script for your terminal."
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e '
        tell application "Terminal"
            # Launch YAMCS
            do script "cd '$(pwd)'/MCS && ./mvnw yamcs:run"
            delay 5
            # Launch Simulator
            do script "cd '$(pwd)'/SIM && python3 simulator_runtime.py"
        end tell
    '
else
    echo "Unsupported operating system"
    exit 1
fi
