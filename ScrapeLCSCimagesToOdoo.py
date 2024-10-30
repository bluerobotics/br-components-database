import subprocess
import os 
import xmlrpc.client
import pandas as pd

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

    odoo_vendors_list = []

    # Step 2: If supplierinfo_ids is not empty, read the records
    if supplierinfo_ids:
        products = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids], {'fields': ['partner_id', 'product_code']})
        for product, product_bre in zip(products, product_bres):
            odoo_vendors_list.append({'BRE Number': product_bre['default_code'], 'Supplier': product['partner_id'], 'SPN': product['product_code']})
    else:
        print("No supplier information found for the provided product template IDs.")

    return supplierinfo_ids, odoo_vendors_list



dir_path = os.path.dirname(os.path.realpath(__file__))
scraper_path = os.path.join(dir_path, "lcsc_scraper", "main.py")
image_path = os.path.join(dir_path, "Images")

odoo_vendors_list = load_odoo_vendors_as_df()

for vendor in odoo_vendors_list:
    # FIND FIRST JLC VENDOR AND SCRAPE ITS IMAGE OFF OF LCSC


    subprocess.run(["python", scraper_path, part_number, image_path])

    # THEN, ADD IMAGE TO ODOO