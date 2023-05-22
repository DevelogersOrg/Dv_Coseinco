# -*- coding: utf-8 -*-
{
	'name': "Facturacion desde Tienda web",

	'summary': """
		Facturacion desde Tienda web""",

	'description': """
		Facturación electrónica - Perú 
		Facturacion desde Tienda web
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'category': 'Website',
	'version': '0.9',

	'depends': [
		'website_sale',
		'solse_vat_pe',
	],
	'data': [
		'views/templates.xml',
	],
	'installable': True,
	'price': 40,
	'currency': 'USD',
}