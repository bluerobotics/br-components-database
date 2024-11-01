import kiutils.symbol
import os
import glob
import pandas as pd
import xmlrpc.client

# Reading symbol libraries from our BR symbols folder
SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols" # TEST LIBRARY
scripts_path = os.path.dirname(os.path.abspath(__file__))
#SYMBOLS_PATH = os.path.join(scripts_path, os.pardir, "Symbols")

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

def load_odoo_as_df():
    """
    Load in BRE parts from Odoo as a pandas Dataframe. This format greatly enhances the ability to compare, analyze, and update parts to the Kicad library.
    All Odoo access should be handled outside of the function to reduce redundancy, as all Odoo functions rely on the connection

    Returns
    -------
    parts_df (pd.DataFrame) : DataFrame containing all of the parts with the following columns:
                              ["BRE Number", "Name", "Description", "Value", "Symbol", "Footprint",  "Datasheet", "Manufacturer", "MPN", "Library"]
    """

    print("Gathering all BRE parts from Odoo...")
    
    # Define the prefix you want to search for
    default_code_prefix = "BRE-"  # Replace with the actual prefix you're searching for

    # Search for products whose default_code starts with the given prefix using 'ilike'
    product_ids = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{default_code_prefix}%"]]])

    odoo_parts_list = []

    # If products are found, read the details of the products
    if product_ids:
        # Read details of the products found by their IDs
        products = models.execute_kw(db, uid, password, 'product.product', 'read', [product_ids], {'fields': ['name', 'default_code', 'component_value', 'datasheet', 'manufacturer', 'mpn', 'library']})
        
        # Print the products' details
        for product in products:
            odoo_parts_list.append({'BRE Number': product['default_code'], 'Description': product['name'], 'Value': product['component_value'], 'Datasheet': product['datasheet'], 'Manufacturer': product['manufacturer'], 'MPN': product['mpn'], 'Library': product['library']})

    else:
        print(f"No products found with default_code starting with: {default_code_prefix}")

    print("All BRE parts loaded successfully.")

    odoo_df = pd.DataFrame(odoo_parts_list).replace(to_replace={False:''})

    return odoo_df

def load_kicad_lib_as_dataframe(symbols_path):
    """
    Load in Kicad libraries as a pandas Dataframe. This format greatly enhances the ability to compare, analyze, and update parts to another database (Odoo, for instance).
    Also pulls in vendor information from parts.

    Parameters
    ----------
    symbols_path (raw str) : The path to the Kicad symbol libraries

    Returns
    -------
    parts_df (pd.DataFrame) : DataFrame containing all of the parts with the following columns:
                              ["BRE Number", "Name", "Description", "Value", "Symbol", "Footprint",  "Datasheet", "Manufacturer", "MPN", "Library"]
    vendords_df (pd.DataFrame) : DataFrame containing all supplier information and respective BRE numbers, containing the columns:
                                 ["BRE Number", "Supplier", "SPN", "Stock"]
    """

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


    print("Kicad libraries loaded successfully.")

    # Create Pandas dataframes from these lists of dictionaries
    # Think of each dictionary as a row in the table
    parts_df = pd.DataFrame(parts_list)
    vendors_df = pd.DataFrame(vendors_list)
    
    return parts_df, vendors_df

