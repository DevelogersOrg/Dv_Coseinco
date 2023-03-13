from odoo import models, fields, api

class QuantationTimePeriod(models.Model):
    _name = 'quantation.time.period'
    _description = 'Quantation Time Period'

    name = fields.Char(string='Periodo de tiempo', required=True)