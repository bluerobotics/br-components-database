import kiutils.symbol, kiutils.items
import random
import os
import glob
import pandas as pd


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

SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"

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

        
        for property in symbol.properties:

            if property.key[:5] == "BR ID" or property.key[:10] == "BRE Number":
                symbol.properties.remove(property)

        hide_attributes(symbol)

    symbol_lib.to_file(encoding='utf-8')

