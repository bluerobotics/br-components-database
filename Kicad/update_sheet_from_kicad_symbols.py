import kiutils.symbol
import os
import glob
import pandas as pd


"""
loop through Kicad symbol libraries
For each Kicad symbol, check the parts sheet for a matching BR number
    If the BR number exists, check for changes
        If changed, make edits
        Otherwise, don't touch that part
    If the BR number doesn't exist, raise an error. All BR numbers should originate in the parts sheet
    If there is no BR ID field for a part, generate a new BR ID and fill out sheet accordingly using the Kicad symbol fields
            "ID":BR_ID, "Name":symbol.libId, "Description":properties["Description"], "Value":properties["Value"], "Symbol":symbol_path, "Footprint":properties["Footprint"],  "Datasheet":properties["Datasheet"], "Manufacturer":manufacturer, "MPN":mpn, "Category":category
    At the end, create a new row in the vendor sheet

Functions to add:
check_for_duplicate_BRID()
check_for_changes()
update_part_in_sheet()
add_BRID_to_kicad_part()
add_part_to_vendor_sheet()
            
"""
# Not really necessary, but initializes the dataframes. This is at good reference for the columns, at least
parts_df = pd.DataFrame(columns=['BR ID','Name','Description','Value','Symbol','Footprint','Datasheet','Manufacturer','MPN', 'Category'])
vendors_df = pd.DataFrame(columns=['BR ID','Supplier','SPN','Stock'])

ID_list = []
parts_list = []
vendors_list = []

# Reading symbol libraries from our BR symbols folder
SYMBOLS_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols"
JLC_PATH = r"C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/jlc-scraper/csv/Parts Inventory on JLCPCB.xlsx"
PARTS_SHEET_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/Kicad/Parts_Library.xlsx"

parts_sheet = pd.read_excel(PARTS_SHEET_PATH, index_col=[0])

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

        # Remove a weird decoding error with the plus/minus sign
        bad_char = b'\xc3\x82'.decode()
        properties["Description"] = properties["Description"].replace(bad_char, '')

        # Some parts don't have a manufacturer and manufacturer part number -- deal with this some other time, for now just populate "None"
        if "Manufacturer" in properties:
            manufacturer = properties["Manufacturer"]
            mpn = properties["Manufacturer Part Num"]
        else:
            manufacturer = "None"
            mpn = "None"

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

    symbol_lib.to_file()

# Create Pandas dataframes from these lists of dictionaries
# Think of each dictionary as a row in the table
parts_df = pd.DataFrame(parts_list)
vendors_df = pd.DataFrame(vendors_list)
