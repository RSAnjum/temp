#!/bin/bash

# Copy files
echo "Copy Files:"
scp -i ssh_key.pem opb.py user@instance_public_dns:
scp -i ssh_key.pem create_service.sh user@instance_public_dns:
scp -i ssh_key.pem setup_and_run.sh user@instance_public_dns:
scp -i ssh_key.pem start_python_in_screen.sh user@instance_public_dns:

echo "Secure copy complete."
echo "ssh -i key_name.pem user@instance_public_dns"
echo "Run: sudo yum install -y dos2unix"
echo "Convert from windows CRLF line endings to Unix style"
echo "Run: dos2unix ./setup_and_run.sh"
echo "Run: dos2unix ./create_service.sh"
echo "Run: dos2unix ./start_python_in_screen.sh"
echo "Make scripts executable"
echo "Run: chmod +x ./setup_and_run.sh"
echo "Run: chmod +x ./create_service.sh"
echo "Run: chmod +x ./start_python_in_screen.sh"
echo "Run: ./setup_and_run.sh to install dependencies"