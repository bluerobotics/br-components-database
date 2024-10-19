import kiutils.symbol

lib_path = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols/BR_Capacitors_0201.kicad_sym"
lib_obj = kiutils.symbol.SymbolLib()
sym_lib = lib_obj.from_file(lib_path)

symbols = sym_lib.symbols

for symbol in symbols:
    properties = {property.key: property.value for property in symbol.properties}
    print(properties)






