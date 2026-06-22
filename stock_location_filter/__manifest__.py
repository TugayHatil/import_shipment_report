# -*- coding: utf-8 -*-
{
    'name': 'Stock Location Filter',
    'version': '15.0.1.0.0',
    'category': 'Stock',
    'summary': 'Filter stock locations for stock quantity calculation',
    'description': """
        This addon adds a boolean field to stock locations to filter which locations
        should be included in stock quantity calculations. Only internal locations
        with the filter checked will be counted.
    """,
    'author': 'Tugay Hatil',
    'website': 'https://github.com/TugayHatil',
    'depends': ['stock', 'import_qty'],
    'data': [
        'views/stock_location_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'license': 'LGPL-3',
}
