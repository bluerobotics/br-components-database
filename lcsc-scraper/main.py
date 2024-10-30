from selenium import webdriver
from bs4 import BeautifulSoup
import re
import requests
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from argparse import ArgumentParser


def get_lcsc_url(part_number):

    # Initialize the WebDriver
    driver = webdriver.Chrome()  # Provide the path to chromedriver if needed

    # Construct and open the search URL
    search_url = f"https://www.lcsc.com/search?q={part_number}"
    driver.get(search_url)

    # Retrieve the current page URL after loading
    part_url = driver.current_url
    print("Current URL:", part_url)

    return part_url

def scrape_image_from_lcsc(part_number, output_path):

    # Initialize the WebDriver
    driver = webdriver.Chrome()  # Provide the path to chromedriver if needed

    # Construct and open the search URL
    search_url = f"https://www.lcsc.com/search?q={part_number}"
    driver.get(search_url)

    # Retrieve the current page URL after loading
    current_url = driver.current_url
    print("Current URL:", current_url)

    # Wait for the specific image container to load
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "v-image__image"))
        )
        time.sleep(3)  # Additional wait to ensure full load
    except:
        print("Image container not loaded.")

    # Get the page source and parse it with BeautifulSoup
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Close the WebDriver as it is no longer needed
    driver.quit()

    # Search for the div containing the background image URL
    image_url = None
    image_div = soup.find('div', class_='v-image__image v-image__image--contain')
    if image_div:
        # Extract the URL from the style attribute using regex
        style = image_div.get('style', '')
        url_match = re.search(r'url\("(.+?)"\)', style)
        if url_match:
            image_url = url_match.group(1)

    # If we found the image URL, download the image with headers
    if image_url:
        print("Image URL:", image_url)

        # Add headers to mimic a real browser request
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
        }

        # Download the image
        response = requests.get(image_url, headers=headers)
        if response.status_code == 200:

            file_path = os.path.join(output_path, part_number.jpg)
            with open(file_path, "wb") as file:
                file.write(response.content)
            print(f"Image downloaded as '{file_path}.jpg'.")
        else:
            print("Failed to download image. Status code:", response.status_code)
    else:
        print("Image URL not found.")


parser = ArgumentParser()
parser.add_argument("part_number", type='str')
parser.add_argement("image_path", type='str')
args = parser.parse_args()
print(f"Grabbing image for part number {args.part_number}")

scrape_image_from_lcsc(args.part_number, args.image_path)

