from odoo import models, fields

class QuotationTimePeriod(models.Model):
    _name = 'quotation.time.period'
    _description = 'Quotation Time Period'

    name = fields.Char(string='Periodo de tiempo', required=True)