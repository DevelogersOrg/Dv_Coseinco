# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import logging

_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = "account.move"

	orden_compra = fields.Char("Orden de compra")