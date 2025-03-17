from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os
import time
import logging
from datetime import datetime
import json

# Logger setup
logger = logging.getLogger()
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler = logging.FileHandler('auto_accept_notification.log')
file_handler.setFormatter(log_format)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_format)
logger.handlers = [file_handler, stream_handler]

# Set to True for testing, False for production
testing_mode = False

# Define ride parameters
RIDE_PARAMETERS = [
    {"type": "Ride", "payout": 80, "driver": "Raza Ul Habib Tahir", "vehicle": "FR19 DZG"},
    {"type": "Business", "payout": 80, "driver": "Raza Ul Habib Tahir", "vehicle": "FR19 DZG"},
    {"type": "First", "payout": 80, "driver": "Raza Ul Habib Tahir", "vehicle": "KM19 WDS"},
    {"type": "Business XL", "payout": 150, "driver": "Raza Ul Habib Tahir", "vehicle": "KX19 UBY"},
    {"type": "Ride XL", "payout": 150, "driver": "Raza Ul Habib Tahir", "vehicle": "KX19 UBY"}
]

# File paths
ACCEPTED_RIDES_FILE = 'accepted_rides.json'
IGNORED_RIDES_FILE = 'ignored_rides.json'
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Load and save ride data
def load_ride_data():
    accepted_rides = set()
    ignored_rides = set()
    try:
        filepath = os.path.join(SCRIPT_DIR, ACCEPTED_RIDES_FILE)
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                accepted_rides = set(json.load(file))
    except Exception as e:
        logging.error(f"Error loading accepted rides: {e}")
    try:
        filepath = os.path.join(SCRIPT_DIR, IGNORED_RIDES_FILE)
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                ignored_rides = set(json.load(file))
    except Exception as e:
        logging.error(f"Error loading ignored rides: {e}")
    return accepted_rides, ignored_rides

def save_ride_data(accepted_rides, ignored_rides):
    try:
        with open(os.path.join(SCRIPT_DIR, ACCEPTED_RIDES_FILE), 'w') as file:
            json.dump(list(accepted_rides), file)
        with open(os.path.join(SCRIPT_DIR, IGNORED_RIDES_FILE), 'w') as file:
            json.dump(list(ignored_rides), file)
    except Exception as e:
        logging.error(f"Error saving ride data: {e}")

accepted_rides, ignored_rides = load_ride_data()

def login(driver):
    driver.get("https://dcp.orange.sixt.com/login")
    wait = WebDriverWait(driver, 2, poll_frequency=0.1)
    try:
        country_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".react-select-container.country-code")))
        ActionChains(driver).click(country_dropdown).perform()
        country_options = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "react-select__option")))
        for option in country_options:
            if "+92" in option.text:
                ActionChains(driver).click(option).perform()
                break
        phone_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "phone-number")))
        phone_input.send_keys("3157726586")
        get_pin_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "get-pin")))
        ActionChains(driver).click(get_pin_button).perform()
        logging.info("Enter the PIN:")
        pin = input("Enter PIN: ")
        pin_input = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "otp")))
        pin_input.send_keys(pin)
        sign_in_button = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "sign-in")))
        ActionChains(driver).click(sign_in_button).perform()
        wait.until(lambda d: d.current_url != "https://dcp.orange.sixt.com/login")
        return True
    except Exception as e:
        logging.error(f"Login failed: {e}")
        return False

def check_session(driver):
    driver.get("https://dcp.orange.sixt.com/availableRides")
    wait = WebDriverWait(driver, 2, poll_frequency=0.1)
    try:
        wait.until(lambda d: "login" not in d.current_url)
        return True
    except TimeoutException:
        return False

def get_reservation_ids(driver):
    """Extract all reservation IDs from the table."""
    try:
        wait = WebDriverWait(driver, 2, poll_frequency=0.1)
        reservation_elements = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".reservation-details .reservation-id")))
        reservation_ids = [elem.text.strip() for elem in reservation_elements]
        logging.info(f"Extracted reservation IDs: {reservation_ids}")
        return reservation_ids
    except Exception as e:
        logging.error(f"Error extracting reservation IDs: {e}")
        return []

