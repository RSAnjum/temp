#!/bin/bash

# Variables (adjust these as needed)
SERVICE_NAME="AutoStartPythonScript"
WORKING_DIR="/home/ec2-user"
USER="ec2-user"
SCREEN_SESSION_NAME="my_script_session"
OUTPUT_LOG="/home/ec2-user/output.log"
ERROR_LOG="/home/ec2-user/error.log"

# Path to the service file
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

# Check if the script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Use sudo."
  exit 1
fi

# Check if the working directory exists
if [ ! -d "$WORKING_DIR" ]; then
  echo "Error: Working directory $WORKING_DIR does not exist"
  exit 1
fi

# Create the service file
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=My Python Script in Screen
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/home/ec2-user/start_python_in_screen.sh
WorkingDirectory=$WORKING_DIR
User=$USER
StandardOutput=file:$OUTPUT_LOG
StandardError=file:$ERROR_LOG
KillMode=control-group
ExecStartPost=/bin/sleep 2

[Install]
WantedBy=multi-user.target
EOF

# Set appropriate permissions for the service file
chmod 644 "$SERVICE_FILE"

# Reload systemd daemon to recognize the new service
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable "$SERVICE_NAME.service"

# Start the service
systemctl start "$SERVICE_NAME.service"

# Check the status of the service
echo "Service created and started. Checking status..."
systemctl status "$SERVICE_NAME.service"

echo "Service setup complete!"
echo "To attach to the screen session, run: screen -r $SCREEN_SESSION_NAME"
echo "To detach from the screen session, press Ctrl+A, then D"