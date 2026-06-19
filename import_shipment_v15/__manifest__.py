{
    'name': 'Import Shipment Management (v15)',
    'version': '15.0.1.0.0',
    'summary': 'Manage import shipments, consolidation, and partial receipts (v15 compatible).',
    'description': """
        This module allows managing import shipments by:
        - Preventing automatic picking creation for import vendors.
        - Collecting PO lines into import shipment lines.
        - Updating quantities via Excel.
        - Creating consolidated incoming pickings.
        - Integrating with MRP for properly calculating planned supply.
        - Custom field: Manufacturer Code on product template.
    """,
    'category': 'Inventory/Purchase',
    'author': 'Antigravity',
    'depends': ['purchase', 'stock', 'mrp', 'purchase_stock', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/import_shipment_excel_wizard_views.xml',
        'views/import_shipment_views.xml',
        'views/stock_picking_type_views.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
