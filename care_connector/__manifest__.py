{
    "name": "Care Connector",
    "summary": "Integration with OHC software",
    "version": "0.0.1",
    "category": "Uncategorized",
    "installable": True,
    "depends": ["base","stock","web","contacts","account"],
    'external_dependencies': {
            'python': ['pydantic'],
        },
    "data": [
        "views/account_move_views.xml",
        "views/product_template_views.xml",
        "views/res_partner_views.xml",
    ],
}