def save_df_to_kicad_lib(updated_parts, symbols_path):
    """
    Use a DataFrame of the updated parts to actually push these updates into their specific Kicad libraries and save the library. 
    By only taking in the updated parts, we can push changes only the libraries that have edits to be made, preventing each change 
    from requiring modification of every BR library.

    Parameters
    ----------
    updated_parts (pd.DataFrame) : A DataFrame containing updated fields for any Kicad parts that had discrepancies with its respective Odoo part
    symbols_path (raw str) : The path to the Kicad symbol libraries
    """

    os.chdir(symbols_path)

    print(f"Updating the following parts: {updated_parts}")

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

        # To save time, first 
        if library in updated_parts['Library'].to_list():
            
            print(f"Updating {library}")
            
            # For each symbol in a given library, populate a new row in the Parts dataframe
            for symbol in symbol_lib.symbols:

                # Grab all the properties from the Kicad Symbol
                properties_dict = {property.key.strip(): property.value.strip() for property in symbol.properties}

                if 'BRE Number' in properties_dict and properties_dict['BRE Number'] in updated_parts.index.to_list():
                    print(f"Updating {properties_dict['BRE Number']}")
                    
                    if 'Manufacturer' not in properties_dict:   # Add Manufacturer field to Kicad symbol if it doesn't already exist
                        add_field_to_symbol(symbol_lib, symbol.libId, "Manufacturer", "")
                    if 'Manufacturer Part Num' not in properties_dict:  # Add Manufacturer Part Num field to Kicad symbol if it doesn't already exist
                        add_field_to_symbol(symbol_lib, symbol.libId, "Manufacturer Part Num", "")

                    updated_part = updated_parts.loc[properties_dict['BRE Number']]
                    for property in symbol.properties:
                        if property.key == 'Description':
                            property.value = updated_part['Description']
                        if property.key == 'Value':
                            property.value = updated_part['Value']
                        if property.key == 'Datasheet':
                            property.value = updated_part['Datasheet']
                        if property.key == 'Manufacturer':
                            property.value = updated_part['Manufacturer']
                        if property.key == 'Manufacturer Part Num':
                            property.value = updated_part['MPN']

                    update_library_field_in_odoo(properties_dict['BRE Number'], library)
                
                sort_symbol_fields(symbol)
                hide_attributes(symbol)

        symbol_lib.to_file(encoding='utf-8')


def add_field_to_symbol(symbol_lib, symbol_name, field_name, field_value):
    """
    Add a custom field to a KiCad symbol (.kicad_sym file) using kiutils.

    Parameters
    ----------
    symbol_lib (kiutils SymbolLib): symbol_lib object being read
    symbol_name (str): The name of the symbol to modify.
    field_name (str): The name of the field to add.
    field_value (str): The value of the field to add.
    """

    # Find the symbol by name
    symbol = None
    for sym in symbol_lib.symbols:
        if sym.libId == symbol_name:
            symbol = sym
            break

    if symbol is None:
        raise ValueError(f'Symbol "{symbol_name}" not found in the library.')

    # Create the new field using kiutils' built-in property structure

    new_field = kiutils.symbol.Property(key=field_name, value=field_value, effects=kiutils.items.common.Effects(font=kiutils.items.common.Font(face=None, height=1.27, width=1.27, thickness=None, bold=False, italic=False, lineSpacing=None, color=None), justify=kiutils.items.common.Justify(horizontally=None, vertically=None, mirror=False), hide=True, href=None), showName=False)

    # Add the new field to the symbol's properties
    symbol.properties.append(new_field)

    # Save the modified symbol back to the file
    print(f'Field "{field_name}" with value "{field_value}" added to symbol "{symbol_name}".')

def hide_attributes(symbol):
    """
    Quick fix to hide all symbol properties besides Reference and Value. This is to patch Kiutils seeming inability to handle the hide attribute (sets everything to be visible...)

    Parameters
    ----------
    symbol (kiutils symbol) : A symbol object containing all property fields and other attributes
    """
    for prop in symbol.properties:
        if prop.key != "Reference" and prop.key != "Value":
            prop.effects.hide = True

def sort_symbol_fields(symbol):
    """
    Function to sort Kicad fields in a standard order, while not deleting any other fields (such as supplier info)

    Parameters
    ----------
    symbol (kiutils symbol) : A symbol containing all property fields and other attributes
    """
    
    # This is the default order
    main_fields = ['Reference', 'Value', 'Footprint', 'Datasheet', 'Manufacturer', 'Manufacturer Part Num', 'BRE Number']
    
    # Create a list of main properties in the order that main_fields is laid out above
    main_properties = []
    for field in main_fields:
        for prop in symbol.properties:
            if prop.key == field:
                main_properties.append(prop)

    # Double check to make sure all required fields are present
    if len(main_properties) < len(main_fields):
        raise ValueError(f'Symbol "{symbol.libId}" does not contain all of the required fields: {main_fields}.')
    
    # Toss in the remaining properties. These can be custom fields, they don't really matter, they'll just be added in the order they appear
    other_properties = [prop for prop in symbol.properties if prop.key not in main_fields]

    symbol.properties = main_properties + other_properties

