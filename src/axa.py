#!/usr/local/bin/python

import argparse
import logging
import yaml

from selenium.webdriver import *
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.chrome.service import Service

from webdriver_manager.chrome import ChromeDriverManager

from prometheus_client import Counter
from prometheus_client import Gauge
from prometheus_client import start_http_server

from time import sleep
from datetime import timedelta, datetime

class Quote:
    def __init__(self, registration, car_name, reference_id, price):
        self._registration = registration
        self._car_name = car_name
        self._reference_id = reference_id
        self._price = price
    
    @property
    def price(self):
        return self._price
        
    @property
    def car_name(self):
        return self._car_name
    
    @property
    def registration(self):
        return self._registration
    
    @property
    def reference_id(self):
        return self._reference_id
    
    @price.setter
    def price(self, price):
        self._price = price
    
    @car_name.setter
    def car_name(self, car_name):
        self._car_name = car_name
    
    @registration.setter
    def registration(self, registration):
        self._registration = registration

    @reference_id.setter
    def reference_id(self, reference_id):
        self._reference_id = reference_id
        
    def __str__(self):
        return f"Ref ID: {self.reference_id:10}, Registration: {self.registration:10}, Quote: €{self.price:7.2f}, Car name: {self.car_name}"
    
class Config:
    def __init__(self, annual_distance, first_name, last_name, date_of_birth, phone_number, email, occupation, eir_code, license_held, registrations):
        self.annual_distance = annual_distance
        self.first_name = first_name
        self.last_name = last_name
        self.date_of_birth = date_of_birth
        self.phone_number = phone_number
        self.email = email
        self.occupation = occupation
        self.eir_code = eir_code
        self.license_held = license_held
        self.registrations = registrations
    def __str__(self):
        return "Annual Distance: " + self.annual_distance + "\n" + \
                "First Name: " + self.first_name + "\n" + \
                "Last Name: " + self.last_name + "\n" + \
                "Date of Birth: " + self.date_of_birth + "\n" + \
                "Phone Number: " + self.phone_number + "\n" + \
                "Email: " + self.email + "\n" + \
                "Occupation: " + self.occupation + "\n" + \
                "EIR Code: " + self.eir_code + "\n" + \
                "License Held: " + self.license_held + "\n"

