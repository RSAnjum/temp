# auto-accept-rides

# Automated Web Testing Setup on AWS EC2 with Chrome and Selenium

This document provides comprehensive instructions for setting up an automated web testing environment on an AWS EC2 t3.micro instance running Ubuntu.  It covers everything from instance creation to running your testing script (`auto_accept_rides_prod.py`).

## 1. AWS EC2 Instance Creation

1. **Log in to the AWS Management Console:** Go to [https://aws.amazon.com/console/](https://aws.amazon.com/console/) and log in to your AWS account.

2. **Navigate to EC2:** Go to the EC2 service.

3. **Launch Instance:** Click "Launch Instances."

4. **Choose an AMI:** Select Amazon Linux AMI (Amazon Machine Image).  Choose a recent version (e.g., AL2023 or AL2022).

5. **Instance Type:** Select `t3.micro` (t3.micro offers 750 Hours or 1 year Hosting Free whichever one comes first).

6. **Key Pair:**
   - **Create a new key pair:**  Give it a descriptive name (e.g., `my-ec2-key`). Download the `.pem` file.  **Keep this file secure!**  You will need it to connect to your instance.  Change permission of the .pem file: `chmod 400 my-ec2-key.pem`
   - **(Optional) Choose an existing key pair:** If you already have a key pair, select it.

7. **Network Settings (Security Groups):**
   - Create a new security group or modify an existing one.
   - Add a rule to allow SSH traffic (port 22) from your IP address or a trusted range of IP addresses.  This is *crucial* for connecting to your instance.  For testing, you might temporarily allow from 0.0.0.0/0 (all IPs) but **do not do this in production**.

8. **Storage:** Accept the default storage settings or customize as needed.

9. **Advanced Details (Optional):**  You can leave these as default for this setup.

10. **Review and Launch:** Review your settings and launch the instance.

11. **Get Public DNS/IP:** After the instance is running, you'll need its public DNS name or IP address.  You can find this in the EC2 console, under the "Instances" tab.

# EC2 Deployment for Python Script

This repository contains scripts to deploy and run a Python script on an EC2 instance as a persistent service.

## Overview

The deployment process consists of three main steps:
1. **Copy Files**: Transfer necessary files to the EC2 instance
2. **Install Dependencies**: Set up the environment with required packages
3. **Create Service**: Configure a systemd service for persistent execution

## Files

- `scp.sh` - Script to copy files to EC2 instance
- `setup_and_run.sh` - Script to install dependencies and set up the environment
- `create_service.sh` - Script to create a systemd service
- `start_python_in_screen.sh` - Script to run python script in screen by system service
- `opb.py` - Main Python script to run (your application)

## Deployment Instructions

### Step 1: Copy Files to EC2 Instance

Run the `copy_files.sh` script to transfer all required files to your EC2 instance:

```bash
chmod +x scp.sh
./scp.sh
```

Make sure to update the script with your:
- SSH key file path
- EC2 instance username
- EC2 instance public DNS

### Step 2: Prepare scripts

SSH into your EC2 instance and run the setup script:

```bash
ssh -i your_key.pem user@instance_public_dns
```

## Convert from windows CRLF line endings to unix style

```bash
sudo yum install -y dos2unix
dos2unix ./setup_and_run.sh
dos2unix ./create_service.sh
dos2unix ./start_python_in_screen_sh.sh
```

## Make them execuatable

```bash
chmod+x ./setup_and_run.sh
chmod+x ./create_service.sh
chmod+x ./start_python_in_screen.sh
```

### Step 3: Install dependencies

```bash
./setup_and_run.sh
```

This script:
- Updates the system
- Installs Python 3 and other required packages
- Sets up Chrome and ChromeDriver
- Installs necessary system dependencies
- Installs required Python packages (selenium, webdriver-manager, pyvirtualdisplay, screen)

### Step 4: Create and Configure Service

Run the service creation script to set up a systemd service:

```bash
sudo ./create_service.sh
```

This script:
- Creates a systemd service file
- Configures the service to run your Python script in a screen session
- Enables the service to start automatically on boot
- Starts the service

## Working with the Service

### Service Management

```bash
# Check status
sudo systemctl status AutoStartPythonScript

# Start service
sudo systemctl start AutoStartPythonScript

# Stop service
sudo systemctl stop AutoStartPythonScript

# Restart service
sudo systemctl restart AutoStartPythonScript
```

### Screen Session Management

The Python script runs in a screen session:

```bash
# Attach to screen session
screen -r my_script_session

# Detach from screen (without stopping)
# Press Ctrl+A, then D
```

## Logs

Logs are stored at:
- Standard output: `/home/ec2-user/output.log`
- Standard error: `/home/ec2-user/error.log`

## Customization

Edit the `create_service.sh` script to customize:
- Service name
- Script path
- Working directory
- User
- Screen session name
- Log file locations