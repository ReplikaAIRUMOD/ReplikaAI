#!/usr/local/bin/python3

import os
import sys
import time
import platform
import colorama
from dotenv import load_dotenv
from datetime import datetime
from selenium.common.exceptions import (NoSuchElementException, 
                                     WebDriverException,
                                     TimeoutException)
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service

# Initialize colorama
colorama.init()

# Load .env credentials
load_dotenv()
email = os.environ.get("REPLIKA_CLIENT_EMAIL")
password = os.environ.get("REPLIKA_CLIENT_PASSWORD")

if not email or not password:
    print(colorama.Fore.RED + "ERROR: Email or password not found in .env file" + colorama.Fore.RESET)
    sys.exit(1)

def get_firefox_profile_path():
    """Get Firefox profile path with validation"""
    system_platform = platform.system()
    profile_name = "inmersprofile.default-release"
    
    if system_platform == "Windows":
        base_path = os.path.join(os.environ['APPDATA'], '..', 'Local', 'Mozilla', 'Firefox', 'Profiles')
    elif system_platform == "Linux":
        base_path = os.path.expanduser("~/snap/firefox/common/.mozilla/firefox")
    elif system_platform == "FreeBSD":
        base_path = os.path.expanduser("~/.mozilla/firefox")
    else:
        print(colorama.Fore.RED + "ERROR: Unsupported OS" + colorama.Fore.RESET)
        sys.exit(1)
    
    profile_path = os.path.join(base_path, profile_name)
    if not os.path.exists(profile_path):
        print(colorama.Fore.YELLOW + f"WARNING: Firefox profile not found at {profile_path}")
        print("Please create the profile first or check the profile name." + colorama.Fore.RESET)
        sys.exit(1)
    
    return profile_path

def initialize_driver():
    """Initialize Firefox WebDriver"""
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.binary_location = "/usr/local/bin/firefox"
    
    try:
        profile_path = get_firefox_profile_path()
        firefox_options.add_argument('--profile')
        firefox_options.add_argument(profile_path)
        
        service = Service(executable_path="/usr/local/bin/geckodriver")
        driver = webdriver.Firefox(options=firefox_options, service=service)
        return driver
    except WebDriverException as e:
        print(colorama.Fore.RED + f"ERROR: Failed to initialize WebDriver\n{e}" + colorama.Fore.RESET)
        sys.exit(1)

def login_to_replika(driver):
    """Handle Replika login"""
    try:
        driver.get("https://my.replika.com/")
        
        try:
            login_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(text(), "Log in")]'))
            )
            login_button.click()
        except TimeoutException:
            pass
        
        try:
            email_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'login-email'))
            )
            email_input.send_keys(email)

            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'login-password'))
            )
            password_input.send_keys(password)
            password_input.submit()

            WebDriverWait(driver, 20).until(
                EC.url_contains('https://my.replika.com/')
            )
            time.sleep(3)
        except TimeoutException:
            pass
            
    except Exception as e:
        print(colorama.Fore.RED + f"ERROR during login: {e}" + colorama.Fore.RESET)
        driver.quit()
        sys.exit(1)

def add_message(message, initial_time):
    """Save message to conversation log"""
    now = datetime.now()
    time_now = now.strftime("%H:%M:%S")
    date = now.strftime("%Y-%m-%d")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    repo_dir = os.path.join(base_dir, "conversations", date)

    os.makedirs(repo_dir, exist_ok=True)
    filepath = os.path.join(repo_dir, initial_time + ".txt")

    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"{time_now}: {message.strip()}\n")

def send_message(driver, message):
    """Send message to Replika"""
    try:
        input_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'textarea[class*="TextArea-sc-"]'))
        )
        input_box.send_keys(message + Keys.RETURN)
        
        # Verify message was sent by checking for the message bubble
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, f'//div[contains(@class, "MessageGroup__StyledMessage") and contains(., "{message}")]')
            )
        )
        return True
    except Exception as e:
        print(colorama.Fore.RED + f"ERROR sending message: {e}" + colorama.Fore.RESET)
        return False

