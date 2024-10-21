import kiutils.symbol
import re

lib_path = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols/BR_Capacitors_0201.kicad_sym"
lib_obj = kiutils.symbol.SymbolLib()
sym_lib = lib_obj.from_file(lib_path)

symbols = sym_lib.symbols

for symbol in symbols:
    properties = {property.key: property.value for property in symbol.properties}
    print(symbol.libId)
    supplier_properties = {property: properties[property] for property in properties if property[:8]=="Supplier"}
    supplier_number = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]=='P'}
    supplier_names = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]!='P'}
    print(supplier_names, supplier_number)

    for name in supplier_names:
        for number in supplier_number:
            if name[-1] == number[-1]:
                print(name, number)






