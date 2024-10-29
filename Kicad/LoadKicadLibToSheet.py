import kiutils.symbol, kiutils.items
import os
import glob
import pandas as pd

# SET TO YOUR DESIRED PATHS ################################################################################
SYMBOLS_PATH = r"C:\Users\emill\Documents\GitHub\br-kicad-lib\Symbols"
OUTPUT_PATH = r"C:\Users\emill\Documents\GitHub\br-kicad-lib\Symbols"

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


parts_list = []

# Ignore any thing that looks like this
null_strings = ["", " ", "-", "--", "~", "NA", "N/A"]


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

        #sort_symbol_fields(symbol)
        #hide_attributes(symbol)

        # Grab all the properties from the Kicad Symbol
        properties = {property.key.strip(): property.value.strip() for property in symbol.properties}

        # Append a dictionary of all part properties to the parts list -- this will be converted to a Pandas dataframe at the end
        parts_list.append(properties)

# Create Pandas dataframes from these lists of dictionaries
# Think of each dictionary as a row in the table
parts_df = pd.DataFrame(parts_list)

# Save dataframes to excel files
parts_df.to_excel(os.path.join(OUTPUT_PATH, "Test_Parts_Library.xlsx"))    
