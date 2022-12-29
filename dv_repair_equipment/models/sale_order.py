from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    repair_user_id = fields.Many2one('res.users', string="Tecnico", check_company=True)
    equipment_failure_report = fields.Text(string='Reporte de Falla')
    initial_diagnosis = fields.Text(string='Diagnóstico Inicial')
    comments = fields.Text(string='Observaciones')
    
