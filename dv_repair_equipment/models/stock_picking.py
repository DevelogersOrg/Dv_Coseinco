from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    picking_state = fields.Selection([('tb_confirmed', 'Equipo a confirmar recepción'), ('confirmed', 'Recepción de Equipo Confirmado'), ('to_ship', 'Despacho Programado'), ('delivered', 'Entregado')], string='Estado', default='tb_confirmed', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).picking_state.selection]