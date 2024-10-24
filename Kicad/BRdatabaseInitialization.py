import kiutils.symbol, kiutils.items
import random
import os
import glob
import pandas as pd

#### Function for generating a unique BR ID ####
def generate_BRID(existing_BRIDs):

    # Set number of digits in unique BRID
    num_digits = 6      

    # Increment by 1 until the BRID doesn't exist
    for n in range(10**num_digits):

        # Convert to a zero padded string (to fill the desired number of digits -- e.g, 1 --> '0001')
        BR_num = str(n).zfill(num_digits)
        BRID = 'BRE-' + BR_num

        # If the new BRID isn't currently used, we've found the one!
        if BRID not in existing_BRIDs:
            break

    return BRID

def add_field_to_symbol(symbol_lib, symbol_name, field_name, field_value):
    """
    Add a custom field to a KiCad symbol (.kicad_sym file) using kiutils.

    Args:
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
    field_id = len(symbol.properties)  # Set ID to the next available index
    new_field = kiutils.symbol.Property(key=field_name, value=field_value, id=field_id, effects=kiutils.items.common.Effects(font=kiutils.items.common.Font(face=None, height=1.27, width=1.27, thickness=None, bold=False, italic=False, lineSpacing=None, color=None), justify=kiutils.items.common.Justify(horizontally=None, vertically=None, mirror=False), hide=True, href=None), showName=False)

    # Add the new field to the symbol's properties
    symbol.properties.append(new_field)

    # Save the modified symbol back to the file
    print(f'Field "{field_name}" with value "{field_value}" added to symbol "{symbol_name}".')

def hide_attributes(symbol):

    for prop in symbol.properties:
        if prop.key != "Reference" and prop.key != "Value":
            prop.effects.hide = True

# Not really necessary, but initializes the dataframes. This is at good reference for the columns, at least
parts_df = pd.DataFrame(columns=['BR ID','Name','Description','Value','Symbol','Footprint','Datasheet','Manufacturer','MPN', 'Category'])
vendors_df = pd.DataFrame(columns=['BR ID','Supplier','SPN','Stock'])

ID_list = []
parts_list = []
vendors_list = []

# Reading symbol libraries from our BR symbols folder
# SYMBOLS_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols"
# JLC_PATH = r"C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/jlc-scraper/csv/Parts Inventory on JLCPCB.xlsx"
# OUTPUT_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/Kicad"
SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"
JLC_PATH = r"C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/jlc-scraper/csv/Parts Inventory on JLCPCB.xlsx"
OUTPUT_PATH = "C:/Users/JacobBrotmanKrass/Documents"
os.chdir(SYMBOLS_PATH)
for lib_file in glob.glob("*.kicad_sym"):

    # Extract library nickname/category -- e.g., 0402_Capacitors
    lib_nickname = lib_file.replace(".kicad_sym", "")

    # Skip these libraries, they don't need to be documented (obsolete or not actual parts)
    if (lib_nickname == "BR~Deprecated") or (lib_nickname == "BR_Virtual_Parts"):
        continue
    print(lib_nickname)

    # Open symbol library
    lib_path = os.path.join(SYMBOLS_PATH, lib_file)
    symbol_lib = kiutils.symbol.SymbolLib().from_file(lib_path)
    
    # The Category is the library nickname, without the BR_ at the beginning
    category = lib_nickname[3:]

    # For each symbol in a given library, populate a new row in the Parts dataframe
    for symbol in symbol_lib.symbols:

        # Symbol path in Kicad
        symbol_path = f"{lib_nickname}:{symbol.entryName}"

        # Generate a unique BR ID --- Only necessary for this first commit of Kicad parts into our BR "database"
        BR_ID = generate_BRID(ID_list)
        ID_list.append(BR_ID)

        # Grab all the properties from the Kicad Symbol
        properties = {property.key: property.value for property in symbol.properties}


        # Some parts don't have a manufacturer and manufacturer part number -- deal with this some other time, for now just populate "None"
        if "Manufacturer" in properties:
            manufacturer = properties["Manufacturer"]
            mpn = properties["Manufacturer Part Num"]
        else:
            manufacturer = ""
            mpn = ""

        # Append a dictionary of all part properties to the parts list -- this will be converted to a Pandas dataframe at the end
        parts_list.append({"BR ID":BR_ID, "Name":symbol.libId, "Description":properties["Description"], "Value":properties["Value"], "Symbol":symbol_path, "Footprint":properties["Footprint"],  "Datasheet":properties["Datasheet"], "Manufacturer":manufacturer, "MPN":mpn, "Category":category})

        # Add BR ID to the symbol
        add_field_to_symbol(symbol_lib, symbol.libId, "BR ID", BR_ID)
        hide_attributes(symbol)

        # Extract all supplier-related properties: supplier X with suppler number X
        supplier_properties = {property: properties[property] for property in properties if property[:8]=="Supplier"}
        supplier_numbers = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]=='P'}
        supplier_names = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]!='P'}

        # Ignore any thing that looks like this
        null_strings = ["", " ", "-", "--", "~", "NA", "N/A"]

        # Loop through and add vendors and the respective supplier number when the number X at the end matches (supplier 1 --> supplier part num 1)
        for name in supplier_names:
            for number in supplier_numbers:
                if name[-1] == number[-1]:
                    if supplier_numbers[number] not in null_strings:

                        # Append dictionary of supplier properties for each SPN to the vendors list
                        # this will be converted to Pandas dataframe at the end
                        vendors_list.append({"BR ID":BR_ID, "Supplier":supplier_names[name], "SPN":supplier_numbers[number], "Stock":0})

    symbol_lib.to_file(encoding='utf-8')

# Create Pandas dataframes from these lists of dictionaries
# Think of each dictionary as a row in the table
parts_df = pd.DataFrame(parts_list)
vendors_df = pd.DataFrame(vendors_list)

# Create dataframe from the JLC scrape spreadsheet
jlc_df = pd.read_excel(JLC_PATH)

# Merge the vendors and JLC dataframes by Supplier Part Number
jlc_df.rename(columns={"JLCPCB Part #":"SPN"}, inplace=True)
merged_df = pd.merge(vendors_df.set_index("SPN"), jlc_df.set_index("SPN"), on="SPN", how='left')

# Populate the stock column using the maximum value of the three sources of JLC stock
merged_df["Stock"] = merged_df[["JLCPCB Parts Qty", "Global Sourcing Parts Qty", "Consigned Parts Qty"]].max(axis=1)

# I think we only want the BR ID, Supplier, SPN, and Stock columns
vendor_stock_df = merged_df.reset_index()[["BR ID", "Supplier", "SPN", "Stock"]]

# Create a hierarchical index using the BR ID and its various associated supplier part numbers 
vendor_stock_df.set_index(["BR ID", "SPN"], inplace=True)

# Set parts index to BR ID as well (no need for hierarchical indexing here, though)
parts_df.set_index(["BR ID"], inplace=True)

# Save dataframes to excel files
vendor_stock_df.to_excel(os.path.join(OUTPUT_PATH, "Test_Vendor_Stock.xlsx"))
parts_df.to_excel(os.path.join(OUTPUT_PATH, "Test_Parts_Library.xlsx"))    