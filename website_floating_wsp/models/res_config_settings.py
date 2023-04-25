# -*- coding: utf-8 -*-
# License MIT #

from odoo import api, fields, models, tools

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'
	
	floating_wsp_id = fields.Many2one(comodel_name='website_floating_wsp', related="website_id.floating_wsp_id" , readonly=False)


