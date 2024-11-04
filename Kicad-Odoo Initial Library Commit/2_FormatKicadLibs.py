from kiutils.items.common import Position, Justify
import kiutils.symbol
import os
import glob

SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"
current_path = os.path.dirname(os.path.abspath(__file__))
#SYMBOLS_PATH = os.path.join(current_path, os.pardir, os.pardir, "br-kicad-lib", "Symbols")

def format_symbol(symbol, library):
    
    if 'Capacitor' in library:
        y = to_mm(3000)
        for property in symbol.properties:
            if property.key == "Reference":
                property.position = Position(X=to_mm(40), Y=to_mm(70), angle=0)
                property.effects.justify = Justify(horizontally = "left")
            elif property.key == "Value":
                property.position = Position(X=to_mm(40), Y=to_mm(-70), angle=0)  
                property.effects.justify = Justify(horizontally="left")
            else:
                property.position = Position(X=to_mm(0), Y=y, angle=0)  
                property.effects.justify = Justify(horizontally="left")
                y -= to_mm(100)  

    elif 'Resistor' in library:
        y = to_mm(3000)
        for property in symbol.properties:
            if property.key == "Reference":
                property.position = Position(X=to_mm(60), Y=to_mm(50), angle=0)
                property.effects.justify = Justify(horizontally = "left")

            elif property.key == "Value":
                property.position = Position(X=to_mm(60), Y=to_mm(-50), angle=0)  
                property.effects.justify = Justify(horizontally="left")
            else:
                property.position = Position(X=to_mm(0), Y=y, angle=0)  
                property.effects.justify = Justify(horizontally="left")
                y -= to_mm(100)

    else:
        y = to_mm(3000)
        for property in symbol.properties:
            if property.key == "Reference":
                pass
            elif property.key == "Value":
                pass
            else:
                property.position = Position(X=to_mm(0), Y=y, angle=0)  
                property.effects.justify = Justify(horizontally="left")
                y -= to_mm(100)                                            

def to_mm(mils):
    return mils * 0.0254

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
    new_field = kiutils.symbol.Property(key=field_name, value=field_value, effects=kiutils.items.common.Effects(font=kiutils.items.common.Font(face=None, height=1.27, width=1.27, thickness=None, bold=False, italic=False, lineSpacing=None, color=None), justify=Justify(horizontally='left', vertically=None, mirror=False), hide=True, href=None), showName=False)

    # Add the new field to the symbol's properties
    symbol.properties.append(new_field)

    # Save the modified symbol back to the file
    print(f'Field "{field_name}" with value "{field_value}" added to symbol "{symbol_name}".')

def hide_attributes(symbol, props_to_show=["Reference", "Value"]):

    for prop in symbol.properties:
        if prop.key not in props_to_show:
            prop.effects.hide = True
        else: prop.effects.hide = False

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


#########################################################################################################################################

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
        
        # Grab all the properties from the Kicad Symbol
        properties = {property.key.strip(): property.value.strip() for property in symbol.properties}

        format_symbol(symbol, library)
        sort_symbol_fields(symbol)
        hide_attributes(symbol)

    symbol_lib.to_file(encoding='utf-8')