class QuoteHandler:
    def __init__(self):
        self._failed_attempts = Counter('failed_attempts', 'Failed attempts')
        self._registration_metrics = Gauge("quote_prices", "Quote for registrations", ['registration', 'car_name'])
        logging.basicConfig(
            format='%(asctime)s %(levelname)-8s %(message)s',
            level=logging.INFO,
            datefmt='%Y-%m-%d %H:%M:%S')
        self._logger = logging.getLogger(__name__)
        self._logger.level = logging.INFO
        
    @property
    def failed_attempts(self):
        return self._failed_attempts
    
    @property
    def registration_metrics(self):
        return self._registration_metrics

    @property
    def logger(self):
        return self._logger


    def wait_for_element(self, driver, wait_time_seconds, by_type, string):
        WebDriverWait(driver, wait_time_seconds).until(EC.presence_of_element_located((by_type, string)))

    def get_driver(self):
        self.logger.debug("Getting browser driver")
        chrome_options = ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--disable-extensions")
        driver = Chrome(
            service=Service(ChromeDriverManager(
                print_first_line=False, log_level=logging.WARNING).install()), 
            options=chrome_options)
        self.logger.debug("Done getting browser driver")
        return driver

    def _accept_cookies(self, driver):
        # accept cookies
        try:
            self.logger.debug("Accepting cookies")
            self.wait_for_element(driver, 15, By.ID, '_evidon-accept-button')
            driver.find_element(By.ID, "_evidon-accept-button").click()
            self.logger.debug("Done accepting cookies")
        except Exception as e:
            self.logger.error(e)

    def _go_to_car_insurance_page(self, driver):
        # Go to parent car insurance page
        self.logger.debug("Navigating to car insurance page")
        self.wait_for_element(driver, 15, By.XPATH, '//a[text()="Car Insurance"]')
        driver.execute_script("arguments[0].click();", driver.find_element(By.LINK_TEXT, "Car Insurance"))
        # Go to car insurance page where the form is present
        self.wait_for_element(driver, 15, By.XPATH, '//a[text()="Get a car insurance quote"]')
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, '//a[text()="Get a car insurance quote"]'))
        self.logger.debug("Done navigating to car insurance page")

    def _confirm_car(self, driver, registration):
        # confirm car with registration number
        self.logger.debug(f"Confirming car details with registration '{registration}'")
        self.wait_for_element(driver, 15, By.ID, "VehicleDetails.HasRegNumber1")
        driver.find_element(By.XPATH, "//*[@id='VehicleDetails.HasRegNumber1']/..").click()
        self.wait_for_element(driver, 15, By.ID, "VehicleDetails.VehicleRegistrationNumber")
        driver.find_element(By.ID, "VehicleDetails.VehicleRegistrationNumber").send_keys(registration)
        driver.find_element(By.XPATH, '//button[text()="Find car"]').click()
        self.wait_for_element(driver, 15, By.ID, "VehicleDetails.ConfirmCarSearchBtn1")
        car_name = driver.find_element(By.XPATH, '//label[text()="Is this the correct car?"]/following-sibling::span/div').text
        driver.find_element(By.XPATH, "//*[@id='VehicleDetails.ConfirmCarSearchBtn1']/..").click()
        self.logger.debug(f"Done confirming car details with registration '{registration}', name '{car_name}'")
        return car_name

    def _business_use_info(self, driver):
        # For business use or not
        self.logger.debug("Inputting business use info")
        self.wait_for_element(driver, 15, By.ID, "VehicleDetails.IsVehicleForBusinessUse2")
        driver.find_element(By.XPATH, "//*[@id='VehicleDetails.IsVehicleForBusinessUse2']/..").click()
        self.wait_for_element(driver, 15, By.ID, "VehicleDetails.IsVehicleForCommutingUse1")
        driver.find_element(By.XPATH, "//*[@id='VehicleDetails.IsVehicleForCommutingUse1']/..").click()
        self.logger.debug("Done inputting business use info")

    def _annual_distance(self, driver, annual_distance):
        self.logger.debug(f"Inputting expected annual distance travelled with '{annual_distance}'")
        self.wait_for_element(driver, 15, By.ID, 'VehicleDetails.AnnualDistanceDrivenTypeId')
        Select(driver.find_element(By.ID, "VehicleDetails.AnnualDistanceDrivenTypeId")).select_by_visible_text(annual_distance)
        self.logger.debug(f"Done inputting expected annual distance travelled with '{annual_distance}'")

    def _user_info(self, driver, first_name, last_name, date_of_birth, email, phone_number):
        # User info
        self.logger.debug("Inputting user information")
        self.wait_for_element(driver, 15, By.ID, "ProposerDetails.TitleTypeId1")
        driver.find_element(By.XPATH, "//*[@id='ProposerDetails.TitleTypeId1']/..").click()
        driver.find_element(By.ID, "ProposerDetails.FirstName").send_keys(first_name)
        driver.find_element(By.ID, "ProposerDetails.LastName").send_keys(last_name)
        driver.find_element(By.ID, "ProposerDetails.DateOfBirth.Day").send_keys(date_of_birth.split('-')[2])
        driver.find_element(By.ID, "ProposerDetails.DateOfBirth.Month").send_keys(date_of_birth.split('-')[1]) 
        driver.find_element(By.ID, "ProposerDetails.DateOfBirth.Year").send_keys(date_of_birth.split('-')[0])
        driver.find_element(By.ID, "ProposerDetails.EmailAddress").send_keys(email)
        driver.find_element(By.XPATH, "//input[@name='phone-number']").send_keys(phone_number)
        self.logger.debug("Done inputting user information")

    def _employment_info(self, driver, occupation):
        self.logger.debug(f"Confirming employment information as '{occupation}'")
        self.wait_for_element(driver, 15, By.ID, "ProposerDetails.EmploymentStatusTypeId1")
        driver.find_element(By.XPATH, "//*[@id='ProposerDetails.EmploymentStatusTypeId1']/..").click()
        self.wait_for_element(driver, 15, By.ID, "ProposerDetails.OccupationTypeDescription")
        driver.find_element(By.ID, "ProposerDetails.OccupationTypeDescription").send_keys(occupation)
        driver.find_element(By.XPATH, "//*[@id='react-autowhatever-1--item-0']").click()
        self.logger.debug(f"Done confirming employment information as '{occupation}'")

    def _address_info(self, driver, eir_code):
        self.logger.debug("Confirming address")
        self.wait_for_element(driver, 15, By.ID, "ProposerDetails.AddressDisplayFormatted")
        driver.find_element(By.ID, "ProposerDetails.AddressDisplayFormatted").send_keys(eir_code)
        self.wait_for_element(driver, 15, By.ID, "react-autowhatever-1--item-0")
        driver.find_element(By.XPATH, "//*[@id='react-autowhatever-1--item-0']").click()
        driver.find_element(By.XPATH, "//*[@id='ProposerDetails.HouseHoldTypeId1']/..").click()
        self.logger.debug("Done confirming address")

    def _license_info(self, driver, license_held):
        # License type
        self.logger.debug(f"Inputting license information with license held for '{license_held}'")
        self.wait_for_element(driver, 15, By.ID, "DrivingHistory.DrivingLicenceTypeId2")
        driver.find_element(By.XPATH, "//*[@id='DrivingHistory.DrivingLicenceTypeId2']/..").click()
        self.wait_for_element(driver, 15, By.ID, "DrivingHistory.AdvancedDriverTrainingTypeId2")
        driver.find_element(By.XPATH, "//*[@id='DrivingHistory.AdvancedDriverTrainingTypeId2']/..").click()
        # Licene held
        Select(driver.find_element(By.ID, "DrivingHistory.YearsLicenceHeldTypeId")).select_by_visible_text(license_held)
        # Penalty points
        driver.find_element(By.XPATH, "//*[@id='DrivingHistory.PenaltyPointsDetails.HasPenaltyPoints2']/..").click()
        self.logger.debug(f"Done inputting license information with license held for '{license_held}'")

    def _insurance_info(self, driver):
        self.logger.debug("Inputting previous insurance information")
        # Recent insurance
        self.wait_for_element(driver, 15, By.ID, "DrivingHistory.DrivingExperienceTypeId2")
        driver.find_element(By.XPATH, "//*[@id='DrivingHistory.DrivingExperienceTypeId2']/..").click()
        # More people in the house discount
        driver.find_element(By.XPATH, "//*[@id='CoverDetails.HasMultiProductDiscount2']/..").click()
        # # How to pay the price?
        # driver.find_element(By.XPATH, "//*[@id='CoverDetails.NormalPaymentMethodTypeId1']/..").click()
        self.logger.debug("Done inputting previous insurance information")

    def _submit_and_get_quote(self, driver, registration, car_name):
        # Terms and conditions
        self.logger.debug(f"Submitting request and getting quote for '{registration}'")
        self.wait_for_element(driver, 15, By.ID, "ConfirmAssumptions")
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, "//input[@id='ConfirmAssumptions']"))
        # submit
        self.wait_for_element(driver, 15, By.ID, "getquote-btn")
        driver.find_element(By.ID, "getquote-btn").click()
        # wait till quote there
        self.wait_for_element(driver, 45, By.ID, "YourQuote.Quote")
        # Ref ID and quote
        self.wait_for_element(driver, 15, By.ID, "CarQuotePremium.QuoteReferenceIdForDisplay")
        ref_id = driver.find_element(By.XPATH, '//*[@id="CarQuotePremium.QuoteReferenceIdForDisplay"]').text
        quote = driver.find_element(By.XPATH, '//*[@id="YourQuote.Quote"]/div/div[1]/span/div/div[1]/div[2]').text
        quote = Quote(registration, car_name, ref_id, float(quote[1:]))
        self.logger.debug(f"Done submitting request and getting quote for '{registration}', retrieved quote: '{quote}'")
        return quote

    def _save_quote_reference_id(self, driver):
        self.logger.debug("Saving quote reference ID")
        try:
            self.wait_for_element(driver, 15, By.XPATH, '//button[text()="Save Quote"]')
            driver.find_element(By.XPATH, '//button[text()="Save Quote"]').click()
            self.logger.debug('Used //button[text()="Save Quote"]')
        except:
            self.wait_for_element(driver, 15, By.XPATH, '//a[text()="Save this Quote"]')
            driver.find_element(By.XPATH, '//a[text()="Save this Quote"]').click()
            self.logger.debug('Used //a[text()="Save this Quote"]')

        self.logger.debug("Done saving quote reference ID")

    def get_quote(self, config, registration, retry=3, sleep_time=60):
        self.logger.info(f"Getting quote for registration '{registration}'")
        driver = self.get_driver()
        for attempt in range(retry):
            try:
                self.logger.debug(f"Attempt ({attempt+1}/{retry}): Getting quote for registration '{registration}'")
                driver.get("https://www.axa.ie/")
                self._accept_cookies(driver)
                self._go_to_car_insurance_page(driver)
                car_name = self._confirm_car(driver, registration)
                self._business_use_info(driver)
                self._annual_distance(driver, config.annual_distance)
                self._user_info(driver, config.first_name, config.last_name, config.date_of_birth, config.email, config.phone_number)
                self._employment_info(driver, config.occupation)
                self._address_info(driver, config.eir_code)
                self._license_info(driver, config.license_held)
                self._insurance_info(driver)
                quote = self._submit_and_get_quote(driver, registration, car_name)
                self._save_quote_reference_id(driver)
                self.registration_metrics.labels(registration=registration, car_name=car_name).set(quote.price)
                self.logger.debug(f"Done getting quote for registration '{registration}': '{car_name}' with quote '{quote}'")
                self.logger.info(f"{quote}")
                return quote
            except Exception as e:
                self.failed_attempts.inc()
                self.logger.exception(e)
                self.logger.error(f"Attempt ({attempt+1}/{retry}): Failed to get quote for registration '{registration}'. Retrying after sleeping for {self._get_formatted_time(sleep_time)}")
                sleep(sleep_time)

    def get_quotes(self, config, registrations, retry=3, sleep_time=60):
        self.logger.debug(f"Getting quotes for registrations '{registrations}'")
        quotes = set()
        for registration in registrations:
            quotes.add(self.get_quote(config, registration, retry=retry, sleep_time=sleep_time))
        self.logger.debug(f"Done getting quotes for registrations '{registrations}'")
        return quotes
    
    def print_summary(self, quotes):
        self.logger.info("====== Summary ======")
        [self.logger.info(quote) for quote in quotes]
        self.logger.info("======== End ========")
        
    def monitor_forever(self, config, retry=3, sleep_time=60, monitor_break_seconds=8*60*60):
        self.logger.info(f"Starting monitoring with interval of {self._get_formatted_time(monitor_break_seconds)}")
        while True:
            self.logger.info(f"Monitoring triggered at {datetime.now()}")
            self.get_quotes(config, config.registrations, retry=retry, sleep_time=sleep_time)
            sleep(monitor_break_seconds)

    def _get_formatted_time(self, time_in_seconds):
        return f"{timedelta(seconds=time_in_seconds)} (hh:mm:ss)"