def accept_new_ride(driver, existing_ids):
    """Identify the new reservation ID and click its Accept button."""
    try:
        wait = WebDriverWait(driver, 10, poll_frequency=0.5)
        current_ids = get_reservation_ids(driver)
        new_ids = [rid for rid in current_ids if rid not in existing_ids]

        if new_ids:
            new_id = new_ids[0]
            logging.info(f"New reservation ID detected: {new_id}")
            # Find all table rows within tbody
            row_elements = driver.find_elements(By.CSS_SELECTOR, "tbody tr")
            for row in row_elements:
                id_element = row.find_element(By.CSS_SELECTOR, ".reservation-id")
                if id_element.text.strip() == new_id:
                    accept_button = row.find_element(By.CSS_SELECTOR, ".accept-ride button.button")
                    accept_button.click()
                    logging.info(f"Clicked 'Accept' button for reservation ID: {new_id}")
                    break
            return new_id
        else:
            logging.info("No new reservation IDs found.")
            return None
    except Exception as e:
        logging.error(f"Error accepting new ride: {e}")
        return None


def handle_notifications(driver, initial_reservation_ids):
    """Enable and intercept browser notifications, then accept new rides."""
    logging.info("Setting up notification permissions and interception...")
    script = """
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
    window.notifications = [];
    window.originalNotification = Notification;
    window.Notification = function(title, options) {
        var notification = new window.originalNotification(title, options);
        window.notifications.push({title: title, options: options, timestamp: Date.now()});
        console.log('Notification intercepted:', title, options);
        return notification;
    };
    window.Notification.prototype = window.originalNotification.prototype;
    window.Notification.permission = window.originalNotification.permission;
    """
    driver.execute_script(script)
    logging.info("Notification interception enabled")

    wait = WebDriverWait(driver, 2, poll_frequency=0.1)  # Reduced timeout from 3 to 2
    poll_interval = 0.2  # Increased from 0.1 to 0.5 for efficiency
    notification_count = 0
    existing_ids = initial_reservation_ids

    while True:
        try:
            notifications = driver.execute_script("""
            return window.notifications.splice(0, window.notifications.length).filter(n => 
                n.timestamp > Date.now() - 3600000);
            """)
            if notifications:
                for notification in notifications:
                    notification_count += 1
                    title = notification.get('title', 'No Title')
                    options = notification.get('options', {})
                    body = options.get('body', 'No Body')
                    timestamp = notification.get('timestamp')

                    logging.info(f"Notification received - Title: '{title}', Body: '{body}'")
                    logging.info(f"Total notifications received: {notification_count}")

                    if title == "New Ride":
                        logging.info("New ride notification detected")
                        try:
                            reset_all_button = driver.find_element(By.CLASS_NAME, "clear-filter")
                            reset_all_button.click()
                            logging.info("Clicked 'Reset All' button")
                        except TimeoutException:
                            logging.error("Reset All button not found")
                            driver.refresh()
                            continue

                        new_id = accept_new_ride(driver, existing_ids)
                        if new_id:
                            existing_ids.append(new_id)
                        
                        try:
                            modal = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal")))
                            if modal.is_displayed():
                                logging.info("Modal is visible, processing...")
                                process_modal_after_notification(driver)
                            else:
                                logging.warning("Modal element found but not displayed")
                                continue
                        except TimeoutException:
                            logging.warning("Modal not appeared")
                            continue
                    else:
                        logging.info(f"Notification skipped - Title: {title}")
        except Exception as e:
            logging.error(f"Error in notification handling loop: {e}")

def is_within_16_hours(time_str):
    try:
        now = datetime.now()
        if "Tomorrow" in time_str:
            # Handle "Tomorrow HH:MM" format
            time_parts = time_str.replace("Tomorrow", "").strip().split(":")
            tomorrow = now.replace(day=now.day + 1, hour=int(time_parts[0]), minute=int(time_parts[1]), second=0, microsecond=0)
            # Calculate hours difference
            hours_diff = (tomorrow - now).total_seconds() / 3600
            return hours_diff < 16
        elif "Today" in time_str:
            # Handle "Today HH:MM" format
            time_parts = time_str.replace("Today", "").strip().split(":")
            today = now.replace(hour=int(time_parts[0]), minute=int(time_parts[1]), second=0, microsecond=0)
            # Calculate hours difference
            hours_diff = (today - now).total_seconds() / 3600
            return hours_diff < 16
        else:
            # Original format handling (d/m/Y H:M)
            ride_time = datetime.strptime(time_str, '%d/%m/%Y %H:%M')
            return (ride_time - now).total_seconds() < 57600  # 16 hours in seconds (16 * 60 * 60)
    except Exception as e:
        logging.error(f"Error parsing time '{time_str}': {e}")
        # Default to True for safety (better to reject than accept wrongly)
        return True

