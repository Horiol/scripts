#!/bin/bash

# Exit on error, undefined variables, and propagate pipe failures
set -euo pipefail

OBSIDIAN_DIR="$HOME/Obsidian"
OBSIDIAN_APP="/snap/bin/obsidian"

# Function to clean up on exit
cleanup() {
    # Only attempt unmount if we mounted it in this script
    if [[ -n "${mounted_by_script:-}" ]]; then
        echo "Cleaning up mount point..."
        fusermount -u "$OBSIDIAN_DIR" || true
    fi
}

# Register cleanup function
trap cleanup EXIT

# Check if directory exists
if [[ ! -d "$OBSIDIAN_DIR" ]]; then
    echo "Creating Obsidian directory at $OBSIDIAN_DIR"
    mkdir -p "$OBSIDIAN_DIR"
fi

# Check if already mounted
if mount | grep -q "$OBSIDIAN_DIR"; then
    echo "Drive already mounted at $OBSIDIAN_DIR"
else
    echo "Mounting Drive to $OBSIDIAN_DIR..."
    rclone mount Drive:Obsidian $OBSIDIAN_DIR --allow-non-empty --daemon
    
    # Mark that we mounted it in this script
    mounted_by_script=1
    
    # Wait for mount to be ready (max 10 seconds)
    max_attempts=10
    attempts=0
    while ! mount | grep -q "$OBSIDIAN_DIR"; do
        sleep 1
        ((attempts++))
        echo "Waiting for mount to be ready... ($attempts/$max_attempts)"
        if [[ $attempts -ge $max_attempts ]]; then
            echo "Failed to mount Drive. Check your rclone configuration."
            exit 1
        fi
    done
    echo "Drive successfully mounted"
fi

# Check if Obsidian exists
if [[ ! -f "$OBSIDIAN_APP" ]]; then
    echo "Error: Obsidian application not found at $OBSIDIAN_APP"
    exit 1
fi

# Launch Obsidian
echo "Launching Obsidian..."
"$OBSIDIAN_APP" &

# Allow Obsidian to start before script exits
sleep 2
echo "Script completed successfully"

exit 0

