{
    'name': 'Partner, Sale & Delivery Customizations',
    'version': '18.0.0.1',
    'summary': 'Enhancements in Partner, Sale Order, Delivery, MRP and PO modules',
    'description': """
        Developed by Krina Solanki.

        - Partner searchable by Ref
        - Ref in partner Many2one display
        - Tag sync from SO to DO
        - Tag visibility & search in DO
        - Lock MO qty after confirm
        - Split PO by category
        - Auto email on delivery
        - Unique category name
        - Char field copy-to-clipboard widget
        - Change default search filter
    """,
    'depends': ['base', 'sale_management', 'stock', 'mrp', 'purchase', 'sale'],
    'data': [
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/mail_template.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
