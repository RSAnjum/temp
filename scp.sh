#!/bin/bash

# Copy files
scp -i keys/fnf.pem setup_and_run.sh ubuntu@ec2-13-60-61-212.eu-north-1.compute.amazonaws.com:
scp -i keys/fnf.pem testing/sandboxed_testing.py ubuntu@ec2-13-60-61-212.eu-north-1.compute.amazonaws.com:
scp -i keys/fnf.pem auto_accept_rides_prod.py ubuntu@ec2-13-60-61-212.eu-north-1.compute.amazonaws.com:
scp -i keys/fnf.pem requirements.txt ubuntu@ec2-13-60-61-212.eu-north-1.compute.amazonaws.com:

echo "Secure copy complete."
echo "ssh into the instance and run setup_and_run.sh to setup the environment and run the script."
echo "ssh -i key_name.pem ubuntu@instance_public_dns"