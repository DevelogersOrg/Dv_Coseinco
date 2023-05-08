# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
_logging = logging.getLogger(__name__)


class L10nLatamDocumentType(models.Model):
	_inherit = 'l10n_latam.document.type'

	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	is_cpe = fields.Boolean('Es un CPE', help="Es un comprobante electronico")
	sub_type = fields.Selection([('sale', 'Ventas'), ('purchase', 'Compras')], string="Sub tipo")
	is_synchronous = fields.Boolean("Es sincrono", default=True)
	is_synchronous_anull = fields.Boolean("Anulación sincrona", default=True)
	nota_credito = fields.Many2one('l10n_latam.document.type', string='Nota credito', domain=[('code', '=', '07')])
	nota_debito = fields.Many2one('l10n_latam.document.type', string='Nota debito', domain=[('code', '=', '08')])
	usar_prefijo_personalizado = fields.Boolean('Personalizar prefijo')
	prefijo = fields.Char('Prefijo')
	correlativo_inicial = fields.Integer('Correlativo inicial', default=1, help="Correlativo usado para el primer comprobante emitidio con este tipo de documento")