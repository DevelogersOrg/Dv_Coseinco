# -*- coding: utf-8 -*-
{
	'name': "Web Publica CPE",

	'summary': """
		Web publica para consultar los comprobantes""",

	'description': """
		Facturación electrónica - Perú 
		Web publica para consultar los comprobantes
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'category': 'Website',
	'version': '14.0.0.2',

	'depends': [
		'website',
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/busqueda_cpe_template.xml',
	],
	'installable': True,
	'price': 15,
	'currency': 'USD',
}