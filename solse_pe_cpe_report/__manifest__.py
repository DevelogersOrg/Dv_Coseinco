# -*- coding: utf-8 -*-
{
	'name': "CPE Reportes",

	'summary': """
		Reporte de los comprobantes electrónicos""",

	'description': """
		Facturación electrónica - Perú 
		Reporte de los comprobantes electrónicos
	""",

	'author': "F & M Solutions Service S.A.C",
	'website': "https://www.solse.pe",
	'category': 'Financial',
	'version': '1.3',

	'depends': [
		'solse_pe_edi',
		'solse_pe_cpe',
	],
	'data': [
		'security/ir.model.access.csv',
		'views/pe_cpe_report_view.xml',
		'views/pe_cpe_descargar_view.xml',
		'wizard/pe_cpe_report_wizard_view.xml',
		'data/tareas_programadas.xml',
		'data/mail_template.xml',
	],
	'installable': True,
	'price': 60,
	'currency': 'USD',
}