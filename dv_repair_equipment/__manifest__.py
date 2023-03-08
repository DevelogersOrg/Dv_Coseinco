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
        'data/repair_order_type.xml',
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/res_users_views.xml',
        'views/sale_order_views.xml',
        'views/repair_order_type_views.xml',
        'views/purchase_order_views.xml',
        'views/crm_lead_views.xml',
        'views/stock_transfer_status_views.xml',
        'views/account_move_views.xml',
        'views/account_move_treasury_views.xml',
        'views/menu_items.xml',
        'templates/external_layout_standard.xml',
        'templates/quotation_report_layout.xml',
        'templates/technician_info_report.xml',
        'templates/ir_actions_report.xml',
    ],
    "auto_install": False,
    "installable": True,
    "images":[],
}