def get_args():
    parser = argparse.ArgumentParser("axa", description="Get car insurance quotes from Axa based on certain assumption. Read the README on https://github.com/Kimi450/axa for more information. Provide the arguments from either 'no_config_file_args_group' or 'config_file_args_group'.")

    no_config_file_args_group = parser.add_argument_group("no_config_file_args_group", "Group of required arguments if no config file is provided")
    no_config_file_args_group.add_argument("--annual-distance", dest="annual_distance", help="Annual distance driven (exactly as seen on the website)", type=str)
    no_config_file_args_group.add_argument("--first-name", dest="first_name", help="Your first name", type=str)
    no_config_file_args_group.add_argument("--last-name", dest="last_name", help="Your last name", type=str)
    no_config_file_args_group.add_argument("--date-of-birth", dest="date_of_birth", help="Your date of birth in format yyyy-mm-dd", type=str)
    no_config_file_args_group.add_argument("--phone-number", dest="phone_number", help="Your phone number", type=str)
    no_config_file_args_group.add_argument("--email", dest="email", help="Your email ID", type=str)
    no_config_file_args_group.add_argument("--occupation", dest="occupation", help="You occupation (exactly as seen on the website)", type=str)
    no_config_file_args_group.add_argument("--eir-code", dest="eir_code", help="Your eircode", type=str)
    no_config_file_args_group.add_argument("--license-held", dest="license_held", help="Time license held for (exactly as seen on the website)", type=str)
    no_config_file_args_group.add_argument("--registrations", dest="registrations", help="List of vehicle registrations", type=str, action="extend", nargs="+")
    no_config_file_args_group.add_argument("--prometheus-client-port", dest="prometheus_client_port", help="Port at which the Prometheus client server runs", type=int)

    config_file_args_group = parser.add_argument_group("config_file_args_group", "Group of required arguments if config file is provided")
    config_file_args_group.add_argument("--config-file", dest="config_file", help="Config file instead of inputting all the required parameters", type=str)

    args = parser.parse_args()

    list_no_config_file_args = [args.annual_distance,
        args.first_name, args.last_name, args.date_of_birth,
        args.phone_number, args.email, args.occupation,
        args.eir_code, args.license_held, args.registrations,
        args.prometheus_client_port]
    list_config_file_args = [args.config_file]

    def _all_present_in_group(group):
        return all([arg is not None for arg in group])

    def _none_present_in_group(group):
        return all([arg is None for arg in group])


    if (_all_present_in_group(list_no_config_file_args) and _none_present_in_group(list_config_file_args)) \
       or (_all_present_in_group(list_config_file_args) and _none_present_in_group(list_no_config_file_args)):
        pass #alls good
    else:
        parser.error("Please provide all args from either 'no_config_file_args_group' or 'config_file_args_group' groups.")
        exit()

    return args

