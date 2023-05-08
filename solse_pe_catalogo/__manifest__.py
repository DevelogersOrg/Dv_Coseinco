# -*- coding: utf-8 -*-
{
	'name': "Catalogo SUNAT ",

	'summary': """
		Catalogo SUNAT""",

	'description': """
		Catalogo SUNAT
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'account',
	'version': '0.1',

	'depends': [
		'base',
		'l10n_pe',
	],
	'data': [
		'security/pe_datas_security.xml',
		'security/ir.model.access.csv',
		'data/pe_datas.xml',
		'data/pe.datas.csv',
		'views/pe_datas_view.xml',
	],
	'qweb': [],
	'installable': True,
}