import kiutils.symbol
import re

lib_path = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols/BR_Capacitors_0201.kicad_sym"
sym_lib = kiutils.symbol.SymbolLib().from_file(lib_path)


for symbol in sym_lib.symbols:
    properties = {property.key: property.value for property in symbol.properties}
    print(symbol.libId)
    # print(properties)
    for prop in symbol.properties:
        if prop.key != "Reference"print(prop.key)













