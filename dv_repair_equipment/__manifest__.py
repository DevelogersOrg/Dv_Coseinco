# -*- coding: utf-8 -*-
{
    "name" : "Reparaciones - Coseinco SA",
    "version" : "14.0.1.0",
    "category" : "",
    "depends" : ['purchase', 'stock', 'repair', 'sale_management', 'crm', 'account'],
    "author": "develogers",
    'summary': '',
    "website" : "https://www.develogers.com",
    "data": [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/repair_order_type_views.xml',
        'views/purchase_order_views.xml',
        'views/crm_lead_views.xml',
        'views/stock_inventory_views.xml',
        'views/stock_picking_views.xml',
        'views/account_move_views.xml',
        'views/menu_items.xml',
    ],
    'demo': [
        'data/repair_order_type.xml',
    ],
    "auto_install": False,
    "installable": True,
    "images":[],
}
