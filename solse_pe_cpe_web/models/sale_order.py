# -*- coding: utf-8 -*-
import logging
from . import constantes
from odoo import api, models, fields, _

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
	_inherit = "sale.order"

	pe_invoice_code = fields.Selection(constantes.COMPROBANTES, 'Tipo de comprobante')

	def pasar_variables_web(self, parametros):
		self.write({
			'pe_invoice_code': parametros['pe_invoice_code'] or False,
		})