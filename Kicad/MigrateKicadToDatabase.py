import psycopg2
import kiutils.symbol
import random
import os
import glob

#### Function for generating a unique BR ID ####
def generate_BRID(cursor):
    num_digits = 4
    BR_num = []
    cursor.execute('SELECT "ID" FROM public."Parts";')
    existing_BRIDs = [row[0] for row in cursor.fetchall()]
    while 1:
        BR_num = []
        for i in range(num_digits):
            BR_num.append(random.randint(0,9))
        BRID = 'BREE' + ''.join(map(str, BR_num))

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
    print(lib_file)

    lib_nickname = lib_file.replace(".kicad_sym", "")
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

        cursor.execute('SELECT * FROM public."Parts";')
        cursor.execute('INSERT INTO public."Parts"("ID", "Description", "Symbols", "Footprints", "Value", "Datasheet", "Category") VALUES(%s, %s, %s, %s, %s, %s, %s)', (BR_ID, properties["Description"], symbol_path, properties["Footprint"], properties["Value"], properties["Datasheet"], category))




conn.commit()
conn.close()
