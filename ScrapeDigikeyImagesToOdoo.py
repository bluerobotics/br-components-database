"""
client_id = "xc0ktW7Fap5V4EkA0IvI076C9nvVlecH"
redirect_uri = "https://localhost"  # Or a custom callback URL

auth_url = f"https://api.digikey.com/v1/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=productinformation"
print("Go to this URL in your browser to authorize:", auth_url)
https://api.digikey.com/v1/oauth2/authorize?response_type=code&client_id=xc0ktW7Fap5V4EkA0IvI076C9nvVlecH&redirect_uri=https://localhost

"""



import requests
import json
import time
import sys
from urllib.parse import quote
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

#filename is needed to store login information in a JSON file
#auth_code will be received code from the request link below...
# IF WE NEED A NEW AUTH_CODE, go to https://api.digikey.com/v1/oauth2/authorize?response_type=code&client_id=xc0ktW7Fap5V4EkA0IvI076C9nvVlecH&redirect_uri=https://localhost
# The code will actually be in the resulting url of the error page
code = 'AvTChEDg'
token_filename = 'digikey_token.json'
client_id = "xc0ktW7Fap5V4EkA0IvI076C9nvVlecH"

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


def get_access_token(auth_code, filename):
    token = load_token_from_file(filename)
    url = 'https://api.digikey.com/v1/oauth2/token'
    url_data = {
        'code': auth_code,
        'client_id': token['client_id'],
        'client_secret': token['client_secret'],
        'redirect_uri': 'https://localhost',
        'grant_type': 'authorization_code'
    }
    response = requests.post(url, data=url_data)
    if response.status_code == 200:
        print('\033[32mAccess Token get SUCCESS\033[0m')
        response_data = response.json()
        token['access_token'] = response_data['access_token']
        token['refresh_token'] = response_data['refresh_token']
        token['expires_in'] = response_data['expires_in']
        token['refresh_token_expires_in'] = response_data['refresh_token_expires_in']
        token['token_type'] = response_data['token_type']

    print(token)

    with open(filename, "w") as arquivo:
        json.dump(token, arquivo)

    return token


def load_token_from_file(filename):
    with open(filename, 'r') as arquivo:
        token = json.load(arquivo)

    if token != False:
        print('\033[32mToken load SUCCESS.\033[0m')
    else:
        print('\033[31m\033[1mToken load FAILED.\033[0m')
    return token

def get_refresh_token(token, filename):
    url = 'https://api.digikey.com/v1/oauth2/token'

    if token == False:
        return False

    url_data = {
        'client_id': token['client_id'],
        'client_secret': token['client_secret'],
        'refresh_token': token['refresh_token'],
        'grant_type': 'refresh_token'
    }
    response = requests.post(url, data=url_data)
    
    if response.status_code == 200:
        print('\033[32mToken refresh SUCCESS\033[0m')
        response_data = response.json()


        token['access_token'] = response_data['access_token']
        token['refresh_token'] = response_data['refresh_token']
        token['expires_in'] = response_data['expires_in']
        token['refresh_token_expires_in'] = response_data['refresh_token_expires_in']
        token['token_type'] = response_data['token_type']

        with open(filename, "w") as arquivo:
            json.dump(token, arquivo)
    else:
        print('\033[31m\033[1mToken refreshed FAILED\033[0m')
        print(response.status_code)
        print(response.reason)

    if response:
        return(token)
    else:
        return False

def get_digikey_image_url(part_number, token):


    url = f"https://api.digikey.com/Search/v3/Products/{part_number}"  # Use the search endpoint if available
    print(url)
    headers = {
        "Authorization": f"Bearer {token['access_token']}",
        "X-DIGIKEY-Client-Id": client_id,
        "X-DIGIKEY-Locale-Site": "US",
        "X-DIGIKEY-Locale-Language": "en",
        "X-DIGIKEY-Locale-Currency": "USD",
    }

    response = requests.get(url, headers=headers)

    # Assuming you have a successful response
    if response.status_code == 200:
        product_data = response.json()
        # print(json.dumps(product_data, indent=4))  # Pretty print the full JSON data

        # Check if 'PrimaryPhotoURL' or another field exists for the image URL
        image_url = product_data.get("PrimaryPhoto") or product_data.get("ImageUrl")  # Adjust if necessary
        if image_url:
            print("Product Image URL:", image_url)
            return image_url
        else:
            print("Image not found in this product data.")
    else:
        print("Error:", response.status_code, response.text)

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

#get_access_token(code, token_filename)
token = load_token_from_file('digikey_token.json')
print(token)

#time.sleep(0.5)

print('\033[31mRefreshing token: \033[0m')
token_refreshed = get_refresh_token(token, token_filename)

print(token_refreshed)


# If an image already exists, determines if it gets overwritten
OVERWRITE_OK = True 

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
        if  OVERWRITE_OK:
            print(f"Overwriting image for {product[0]['default_code']}")
        else:
            print(f"{product[0]['default_code']} already has an image.")
            continue

    print("The product does not have an image, checking for a Digikey number.")
    # Search the Odoo vendors dataframe for Digikey parts with just the BRE number of interest
    product_digikey = odoo_vendors_df[(odoo_vendors_df["BRE Number"] == product[0]['default_code']) & (odoo_vendors_df["Supplier"].str.contains("Digikey", case=False))]

    # If this dataframe slice isn't empty, we can use the Digikey part number to scrape the image url off of Digikey's webpage
    if product_digikey.empty:
        print(f"{product[0]['default_code']} does not have a Digikey number")
        continue

    print(f"{product[0]['default_code']} has a Digikey number")
    digikey_part_number = product_digikey.iloc[0].SPN
    image_url = get_digikey_image_url(digikey_part_number, token_refreshed)

    if image_url == None: 
        print("Digikey has no image for this part")
        continue

    add_image_to_odoo_part(product_id, product, image_url)
        