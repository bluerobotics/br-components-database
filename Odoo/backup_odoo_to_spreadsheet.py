# BOM Stock Spreadsheet Generator
# For any given schematic, run this script through the Generate Legacy Bill of Materials interface in Kicad.

"""
    @package
    The script outputs a spreadsheet to the project folder that lists each component and related vendor information, all pulled from Odoo.
    Special formatting highlights components that do not have enough stock for the PCB order.
    Includes a cell to indicate the number of boards desired.
    Output: CSV (comma-separated)
    Grouped By: Libref
    Sorted By: Ref
    Fields: BRE Number, Reference, Description, Quantity/Board, Total Quantity, MPN, JLCPCB Part #, JLC Stock, Global + Consigned Stock, Alt JLC Parts, DigiKey Parts, Mouser Parts, Other Vendor Parts

    Outputs ungrouped components first, then outputs grouped components.

    Command line:
    python "pathToFile/bom_stock_spreadsheet.py" "%I" "%O"
"""

from __future__ import print_function

import os
import pandas as pd
from collections import defaultdict
import xmlrpc.client
import xlsxwriter
from xlsxwriter.utility import xl_col_to_name
from datetime import datetime

INDENT = 10*" "

# Odoo connection details
url = "https://dev2-v17.apps.bluerobotics.com/"
db = "20241009_v2"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')



def getVendorInfo(bre_number, specific_supplier='all'):
    """
    Extract vendor info for a specified BRE, with the option to access a specific supplier only. 

    Parameters
    ----------
    bre_number (str) : The BRE number of the desired part
    specific_supplier (str) : Defaults to 'JLCPCB', specifies which supplier to pull vendor info from. Use 'all' to grab vendor info irrespective of supplier

    Returns
    -------
    specific_supplier_info (list of dicts) : A list of dicts containing each supplier, SPN, and stock numbers
    """
    # Search for the product by BRE number to get its product ID
    product_id = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', '=', f"{bre_number}"]]])

    product = models.execute_kw(db, uid, password, 'product.product', 'read', [product_id], {'fields': ['product_tmpl_id']})

    # If product empty list, just return a blank
    if not product:
        return {'partner_id':[0,''], 'product_code':'', 'jlcpcb_inventory':0, 'global_sourcing_inventory':0, 'consigned_inventory':0}

    # Search for the corresponding supplier info IDs for the given prodcut
    supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[['product_tmpl_id', '=', product[0]['product_tmpl_id'][0]]]])

    #print(supplierinfo_ids)
    supplierinfo_records = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids])

    # Get the supplier info
    general_supplier_info = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids], {'fields': ['partner_id', 'product_code', 'vendor_comment', 'jlcpcb_inventory', 'global_sourcing_inventory', 'consigned_inventory']}) 
    
    if specific_supplier == 'all':          # If all suppliers are requested, just output the whole output from Odoo
        specific_supplier_info = general_supplier_info
    else:                                   # If a specific supplier is requested, check for the supplier name in each Odoo vendor entry and add matches to a list
        specific_supplier_info = []
        for supplier_info in general_supplier_info:
            if supplier_info['partner_id'][1]==specific_supplier:
                specific_supplier_info.append(supplier_info)
        # If there were no matches, output a blank vendor with 0 stock
        if not specific_supplier_info:
            specific_supplier_info = [{'partner_id':'', 'product_code':'', 'vendor_comment':'','jlcpcb_inventory':0, 'global_sourcing_inventory':0, 'consigned_inventory':0}]

    return specific_supplier_info