def update_library_field_in_odoo(bre_number, library):
    """
    Update the library field in Odoo from Kicad, as this information is stored directly in the Kicad library structure. This is really the only info coming from Kicad to Odoo.

    Parameters
    ----------
    bre_number (str) : A string of the form BRE-xxxxxx, indicates which part to update in Odoo
    library (str) : The name of the library to fill the field in Odoo
    """

    print("Updating library field in Odoo...")
    product_id = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', '=', bre_number]]])
    models.execute_kw(db, uid, password, 'product.product', 'write', [product_id, {'library': library}])

def duplicate_handling(kicad_df):
    """
    Handle Kicad parts that share the same BRE number. We need to make sure that any discrepancies that are synced from Odoo are detected.
    This is necessary because the df.compare method requires duplicates to be removed. 
    duplicate_handling() modifies the field of the FIRST of the duplicates to say "CHANGE" in the description, marking that BRE for update, even if it's one of the other duplicates that has the discrepancy

    Parameters
    ----------
    kicad_df (pd.DataFrame) : A DataFrame of Kicad library parts
    """
    # Isolate parts that share BR numbers and group by BRE number
    for bre, group in kicad_df[kicad_df.duplicated(subset="BRE Number", keep=False)].groupby("BRE Number"):

        # We only care about the columns that show up in Odoo
        group = group[["BRE Number", "Description", "Value", "Datasheet", "Manufacturer", "MPN"]]

        # Loop through and detect any differences between the first part and subsequent BRE duplicates
        for idx, row in group.iterrows():
            difference_indicator = (~(group.iloc[0]==row)).sum()

            # If differences are detected, change the first part's Description field to "CHANGE"
            if difference_indicator > 0:    
                print(f"Differences discovered between Kicad parts labelled {bre}, marking to update all from Odoo...")
                kicad_df.loc[group.index[0], "Description"] = "CHANGE"

#########################################################################################################################################

# Load in Odoo parts as a pandas DataFrame
odoo_df = load_odoo_as_df()

# Load in Kicad parts as a dataframe (we won't actually be using vendor info from Kicad)
kicad_df, vendors_df = load_kicad_lib_as_dataframe(SYMBOLS_PATH)

# We have to make sure there are no duplicate BRE numbers before updating the Kicad library--the process is one-to-one
# Detect any discrepancies between the duplicates before removing them
duplicate_handling(kicad_df)
kicad_df.drop_duplicates(subset="BRE Number", keep='first', inplace=True)

# Set and sort DataFrame index as BRE Number
kicad_df.set_index("BRE Number", inplace=True)
kicad_df.sort_index(inplace=True)

# Drop any duplicate BRE columns just in case (very unlikely in Odoo)
odoo_df.drop_duplicates(subset="BRE Number", inplace=True)

# Set and sort DataFrame index as BRE Number
odoo_df.set_index("BRE Number", inplace=True)
odoo_df.sort_index(inplace=True)

# Drop the library column from the Odoo dataframe; Kicad has no use for this field (Odoo actually gets this info from Kicad)
odoo_df.drop(columns=['Library'], inplace=True)

kicad_old = kicad_df.copy()

# Update fields from Odoo to Kicad dataframe
kicad_df.update(odoo_df)

# Compares the updated Kicad dataframe to the old one to determine what parts need to be updated in the library (efficiency!)
changes = kicad_df.compare(kicad_old, result_names=("new", "old"))

# If there are no changes, we're all good to quit the program
if changes.empty: 
    print("Kicad libraries already up to date!")
    quit()

print(changes)

# Focus on just the updated parts
updated_parts = kicad_df.loc[changes.index]

# Push these changes to the kicad library
save_df_to_kicad_lib(updated_parts, SYMBOLS_PATH)