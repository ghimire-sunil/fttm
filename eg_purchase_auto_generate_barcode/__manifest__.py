{
    'name': 'Purchase Auto Generate Barcode',
    'version': '18.0',
    'category': 'Products',
    'summary': 'Automatically generates barcode for products and product variants in purchase orders.automatically generates barcode, barcode generation, barcode, auto generate barcode, purchase barcode generate',
    'description': """
        This module automatically generates barcode numbers for products and product variants 
        in purchase orders, making it easier to manage product identification and tracking in Odoo.
        
        Key Features:
        - Automatic Barcode Generation for Products
        - Display Barcode in Purchase Order and Product Form
        - Barcode Generation for Product Variants
        - Easy Integration with Odoo Purchase and Inventory Management
    """,
    'author': 'Smarten Technologies Pvt. Ltd.',
    'website': "https://www.smarten.com.np",
    'depends': ['purchase'],
    'data': [
        'views/product_barcode_sequence.xml',
        'views/product_template_view.xml',
        'views/product_product_view.xml',
    ],
    'license': "OPL-1",
    'installable': True,
    'application': True,
    'auto_install': False,
}
