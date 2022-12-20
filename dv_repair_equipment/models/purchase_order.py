from odoo import models, fields, api

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_state = fields.Selection([('required', 'Requerimiento de Compra'), ('received', 'Compra Recibida')], string='Estado', default='required', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).purchase_state.selection]