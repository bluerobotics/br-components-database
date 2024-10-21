import psycopg2
import kiutils.symbol
import random
import os
import glob

#### Function for generating a unique BR ID ####
def generate_BRID(cursor):

    # Set number of digits in unique BRID
    num_digits = 4      
    
    # Gather all existing BRID's from the databasde
    cursor.execute('SELECT "ID" FROM public."Parts";')
    existing_BRIDs = [row[0] for row in cursor.fetchall()]

    # Increment by 1 until the BRID doesn't exist
    for n in range(10**num_digits):

        # Convert to a zero padded string (to fill the desired number of digits -- e.g, 1 --> '0001')
        BR_num = str(n).zfill(num_digits)
        BRID = 'BREE' + BR_num

        # If the new BRID isn't currently used, we've found the one!
        if BRID not in existing_BRIDs:
            break

    return BRID

# Connect to the database
conn = psycopg2.connect(database = "pi",
                        user = "pi",
                        host = "192.168.1.100",
                        password = "BlueBoat2020",
                        port = 5432)

# Initialize a cursor to navigate and edit the database
cursor = conn.cursor()
# Grab the column names of the Parts table
cursor.execute('Select * FROM public."Parts" LIMIT 0')
part_cols =  [desc[0] for desc in cursor.description]
# Create a tuple of lists representing each row in the Parts table
cursor.execute('SELECT * FROM public."Parts";')
parts_table = cursor.fetchall()

# Create a dictionary for each part (useful for pulling stuff out of database, not used here)
for part in parts_table:
    part_dict = {part_cols[idx]: value for idx, value in enumerate(part)}

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

    # If this category is not yet in the Categories table, add it
    cursor.execute('SELECT * FROM public."Categories";')
    categories_db = [row[0] for row in cursor.fetchall()]
    print(category)
    if category not in categories_db:
        cursor.execute('INSERT INTO public."Categories"("Category") VALUES(%s)', (category,))

    # For each symbol in a given library, populate a new row in the Parts table of the database
    cursor.execute('SELECT * FROM public."Parts";')
    for symbol in sym_lib.symbols:
        symbol_path = f"{lib_nickname}:{symbol.entryName}"
        BR_ID = generate_BRID(cursor)
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

        cursor.execute('SELECT * FROM public."Parts";')
        cursor.execute('INSERT INTO public."Parts"("ID", "Name", "Description", "Value", "Symbol", "Footprint",  "Datasheet", "Manufacturer", "MPN", "Category") VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (BR_ID, symbol.libId, properties["Description"], properties["Value"], symbol_path, properties["Footprint"], properties["Datasheet"], manufacturer, mpn, category))
        
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
                




conn.commit()
conn.close()
