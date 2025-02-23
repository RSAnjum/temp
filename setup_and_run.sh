#!/bin/bash

# Exit on any error during setup
set -e

# Update package list and install base dependencies
echo "Installing base dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv wget unzip curl gnupg

# Set non-interactive mode for apt
export DEBIAN_FRONTEND=noninteractive
echo "DEBIAN_FRONTEND set to noninteractive"

# Add Google's signing key
echo "Adding Google Chrome signing key..."
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Add Chrome repository
echo "Adding Google Chrome repository..."
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list'

# Install Chrome
echo "Installing Google Chrome..."
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Get Chrome major version
echo "Detecting Chrome version..."
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d '.' -f 1)
echo "Chrome major version: $CHROME_VERSION"

# Download and install chromedriver-linux64
echo "Downloading and installing chromedriver-linux64 $LATEST_VERSION..."
sudo apt install chromium-chromedriver

# Create virtual environment
echo "Setting up virtual environment..."
rm -rf myenv   # Clean any old environment
python3 -m venv myenv

# Explicitly use the virtual environment's pip to install dependencies
echo "Installing Python dependencies from requirements.txt..."
VENV_PIP="./myenv/bin/pip"
if [ -f "requirements.txt" ]; then
    $VENV_PIP install --no-cache-dir -r requirements.txt
    echo "Python dependencies installed."
else
    echo "Error: requirements.txt not found. Installing selenium as a fallback..."
    $VENV_PIP install --no-cache-dir selenium
fi

# Verify pip works by listing installed packages
echo "Verifying pip installation..."
$VENV_PIP list

echo "Setup complete. Virtual environment 'myenv' is ready."
echo "Activate it with: source myenv/bin/activate"
echo "Run your script with: ./myenv/bin/python auto_accept_rides_prod.py"