from odoo import models, fields, api

class RepairOrder(models.Model):
    _inherit = 'repair.order'

    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), ('prh_proccess', 'En Proceso de Compra'), ('confirmed', 'Confirmado')], string='Estado', default='new', group_expand='_expand_states', index=True)
    repair_order_type_id = fields.Many2one('repair.order.type', string='Tipo de Servicio a Desarrollar', required=True)
    crm_lead_id = fields.Many2one('crm.lead', string='Cotización')

    # ?
    description = fields.Char(string='Servicio', required=True)
    lead_ticket_number = fields.Char(string='Número de Ticket', required=True)
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        index=True, states={'confirmed': [('readonly', True)]}, check_company=True, change_default=True,
        help='Choose partner for whom the order will be invoiced and delivered. You can find a partner by its Name, TIN, Email or Internal Reference.')
    user_id = fields.Many2one('res.users', string="Tecnico", default=lambda self: self.env.user, check_company=True, related="crm_lead_id.repair_user_id")


    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).repair_state.selection]


    def action_change_state(self):
        """
        Función para cambiar el estado del cliente
        """
        # Lista de posible estados
        REPAIR_STATES = ['new', 'assigned', 'dg_ready', 'prh_proccess', 'confirmed']
        current_state = REPAIR_STATES.index(self.repair_state)

        # Cambiar el estado al siguiente, si es el último, se queda en el mismo
        self.repair_state = REPAIR_STATES[current_state + 1] if current_state < len(REPAIR_STATES) - 1 else REPAIR_STATES[current_state]
        
        # Si el estado es 'dg_ready' se crea la orden de reparación
        if self.repair_state == 'dg_ready': self.action_create_client_order() 

        # Recargar la vista
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_create_client_order(self):
        """
        Función para crear una orden de reparación para el cliente
        """
