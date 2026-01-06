{
    "name": "Custom Import",
    "version": "1.0",
    "category": "Stock",
    "summary": """Custom Import for Sale Order""",
    "description": """This module allows for custom import functionality for sale orders""",
    "author": "Laxmi Tamang",
    "website": "https://www.smarten.com.np",
    "depends": ["sale_management"],
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/sale_order.xml",
        "views/purchase_order.xml",
    ],
    "installable": True,
    "auto_install": False,
}
