from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), ('quoted', 'Cotizado'), ('confirmed', 'Confirmado'),], string='Estado', default='new', group_expand='_expand_states', index=True)
                                            
    repair_order_type_id = fields.Many2one('repair.order.type', string='Tipo de Servicio a Desarrollar', required=True)
    mesage_client = fields.Text(string='Mensaje al Cliente')
    repair_order_id = fields.Many2one('repair.order', string='Orden de Reparación')

    name = fields.Char(
        'Asunto', index=True, required=True,
        compute='_compute_name', readonly=False, store=True)
    ticket_number = fields.Char(string='Número de Ticket', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('crm.lead'))
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference."
        ,required=True)
    
    repair_user_id = fields.Many2one('res.users', string="Tecnico", default=lambda self: self.env.user, check_company=True, required=True)


    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).client_state.selection]


    def action_change_state(self):
        """
        Función para cambiar el estado del cliente
        """
        # Lista de posible estados
        CLIENT_STATES = ['new', 'assigned', 'dg_ready', 'quoted', 'confirmed']
        current_state = CLIENT_STATES.index(self.client_state)

        # Cambiar el estado al siguiente, si es el último, se queda en el mismo
        self.client_state = CLIENT_STATES[current_state + 1] if current_state < len(CLIENT_STATES) - 1 else CLIENT_STATES[current_state]
        
        # Si el estado es 'dg_ready' se crea la orden de reparación
        if self.client_state == 'dg_ready': self.action_create_repair_order() 

        # Recargar la vista
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    def action_create_repair_order(self):
        """
        Función para crear la orden de reparación
        """
        self.env['repair.order'].create({'crm_lead_id': self.id, 'product_id': 5, 'name': self.name, 'product_uom': 1, 'location_id': 1})

    