def load_odoo_as_df():
    """
    Load in BRE parts from Odoo as a pandas Dataframe. This format greatly enhances the ability to compare, analyze, and update parts to the Kicad library.
    All Odoo access should be handled outside of the function to reduce redundancy, as all Odoo functions rely on the connection

    Returns
    -------
    parts_df (pd.DataFrame) : DataFrame containing all of the parts with the following columns:
                            ["BRE Number", "Name", "Description", "Value", "Symbol", "Footprint",  "Datasheet", "Manufacturer", "MPN", "Library"]
    """

    print(INDENT +  "Gathering all BRE parts from Odoo...")
    
    # Define the prefix you want to search for
    default_code_prefix = "BRE-"  # Replace with the actual prefix you're searching for

    # Search for products whose default_code starts with the given prefix using 'ilike'
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])

    odoo_parts_list = []

    # If products are found, read the details of the products
    if product_ids:
        # Read details of the products found by their IDs
        products = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': ['name', 'default_code', 'component_value', 'datasheet', 'manufacturer', 'mpn', 'primary_jlcpcb_pn', 'library']})
        
        # Print the products' details
        for product in products:
            odoo_parts_list.append({'BRE Number': product['default_code'], 'Description': product['name'], 'Value': product['component_value'], 'Datasheet': product['datasheet'], 'Manufacturer': product['manufacturer'], 'MPN': product['mpn'], 'JLCPN': product['primary_jlcpcb_pn'], 'Library': product['library']})

    else:
        print(INDENT +  f"No products found with default_code starting with: {default_code_prefix}")

    print(INDENT +  "All BRE parts loaded successfully.")

    odoo_df = pd.DataFrame(odoo_parts_list).replace(to_replace={False:''})
    odoo_df = odoo_df.map(lambda x: x.strip() if isinstance(x, str) else x)

    return odoo_df

def load_odoo_vendors_as_df():

    print(INDENT + "Gathering all BRE parts from Odoo...")
    
    # Define the prefix you want to search for
    default_code_prefix = "BRE-"  # Replace with the actual prefix you're searching for

    # Search for products whose default_code starts with the given prefix using 'ilike'
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])
    # Read in all BRE parts, access their product_tmpl_id (links to vendor info) and default_code (BRE Number)
    products = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': ['product_tmpl_id', 'default_code']})

    # Create a list of all product template IDs
    product_tmpl_ids = [product['product_tmpl_id'][0] for product in products]
    # Create a map of these IDs to their respective BRE numbers
    product_bre_map = {product['product_tmpl_id'][0]: product['default_code'] for product in products}

    # Check if any supplier info records exist for the given product template IDs
    supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[['product_tmpl_id', 'in', product_tmpl_ids]]])

    odoo_vendors_list = []

    # If supplierinfo_ids is not empty, read the records
    if supplierinfo_ids:
        suppliers = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids], {'fields': ['partner_id', 'product_code', 'product_tmpl_id']})
        for supplier in suppliers:
            odoo_vendors_list.append({'BRE Number': product_bre_map[supplier['product_tmpl_id'][0]], 'Supplier': supplier['partner_id'][1], 'SPN': supplier['product_code']})
    else:
        print(INDENT + "No supplier information found for the provided product template IDs.")

    odoo_vendors_df = pd.DataFrame(odoo_vendors_list)

    return supplierinfo_ids, odoo_vendors_df

def draw_box(row_start, row_end, col_start, col_end, border_style=1, color='black'):
    width = col_end - col_start + 1
    height = row_end - row_start + 1
    if row_start>0: worksheet.write_row(row_start-1, col_start, ['' for i in range(width)], workbook.add_format({'bottom':border_style, 'border_color':color}))
    worksheet.write_row(row_end+1, col_start, ['' for i in range(width)], workbook.add_format({'top':border_style, 'border_color':color}))
    if col_start>0: worksheet.write_column(row_start, col_start-1, ['' for i in range(height)], workbook.add_format({'right':border_style, 'border_color':color}))
    worksheet.write_column(row_start, col_end+1, ['' for i in range(height)], workbook.add_format({'left':border_style, 'border_color':color}))

def copy_format(book, fmt):
    properties = [f[4:] for f in dir(fmt) if f[0:4] == 'set_']
    dft_fmt = book.add_format()
    return book.add_format({k : v for k, v in fmt.__dict__.items() if k in properties and dft_fmt.__dict__[k] != v})

#####################################################################################################################################################################################

script_path = os.path.abspath(__file__)
github_path = None
head, tail = os.path.split(script_path)
while(tail):
    head, tail = os.path.split(head)
    if tail == "GitHub":
        github_path = os.path.join(head,tail)
output_dir = os.path.join(github_path, 'br-components-database', 'Odoo')
# Set the output file name explicitly to "lumen2 Stock Info.xlsx"
output_file = "Odoo Electronics Backup.xlsx"


# Create an excel workbook and add a fresh worksheet
workbook = xlsxwriter.Workbook(os.path.join(output_dir, output_file), {'strings_to_formulas': True})
worksheet = workbook.add_worksheet()

