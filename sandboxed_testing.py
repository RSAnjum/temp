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
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless=new")  # Updated headless mode
    chrome_options.add_argument("--window-size=1920,1080")  # Set explicit window size
    
    # Configure Chrome binary location (from previous installation)
    chrome_options.binary_location = '/opt/chrome/chrome'
    
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def login(driver):
    print("Initiating login process...")
    driver.get(LOGIN_URL)
    
    try:
        # Wait for page to fully load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "username"))
        )

        # Prompt for credentials
        username = input("Enter username: ")
        password = input("Enter password: ")

        # Find elements with explicit waits
        username_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "username"))
        )
        password_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "password"))
        )
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "submit-button"))
        )

        # Clear fields and enter credentials
        username_field.clear()
        username_field.send_keys(username)
        password_field.clear()
        password_field.send_keys(password)

        # Scroll into view and click using JavaScript
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        driver.execute_script("arguments[0].click();", submit_button)

        # Wait for page to change
        WebDriverWait(driver, 15).until(
            EC.url_contains("/admin")
        )
        
        # Check login success
        if "status_overview" in driver.current_url:
            print("Login successful!")
            return True
        else:
            print("Login failed - unexpected post-login URL:", driver.current_url)
            return False

    except Exception as e:
        print(f"Login error: {str(e)}")
        driver.save_screenshot("login_error.png")
        return False

def check_session(driver):
    print("Checking existing session...")
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        if "current_users" in driver.current_url:
            print("Valid session found!")
            return True
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