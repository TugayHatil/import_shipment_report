# -*- coding: utf-8 -*-
{
    'name': 'Import Qty - Stock Information',
    'version': '15.0.1.0.0',
    'category': 'Purchase',
    'summary': 'Add stock quantity column to import shipment list',
    'description': """
        This addon adds a stock quantity column to the import shipment list view.
        It shows the current stock quantity from the product card.
    """,
    'author': 'Tugay Hatil',
    'website': 'https://github.com/TugayHatil',
    'depends': ['import_shipment_v15', 'stock'],
    'data': [
        'views/import_shipment_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
