{
    'name': 'BRE Tools',
    'version': '1.0',
    'category': 'Inventory',
    'summary': 'Custom tools for managing BRE Numbers',
    'depends': ['product', 'osi_br_purchase_ext'],
    'data': [
        'data/ir_sequence_data.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'auto_install': False,
}