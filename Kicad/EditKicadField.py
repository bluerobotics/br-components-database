import kiutils.symbol
import os
import glob
import pandas as pd
import xmlrpc.client

# Reading symbol libraries from our BR symbols folder
SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols" # TEST LIBRARY
scripts_path = os.path.dirname(os.path.abspath(__file__))
#SYMBOLS_PATH = os.path.join(scripts_path, os.pardir, "Symbols")

def edit_kicad_field(symbol_lib, field, new_value, current_value='any'):
    """
    Load in Kicad libraries as a pandas Dataframe. This format greatly enhances the ability to compare, analyze, and update parts to another database (Odoo, for instance).
    Also pulls in vendor information from parts.

    Parameters
    ----------
    symbol_lib (kiutils.) : The path to the Kicad symbol libraries

    Returns
    -------
    parts_df (pd.DataFrame) : DataFrame containing all of the parts with the following columns:
                              ["BRE Number", "Name", "Description", "Value", "Symbol", "Footprint",  "Datasheet", "Manufacturer", "MPN", "Library"]
    vendords_df (pd.DataFrame) : DataFrame containing all supplier information and respective BRE numbers, containing the columns:
                                 ["BRE Number", "Supplier", "SPN", "Stock"]
    """

    # For each symbol in a given library, populate a new row in the Parts dataframe
    for symbol in symbol_lib.symbols:

        for property in symbol.properties:
            if property.key == field:
                print(f"Looking to change field {field} for {symbol.libId}")
                if current_value == 'any':
                    property.value = new_value
                elif property.value == current_value:
                    property.value = new_value
                else:
                    print(f"Current value {property.value} does not match {current_value}")

        # Grab all the properties from the Kicad Symbol
        properties = {property.key: property.value for property in symbol.properties}
        print(properties[field])

        hide_attributes(symbol)

    symbol_lib.to_file(encoding='utf-8')

    print("Kicad libraries edited successfully.")

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


#########################################################################################################################################

os.chdir(SYMBOLS_PATH)

# SPECIFY WHICH FILES TO EDIT IN THE GLOB

for lib_file in glob.glob("BR_Resistors_0402.kicad_sym"):

    edit_kicad_field(lib_file, field="Footprint", new_value="BR_Passives:C_0402_1005Metric-minimized", old_value="BR_Passives:R_0402_1005Metric")