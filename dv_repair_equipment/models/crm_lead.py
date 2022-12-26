from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Estados de cliente y tecnico
    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), (
        'quoted', 'Cotizado'), ('confirmed', 'Confirmado'), ], string='Estado', default='new', group_expand='_expand_client_states', index=True)
    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'),
                ('prh_proccess', 'En Proceso de Compra'), ('confirmed', 'Confirmado')],
                string='Estado', default='new', group_expand='_expand_repair_states', index=True)
    crm_type = fields.Selection([('repair', 'Tecnica'), ('client', 'Atención al Cliente'), ('both', 'Tecnica y Atención al Cliente')], string='Area')
    
    name = fields.Char(
        'Asunto', index=True, 
        compute='_compute_name', readonly=False, store=True)
    n_ticket = fields.Char(string='Número de Ticket')
    repair_order_type_id = fields.Many2one('repair.order.type', string='Tipo de Servicio a Desarrollar', )

    partner_id = fields.Many2one(
        'res.partner', string='Cliente', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.", )

    repair_order_components_ids = fields.One2many('repair.order.components', 'crm_lead_id', string='Componentes del Producto')

    repair_user_id = fields.Many2one(
        'res.users', string="Tecnico", default=lambda self: self.env.user, check_company=True, )

    def _expand_client_states(self, states, domain, order):
        return [key for key, val in type(self).client_state.selection]

    def _expand_repair_states(self, states, domain, order):
        return [key for key, val in type(self).repair_state.selection]

    has_quotation = fields.Boolean(string='Está cotizado', compute='_compute_has_quotation', store=True)
    
    @api.depends('sale_order_count')
    def _compute_has_quotation(self):
        for record in self:
            if record.sale_order_count > 0:
                has_quotation = True
                record.client_state = 'quoted'
            else:
                has_quotation = False
            record.has_quotation = has_quotation    
   
    has_confirmed_quotation = fields.Boolean(string='Está confirmado', compute='_compute_has_confirmed_quotation', store=True)         
    @api.depends('order_ids.state')
    def _compute_has_confirmed_quotation(self):
        for record in self:
            if any(order.state == 'done' for order in record.order_ids):
                has_confirmed_quotation = True
                record.client_state = 'confirmed'
            else:
                has_confirmed_quotation = False
            record.has_confirmed_quotation = has_confirmed_quotation
                
    def action_change_state(self):
        """
        Función para cambiar el estado del cliente
        """
        if self.crm_type == 'both':
            return
        
        current_state = self.client_state if self.crm_type == 'client' else self.repair_state

        # Lista de posible estados
        STATES = ['new', 'assigned', 'dg_ready']
        next_state = STATES[STATES.index(current_state) + 1]

        if self.crm_type == 'client':
            self.client_state = next_state
        
        if self.crm_type == 'repair':
            self.repair_state = next_state

        # Si el diagnóstico está listo, mostrar en ambos lados el registro
        if next_state == 'dg_ready':
            if self.crm_type == 'client': self.repair_state = 'dg_ready'
            if self.crm_type == 'repair': self.client_state = 'dg_ready'
            self.crm_type = 'both'

        # Recargar la vista
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def gen_ticket_number(self):
        """
        Función para generar el número de ticket
        """
        self.n_ticket = f'000000000{self.id}'


    def action_create_repair_order(self):
        """
        Función para crear la orden de reparación
        """
    # LOS DATOS QUE SE PASARAN; AUN NO ESTAN DEFINIDOS
        self.env['repair.order'].create({'crm_lead_id': self.id, 'product_id': 5, 'name': self.name, 'product_uom': 1, 'location_id': 1})
