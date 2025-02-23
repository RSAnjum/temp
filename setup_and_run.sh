#!/bin/bash

# Update system
sudo yum update -y

# Install necessary packages
sudo yum install -y python3 git
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
curl -O https://bootstrap.pypa.io/get-pip.py
python3 get-pip.py
sudo yum install -y Xvfb xorg-x11-xauth xorg-x11-utils xorg-x11-server-utils
sudo yum install -y libXfont xorg-x11-fonts* xorg-x11-server-Xvfb
sudo yum install -y alsa-lib cups-libs gtk3 libXScrnSaver libXcomposite libXcursor libXi libXtst nss pango GConf2 at-spi2-core
sudo yum install -y unzip jq curl

# Get the latest stable version of Chrome
LATEST_VERSION=$(curl -s https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json | jq -r '.channels.Stable.version')
echo "Latest stable version: $LATEST_VERSION"

# Download Chrome and ChromeDriver
wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$LATEST_VERSION/linux64/chrome-linux64.zip
wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/$LATEST_VERSION/linux64/chromedriver-linux64.zip

# Unzip and install
unzip chrome-linux64.zip
unzip chromedriver-linux64.zip

# Move to standard locations
sudo mv chrome-linux64 /opt/chrome
sudo mv chromedriver-linux64 /opt/chromedriver

# Create symlinks
sudo ln -s /opt/chrome/chrome /usr/local/bin/google-chrome
sudo ln -s /opt/chromedriver/chromedriver /usr/local/bin/chromedriver

# Verify versions
google-chrome --version
chromedriver --version

# Install additional dependencies
sudo curl https://intoli.com/install-google-chrome.sh | bash
sudo ln -s /usr/bin/google-chrome /usr/bin/chromium
chromedriver --version
google-chrome --version
sudo yum install -y gtk3-devel gtk2-devel libnotify-devel GConf2 nss libXScrnSaver alsa-lib

# Install Python packages
pip3 install selenium webdriver-manager pyvirtualdisplay

# Setup virtual framebuffer and DISPLAY environment
Xvfb :99 -screen 0 1920x1080x24 > /dev/null 2>&1 &
export DISPLAY=:99

echo "Setup complete."
echo "Run your script with:python auto_accept_rides_prod.py"