#!/bin/bash

SCREEN_SESSION_NAME="my_script_session"
PYTHON_SCRIPT="/home/ec2-user/opb.py"
WORKING_DIR="/home/ec2-user"
PID_FILE="/home/ec2-user/screen_pid"

echo "Starting script at $(date)" >&2
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "Error: Python script not found at $PYTHON_SCRIPT" >&2
    exit 1
fi

cd "$WORKING_DIR" || {
    echo "Failed to change to $WORKING_DIR" >&2
    exit 1
}

echo "Launching screen session..." >&2
# Run screen in detached mode with explicit command execution
/usr/bin/screen -dmS "$SCREEN_SESSION_NAME" /bin/bash -c "/usr/bin/python3 $PYTHON_SCRIPT"

# Wait for the session to initialize
sleep 2

# Check if the session is running and get its PID
SESSION_PID=$(sudo -u ec2-user /usr/bin/screen -ls | grep "$SCREEN_SESSION_NAME" | awk '{print $1}' | cut -d'.' -f1)
if [ -n "$SESSION_PID" ]; then
    echo "$SESSION_PID" > "$PID_FILE"
    echo "Screen session '$SCREEN_SESSION_NAME' started successfully with PID $SESSION_PID at $(date)"
else
    echo "Failed to start screen session '$SCREEN_SESSION_NAME' at $(date)" >&2
    echo "Screen listing: $(sudo -u ec2-user /usr/bin/screen -ls)" >&2
    exit 1
fi