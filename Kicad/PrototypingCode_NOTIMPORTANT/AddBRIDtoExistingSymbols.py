import kiutils.symbol
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
    new_field = kiutils.symbol.Property(key=field_name, value=field_value, id=field_id)

    # Add the new field to the symbol's properties
    symbol.properties.append(new_field)

    # Save the modified symbol back to the file
    print(f'Field "{field_name}" with value "{field_value}" added to symbol "{symbol_name}".')


parts_df = pd.DataFrame(columns=['ID','Name','Description','Value','Symbol','Footprint','Datasheet','Manufacturer','MPN', 'Category'])
vendors_df = pd.DataFrame(columns=['ID','Supplier','SPN','Stock'])

ID_list = []
parts_list = []
vendors_list = []

# Reading symbol libraries from our BR symbols folder
SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"
os.chdir(SYMBOLS_PATH)
for lib_file in glob.glob("*.kicad_sym"):

    lib_nickname = lib_file.replace(".kicad_sym", "")
    if lib_nickname == "BR~Deprecated":
        continue
    print(lib_nickname)
    lib_path = os.path.join(SYMBOLS_PATH, lib_file)
    symbol_lib = kiutils.symbol.SymbolLib().from_file(lib_path)
    #symbol_lib.read(lib_path)
    # The Category is the library nickname, without the BR_ at the beginning
    category = lib_nickname[3:]



    # For each symbol in a given library, populate a new row in the Parts table of the database
    for symbol in symbol_lib.symbols:
        symbol_path = f"{lib_nickname}:{symbol.entryName}"
        BR_ID = generate_BRID(ID_list)
        ID_list.append(BR_ID)
        properties = {property.key: property.value for property in symbol.properties}
        bad_char = b'\xc3\x82'.decode()
        print(properties)
        properties["Description"] = properties["Description"].replace(bad_char, '')
        if "Manufacturer" in properties:
            manufacturer = properties["Manufacturer"]
            mpn = properties["Manufacturer Part Num"]
        else:
            manufacturer = "None"
            mpn = "None"

        parts_list.append({"BR ID":BR_ID, "Name":symbol.libId, "Description":properties["Description"], "Value":properties["Value"], "Symbol":symbol_path, "Footprint":properties["Footprint"],  "Datasheet":properties["Datasheet"], "Manufacturer":manufacturer, "MPN":mpn, "Category":category})
        add_field_to_symbol(symbol_lib, symbol.libId, "BR ID", BR_ID)

    symbol_lib.to_file()



parts_df = pd.DataFrame(parts_list)
                
