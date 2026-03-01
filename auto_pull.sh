#!/bin/bash
# Navigate to your repo
cd /data/data/com.termux/files/home/open-vulnera

# Start infinite loop
while true; do
    echo "[$(date)] Pulling latest changes..."
    git pull
    sleep 5
done
