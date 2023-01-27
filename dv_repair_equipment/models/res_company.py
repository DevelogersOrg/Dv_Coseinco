from odoo import api, fields, models

class ResCompany(models.Model):
  _inherit = 'res.company'

  # x_default_supplier_id = fields.Many2one('res.partner', string="Proveedor por defecto")