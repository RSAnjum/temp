# auto-accept-rides

### GAMEPLAN V1.0  
1. make a script that loads credentials from the website/ stores the session token
2. use those credentials in script to test functionality of V1.0 script
3. deply on docker on local machine and run test cases
4. check to see if the credentials expire
5. iterative improvements

### GAMEPLAN V1.1-V1.6
1. Debugging and fixing the ever living shit out of the script

### GAMEPLAN V1.7
0. Put the laptop in the honda -->> finetune the delays
1. Ready for deployment
2. Spin up a t2 or a t3 micro ec2 instance
3. sync up the code
4. run
5. let it go
6. Spread you wings beauty


# Automated Web Testing Setup on AWS EC2 with Chrome and Selenium

This document provides comprehensive instructions for setting up an automated web testing environment on an AWS EC2 t3.micro instance running Ubuntu.  It covers everything from instance creation to running your testing script (`auto_accept_rides_prod.py`).

## 1. AWS EC2 Instance Creation

1. **Log in to the AWS Management Console:** Go to [https://aws.amazon.com/console/](https://aws.amazon.com/console/) and log in to your AWS account.

2. **Navigate to EC2:** Go to the EC2 service.

3. **Launch Instance:** Click "Launch Instances."

4. **Choose an AMI:** Select an Ubuntu AMI (Amazon Machine Image).  Choose a recent version (e.g., Ubuntu 22.04 or 24.04).

5. **Instance Type:** Select `t3.micro` (or your preferred instance type).

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

## 2. Connecting to the EC2 Instance via SSH

Open your terminal (Linux/macOS) or PowerShell (Windows).

```bash
 ssh -i my-ec2-key.pem ubuntu@your_instance_public_dns_or_ip
```

## 3. Uploading Required Files

Once connected, upload the necessary scripts and files:

```bash
 scp -i my-ec2-key.pem setup.sh ubuntu@your_instance_public_dns_or_ip:
 scp -i my-ec2-key.pem sandboxed_testing.py ubuntu@your_instance_public_dns_or_ip:
 scp -i my-ec2-key.pem requirements.txt ubuntu@your_instance_public_dns_or_ip:
```

## 4. Running the Setup Script

Make the setup script executable:

```bash
chmod +x setup_and_run.sh
```

Run the setup script:

```bash
./setup_and_run.sh
```

### What the Setup Script Does:
- Installs base dependencies (`Python`, `pip`, `wget`, `unzip`, `curl`, `gnupg`).
- Sets non-interactive mode for `apt`.
- Adds the Google Chrome signing key and repository.
- Installs Google Chrome.
- Detects the Chrome version.
- Downloads and installs ChromeDriver.
- Creates a Python virtual environment.
- Installs Python dependencies from `requirements.txt` (or `selenium` as a fallback).

## 5. Running the Script Using Python Virtual Environment

### Activating the Virtual Environment

```bash
echo "Activate it with: source myenv/bin/activate"
```

### Runnin the script

```bash
echo "Run your script with: ./myenv/bin/python auto_accept_rides_prod.py"
```


## 6. Important Notes

### Security Considerations
- Do **not** expose port `22` (SSH) to the entire internet in a production environment.
- Use a bastion host or other secure methods to access your instances.

### Dependency Management
- Ensure a `requirements.txt` file is available, listing all necessary Python packages (e.g., `selenium`).
- `auto_accept_rides_prod.py` is the main Python script that performs web testing.

### Logging & Process Management
- The script writes its output to `auto_accept_rides_prod.log`.
- A virtual environment is used to isolate dependencies.
- ChromeDriver version compatibility is handled automatically.
- The setup script removes downloaded files after installation to reduce the image size.
- `auto_accept_rides_prod.py` runs in the background using `nohup`, allowing it to continue executing even after disconnection.

---

This guide ensures a streamlined setup for automated web testing on an EC2 instance with Chrome and Selenium.

