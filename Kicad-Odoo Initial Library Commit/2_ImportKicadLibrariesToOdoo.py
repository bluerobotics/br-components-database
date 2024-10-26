import xmlrpc.client
import traceback
import pandas as pd
import glob
import os
import kiutils.symbol, kiutils.items

# Odoo connection details
url = "https://dev2-v17.apps.bluerobotics.com/"
db = "20241009"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def submit_new_part(bre_number, description, datasheet, library, manufacturer, mpn):
    """
    Function to submit a new part to Odoo. Will create the product and update its Vendor table.

    Parameters
    ----------
    bre_number (str) : A unique product ID of the form [BRE-xxxxxx], this is the only circumstance where it is generated outside of Odoo
    description (str) : The part's description, from the Description field in Kicad
    datasheet (str) : The part datasheet's URL, from the Datasheet field in Kicad
    library (str) : The BR Kicad Library name, extracted from the Kicad file name (ex: Capacitors_0402)
    manufacturer (str) : The part's manufacturer, from the Manufacturer field in Kicad
    mpn (str) : The part's manufacture part number, from the Manufacturer Part Num field in Kicad

    """

    company_id = models.execute_kw(db, uid, password, 'res.company', 'search', [[['name', 'ilike', "Blue Robotics Inc."]]])

    try:
        # Create the new product
        new_product_id = models.execute_kw(db, uid, password, 'product.product', 'create', [{
            'default_code': bre_number,
            'name': description,
            'bre_number': bre_number,
            'datasheet': datasheet,
            'manufacturer': manufacturer,
            'mpn': mpn,
            'library': library,
            'sale_ok': False,
            'detailed_type': "product",
            'company_id': company_id[0],
        }])

        print(f"Success: New part created with ID {new_product_id}")

    except Exception as e:
        # Capture the full traceback to show the detailed error
        error_message = traceback.format_exc()
        print(f"An error occurred: {error_message}")

def add_vendor_info(bre_number, supplier, spn):
    """
    Function to add a supplier and supplier part number to a specified BRE numbered part in Odoo

    Parameters
    ----------
    bre_number (str) : A unique product ID of the form [BRE-xxxxxx], links Odoo and Kicad parts together
    supplier (str) : The supplier to be added to the specified part's Vendors table in Odoo
    spn (str) : The respective supplier part number to be added to the Vendors table in Odoo
    """
    # Search for the supplier ID in res.partner (returns a list of matches, should just be the first one)
    supplier_id = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['name', 'ilike', supplier]]])
    if not supplier_id:
        print(f"Error: Supplier {supplier} not found.")
        return
    
    # Search for the product ID (internal to Odoo, not the BRE)
    product_id = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', '=', bre_number]]])

    # Create a new vendor in the correct product's purchase page
    models.execute_kw(db, uid, password, 'product.supplierinfo', 'create', [{
        'product_id': product_id[0],
        'partner_id': supplier_id[0],
        'product_code': spn,
    }])
    
def load_kicad_lib_as_dataframe(symbols_path):
    
    os.chdir(symbols_path)

    parts_list = []
    vendors_list = []
    
    print("Loading in libraries from Kicad...")
    
    for lib_file in glob.glob("*.kicad_sym"):

        # Extract library nickname/category -- e.g., 0402_Capacitors
        lib_nickname = lib_file.replace(".kicad_sym", "")

        # Skip these libraries, they don't need to be documented (obsolete or not actual parts)
        if (lib_nickname == "BR~Deprecated") or (lib_nickname == "BR_Virtual_Parts"):
            continue

        # Open symbol library
        lib_path = os.path.join(symbols_path, lib_file)
        symbol_lib = kiutils.symbol.SymbolLib().from_file(lib_path)
        
        # The Category is the library nickname, without the BR_ at the beginning
        library = lib_nickname[3:]

        # For each symbol in a given library, populate a new row in the Parts dataframe
        for symbol in symbol_lib.symbols:

            # Symbol path in Kicad
            symbol_path = f"{lib_nickname}:{symbol.entryName}"

            # Grab all the properties from the Kicad Symbol
            properties = {property.key: property.value for property in symbol.properties}

            # Some parts don't have a manufacturer and manufacturer part number -- deal with this some other time, for now just populate "None"
            if "Manufacturer" in properties:
                manufacturer = properties["Manufacturer"]
                mpn = properties["Manufacturer Part Num"]
            else:
                manufacturer = ""
                mpn = ""

            if "BRE Number" in properties:
                BRE = properties["BRE Number"]
                if len(BRE) < 7:
                    BRE = ""
            else:
                BRE = ""
            # Append a dictionary of all part properties to the parts list -- this will be converted to a Pandas dataframe at the end
            parts_list.append({"BRE Number":BRE, "Name":symbol.libId, "Description":properties["Description"], "Value":properties["Value"], "Symbol":symbol_path, "Footprint":properties["Footprint"],  "Datasheet":properties["Datasheet"], "Manufacturer":manufacturer, "MPN":mpn, "Library":library})

            # Extract all supplier-related properties: supplier X with suppler number X
            supplier_properties = {property: properties[property] for property in properties if property[:8]=="Supplier"}
            supplier_numbers = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]=='P'}
            supplier_names = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]!='P'}

            # Ignore anything that looks like this
            null_strings = ["", " ", "-", "--", "~", "NA", "N/A"]

            # Loop through and add vendors and the respective supplier number when the number X at the end matches (supplier 1 --> supplier part num 1)
            for name in supplier_names:
                for number in supplier_numbers:
                    if name[-1] == number[-1]:
                        if supplier_numbers[number] not in null_strings:

                            # Append dictionary of supplier properties for each SPN to the vendors list
                            # this will be converted to Pandas dataframe at the end
                            vendors_list.append({"BRE Number":BRE, "Supplier":supplier_names[name], "SPN":supplier_numbers[number], "Stock":0})



    # Create Pandas dataframes from these lists of dictionaries
    # Think of each dictionary as a row in the table
    parts_df = pd.DataFrame(parts_list)
    vendors_df = pd.DataFrame(vendors_list)
    
    return parts_df, vendors_df


SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"

full_parts_df, vendors_df = load_kicad_lib_as_dataframe(SYMBOLS_PATH)
odoo_df = full_parts_df[["BRE Number", "Description", "Datasheet", "Manufacturer", "MPN", "Library"]]

for idx, row in odoo_df.iloc[:10].iterrows():
    submit_new_part(row["BRE Number"], row["Description"], row["Datasheet"], row["Library"], row["Manufacturer"], row["MPN"])
    print(row["BRE Number"])
    for idx, vendor in vendors_df[vendors_df["BRE Number"] == row["BRE Number"]].iterrows():
        print(vendor["BRE Number"], vendor["Supplier"], vendor["SPN"])
        add_vendor_info(vendor["BRE Number"], vendor["Supplier"], vendor["SPN"])
