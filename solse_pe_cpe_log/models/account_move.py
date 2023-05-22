# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)

class AccountMove(models.Model):
	_inherit = 'account.move'

	no_enviar_rnoaceptados = fields.Boolean("No enviar en Reporte de No Aceptados")