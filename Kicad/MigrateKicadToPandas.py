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

parts_df = pd.DataFrame(columns=['ID','Name','Description','Value','Symbol','Footprint','Datasheet','Manufacturer','MPN', 'Category'])

parts_list = []
# Reading symbol libraries from our BR symbols folder
SYMBOLS_PATH = "C:/Users/JacobBrotmanKrass/Documents/GitHub/br-kicad-lib/Symbols"
os.chdir(SYMBOLS_PATH)
for lib_file in glob.glob("*.kicad_sym"):

    lib_nickname = lib_file.replace(".kicad_sym", "")
    if lib_nickname == "BR~Deprecated":
        continue
    print(lib_nickname)
    lib_path = os.path.join(SYMBOLS_PATH, lib_file)
    lib_obj = kiutils.symbol.SymbolLib()
    sym_lib = lib_obj.from_file(lib_path)
    # The Category is the library nickname, without the BR_ at the beginning
    category = lib_nickname[3:]



    # For each symbol in a given library, populate a new row in the Parts table of the database
    for symbol in sym_lib.symbols:
        symbol_path = f"{lib_nickname}:{symbol.entryName}"
        BR_ID = generate_BRID(parts_df.BR_ID)
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

        parts_list.append({"ID":BR_ID, "Name":symbol.libId, "Description":properties["Description"], "Value":properties["Value"], "Symbol":symbol_path, "Footprint":properties["Footprint"],  "Datasheet":properties["Datasheet"], "Manufacturer":manufacturer, "MPN":mpn, "Category":category})

        print(properties["Description"])

        supplier_properties = {property: properties[property] for property in properties if property[:8]=="Supplier"}
        supplier_numbers = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]=='P'}
        supplier_names = {supp_prop: supplier_properties[supp_prop] for supp_prop in supplier_properties if supp_prop[9]!='P'}
        print(supplier_names, supplier_numbers)

        null_strings = ["", " ", "-", "--", "~", "NA", "N/A"]
        for name in supplier_names:
            for number in supplier_numbers:
                if name[-1] == number[-1]:
                    if supplier_numbers[number] not in null_strings:
                        cursor.execute('SELECT * FROM public."Vendors";')
                        cursor.execute('INSERT INTO public."Vendors"("ID", "Supplier", "SPN", "Stock") VALUES(%s, %s, %s, %s)', (BR_ID, supplier_names[name], supplier_numbers[number], 0))


parts_df = pd.DataFrame(parts_list)
                