# Create various format objects for the workbook
format_light_header = workbook.add_format({'bold': True, 'align':'center'})
format_dark_header = workbook.add_format({'bg_color': 'black', 'font_color': 'white', 'align': 'center', 'bold':True})
format_editable = workbook.add_format({'border': 1, 'border_color': '#dadada'})
format_bold = workbook.add_format({'bold':True})
format_bold_right = workbook.add_format({'bold':True, 'align':'right'})
worksheet.hide_gridlines(option=2)


# Define the columns for the output CSV
column_labels = ['BRE Number', 'Description', 'Value', 'Datasheet', 'Manufacturer', 'MPN', 'JLCPN', 'Library', 
                 'Supplier 1', 'SPN 1', 'Comment 1', 'SPN 1 JLC Stock', 'SPN 1 Global Stock', 'SPN 1 Consigned Stock', 
                 'Supplier 2', 'SPN 2', 'Comment 2', 'SPN 2 JLC Stock', 'SPN 2 Global Stock', 'SPN 2 Consigned Stock', 
                 'Supplier 3', 'SPN 3', 'Comment 3', 'SPN 3 JLC Stock', 'SPN 3 Global Stock', 'SPN 3 Consigned Stock', 
                 'Supplier 4', 'SPN 4', 'Comment 4', 'SPN 4 JLC Stock', 'SPN 4 Global Stock', 'SPN 4 Consigned Stock', 
                 'Supplier 5', 'SPN 5', 'Comment 5', 'SPN 5 JLC Stock', 'SPN 5 Global Stock', 'SPN 5 Consigned Stock']
column_dict = {}
col_number = 0
for col_name in column_labels:
    column_dict[col_name] = xl_col_to_name(col_number)
    col_number += 1

# row and col will be our pointers to cells in the sheet
row = 0
col = 0

worksheet.write_row(row, col, ["Date/Time of Backup:", datetime.now()], format_light_header)

# Write the header row
worksheet.write_row(row, col, column_labels, format_dark_header)

row += 1

# Dictionary to store grouped components
odoo_parts_df = load_odoo_as_df()


# Group components based on part characteristics
for idx, part_row in odoo_parts_df.iterrows():

    empty_supplier_dict = dict.fromkeys(['Supplier 1', 'SPN 1', 'Comment 1', 'SPN 1 JLC Stock', 'SPN 1 Global Stock', 'SPN 1 Consigned Stock', 
                 'Supplier 2', 'SPN 2', 'Comment 2', 'SPN 2 JLC Stock', 'SPN 2 Global Stock', 'SPN 2 Consigned Stock', 
                 'Supplier 3', 'SPN 3', 'Comment 3', 'SPN 3 JLC Stock', 'SPN 3 Global Stock', 'SPN 3 Consigned Stock', 
                 'Supplier 4', 'SPN 4', 'Comment 4', 'SPN 4 JLC Stock', 'SPN 4 Global Stock', 'SPN 4 Consigned Stock', 
                 'Supplier 5', 'SPN 5', 'Comment 5', 'SPN 5 JLC Stock', 'SPN 5 Global Stock', 'SPN 5 Consigned Stock'], ' ')

    part_dict = part_row.to_dict()
    print(part_dict)
    part_dict.update(empty_supplier_dict)
    
    supplier_info = getVendorInfo(part_row['BRE Number'])

    supplier_num = 1
    for supplier in supplier_info:
        print(f'Supplier {supplier_num}', supplier)
        part_dict[f'Supplier {supplier_num}'] = supplier['partner_id'][1]
        part_dict[f'SPN {supplier_num}'] = supplier['product_code']
        part_dict[f'Comment {supplier_num}'] = supplier['vendor_comment']
        part_dict[f'SPN {supplier_num} JLC Stock'] = supplier['jlcpcb_inventory']
        part_dict[f'SPN {supplier_num} Global Stock'] = supplier['global_sourcing_inventory']
        part_dict[f'SPN {supplier_num} Consigned Stock'] = supplier['consigned_inventory']
        supplier_num += 1

    for col_label, cell_value in part_dict.items():
        worksheet.write(f"{column_dict[col_label]}{row+1}", cell_value)

    # print(INDENT + f"{part_dict} added to spreadsheet")
    row += 1


# Autofit column widths to show all info
worksheet.autofit()

# Save and close the xlsx file
workbook.close()

print(INDENT + f"Odoo backup successfully written to {output_file}")

# opens file on Windows for user to see (won't work on Mac/Linux)
os.startfile(output_file)