def process_modal_after_notification(driver):
    wait = WebDriverWait(driver, 10, poll_frequency=0.1)  # Increased timeout to 10s
    try:
        modal = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal")))
        logging.info("Modal is visible")
        modal_title = modal.find_element(By.CSS_SELECTOR, ".modal-header .modal-title").text.strip()
        booking_id = modal_title.split("|")[0].replace("Booking Id:", "").strip()
        ride_type = modal_title.split("|")[1].split("-")[-1].strip() if "-" in modal_title else modal_title.split("|")[1].strip()
        payout = float(modal.find_element(By.CSS_SELECTOR, ".modal-body .payout .head-value").text.replace('£', '').strip())
        departure_time = modal.find_element(By.CSS_SELECTOR, ".modal-body .date-time .head-value").text.strip()

        logging.info(f"Processing modal for Booking ID: {booking_id}, Ride Type: {ride_type}, Payout: £{payout}, Departure Time: {departure_time}")

        if booking_id in accepted_rides or booking_id in ignored_rides:
            logging.info(f"Booking ID {booking_id} already in accepted or ignored rides, closing modal")
            close_modal(driver)
            logging.info(f"Modal closed for Booking ID: {booking_id}")
            return False

        if is_within_16_hours(departure_time):
            logging.info(f"Booking ID {booking_id} is within 16 hours (Departure: {departure_time}), ignoring")
            ignored_rides.add(booking_id)
            save_ride_data(accepted_rides, ignored_rides)
            logging.info(f"Booking ID {booking_id} added to ignored_rides")
            close_modal(driver)
            logging.info(f"Modal closed for Booking ID: {booking_id}")
            return False
        else:
            logging.info(f"Booking ID {booking_id} is outside 16 hours (Departure: {departure_time}), proceeding")

        matched_param = next((p for p in RIDE_PARAMETERS if p["type"] == ride_type and payout >= p["payout"]), None)
        if not matched_param:
            logging.info(f"Booking ID {booking_id} - Ride Type: {ride_type}, Payout: £{payout} does not match any parameters, ignoring")
            ignored_rides.add(booking_id)
            save_ride_data(accepted_rides, ignored_rides)
            logging.info(f"Booking ID {booking_id} added to ignored_rides")
            close_modal(driver)
            logging.info(f"Modal closed for Booking ID: {booking_id}")
            return False
        else:
            logging.info(f"Booking ID {booking_id} - Ride Type: {ride_type}, Payout: £{payout} matches parameters (Required: £{matched_param['payout']}, Driver: {matched_param['driver']}, Vehicle: {matched_param['vehicle']})")

        if select_driver_and_vehicle(driver, matched_param):
            logging.info(f"Booking ID {booking_id} - Driver '{matched_param['driver']}' and Vehicle '{matched_param['vehicle']}' selected successfully")
            button_css = ".modal-footer .close-button" if testing_mode else ".modal-footer .update-button"
            ActionChains(driver).click(wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_css)))).perform()
            logging.info(f"Booking ID {booking_id} - Processed and {'close' if testing_mode else 'accept'} button clicked ({'testing' if testing_mode else 'production'})")
            accepted_rides.add(booking_id)
            save_ride_data(accepted_rides, ignored_rides)
            logging.info(f"Booking ID {booking_id} added to accepted_rides")
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal")))
            logging.info(f"Modal closed after processing Booking ID: {booking_id}")
            return True
        else:
            logging.info(f"Booking ID {booking_id} - Failed to select driver '{matched_param['driver']}' or vehicle '{matched_param['vehicle']}'")
            close_modal(driver)
            logging.info(f"Modal closed for Booking ID: {booking_id} due to selection failure")
            return False
    except Exception as e:
        logging.error(f"Error processing modal for Booking ID {booking_id if 'booking_id' in locals() else 'unknown'}: {e}")
        close_modal(driver)
        logging.info(f"Modal closed due to error")
        return False

