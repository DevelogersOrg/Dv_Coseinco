# -*- encoding: utf-8 -*-
import requests
import logging

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import requests
from io import StringIO
import io
import logging
from PIL import Image
from bs4 import BeautifulSoup
import time
import unicodedata
from odoo.addons.solse_vat_pe.models import servicio_busqueda

_logger = logging.getLogger(__name__)

class Partner(models.Model):
	_inherit = 'res.partner'

	doc_type = fields.Char(related="l10n_latam_identification_type_id.l10n_pe_vat_code")
	doc_number = fields.Char("Numero de documento")
	commercial_name = fields.Char("Nombre commercial", default="-")
	legal_name = fields.Char("Nombre legal", default="-")
	state = fields.Selection(servicio_busqueda.STATE, 'Estado', default="ACTIVO")
	condition = fields.Selection(servicio_busqueda.CONDITION, 'Condicion', default='HABIDO')
	is_validate = fields.Boolean("Está validado")
	last_update = fields.Datetime("Última actualización")
	
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

	@api.model
	def create_from_ui(self, partner):
		if partner.get('last_update', False):
			last_update = partner.get('last_update', False)
			if len(last_update) == 27:
				partner['last_update'] = fields.Datetime.to_string(
					parser.parse(last_update))
		if partner.get('is_validate', False):
			if partner.get('is_validate', False) == 'true':
				partner['is_validate'] = True
			else:
				partner['is_validate'] = False
		if not partner.get('state', False):
			partner['state'] = 'ACTIVO'
		if not partner.get('condition', False):
			partner['condition'] = 'HABIDO'
		if partner.get('doc_type', False) and partner.get('doc_type', False) == '6':
			partner['company_type'] = "company"
		tipo_doc = partner.get('l10n_latam_identification_type_id', False)
		if tipo_doc and tipo_doc != "":
			partner['l10n_latam_identification_type_id'] = int(partner.get('l10n_latam_identification_type_id'))
		else:
			tipo_doc = self.env['l10n_latam.identification.type'].search([("l10n_pe_vat_code", "=", "0")])[0]
			partner['l10n_latam_identification_type_id'] = tipo_doc.id or False
			#raise UserError("Debe seleccionar un tipo de documento valido")
		res = super(Partner, self).create_from_ui(partner)
		return res
