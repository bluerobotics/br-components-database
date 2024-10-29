import subprocess
import os
import pandas as pd
import xmlrpc.client

root_folder = os.path.dirname(os.path.abspath(__file__))  # Get the script's root directory
jlc_path = os.path.join(root_folder, 'jlc-scraper')

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


subprocess.run(["python", os.path.join(jlc_path, 'jlc-scraper.py')])

# Create dataframe from the JLC scrape spreadsheet
jlc_df = pd.read_excel(os.path.join(jlc_path, 'csv', r'Parts Inventory on JLCPCB.xlsx'))


# Extract the Odoo supplierinfo_ids as a list, and load the respective vendor fields as a pandas DataFrame
supplierinfo_ids, odoo_vendors = load_odoo_vendors_as_df()


# Loop through all vendors in Odoo.
# If the supplier part number matches the JLC number from the JLC scraper
# add the JLC stock quantities to the respective Odoo field
for supplierinfo_id, part in zip(supplierinfo_ids, odoo_vendors):

    jlc = jlc_df[jlc_df['JLCPCB Part #'] == part['SPN']]

    if not jlc.empty:
        print(part['SPN'])
        models.execute_kw(db, uid, password, 'product.supplierinfo','write', [[supplierinfo_id], {
            'jlcpcb_inventory': int(jlc['JLCPCB Parts Qty'].iloc[0]),
            'global_sourcing_inventory': int(jlc['Global Sourcing Parts Qty'].iloc[0]),
            'consigned_inventory': int(jlc['Consigned Parts Qty'].iloc[0]),
        }])