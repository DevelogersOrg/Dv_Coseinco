# -*- coding: utf-8 -*-
# Copyright (c) 2019-2020 Juan Gabriel Fernandez More (kiyoshi.gf@gmail.com)
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
{
	'name': "Búsqueda RUC/DNI desde POS",

	'summary': """
		Obtener datos con RUC o DNI desde POS
		""",

	'description': """
		Obtener los datos por RUC o DNI desde POS
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "http://www.solse.pe",

	'category': 'Uncategorized',
	'version': '0.9',

	'depends': ['point_of_sale', 'sale_management', 'pos_sale', 'l10n_pe','solse_vat_pe'],

	'data': [
		'data/res_city_data.xml',
		'views/assets.xml',
	],
	'qweb': [
        'static/src/xml/pos.xml',
    ],
	'demo': [],
	'installable': True,
	'auto_install': False,
	'application': True,
	"sequence": 1,
}