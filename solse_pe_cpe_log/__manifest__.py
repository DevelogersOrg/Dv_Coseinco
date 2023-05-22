# -*- coding: utf-8 -*-
{
	'name': "Log CPE - Perú",

	'summary': """
		Manejo de errores para los cpe's SUNAT - Perú""",

	'description': """
		Manejo de errores para los cpe's SUNAT - Perú
		Manejo de errores para los cpe's SUNAT - Perú
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '1.1',

	'depends': [
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'data/tareas_programdas.xml',
		'views/solse_cpe_view.xml',
	],
	'installable': True,
	'price': 150,
	'currency': 'USD',
}