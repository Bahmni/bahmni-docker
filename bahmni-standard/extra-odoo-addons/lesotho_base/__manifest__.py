{
    "name": "Lesotho Base",
    "summary": "MOH Dispensing Customizations",
    "version": "16.0.1.0.0",
    "category": "Localization",
    "author": "MOH Lesotho",
    "website": "",
    "license": "LGPL-3",
    "depends": [
        "base",
        "contacts",
        "sale",
        "account",
        "stock",
    ],
    "data": [
        "views/view_overrides.xml",
        "views/product_template_views.xml",
        "views/stock_location_views.xml", 
        "views/login_template.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'lesotho_base/static/src/css/custom_backend.css',
        ],
        'web.assets_frontend': [
            'lesotho_base/static/src/css/custom_frontend.css',
        ],
    },
    "installable": True,
    "application": False,
}
