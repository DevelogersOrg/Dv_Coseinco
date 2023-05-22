# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	estado_sunat_string = fields.Char("Estado Sunat", compute="_compute_estado_sunat")
	nro_doc_socio = fields.Char("Número Documento", related="partner_id.doc_number")

	@api.depends('estado_sunat')
	def _compute_estado_sunat(self):
		estados_json = {
			'01': 'Registrado',
			'03': 'Enviado',
			'05': 'Aceptado',
			'07': 'Observado',
			'09': 'Rechazado',
			'11': 'Anulado',
			'13': 'Por anular',
		}
		for reg in self:
			estado = '01'
			if reg.estado_sunat in estados_json:
				estados_json[reg.estado_sunat]
			reg.estado_sunat_string  = estado