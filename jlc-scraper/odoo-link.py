from xmlrpc import client
import xmlrpc.client
import csv
import os

url = "https://dev17.apps.bluerobotics.com/"
db = "20240809"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

# Accessing models
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

# Expanded list of fields to fetch
expanded_fields = [
    'name', 'default_code', 'type', 'categ_id', 'lst_price',
    'standard_price', 'qty_available', 'description', 'barcode',
    'uom_id', 'uom_po_id', 'active', 'volume', 'weight',
    'sale_ok', 'purchase_ok', 'create_date', 'write_date'
]

# Fetching all products with the expanded fields
print("Fetching product data...")
products = models.execute_kw(db, uid, password, 'product.product', 'search_read',
                             [[]],  # Empty domain to search all products
                             {'fields': expanded_fields, 'limit': 1000})

# Directory to save the CSV file
csv_directory = 'csv'  # This will create a folder named 'csv' in the current working directory
os.makedirs(csv_directory, exist_ok=True)

# Updated CSV file path
csv_file_path = os.path.join(csv_directory, 'products.csv')
with open(csv_file_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    # Writing the header with the expanded field names
    writer.writerow(expanded_fields)

    # Writing product data with progress updates
    print("Exporting data to CSV...")
    total_products = len(products)
    for index, product in enumerate(products, start=1):
        # Resolving names from tuples (e.g., 'categ_id', 'uom_id', 'uom_po_id')
        row_data = [
            product.get(field, 'N/A') if field not in ['categ_id', 'uom_id', 'uom_po_id']
            else product.get(field, ['N/A'])[1]
            for field in expanded_fields
        ]
        writer.writerow(row_data)
        # Print progress every 50 products
        if index % 50 == 0 or index == total_products:
            print(f"Processed {index} of {total_products} products...")

print(f"Data exported successfully to {os.path.abspath(csv_file_path)}")
