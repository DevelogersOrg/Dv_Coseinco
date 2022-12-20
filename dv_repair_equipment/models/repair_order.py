from odoo import models, fields, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), ('prh_proccess', 'En Proceso de Compra'), ('confirmed', 'Confirmado')], string='Estado', default='new', group_expand='_expand_states', index=True)
    repair_order_type_id = fields.Selection([('remote', 'Remoto'), ('in_person', 'Presencial'), ('workshop', 'Taller'), ('external', 'Externo')], string='Tipo de Servicio a Desarrollar', required=True, default='remote')

    crm_lead_id = fields.Many2one('crm.lead', string='Cotización')

    # ?
    description = fields.Char(string='Servicio', required=True, related="crm_lead_id.name")
    lead_ticket_number = fields.Char(string='Número de Ticket', required=True, related="crm_lead_id.ticket_number")
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, states={'confirmed': [('readonly', True)]}, check_company=True, change_default=True,
        help='Choose partner for whom the order will be invoiced and delivered. You can find a partner by its Name, TIN, Email or Internal Reference.',
        related="crm_lead_id.partner_id")
    user_id = fields.Many2one('res.users', string="Tecnico", default=lambda self: self.env.user, check_company=True, related="crm_lead_id.repair_user_id")




    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).repair_state.selection]