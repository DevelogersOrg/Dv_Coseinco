from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    move_state = fields.Selection([('in_process', 'En Proceso'), ('tb_invoiced', 'Por Facturar'), ('invoiced', 'Facturado')], string='Estado', default='in_process', group_expand='_expand_states', index=True)
    crm_lead_id = fields.Many2one('crm.lead', string='Cotización')
    client_id = fields.Many2one('res.partner', string="Cliente", related='crm_lead_id.partner_id')
    repair_product_required = fields.One2many('repair.product.required', string='Productos necesitados', related='crm_lead_id.repair_product_required_ids')
    repair_order_components_ids = fields.One2many('repair.order.components', string='Componentes', related='crm_lead_id.repair_order_components_ids')
    repair_observation_detail_ids = fields.One2many('repair.observation.detail', string='Observaciones', related='crm_lead_id.repair_observation_detail_ids')
    equipment_failure_report = fields.Text(string='Reporte de falla', related='crm_lead_id.equipment_failure_report')
    initial_diagnosis = fields.Text(string='Diagnóstico inicial', related='crm_lead_id.initial_diagnosis')
    conclusion = fields.Text(string='Conclusión', related='crm_lead_id.conclusion')
    ready_to_invoice = fields.Boolean(string='Listo para facturar')

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).move_state.selection]

    def change_move_state(self):
        STATES = ['in_process', 'tb_invoiced', 'invoiced']
        self.move_state = STATES[STATES.index(self.move_state) + 1] if self.move_state != 'invoiced' else 'invoiced'
        if self.move_state == 'invoiced':
            self.create_invoice()

            
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    def create_invoice(self):
        self.ensure_one()
        self.ready_to_invoice = True
    
    
    # Tesoreria
    treasury_state = fields.Selection([('to_pay', 'Por Cobrar'), ('paid', 'Cobrado')],
                string='Estado de cobranza', default='to_pay', group_expand='_expand_treasury_states', index=True)
    
    def _expand_treasury_states(self, states, domain, order):
        return [key for key, val in type(self).treasury_state.selection]
    
    def action_treasury_state_pay(self):
        self.treasury_state = 'paid'
        self.payment_state = 'paid'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    #def action_post(self):
    #    res = super().sudo().action_post()
    #    return res