from xmlrpc import client
import xmlrpc.client
import csv
import os

url = "https://dev17.apps.bluerobotics.com/"
db = "20240809"
username = "engineering@bluerobotics.com"
password = "VqqpHGVZCh3yfj7"

# Establishing connection
common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
uid = common.authenticate(db, username, password, {})

# Accessing models
models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

jlcpcb_warehouse = env['stock.warehouse'].search([('name', '=', 'JLCPCB')])

if jlcpcb_warehouse:
    # Unlink delivery and reception routes if set
    jlcpcb_warehouse.write({
        'reception_route_id': False,
        'delivery_route_id': False
    })
    print("Routes have been unlinked from the JLCPCB warehouse.")
else:
    print("JLCPCB warehouse not found.")