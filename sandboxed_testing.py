from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# Test site details
LOGIN_URL = "https://16.16.217.86:943/admin"
TARGET_URL = "https://16.16.217.86:943/admin/current_users"

def setup_driver(profile_name="AdminTestProfile"):
    # Set up Chrome options with persistent profile
    profile_dir = os.path.join(os.getcwd(), profile_name)
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    
    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    # Bypass "Not Secure" warnings
    chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
    chrome_options.add_argument("--allow-insecure-localhost")   # Allow insecure localhost connections
    chrome_options.add_argument("--disable-web-security")       # Disable web security restrictions
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # Uncomment for headless mode
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login(driver):
    print("Initiating login process...")
    driver.get(LOGIN_URL)
    time.sleep(2)

    try:
        # Prompt for username and password via terminal
        username = input("Enter username: ")
        password = input("Enter password: ")

        # Find login elements
        username_field = driver.find_element(By.ID, "username")
        password_field = driver.find_element(By.ID, "password")
        submit_button = driver.find_element(By.ID, "submit-button")

        # Enter credentials
        username_field.send_keys(username)
        password_field.send_keys(password)
        submit_button.click()

        # Wait for page to change (indicating login attempt)
        WebDriverWait(driver, 10).until(
            EC.url_changes(LOGIN_URL)
        )
        
        # Check if login was successful by verifying URL
        if driver.current_url != LOGIN_URL:
            print(f"Login successful! Redirected to: {driver.current_url}")
            return True
        else:
            print("Login failed: Still on login page")
            return False

    except Exception as e:
        print(f"Login error: {e}")
        return False

def check_session(driver):
    print("Checking existing session...")
    driver.get(TARGET_URL)
    time.sleep(2)

    try:
        # If we're still on login page, session is invalid
        if "admin" in driver.current_url and "current_users" in driver.current_url:
            print("Valid session found! Already logged in.")
            return True
        elif "admin" in driver.current_url and "current_users" not in driver.current_url:
            print("No valid session. Redirected to login page.")
            return False
        else:
            print(f"Unexpected URL after session check: {driver.current_url}")
            return False
    except Exception as e:
        print(f"Session check error: {e}")
        return False

def main():
    driver = setup_driver("AdminTestProfile")
    try:
        # Check for existing valid session
        if check_session(driver):
            print(f"Session is valid. Proceeding to {TARGET_URL}")
            driver.get(TARGET_URL)
        else:
            # No valid session, attempt login
            if login(driver):
                print(f"Login completed. Navigating to {TARGET_URL}")
                driver.get(TARGET_URL)
            else:
                print("Login failed. Exiting...")
                return

        # Keep browser open for 10 seconds to verify target page
        print(f"Current URL: {driver.current_url}")
        time.sleep(10)

    except Exception as e:
        print(f"Main error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()