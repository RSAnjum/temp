from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import (TimeoutException, 
                                      NoSuchElementException, 
                                      StaleElementReferenceException,
                                      ElementClickInterceptedException)
import time
import os
import logging
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('auto_accept_prod.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

# Constants
RIDE_PARAMETERS = [
    {"type": "Ride", "payout": 150, "driver": "Raza Ul Habib Tahir", "vehicle": "FR19 DZG"},
    {"type": "Business", "payout": 120, "driver": "Raza Ul Habib Tahir", "vehicle": "FR19 DZG"},
    {"type": "First", "payout": 90, "driver": "Raza Ul Habib Tahir", "vehicle": "KM19 WDS"},
    {"type": "Business XL", "payout": 120, "driver": "Raza Ul Habib Tahir", "vehicle": "KX19UBY"},
    {"type": "Ride XL", "payout": 120, "driver": "Raza Ul Habib Tahir", "vehicle": "KX19UBY"}
]

# Decorators
def retry(max_attempts=3, delay=2):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Attempt {attempts+1} failed: {str(e)}")
                    time.sleep(delay)
                    attempts += 1
            raise Exception(f"Failed after {max_attempts} attempts")
        return wrapper
    return decorator

class RideAcceptor:
    def _init_(self):
        self.driver = None
        self.accepted_rides = set()
        self.wait_timeout = 15
        self.setup_driver()
        
    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={os.path.join(os.getcwd(), 'AutoAcceptProfile')}")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.binary_location = '/opt/chrome/chrome'
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(5)
        
    def wait(self, timeout=None):
        return WebDriverWait(self.driver, timeout or self.wait_timeout)
    
    @retry(max_attempts=3)
    def login(self):
        logger.info("Initiating login process...")
        self.driver.get(f"https://dcp.orange.sixt.com/login")
        
        # Country code selection
        self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".react-select-container.country-code")
        )).click()
        
        country_option = self.wait().until(EC.element_to_be_clickable(
            (By.XPATH, "//div[contains(@class, 'react-select__option') and contains(., '+92')]")
        ))
        self.driver.execute_script("arguments[0].click();", country_option)
        
        # Phone number entry
        phone_field = self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input.phone-number")
        ))
        phone_field.send_keys("3157726586")
        
        # Get PIN
        self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.get-pin")
        )).click()
        
        # PIN entry
        pin = input("Enter PIN: ")
        self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input.otp")
        )).send_keys(pin)
        
        # Final sign-in
        self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "button.sign-in")
        )).click()
        
        return self.wait().until(
            lambda d: "availableRides" in d.current_url
        )
    
    def check_session(self):
        self.driver.get(f"https://dcp.orange.sixt.com/availableRides")
        return "login" not in self.driver.current_url
    
    def process_rides(self):
        while True:
            try:
                self.driver.refresh()
                ride_rows = self.wait().until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, '.available-rides-table tbody tr')
                    )
                )
                
                for row in ride_rows:
                    try:
                        self.process_single_ride(row)
                    except StaleElementReferenceException:
                        logger.warning("Stale ride element, refreshing list...")
                        break
                    
                time.sleep(1.5)
                
            except Exception as e:
                logger.error(f"Error processing rides: {str(e)}")
                self.driver.refresh()
                time.sleep(3)
    
    def process_single_ride(self, row):
        ride_type = row.find_element(By.CLASS_NAME, 'class').text.strip()
        payout = float(row.find_element(By.CLASS_NAME, 'payout').text.replace('£', ''))
        accept_btn = row.find_element(By.CLASS_NAME, 'button-outline')
        
        for param in RIDE_PARAMETERS:
            if (ride_type == param["type"] and payout >= param["payout"]):
                ride_key = f"{ride_type}-{payout}"
                if ride_key in self.accepted_rides:
                    continue
                
                self.accepted_rides.add(ride_key)
                logger.info(f"Accepting ride: {ride_type} - £{payout}")
                self.accept_ride(accept_btn, param)
                self.accepted_rides.remove(ride_key)
                return
    
    def accept_ride(self, button, params):
        try:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
            self.driver.execute_script("arguments[0].click();", button)
            self.handle_modal(params)
        except ElementClickInterceptedException:
            logger.warning("Click intercepted, retrying with JS...")
            self.driver.execute_script("arguments[0].click();", button)
            self.handle_modal(params)
    
    @retry(max_attempts=2)
    def handle_modal(self, params):
        modal = self.wait(10).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "modal"))
        )
        self.select_driver(params["driver"])
        self.select_vehicle(params["vehicle"])
        self.submit_modal()
        
    def select_driver(self, driver_name):
        driver_dropdown = self.wait().until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[id^='react-select'][aria-label='Driver selection']"))
        )
        self.handle_dropdown(driver_dropdown, driver_name)
    
    def select_vehicle(self, vehicle_name):
        vehicle_dropdown = self.wait().until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "[id^='react-select'][aria-label='Vehicle selection']"))
        )
        self.handle_dropdown(vehicle_dropdown, vehicle_name)
    
    def handle_dropdown(self, element, selection):
        self.driver.execute_script("arguments[0].click();", element)
        option = self.wait().until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//div[contains(@class, 'react-select__option') and contains(., '{selection}')]"))
        )
        self.driver.execute_script("arguments[0].click();", option)
    
    def submit_modal(self):
        # For production use:
        # self.wait().until(EC.element_to_be_clickable(
        #     (By.CSS_SELECTOR, ".update-button")
        # )).click()
        
        # For testing:
        self.wait().until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, ".close-button")
        )).click()
        
        self.wait().until(EC.invisibility_of_element_located(
            (By.CLASS_NAME, "modal"))
        )
    
    def run(self):
        try:
            if not self.check_session() and not self.login():
                raise Exception("Login failed")
                
            self.driver.get(f"https://dcp.orange.sixt.com/availableRides")
            self.process_rides()
            
        except Exception as e:
            logger.error(f"Critical error: {str(e)}")
        finally:
            self.driver.quit()

if _name_ == "_main_":
    RideAcceptor().run()