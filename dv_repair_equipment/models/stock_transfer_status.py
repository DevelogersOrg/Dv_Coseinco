from odoo import api, fields, models


class StockTransferStatus(models.Model):
    _name = 'stock.transfer.status'
    _description = 'Stock Transfer Status'

    name = fields.Char(string='Codigo')
    
    crm_lead_id = fields.Many2one('crm.lead')
    repair_product_required_ids = fields.Many2many('repair.product.required', compute='_compute_repair_product_required_ids', store=True)
    
    @api.depends('crm_lead_id.repair_product_required_ids')
    def _compute_repair_product_required_ids(self):
        for record in self:
            repair_product_required_ids = record.crm_lead_id.repair_product_required_ids
            record.repair_product_required_ids = repair_product_required_ids
    
    sale_order_id = fields.Many2one('sale.order')
    
    transfer_state = fields.Selection([('income', 'Ingreso de Respuestos'), ('request', 'Solicitud de Respuestos'), ('delivery', 'Entrega de Respuestos')], string='Estado', default='income', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).transfer_state.selection]
