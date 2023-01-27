from odoo import api, fields, models

class ResUsers(models.Model):
    _inherit = 'res.users'

    x_default_user_singnature = fields.Binary(string="Firma por defecto")