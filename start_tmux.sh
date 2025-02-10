#!/bin/bash

if ! tmux has-session -t o2-session 2>/dev/null; then

# Start a new tmux session named "o2-session" and detach it
tmux new-session -d -s o2-session -n main

# Setup shared environment in first window
tmux send-keys -t o2-session "cd ~/o2-analyser" C-m
tmux send-keys -t o2-session "source o2-env/bin/activate" C-m

# Split both rows into 2 columns (for 2x2 layout)
tmux split-window -t o2-session:0.0 -h
tmux split-window -t o2-session:0.1 -h

# Run the correct commands in each pane
tmux send-keys -t o2-session:0.0 "cd ~/o2-analyser && source o2-env/bin/activate && python main.py" C-m
tmux send-keys -t o2-session:0.1 "cd ~/o2-analyser && source o2-env/bin/activate && sudo o2-env/bin/python -m gunicorn app:server -b 0.0.0.0:80" C-m
tmux send-keys -t o2-session:0.2 "cd ~/o2-analyser && source o2-env/bin/activate && sudo systemctl restart dhcpcd && sudo ip addr add 192.168.4.1/24 dev wlan0 && ip addr show wlan0 && hostname -I" C-m

# Attach session on manual start (optional)
tmux attach -t o2-session

fi
