from odoo import models, fields, api, _

class RepairOrderType(models.Model):
    _name = 'repair.order.type'
    _description = 'Lugar de reparación'

    name = fields.Char('Name', required=True)
