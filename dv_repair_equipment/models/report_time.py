from odoo import models, fields, api, _

class report_time(models.Model):
    _name = 'report.time'

    name = fields.Char(string='TICKET/PROCESO')
    module = fields.Char(string='MODULO')
    stage = fields.Char(string='ETAPA')