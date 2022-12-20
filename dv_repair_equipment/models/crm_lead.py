from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), ('quoted', 'Cotizado'), ('confirmed', 'Confirmado'),], string='Estado', default='new', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).client_state.selection]