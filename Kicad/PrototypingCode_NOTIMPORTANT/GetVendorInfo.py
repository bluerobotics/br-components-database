
import xmlrpc.client

# Odoo connection details
url = "https://dev2-v17.apps.bluerobotics.com/"
db = "20241009_v2"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

def getVendorInfo(bre_number):

    # Search for the supplier ID in res.partner (returns a list of matches, should just be the first one)
    JLC_supplier_id = models.execute_kw(db, uid, password, 'res.partner', 'search', [[['name', 'ilike', "JLCPCB"]]])
    print(JLC_supplier_id)

    # Search for the product by BRE number to get its product ID
    product_id = models.execute_kw(db, uid, password, 'product.product', 'search', [[['default_code', 'ilike', f"{bre_number}%"]]])
    print(product_id)
    # Search for the corresponding supplier info IDs for the given prodcut
    supplierinfo_ids = models.execute_kw(db, uid, password, 'product.supplierinfo', 'search', [[['product_id', '=', product_id]]])

    # Step 2: If supplierinfo_ids is not empty, read the records and obtain 
    print(supplierinfo_ids)


    supplier_info = models.execute_kw(db, uid, password, 'product.supplierinfo', 'read', [supplierinfo_ids], {'fields': ['partner_id', 'product_code', 'jlcpcb_inventory', 'global_sourcing_inventory', 'consigned_inventory']}) 
    JLC_info = {'partner_id':'', 'product_code':'', 'jlcpcb_inventory':0, 'global_sourcing_inventory':0, 'consigned_inventory':0}

    for supplier in supplier_info:
        print("AGH", supplier)
        if supplier['partner_id'][1]=="JLCPCB":
            JLC_info = supplier

    return JLC_info

all_suppliers = models.execute_kw(
    db, uid, password, 'product.supplierinfo', 'search_read',
    [[]],  # Empty domain to fetch all records
    {'fields': ['id', 'product_id', 'partner_id', 'min_qty', 'price']}
)
for supplier in all_suppliers:
    #if supplier['partner_id'][1] == 'JLCPCB':
    print(f"All Supplier Info: {supplier}")