from odoo import models, fields, api

class RepairProductStateProbe(models.Model):
  _name = 'repair.product.state.probe'

  name = fields.Char(string='Descripción', required=True)
  img = fields.Binary(string='Imagen')