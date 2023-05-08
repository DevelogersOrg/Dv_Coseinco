# -*- coding: utf-8 -*-
{
	'name': "CPE Ventas",

	'summary': """
		Enlace del modulo de ventas con la creacion de facturas electronicas""",

	'description': """
		Facturación electrónica - Perú 
		Permite ingresar datos requeridos en la facturacion electronica desde el formulario de orden de venta.
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '1.0',

	'depends': [
		'solse_pe_edi',
		'solse_pe_cpe',
		'sale_management',
	],
	'data': [
		'views/sale_order_view.xml',
		'views/account_move_view.xml',
		'report/report_invoice.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}