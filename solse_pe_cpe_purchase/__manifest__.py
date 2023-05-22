# -*- coding: utf-8 -*-
{
	'name': "CPE Compras",

	'summary': """
		Enlace del modulo de compras con la creacion de facturas electronicas""",

	'description': """
		Facturación electrónica - Perú 
		Agrega un tipo de documento por defecto al momento de crear la factura desde compra, el 
		tipo de documento es filtrado segun la configuracion realizada con el modulo solse_pe_edi
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '1.1',

	'depends': [
		'account',
		'solse_pe_cpe',
	],
	'data': [],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}