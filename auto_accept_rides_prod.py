from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
import os
import logging

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set the logging level

# Define the format for log messages
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler to write logs to 'auto_accept_dev.log'
file_handler = logging.FileHandler('auto_accept_prod.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)

# Stream handler to output logs to the terminal
stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(log_format)

# Clear any existing handlers (optional, to avoid duplicates if re-running in some environments)
logger.handlers = []

# Add both handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(stream_handler)

# Define ride parameters (unchanged)
RIDE_PARAMETERS = [
    {"type": "Ride", "payout": 150, "driver": "Raza Ul Habib Tahir", "vehicle": "FR19 DZG"},
    {"type": "Business", "payout": 120, "driver": "Raza Ul Habib Tahir", "vehicle": "FR19 DZG"},
    {"type": "First", "payout": 90, "driver": "Raza Ul Habib Tahir", "vehicle": "KM19 WDS"},
    {"type": "Business XL", "payout": 120, "driver": "Raza Ul Habib Tahir", "vehicle": "KX19UBY"},
    {"type": "Ride XL", "payout": 120, "driver": "Raza Ul Habib Tahir", "vehicle": "KX19UBY"}
]

accepted_rides = set()

def login(driver):
    logging.info("Initiating login process...")
    driver.get("https://dcp.orange.sixt.com/login")
    time.sleep(2)

    # Select country code (+44) with mouse event
    country_dropdown = driver.find_element(By.CSS_SELECTOR, ".react-select-container.country-code")
    ActionChains(driver).move_to_element(country_dropdown).click().perform()
    time.sleep(0.5)
    
    country_options = driver.find_elements(By.CLASS_NAME, "react-select__option")
    for option in country_options:
        if "+92" in option.text:
            ActionChains(driver).move_to_element(option).click().perform()
            break
    
    # Enter phone number (no click needed)
    phone_input = driver.find_element(By.CLASS_NAME, "phone-number")
    phone_input.send_keys("3157726586")
    
    # Click Get PIN button with mouse event
    get_pin_button = driver.find_element(By.CLASS_NAME, "get-pin")
    ActionChains(driver).move_to_element(get_pin_button).click().perform()
    
    # Wait for user to input PIN
    logging.info("Please enter the PIN you received:")
    pin = input("Enter PIN: ")
    
    # Enter PIN (no click needed)
    pin_input = driver.find_element(By.CLASS_NAME, "otp")
    pin_input.send_keys(pin)
    
    # Click Sign In button with mouse event
    sign_in_button = driver.find_element(By.CLASS_NAME, "sign-in")
    ActionChains(driver).move_to_element(sign_in_button).click().perform()
    
    time.sleep(3)
    return driver.current_url != "https://dcp.orange.sixt.com/login"

def check_session(driver):
    logging.info("Checking session...")
    driver.get("https://dcp.orange.sixt.com/availableRides")
    time.sleep(2)
    return "login" not in driver.current_url

def check_for_matching_rides(driver):
    """Check and accept matching rides from the table."""
    logging.info("Listening for rides...")
    try:
        wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds for elements
        no_rides_counter = 0  # Counter for consecutive no matching rides
        
        while True:  # Keep looping until no more rides are processed
            # Find all ride rows
            ride_rows = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.available-rides-table tbody tr')))
            logging.info(f"Found {len(ride_rows)} ride rows.")
            rides_processed = False  # Track if we processed any rides this loop
            
            for row in ride_rows:
                try:
                    # Extract ride details
                    ride_type = row.find_element(By.CLASS_NAME, 'class').text.strip()
                    payout_text = row.find_element(By.CLASS_NAME, 'payout').text.replace('£', '').strip()
                    try:
                        payout = float(payout_text)
                    except ValueError:
                        logging.warning(f"Could not convert payout text to float: {payout_text}")
                        continue  # Skip this ride if payout conversion fails

                    logging.info(f"Processing ride: {ride_type} - £{payout}")
                    accept_button = row.find_element(By.CLASS_NAME, 'button.button-outline')

                    # Check if this ride matches any parameters
                    for param in RIDE_PARAMETERS:
                        ride_key = f"{ride_type}-{payout}"
                        if (ride_type == param["type"] and 
                            payout >= param["payout"] and 
                            ride_key not in accepted_rides):
                            logging.info(f"Accepting ride: {ride_type} - £{payout}")
                            accepted_rides.add(ride_key)
                            
                            # Click the accept button
                            ActionChains(driver).move_to_element(accept_button).click().perform()
                            time.sleep(2)  # Wait for modal to appear
                            
                            # Handle the modal
                            handle_modal_reopen(driver, lambda: select_driver_and_vehicle(driver, param["driver"], param["vehicle"]))
                            
                            # Wait for modal to close
                            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal")))
                            logging.info("Modal closed successfully.")
                            
                            accepted_rides.remove(ride_key)  # Clear from tracking
                            rides_processed = True
                            no_rides_counter = 0  # Reset counter after processing a ride
                            break  # Exit parameter loop after accepting
                except Exception as e:
                    logging.warning(f"Error processing ride: {e}")
                    continue  # Move to next ride if something fails
            
            if not rides_processed:
                logging.info("No more matching rides found.")
                no_rides_counter += 1  # Increment counter if no rides were processed
                if no_rides_counter >= 5:  # Refresh page after 5 consecutive no matching rides
                    logging.info("Refreshing page due to no matching rides found for 5 consecutive checks.")
                    driver.refresh()
                    no_rides_counter = 0  # Reset counter after refresh
                time.sleep(5)  # Wait for 5 seconds before re-checking the table
            else:
                time.sleep(1)  # Small delay before re-checking the table
        
    except Exception as e:
        logging.error(f"Error in ride checking: {e}")
        driver.refresh()  # Refresh page if something goes wrong
        time.sleep(3)

def handle_modal_reopen(driver, callback):
    logging.info("Handling modal state...")
    wait = WebDriverWait(driver, 10)
    
    try:
        modal = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal")))
        logging.info("Modal detected.")
        
        if modal.is_displayed():
            logging.info("Modal is open. Proceeding with callback...")
            callback()
        else:
            logging.warning("Modal visible but not displayed. Attempting callback anyway...")
            callback()
    except TimeoutException:
        logging.warning("Modal not found within 10 seconds. Refreshing page...")
        driver.refresh()
        time.sleep(3)
        try:
            modal = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal")))
            if modal.is_displayed():
                logging.info("Modal appeared after refresh. Proceeding...")
                callback()
            else:
                logging.warning("Modal still not usable after refresh. Skipping...")
        except Exception as e:
            logging.error(f"Retry failed: {e}")
    except Exception as e:
        logging.error(f"Modal handling error: {e}", exc_info=True)
        driver.refresh()
        time.sleep(3)

def select_driver_and_vehicle(driver, driver_name, vehicle_name):
    logging.info(f"Selecting driver: {driver_name} and vehicle: {vehicle_name}")
    wait = WebDriverWait(driver, 10)
        
    try:
        driver_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#react-select-2-input")))
        parent_dropdown = driver_dropdown.find_element(By.XPATH, "..")
        
        if is_dropdown_on_select(parent_dropdown):
            ActionChains(driver).move_to_element(parent_dropdown).click().perform()
            # Wait for dropdown menu to appear
            try:
                WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".react-select__menu"))
                )
            except TimeoutException:
                logging.error("Driver dropdown menu did not open.")
                return
            driver_option = get_dropdown_option(driver, driver_name)
            if driver_option:
                driver.execute_script("arguments[0].click();", driver_option)
                logging.info(f"Driver selected: {driver_name}")
                select_vehicle(driver, vehicle_name)
            else:
                logging.warning(f"Driver '{driver_name}' not found in dropdown.")
        else:
            logging.info("Driver dropdown not in 'Select' state.")
    except TimeoutException:
        logging.warning(f"Timeout waiting for driver dropdown to be clickable. Refreshing...")
        driver.refresh()
        time.sleep(3)
    except NoSuchElementException as e:
        logging.error(f"Driver dropdown element not found: {e}")
        driver.refresh()
        time.sleep(3)
    except StaleElementReferenceException as e:
        logging.error(f"Stale element in driver selection: {e}")
        driver.refresh()
        time.sleep(3)
    except Exception as e:
        logging.error(f"Unexpected error selecting driver: {e}", exc_info=True)
        driver.refresh()
        time.sleep(3)

