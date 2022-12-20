from odoo import models, fields, api, _

class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    inventory_state = fields.Selection([('income', 'Ingreso de Respuestos'), ('request', 'Solicitud de Respuestos'), ('reservation', 'Reserva de Repuestos'), ('delivery', 'Entrega de Respuestos')], string='Estado', default='income', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).inventory_state.selection]