def parse_config_file(file, perms):
    with open(file, perms) as stream:
        try:
            parsed_yaml=yaml.safe_load(stream)
            config = Config(parsed_yaml["annual_distance"],
                parsed_yaml["first_name"],
                parsed_yaml["last_name"],
                parsed_yaml["date_of_birth"],
                parsed_yaml["phone_number"],
                parsed_yaml["email"],
                parsed_yaml["occupation"],
                parsed_yaml["eir_code"],
                parsed_yaml["license_held"],
                parsed_yaml["registrations"]
            )
            prometheus_client_port = int(parsed_yaml["prometheus_client_port"])
        except yaml.YAMLError as exc:
            print(exc)
            exit()
    return (config, prometheus_client_port)

def parse_args(args):
    if args.config_file is not None: # config file
        config, prometheus_client_port = parse_config_file(args.config_file, 'r')
    else: # args
        config = Config(args.annual_distance, 
            args.first_name, 
            args.last_name, 
            args.date_of_birth, 
            args.phone_number, 
            args.email, 
            args.occupation, 
            args.eir_code, 
            args.license_held,
            args.registrations
        )
        prometheus_client_port = int(args.prometheus_client_port)
    return (config, prometheus_client_port)


def main():
    config, prometheus_client_port = parse_args(get_args())
    start_http_server(prometheus_client_port)
    quote_handler = QuoteHandler()
    quote_handler.monitor_forever(config)

main()