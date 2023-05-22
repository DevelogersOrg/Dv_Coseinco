# -*- coding: utf-8 -*-

{
	'name': 'Tipo de cambio para Perú',
	'version': '14.0.1.0.0',
	'category': 'Extra Tools',
	'summary': 'Automatización de tipo de cambio para Perú',
	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",
	'depends': [
		'base',
		'l10n_pe_currency',
		'solse_vat_pe',
	],
	'data': [
		'data/ir_cron_data.xml',
		'views/account_move_view.xml',
		'views/res_currency_views.xml',
	],
	'installable': True,
	'sequence': 1,
}
