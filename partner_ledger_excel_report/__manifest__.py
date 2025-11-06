# -*- coding: utf-8 -*-
{
    'name': "Partner Ledger Excel Report",
    'summary': "Generate detailed partner ledger reports in Excel format",
    'description': "This module allows users to generate and export Partner Ledger reports directly into Excel format",
    'category': 'Website',
    'version': '0.1',
    'depends': ['base','account','base_accounting_kit'],
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_common_partner_report_views.xml',
        
    ],
    
}