import os
import glob
import pandas as pd
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

default_code_prefix = "BRE-"
# Search for products whose default_code starts with the given prefix using 'ilike'
product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])
products = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': ['name', 'default_code', 'component_value', 'datasheet', 'manufacturer', 'mpn', 'library']})
supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[['product_id', 'in', product_ids]]])

for product in products:
    print(product['default_code'])
    supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[['product_id', '=', product['id']]]])
    print(supplierinfo_ids)

    primary_jlc = None
    max_stock = -1

    if supplierinfo_ids:
        suppliers = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids], {'fields': ['partner_id', 'product_code', 'product_id', 'jlcpcb_inventory', 'global_sourcing_inventory', 'consigned_inventory']})
        for supplier in suppliers:
            print(supplier)

            if supplier['partner_id'] and 'jlcpcb' in supplier['partner_id'][1].strip().lower():
                stock = max(supplier['jlcpcb_inventory'], supplier['global_sourcing_inventory'] + supplier['consigned_inventory'])
                if stock >= max_stock:
                    max_stock = stock
                    primary_jlc = supplier['product_code']

        if primary_jlc:
            # Update the product
            result = models.execute_kw(db, uid, password, 'product.product', 'write', [product['id'], {'primary_jlcpcb_pn': primary_jlc}])

            if result:
                print("Product updated successfully")
            else:
                print("Failed to update product")

        #models.execute_kw(db, uid, password, 'product.supplierinfo', 'write', [supplierinfo_ids], {'fields': ['partner_id', 'product_code', 'product_id', 'jlcpcb_inventory', 'global_sourcing_inventory', 'consigned_inventory']})    

    print(primary_jlc)