def select_vehicle(driver, vehicle_name):
    logging.info(f"Selecting vehicle: {vehicle_name}")
    wait = WebDriverWait(driver, 10)
    
    try:
        vehicle_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#react-select-3-input")))
        parent_dropdown = vehicle_dropdown.find_element(By.XPATH, "..")
        
        logging.info(f"Available vehicle options: {[option.text for option in driver.find_elements(By.CLASS_NAME, 'react-select__option')]}")

        if is_dropdown_on_select(parent_dropdown):
            ActionChains(driver).move_to_element(parent_dropdown).click().perform()  # Already using mouse event
            time.sleep(0.2)
            
            vehicle_option = get_dropdown_option(driver, vehicle_name)
            if vehicle_option:
                ActionChains(driver).move_to_element(vehicle_option).click().perform()  # Mouse event for option
                logging.info(f"Vehicle selected: {vehicle_name}")
                
                # Commented-out when push to production
                cancel_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".close-button.btn.btn-primary")))
                ActionChains(driver).move_to_element(cancel_button).click().perform()  # Mouse event for cancel
                logging.info("Cancel button pressed")

                # Commented-out when testing
                # accept_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".update-button.btn.btn-primary")))
                # ActionChains(driver).move_to_element(accept_button).click().perform()
                # logging.info("Accept button pressed")

                time.sleep(10)
                driver.refresh()
            else:
                logging.warning(f"Vehicle '{vehicle_name}' not found in dropdown.")
        else:
            logging.info("Vehicle dropdown not in 'Select' state.")
    except TimeoutException:
        logging.warning(f"Timeout waiting for vehicle dropdown to be clickable. Refreshing...")
        driver.refresh()
        time.sleep(3)
    except NoSuchElementException as e:
        logging.error(f"Vehicle dropdown element not found: {e}")
        driver.refresh()
        time.sleep(3)
    except StaleElementReferenceException as e:
        logging.error(f"Stale element in vehicle selection: {e}")
        driver.refresh()
        time.sleep(3)
    except Exception as e:
        logging.error(f"Unexpected error selecting vehicle: {e}", exc_info=True)
        driver.refresh()
        time.sleep(3)

