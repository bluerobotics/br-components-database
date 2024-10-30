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
        print(json.dumps(product_data, indent=4))  # Pretty print the full JSON data

        # Check if 'PrimaryPhotoURL' or another field exists for the image URL
        image_url = product_data.get("PrimaryPhoto") or product_data.get("ImageUrl")  # Adjust if necessary
        if image_url:
            print("Product Image URL:", image_url)
            return image_url
        else:
            print("Image not found in this product data.")
    else:
        print("Error:", response.status_code, response.text)




#get_access_token(code, token_filename)
token = load_token_from_file('digikey_token.json')
print(token)

#time.sleep(0.5)

print('\033[31mRefreshing token: \033[0m')
token_refreshed = get_refresh_token(token, token_filename)

print(token)



