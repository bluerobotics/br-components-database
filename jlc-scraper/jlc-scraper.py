import pickle
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import os
import time

# Set up the path to the ChromeDriver executable
root_folder = os.path.dirname(os.path.abspath(__file__))  # Get the script's root directory
chromedriver_path = os.path.join(root_folder, "chromedriver-win64", "chromedriver.exe")  # Path to chromedriver.exe

# Set up download folder path
download_folder = os.path.join(root_folder, "csv")  # Create a "csv" directory in the root

# Specify the path for the cookies file in the root folder
cookies_file = os.path.join(root_folder, "cookies.pkl")

# Specify the expected filename for the downloaded file
downloaded_file_name = "Parts Inventory on JLCPCB.xlsx"
downloaded_file_path = os.path.join(download_folder, downloaded_file_name)

# Create the "csv" directory if it doesn't exist
if not os.path.exists(download_folder):
    os.makedirs(download_folder)

# If the file already exists, delete it
if os.path.exists(downloaded_file_path):
    os.remove(downloaded_file_path)
    print(f"Existing file '{downloaded_file_name}' deleted.")

# Set up Chrome options to specify the download folder
options = webdriver.ChromeOptions()
prefs = {
    "download.default_directory": download_folder,  # Set the default download directory
    "download.prompt_for_download": False,  # Disable download prompt
    "download.directory_upgrade": True,  # Allow directory upgrade
    "safebrowsing.enabled": True  # Enable safe browsing
}
options.add_experimental_option("prefs", prefs)

# Set up the Selenium WebDriver Service
service = Service(executable_path=chromedriver_path)

# Set up Selenium WebDriver with Chrome
driver = webdriver.Chrome(service=service, options=options)

try:
    # Open the JLCPCB homepage
    driver.get("https://jlcpcb.com/")

    # Load cookies from the file in the root folder if it exists
    if os.path.exists(cookies_file):
        with open(cookies_file, "rb") as file:
            cookies = pickle.load(file)
            for cookie in cookies:
                # Some cookies may have 'sameSite' restrictions or a 'domain' attribute that needs to be removed
                cookie.pop('sameSite', None)
                cookie.pop('domain', None)
                driver.add_cookie(cookie)
        print("Cookies loaded successfully from the root folder!")

    # Refresh the page to apply cookies and check if already logged in
    driver.refresh()
    time.sleep(2)  # Wait for 2 seconds to refresh

    # Hover over the element to trigger the "Sign in" button appearance
    try:
        # Locate the element that triggers the "Sign in" button on hover
        trigger_element = driver.find_element(By.ID, "home_sign in")

        # Use ActionChains to hover over the element
        actions = ActionChains(driver)
        actions.move_to_element(trigger_element).perform()
        print("Hovered over the trigger element successfully.")

        # Wait for 2 seconds to allow the "Sign in" button to become clickable
        time.sleep(2)

        # Locate the "Sign in" button using the full XPath
        sign_in_button = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/nav/div/div[2]/span[2]/div/div[1]/button")

        # Click the "Sign in" button
        sign_in_button.click()
        print("Sign in button clicked successfully!")
    except Exception as e:
        print(f"Failed to hover and click the Sign in button: {e}")

    # Save cookies after clicking the sign-in button, if needed
    new_cookies = driver.get_cookies()
    with open(cookies_file, "wb") as file:
        pickle.dump(new_cookies, file)
    print("Cookies updated and saved successfully in the root folder!")

    # Navigate to the specified URL
    driver.get("https://jlcpcb.com/user-center/smtPrivateLibrary/myPartsLib")
    print("Navigated to the parts library page.")

    # Click the first specified button on the page
    try:
        # Locate the button using the full XPath
        first_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/main/div/div[2]/div/div/div[2]/div[2]/div[2]"))
        )

        # Scroll the button into view using JavaScript
        driver.execute_script("arguments[0].scrollIntoView(true);", first_button)

        # Click the button using JavaScript
        driver.execute_script("arguments[0].click();", first_button)
        print("First button clicked successfully using JavaScript!")
    except Exception as e:
        print(f"Failed to click the first button: {e}")

    # Click the second specified button on the page to download the file
    try:
        # Locate the second button using the full XPath
        second_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div/div/main/div/div[2]/div/div/div/div[1]/div[2]/button"))
        )

        # Scroll the second button into view using JavaScript
        driver.execute_script("arguments[0].scrollIntoView(true);", second_button)

        # Click the second button using JavaScript
        driver.execute_script("arguments[0].click();", second_button)
        print("Second button clicked successfully to initiate file download!")
    except Exception as e:
        print(f"Failed to click the second button: {e}")

    # Wait for the download to complete
    time.sleep(2)

    # Check if the file was downloaded successfully
    if os.path.exists(downloaded_file_path):
        print(f"File '{downloaded_file_name}' downloaded successfully.")
    else:
        print(f"File '{downloaded_file_name}' was not downloaded.")

    # Wait for 2 seconds to allow for visual verification
    time.sleep(2)

finally:
    # Close the browser
    driver.quit()
