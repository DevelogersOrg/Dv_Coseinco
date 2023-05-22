# -*- encoding: utf-8 -*-
import requests
import logging
from . import constantes

from datetime import datetime

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class State(models.Model):
	_inherit = 'res.country.state'

	provincias_ids = fields.One2many('res.city', 'state_id', 'Princias')

	def get_website_sale_privincias(self, mode='billing'):
		return self.sudo().provincias_ids

class City(models.Model):
	_inherit = 'res.city'

	distritos_ids = fields.One2many('l10n_pe.res.city.district', 'city_id', 'Distritos')

	def get_website_sale_distritos(self, mode='billing'):
		return self.sudo().distritos_ids

class Partner(models.Model):
	_inherit = 'res.partner'

	pe_invoice_code = fields.Selection(constantes.COMPROBANTES, 'Tipo de comprobante', default="01")