def get_bot_responses(driver):
    """Get Replika's responses using stable class name patterns"""
    try:
        # Wait for at least one bot message to appear
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, 'div[role="row"][class*="MessageHover__MessageHoverRoot-sc-"]')
            )
        )
        
        # Get all message rows
        messages = driver.find_elements(
            By.CSS_SELECTOR,
            'div[role="row"][class*="MessageHover__MessageHoverRoot-sc-"]'
        )
        
        responses = []
        for msg in messages:
            # Check if it's a bot message (has Replika's name in the metadata)
            if msg.find_elements(By.CSS_SELECTOR, 'span[aria-colindex="2"]'):
                try:
                    # Get the message text from the polite span
                    text_element = msg.find_element(
                        By.CSS_SELECTOR,
                        'span[aria-live="polite"] span'
                    )
                    if text_element and text_element.text.strip():
                        responses.append(text_element.text.strip())
                except NoSuchElementException:
                    continue
        
        return responses
        
    except TimeoutException:
        print(colorama.Fore.YELLOW + "Timeout waiting for response" + colorama.Fore.RESET)
    except Exception as e:
        print(colorama.Fore.RED + f"ERROR getting responses: {e}" + colorama.Fore.RESET)
    
    return []

def handle_image_response(driver):
    """Handle image responses from Replika"""
    try:
        images = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, 'img[data-testid="chat-message-image"]')
            )
        )
        if images:
            return images[-1].get_attribute("src")
    except Exception as e:
        print(colorama.Fore.RED + f"ERROR handling image: {e}" + colorama.Fore.RESET)
    return None

def replika_interaction(driver, message):
    """Handle a complete interaction cycle"""
    initial_time = datetime.now().strftime("%m-%d-%Y_%H-%M-%S")
    
    if message.lower() in ("exit", "quit"):
        driver.quit()
        sys.exit(0)
    
    # Send message
    if not send_message(driver, message):
        return
    
    add_message(f"You: {message}", initial_time)
    
    # Wait for response
    time.sleep(5)  # Initial wait for response to start generating
    
    # Get all responses (including previous ones)
    all_responses = get_bot_responses(driver)
    if all_responses:
        latest_response = all_responses[-1]
        print(colorama.Fore.GREEN + f"Replika: {latest_response}" + colorama.Fore.RESET)
        add_message(f"Replika: {latest_response}", initial_time)
    else:
        # Check for image response
        image_url = handle_image_response(driver)
        if image_url:
            print(colorama.Fore.GREEN + f"Replika sent an image: {image_url}" + colorama.Fore.RESET)
            add_message(f"Replika (image): {image_url}", initial_time)
            
            print(colorama.Fore.YELLOW + "\nOptions: [1] Send another one [2] Stop" + colorama.Fore.CYAN)
            choice = input("Your choice (1/2): ").strip().lower()
            
            try:
                if choice == "1":
                    driver.find_element(By.XPATH, '//button[text()="Send another one"]').click()
                    time.sleep(6)
                else:
                    driver.find_element(By.XPATH, '//button[text()="Stop"]').click()
                    time.sleep(3)
            except Exception as e:
                print(colorama.Fore.RED + f"ERROR handling image options: {e}" + colorama.Fore.RESET)
        else:
            print(colorama.Fore.RED + "No response received from Replika" + colorama.Fore.RESET)

def main():
    # Initialize conversations directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    conversations_dir = os.path.join(base_dir, "conversations")
    os.makedirs(conversations_dir, exist_ok=True)
    
    # Initialize driver and login
    driver = initialize_driver()
    login_to_replika(driver)
    
    # Handle command line or interactive mode
    if len(sys.argv) == 2:
        try:
            replika_interaction(driver, sys.argv[1])
            time.sleep(2)
            driver.quit()
        except KeyboardInterrupt:
            print("\n" + colorama.Fore.YELLOW + "Closing..." + colorama.Fore.RESET)
            driver.quit()
            sys.exit(0)
    else:
        print(colorama.Fore.BLUE + "\nReplika CLI Client - Type 'exit' or 'quit' to end\n" + colorama.Fore.RESET)
        try:
            while True:
                print(colorama.Fore.YELLOW + "You:" + colorama.Fore.CYAN, end=" ")
                message = input().strip()
                if not message:
                    continue
                replika_interaction(driver, message)
        except KeyboardInterrupt:
            print("\n" + colorama.Fore.YELLOW + "Closing..." + colorama.Fore.RESET)
        finally:
            driver.quit()

if __name__ == '__main__':
    main()