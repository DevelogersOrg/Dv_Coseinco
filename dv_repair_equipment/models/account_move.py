from odoo import models, fields, api, _

class AccountMove(models.Model):
    _inherit = 'account.move'

    move_state = fields.Selection([('in_process', 'En Proceso'), ('tb_invoiced', 'Por Facturar'), ('invoiced', 'Facturado')], string='Estado', default='in_process', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).move_state.selection]