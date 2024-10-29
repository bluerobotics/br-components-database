from selenium import webdriver
from bs4 import BeautifulSoup
import re
import requests
import time

# Initialize the WebDriver
driver = webdriver.Chrome()  # Provide the path to chromedriver if needed

# Open the target URL
driver.get("https://www.lcsc.com/product-detail/Aluminum-Electrolytic-Capacitors-SMD_Nichicon-UWT1H221MNL1GS_C125977.html")  # Replace with the actual URL of the product page

# Wait for the page to load completely
time.sleep(3)  # Adjust as needed based on page load speed

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

# If we found the image URL, download the image
if image_url:
    print("Image URL:", image_url)

    # Download the image
    response = requests.get(image_url)
    with open("product_image.jpg", "wb") as file:
        file.write(response.content)
    print("Image downloaded as 'product_image.jpg'.")

else:
    print("Image URL not found.")