def select_driver_and_vehicle(driver, matched_param):
    wait = WebDriverWait(driver, 10, poll_frequency=0.1)
    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        try:
            logging.info(f"Attempt {attempt + 1}/{max_attempts} to select driver '{matched_param['driver']}' and vehicle '{matched_param['vehicle']}'")
            
            # Locate and click the driver dropdown
            driver_dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.react-select__control")))
            logging.info("Driver dropdown located and clickable")
            ActionChains(driver).click(driver_dropdown).perform()
            logging.info("Driver dropdown clicked")
            
            # Wait for the menu and select the driver option by text
            driver_menu = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".react-select__menu")))
            driver_option_xpath = f"//div[contains(@class, 'react-select__option') and contains(text(), '{matched_param['driver']}')]"
            driver_option = wait.until(EC.element_to_be_clickable((By.XPATH, driver_option_xpath)))
            logging.info(f"Driver option '{matched_param['driver']}' located")
            driver.execute_script("arguments[0].click();", driver_option)
            logging.info(f"Selected driver option: '{matched_param['driver']}'")

            # Locate and click the vehicle dropdown (second dropdown)
            vehicle_dropdowns = driver.find_elements(By.CSS_SELECTOR, "div.react-select__control")
            if len(vehicle_dropdowns) >= 2:
                logging.info(f"Found {len(vehicle_dropdowns)} dropdowns, selecting vehicle from second dropdown")
                ActionChains(driver).click(vehicle_dropdowns[1]).perform()
                logging.info("Vehicle dropdown clicked")
                
                # Wait for the vehicle menu and select the vehicle option by text
                vehicle_menu = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".react-select__menu")))
                vehicle_option_xpath = f"//div[contains(@class, 'react-select__option') and contains(text(), '{matched_param['vehicle']}')]"
                vehicle_option = wait.until(EC.element_to_be_clickable((By.XPATH, vehicle_option_xpath)))
                logging.info(f"Vehicle option '{matched_param['vehicle']}' located")
                driver.execute_script("arguments[0].click();", vehicle_option)
                logging.info(f"Selected vehicle option: '{matched_param['vehicle']}'")
                return True
            else:
                logging.info(f"Insufficient dropdowns found: {len(vehicle_dropdowns)}, expected at least 2")
                return False

        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt == max_attempts:
                logging.error("Max attempts reached, giving up.")
                return False
    return False

def close_modal(driver):
    wait = WebDriverWait(driver, 1, poll_frequency=0.1)
    try:
        ActionChains(driver).click(driver.find_element(By.CSS_SELECTOR, ".modal-footer .close-button")).perform()
        wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal")))
    except Exception:
        try:
            ActionChains(driver).click(driver.find_element(By.CSS_SELECTOR, ".modal-header .close")).perform()
            wait.until(EC.invisibility_of_element_located((By.CLASS_NAME, "modal")))
        except Exception:
            pass  # If all fails, proceed

def main():
    chrome_options = Options()
    profile_dir = os.path.join(os.getcwd(), "AutoAcceptProfile")
    os.makedirs(profile_dir, exist_ok=True)
    
    chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    chrome_options.add_argument("--window-size=1366,768")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0.4430.212 Safari/537.36")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")  # Disable images
    chrome_options.add_experimental_option("prefs", {"profile.default_content_setting_values": {"notifications": 1},
                                                     "profile.content_settings.exceptions": {"notifications": {"https://dcp.orange.sixt.com,*": {"setting": 1}}}})
    
    if not testing_mode:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(10)  # Set page load timeout

    try:
        if not check_session(driver) and not login(driver):
            logging.error("Login failed. Exiting...")
            return
        
        driver.get("https://dcp.orange.sixt.com/availableRides")
        # Extract initial reservation IDs after session check
        initial_reservation_ids = get_reservation_ids(driver)
        handle_notifications(driver, initial_reservation_ids)
        
    except Exception as e:
        logging.error(f"Fatal error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()