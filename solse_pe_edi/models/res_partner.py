# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.osv import expression

STATE = [('ACTIVO', 'ACTIVO'),
		 ('BAJA DE OFICIO', 'BAJA DE OFICIO'),
		 ('BAJA DEFINITIVA', 'BAJA DEFINITIVA'),
		 ('BAJA PROVISIONAL', 'BAJA PROVISIONAL'),
		 ('SUSPENSION TEMPORAL', 'BAJA PROVISIONAL'),
		 ('INHABILITADO-VENT.UN', 'INHABILITADO-VENT.UN'),
		 ('BAJA MULT.INSCR. Y O', 'BAJA MULT.INSCR. Y O'),
		 ('PENDIENTE DE INI. DE', 'PENDIENTE DE INI. DE'),
		 ('OTROS OBLIGADOS', 'OTROS OBLIGADOS'),
		 ('NUM. INTERNO IDENTIF', 'NUM. INTERNO IDENTIF'),
		 ('ANUL.PROVI.-ACTO ILI', 'ANUL.PROVI.-ACTO ILI'),
		 ('ANULACION - ACTO ILI', 'ANULACION - ACTO ILI'),
		 ('BAJA PROV. POR OFICI', 'BAJA PROV. POR OFICI'),
		 ('ANULACION - ERROR SU', 'ANULACION - ERROR SU')]

CONDITION = [('HABIDO', 'HABIDO'),
			 ('NO HABIDO', 'NO HABIDO'),
			 ('NO HALLADO', 'NO HALLADO'),
			 ('PENDIENTE', 'PENDIENTE'),
			 ('NO HALLADO SE MUDO D', 'NO HALLADO SE MUDO D'),
			 ('NO HALLADO NO EXISTE', 'NO HALLADO NO EXISTE'),
			 ('NO HALLADO FALLECIO', 'NO HALLADO FALLECIO'),
			 ('-', 'NO HABIDO'),
			 ('NO HALLADO OTROS MOT', 'NO HALLADO OTROS MOT'),
			 ('NO APLICABLE', 'NO APLICABLE'),
			 ('NO HALLADO NRO.PUERT', 'NO HALLADO NRO.PUERT'),
			 ('NO HALLADO CERRADO', 'NO HALLADO CERRADO'),
			 ('POR VERIFICAR', 'POR VERIFICAR'),
			 ('NO HALLADO DESTINATA', 'NO HALLADO DESTINATA'),
			 ('NO HALLADO RECHAZADO', 'NO HALLADO RECHAZADO')]

class Pertner(models.Model):
	_inherit = "res.partner"

	doc_type = fields.Char(related="l10n_latam_identification_type_id.l10n_pe_vat_code")
	doc_number = fields.Char("Numero de documento")
	commercial_name = fields.Char("Nombre commercial", default="-")
	legal_name = fields.Char("Nombre legal", default="-")
	state = fields.Selection(STATE, 'Estado', default="ACTIVO")
	condition = fields.Selection(CONDITION, 'Condicion', default='HABIDO')
	is_validate = fields.Boolean("Está validado")
	last_update = fields.Datetime("Última actualización")
	buen_contribuyente = fields.Boolean('Buen contribuyente')
	a_partir_del = fields.Date('A partir del')
	resolucion = fields.Char('Resolución')

	cod_doc_rel = fields.Char("Cod Doc relacionado", related="parent_id.l10n_latam_identification_type_id.l10n_pe_vat_code", store=True)
	numero_temp = fields.Char("Número doc relacionado", related="parent_id.doc_number", store=True)
	nombre_temp = fields.Char("Nombre relacionado", related="parent_id.name", store=True)

	es_agente_retencion = fields.Boolean('Es agente de retención')

	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		if operator in expression.NEGATIVE_TERM_OPERATORS:
			domain = [("doc_number", operator, name), ("name", operator, name)]
		else:
			domain = ['|', ("doc_number", operator, name), ("name", operator, name)]
		
		lines = self.search(expression.AND([domain, args]), limit=limit)
		return lines.name_get()

	@staticmethod
	def validate_ruc(vat):
		factor = '5432765432'
		sum = 0
		dig_check = False
		if len(vat) != 11:
			return False
		try:
			int(vat)
		except ValueError:
			return False
		for f in range(0, 10):
			sum += int(factor[f]) * int(vat[f])
		subtraction = 11 - (sum % 11)
		if subtraction == 10:
			dig_check = 0
		elif subtraction == 11:
			dig_check = 1
		else:
			dig_check = subtraction
		if not int(vat[10]) == dig_check:
			return False
		return True
