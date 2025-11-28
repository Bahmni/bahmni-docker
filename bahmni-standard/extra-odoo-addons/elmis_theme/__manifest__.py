# -*- coding: utf-8 -*-
{
    'name': 'eLMIS Theme Branding',
    'version': '16.0.1.0.0',
    'summary': 'Replace Odoo logos and apply eLMIS theme',
    'description': 'Brand Odoo backend: change logo, favicon, colors, and topbar theme.',
    'depends': ['web'],
    'data': [
    ],
    'assets': {
        'web.assets_backend': [
            'elmis_theme/static/src/css/custom_backend.css',
        ],
        'web.assets_frontend': [
            'elmis_theme/static/src/css/custom_frontend.css',
        ],
    },
    'installable': True,
}
