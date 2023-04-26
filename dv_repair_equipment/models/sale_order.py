from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    repair_user_id = fields.Many2one('res.users', string="Tecnico", check_company=True)
    equipment_failure_report = fields.Text(string='Reporte de Falla')
    initial_diagnosis = fields.Text(string='Diagnóstico Inicial')
    comments = fields.Text(string='Observaciones')
    
    quotation_terms_conditions_id = fields.Many2one('quotation.terms.conditions', string='Términos y condiciones')
    quotation_time_period_for_payment_type_id = fields.Many2one('quotation.time.period', string='Forma de pago')
    quotation_time_period_for_shipping_time_id = fields.Many2one('quotation.time.period', string='Tiempo de entrega')
    quotation_time_period_for_guarantee_id = fields.Many2one('quotation.time.period', string='Garantía')
    quotation_time_period_for_validity_id = fields.Many2one('quotation.time.period', string='Validez de la cotización')
