import kiutils.symbol
import re
import chardet

lib_path = r"C:/Users/JacobBrotmanKrass/Documents/Test Library/Symbols/BR_Capacitors_0201_.kicad_sym"


sym_lib = kiutils.symbol.SymbolLib().from_file(lib_path)


for symbol in sym_lib.symbols:
    properties = {property.key: property.value for property in symbol.properties}
    print(symbol.libId)
    # print(properties)

    
    print(properties["BR ID"])















