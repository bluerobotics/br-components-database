"""
USE WITH CAUTION
A utility to delete all parts with BRE numbers from Odoo. There's no undoing this. Really just for prototyping, this should never be used in normal workflow.
"""


import xmlrpc.client

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


# Define the prefix you want to search for
default_code_prefix = "BRE-" 

# Search for products whose default_code starts with the given prefix using 'ilike'
product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])

for product_id in product_ids:
    print("Deleting ", product_id)

    # Delete supplier information linked to the product
    try:
        supplier_ids = models.execute_kw(
            db, uid, password, 'product.supplierinfo', 'search', [[['product_id', '=', product_id]]]
        )
        if supplier_ids:
            models.execute_kw(db, uid, password, 'product.supplierinfo', 'unlink', [supplier_ids])
            print(f'Supplier information for product ID {product_id} was successfully deleted.')
    except Exception as e:
        print(f'Error deleting supplier information: {e}')

    # Perform the deletion
    try:
        models.execute_kw(db, uid, password, 'product.product', 'unlink', [[product_id]])
        print(f'Product with ID {product_id} was successfully deleted.')
    except Exception as e:
        print(f'An error occurred: {e}')