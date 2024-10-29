import kiutils.symbol, kiutils.items
import random
import os
import glob
import pandas as pd

#### Function for generating a unique BRE Number ####
def generate_BRE(existing_BREs):

    # Set number of digits in unique BRE
    num_digits = 6      

    # Increment by 1 until the BRE doesn't exist
    for n in range(10**num_digits):

        # Convert to a zero padded string (to fill the desired number of digits -- e.g, 1 --> '0001')
        BR_num = str(n).zfill(num_digits)
        BRE = 'BRE-' + BR_num

        # If the new BRE isn't currently used, we've found the one!
        if BRE not in existing_BREs:
            break

    return BRE

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
    new_field = kiutils.symbol.Property(key=field_name, value=field_value, effects=kiutils.items.common.Effects(font=kiutils.items.common.Font(face=None, height=1.27, width=1.27, thickness=None, bold=False, italic=False, lineSpacing=None, color=None), justify=kiutils.items.common.Justify(horizontally=None, vertically=None, mirror=False), hide=True, href=None), showName=False)

    # Add the new field to the symbol's properties
    symbol.properties.append(new_field)

    # Save the modified symbol back to the file
    print(f'Field "{field_name}" with value "{field_value}" added to symbol "{symbol_name}".')

def hide_attributes(symbol):

    for prop in symbol.properties:
        if prop.key != "Reference" and prop.key != "Value":
            prop.effects.hide = True

def sort_symbol_fields(symbol):
    """
    Function to sort Kicad fields in a standard order, while not deleting any other fields (such as supplier info)

    Parameters
    ----------
    symbol (kiutils symbol) : A symbol containing all of the 
    """
    
    # This is the default order
    main_fields = ['Reference', 'Value', 'Footprint', 'Datasheet', 'Manufacturer', 'Manufacturer Part Num', 'BRE Number']
    
    main_properties = []
    for field in main_fields:
        for prop in symbol.properties:
            if prop.key == field:
                main_properties.append(prop)

    if len(main_properties) < len(main_fields):
        print(main_properties)
        raise ValueError(f'Symbol "{symbol.libId}" does not contain all of the required fields: {main_fields}.')
    
    other_properties = [prop for prop in symbol.properties if prop.key not in main_fields]

    symbol.properties = main_properties + other_properties




# Not really necessary, but initializes the dataframes. This is at good reference for the columns, at least
parts_df = pd.DataFrame(columns=['BRE Number','Name','Description','Value','Symbol','Footprint','Datasheet','Manufacturer','MPN', 'Library'])
vendors_df = pd.DataFrame(columns=['BRE Number','Supplier','SPN','Stock'])

BRE_list = []
MPN_list = [] 

parts_list = []
vendors_list = []

# Ignore any thing that looks like this
null_strings = ["", " ", "-", "--", "~", "NA", "N/A"]

# Reading symbol libraries from our BR symbols folder
# SYMBOLS_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols"
# JLC_PATH = r"C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/jlc-scraper/csv/Parts Inventory on JLCPCB.xlsx"
# OUTPUT_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-components-database/Kicad"
SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"
OUTPUT_PATH = "C:/Users/JacobBrotmanKrass/Documents"
os.chdir(SYMBOLS_PATH)
for lib_file in glob.glob("*.kicad_sym"):

    # Extract library nickname/library -- e.g., 0402_Capacitors
    lib_nickname = lib_file.replace(".kicad_sym", "")

    # Skip these libraries, they don't need to be documented (obsolete or not actual parts)
    if (lib_nickname == "BR~Deprecated") or (lib_nickname == "BR_Virtual_Parts"):
        continue
    print(lib_nickname)

    # Open symbol library
    lib_path = os.path.join(SYMBOLS_PATH, lib_file)
    symbol_lib = kiutils.symbol.SymbolLib().from_file(lib_path)
    
    # The library is the library nickname, without the BR_ at the beginning
    library = lib_nickname[3:]

    # For each symbol in a given library, populate a new row in the Parts dataframe
    for symbol in symbol_lib.symbols:

        # Symbol path in Kicad
        symbol_path = f"{lib_nickname}:{symbol.entryName}"



        # Grab all the properties from the Kicad Symbol
        properties = {property.key.strip(): property.value.strip() for property in symbol.properties}

        # Some parts don't have a manufacturer and manufacturer part number -- deal with this some other time, for now just populate "None"
        if "Manufacturer" in properties:
            manufacturer = properties["Manufacturer"]
            mpn = properties["Manufacturer Part Num"]

            if mpn not in MPN_list:     # If MPN is new, generate a unique BRE Number --- Only necessary for this first commit of Kicad parts into our BR "database"
                BRE = generate_BRE(BRE_list)
                BRE_list.append(BRE)
                if mpn not in null_strings: MPN_list.append(mpn)
            else:                       # If the MPN has already been accounted for, these are the same part and should be given the same BR ID
                for part in parts_list:
                    if part["MPN"] == mpn:
                        BRE = part["BRE Number"]
        else:
            manufacturer = ""
            mpn = ""
            add_field_to_symbol(symbol_lib, symbol.libId, "Manufacturer", "")
            add_field_to_symbol(symbol_lib, symbol.libId, "Manufacturer Part Num", "")
            BRE = generate_BRE(BRE_list)
            BRE_list.append(BRE)
            print(f"Added empty manufacturing fields to {symbol.libId}")


        # Append a dictionary of all part properties to the parts list -- this will be converted to a Pandas dataframe at the end
        parts_list.append({"BRE Number":BRE, "Name":symbol.libId, "Description":properties["Description"], "Value":properties["Value"], "Symbol":symbol_path, "Footprint":properties["Footprint"],  "Datasheet":properties["Datasheet"], "Manufacturer":manufacturer, "MPN":mpn, "Library":library})

        # Add BRE Number to the symbol
        add_field_to_symbol(symbol_lib, symbol.libId, "BRE Number", BRE)
        sort_symbol_fields(symbol)
        hide_attributes(symbol)

        # Extract all supplier-related properties: supplier X with suppler number X
        supplier_properties = {property: properties[property] for property in properties if property[:8]=="Supplier"}
        supplier_numbers = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]=='P'}
        supplier_names = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]!='P'}

        # Loop through and add vendors and the respective supplier number when the number X at the end matches (supplier 1 --> supplier part num 1)
        for name in supplier_names:
            for number in supplier_numbers:
                if name[-1] == number[-1]:
                    if supplier_numbers[number] not in null_strings:

                        # Append dictionary of supplier properties for each SPN to the vendors list
                        # this will be converted to Pandas dataframe at the end
                        vendors_list.append({"BRE Number":BRE, "Supplier":supplier_names[name], "SPN":supplier_numbers[number]})

    symbol_lib.to_file(encoding='utf-8')

# Create Pandas dataframes from these lists of dictionaries
# Think of each dictionary as a row in the table
parts_df = pd.DataFrame(parts_list)
vendors_df = pd.DataFrame(vendors_list)

odoo_parts = parts_df[["BRE Number", "Description", "Datasheet", "Manufacturer", "MPN", "Library"]]


""" SEND TO ODOO INSTEAD """
# Save dataframes to excel files
vendors_df.to_excel(os.path.join(OUTPUT_PATH, "Test_Vendor_Stock.xlsx"))
parts_df.to_excel(os.path.join(OUTPUT_PATH, "Test_Parts_Library.xlsx"))    
odoo_parts.to_excel(os.path.join(OUTPUT_PATH, "Test_Odoo_Parts.xlsx")) 