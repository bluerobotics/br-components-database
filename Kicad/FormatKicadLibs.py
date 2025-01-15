from kiutils.items.common import Position, Justify
import kiutils.symbol
import os
import glob

def format_symbol(symbol, library):
    
    if 'Capacitor' in library:
        y = to_mm(3000)
        for property in symbol.properties:
            if property.key == "Reference":
                property.position = Position(X=to_mm(40), Y=to_mm(70), angle=0)
                property.effects.justify = Justify(horizontally = "left")
                print(property.effects.justify)
            elif property.key == "Value":
                property.position = Position(X=to_mm(40), Y=to_mm(-70), angle=0)  
                property.effects.justify = Justify(horizontally="left")
            else:
                property.position = Position(X=to_mm(0), Y=y, angle=0)  
                property.effects.justify = Justify(horizontally=None)
                y -= to_mm(100)  

    elif 'Resistor' in library:
        y = to_mm(3000)
        for property in symbol.properties:
            if property.key == "Reference":
                property.position = Position(X=to_mm(60), Y=to_mm(50), angle=0)
                property.effects.justify = Justify(horizontally = "left")
                print(property.effects.justify)
            elif property.key == "Value":
                property.position = Position(X=to_mm(60), Y=to_mm(-50), angle=0)  
                property.effects.justify = Justify(horizontally="left")
            else:
                property.position = Position(X=to_mm(0), Y=y, angle=0)  
                property.effects.justify = Justify(horizontally=None)
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
                property.effects.justify = Justify(horizontally=None)
                y -= to_mm(100)                                            

def to_mm(mils):
    return mils * 0.0254

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


SYMBOLS_PATH = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols"

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
        
        format_symbol(symbol, library)
        sort_symbol_fields(symbol)
        hide_attributes(symbol)

    symbol_lib.to_file(encoding='utf-8')

