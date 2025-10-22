# -*- coding: utf-8 -*-
{
    'name': "cash_denomination",
    'summary': "Cash Denomination",
    'description': "Cash Denomination",
    'category': 'Website',
    'version': '0.1',
    'depends': ['base','account','website'],
    'data': [
        'security/ir.model.access.csv', 
        'views/cash_denomination_views.xml',
        'views/cash_counter_views.xml',
        'views/cash_transfer_views.xml',
        'views/cash_denomination_templates.xml',
    ],
    'assets': {
            'web.assets_frontend': [
                'cash_denomination/static/src/js/cash_denomination.js',
            ],
        },
}