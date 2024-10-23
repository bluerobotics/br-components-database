import xmlrpc.client
import traceback
import string
import os
import pandas as pd

# Odoo connection details
url = "https://dev17.apps.bluerobotics.com/"
db = "20240809"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

PARTS_SHEET_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/Kicad/Parts_Library.xlsx"
parts_sheet = pd.read_excel(PARTS_SHEET_PATH, index_col=[0])

for BR_ID, symbol in parts_sheet.iterrows():

    # Search for product by its default code (e.g., 'PROD001')
    product_id = models.execute_kw(db, uid, password, 'product.product', 'search', [[('default_code', '=', BR_ID)]])

    if product_id:
        # Update the product
        result = models.execute_kw(db, uid, password, 'product.product', 'write', [product_id, {
            'ID': BR_ID,
            'category': symbol.Category,
            'name': symbol.Name,
            'value': symbol.Value,
            'description': symbol.Description,
            'datasheet': symbol.Datasheet,
            'manufacturer': symbol.Manufacturer,
            'MPN': symbol.MPN
        }])

        if result:
            print("Product updated successfully")
        else:
            print("Failed to update product")
    else:
        print("Product does not yet exist in Odoo")

        result = models.execute_kw(db, uid, password, 'product.product', 'create', [product_id, {
            'ID': BR_ID,
            'category': symbol.Category,
            'name': symbol.Name,
            'value': symbol.Value,
            'description': symbol.Description,
            'datasheet': symbol.Datasheet,
            'manufacturer': symbol.Manufacturer,
            'MPN': symbol.MPN
        }])