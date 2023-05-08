# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class Partner(models.Model):
	_inherit = 'res.partner'

	pe_driver_license = fields.Char("Licencia de conducir")
	doc_name = fields.Char(related="l10n_latam_identification_type_id.name")
