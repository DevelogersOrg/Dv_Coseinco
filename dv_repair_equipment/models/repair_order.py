from odoo import models, fields, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), ('prh_proccess', 'En Proceso de Compra'), ('confirmed', 'Confirmado')], string='Estado', default='new', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).repair_state.selection]