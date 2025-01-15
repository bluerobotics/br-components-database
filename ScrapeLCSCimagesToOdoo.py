"""
LCSC Image Scraper
Grabs images of products with JLC numbers by going to the LCSC website, navigating to the part, downloading the image, and uploading it to the Odoo part.
These images are less impressive than DigiKeys, so best used to just fill in the blanks.
"""

from selenium import webdriver
from bs4 import BeautifulSoup
import re
import requests
import base64
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import xmlrpc.client
import pandas as pd
import traceback


# Odoo connection details
url = "https://dev2-v17.apps.bluerobotics.com/"
db = "20241009_v2"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

print("Establishing connection to Odoo Server...")
# Establishing connection
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
print("Connected.")

def load_odoo_vendors_as_df():

    print("Gathering all BRE parts from Odoo...")
    
    # Define the prefix you want to search for
    default_code_prefix = "BRE-"  # Replace with the actual prefix you're searching for

    # Search for products whose default_code starts with the given prefix using 'ilike'
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])

    # Step 1: Check if any supplier info records exist for the given product template IDs
    supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[['product_id', 'in', product_ids]]])
    product_bres = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': ['default_code']})
    product_bre_map = {product['id']: product['default_code'] for product in product_bres}

    odoo_vendors_list = []

    # Step 2: If supplierinfo_ids is not empty, read the records
    if supplierinfo_ids:
        suppliers = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids], {'fields': ['partner_id', 'product_code', 'product_id']})
        for supplier in suppliers:
            odoo_vendors_list.append({'BRE Number': product_bre_map[supplier['product_id'][0]], 'Supplier': supplier['partner_id'][1], 'SPN': supplier['product_code']})
    else:
        print("No supplier information found for the provided product template IDs.")

    odoo_vendors_df = pd.DataFrame(odoo_vendors_list)

    return supplierinfo_ids, odoo_vendors_df

def get_lcsc_image_url(part_number):

    # Set up Chrome options for headless mode
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--no-sandbox")  # Optional: for compatibility
    options.add_argument("--disable-dev-shm-usage")  # Optional: for compatibility

    # Initialize the WebDriver
    driver = webdriver.Chrome(options)  # Provide the path to chromedriver if needed

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
        return image_url
    else:
        print("Image URL not found.")

def add_image_to_odoo_part(product_id, product, image_url):

    # Add headers to mimic a real browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }

    response = requests.get(image_url, headers=headers)

    if response.status_code == 200:

        # Convert the image to base64 encoding
        image_base64 = base64.b64encode(response.content).decode('utf-8')

        try:
            # Create the new product
            models.execute_kw(db, uid, password, 'product.product', 'write', [[product_id], {'image_1920': image_base64}])

            print(f"Success: New image added to {product[0]['default_code']}")

        except Exception as e:
            # Capture the full traceback to show the detailed error
            error_message = traceback.format_exc()
            print(f"An error occurred: {error_message}")

    else:
        print("Failed to get image. Status code:", response.status_code)

dir_path = os.path.dirname(os.path.realpath(__file__))
scraper_path = os.path.join(dir_path, "lcsc-scraper", "main.py")
image_path = os.path.join(dir_path, "Images")

supplierinfo_ids, odoo_vendors_df = load_odoo_vendors_as_df()

#for vendor in odoo_vendors_list:
    # FIND FIRST JLC VENDOR AND SCRAPE ITS IMAGE OFF OF LCSC

# Specify BRE numbers
default_code_prefix = "BRE-"  

# Search for products whose default_code starts with the given prefix using 'ilike'
product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])

for product_id in product_ids:

    # Read the image_1920 field
    product = models.execute_kw(db, uid, password, 'product.product', 'read', [product_id], {'fields': ['image_1920', 'default_code']})

    # Check if image_1920 contains data
    if product[0]['image_1920']:
        print(f"{product[0]['default_code']} already has an image.")
        continue

    print("The product does not have an image, checking for a JLC number.")
    # Search the Odoo vendors dataframe for JLC parts with just the BRE number of interest
    product_jlc = odoo_vendors_df[(odoo_vendors_df["BRE Number"] == product[0]['default_code']) & (odoo_vendors_df["Supplier"] == "JLCPCB")]

    # If this dataframe slice isn't empty, we can use the JLC part number to scrape the image url off of LCSC's webpage
    if product_jlc.empty:
        print(f"{product[0]['default_code']} does not have a JLCPCB number")
        continue

    print(f"{product[0]['default_code']} has a JLCPCB number")
    jlc_part_number = product_jlc.iloc[0].SPN
    image_url = get_lcsc_image_url(jlc_part_number)

    if image_url == None: 
        print("LCSC has no image for this part")
        continue

    add_image_to_odoo_part(product_id, product, image_url)
        

