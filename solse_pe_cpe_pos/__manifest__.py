# -*- coding: utf-8 -*-
{
	'name': "CPE desde POS",

	'summary': """
		Facturación electronica desde POS""",

	'description': """
		Facturación electronica desde POS
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'category': 'Operations',
	'version': '14.0.0.3',

	'depends': [
		'solse_pe_edi',
		'solse_pe_cpe',
		'point_of_sale',
		'sale_management',
		'pos_sale',
	],
	'data': [
		'security/ir.model.access.csv',
		'security/solse_pos_security.xml',
		'wizard/pos_recover_wizard_view.xml',
		'wizard/sale_make_order_advance_view.xml',
		'views/assets.xml',
		'views/pos_config_view.xml',
		'views/pos_order_view.xml',
		'views/pos_session_view.xml',
		'views/sale_order_view.xml',
	],
	'qweb': [
		'static/src/xml/pos.xml',
		'static/src/xml/point_of_sale.xml',
	],
	'installable': True,
	'price': 150,
	'currency': 'USD',
}