def is_dropdown_on_select(dropdown):
    try:
        value_container = dropdown.find_element(By.CLASS_NAME, "react-select__single-value")
        return value_container.text.strip() == "Select"
    except NoSuchElementException:
        return True  # Assume selectable if no value is present

def get_dropdown_option(driver, text):
    try:
        # Wait for the dropdown menu to appear
        menu = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".react-select__menu"))
        )
        options = menu.find_elements(By.CLASS_NAME, "react-select__option")
        for option in options:
            if option.text.strip() == text:
                return option
        logging.warning(f"Option '{text}' not found in menu. Available options: {[o.text.strip() for o in options]}")
        return None
    except TimeoutException:
        logging.error("Dropdown menu did not appear.")
        return None
    except Exception as e:
        logging.error(f"Error getting dropdown option: {e}")
        return None

def main():
    chrome_options = Options()
    profile_dir = os.path.join(os.getcwd(), "AutoAcceptProfile")
    if not os.path.exists(profile_dir):
        os.makedirs(profile_dir)
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--headless")  # Uncomment for headless mode
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        if not check_session(driver):
            if not login(driver):
                logging.error("Login failed. Exiting...")
                return
            logging.info("Login successful!")
        
        driver.get("https://dcp.orange.sixt.com/availableRides")
        time.sleep(3)

        while True:
            check_for_matching_rides(driver)
            time.sleep(1.5)
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
    finally:
        driver.quit()

if __name__ == "__main__":
    main()