from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Estados de cliente y tecnico
    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), (
        'quoted', 'Cotizado'), ('confirmed', 'Confirmado'), ], string='Estado', default='new', group_expand='_expand_client_states', index=True)
    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'),
                ('prh_proccess', 'En Proceso de Compra'), ('confirmed', 'Confirmado')],
                string='Estado', default='new', group_expand='_expand_repair_states', index=True)
    is_from_client_view = fields.Boolean(string='Es parte de la vista de cliente?')
    is_displayed_in_both = fields.Boolean(string='Se muestra en ambos lados?', default=False)
    
    name = fields.Char(
        'Asunto', index=True, 
        compute='_compute_name', readonly=False, store=True)
    n_ticket = fields.Char(string='Número de Ticket')
    repair_order_type_id = fields.Many2one('repair.order.type', string='Tipo de Servicio a Desarrollar', )

    partner_id = fields.Many2one(
        'res.partner', string='Cliente', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.", )

    # TODO indentificar de que viscta se esta llamando
    # current_view_id = fields.Char(string='Vista Actual', compute='_compute_current_view_id')

    # @api.model
    # def _compute_current_view_id(self):
    #     for record in self:
    #         record.current_view_id = self.env.context.get('view_id')

    repair_user_id = fields.Many2one(
        'res.users', string="Tecnico", check_company=True, )


    # Datos de Equipo
    n_active = fields.Char(string='N° Activo')
    n_serie = fields.Char(string='N° Serie')
    repair_equipment_type_id = fields.Many2one('repair.equipment.type', string='Tipo de Equipo')
    equipment_model = fields.Char(string='Modelo')
    equipment_accessories = fields.Char(string='Accesorios')
    equipment_failure_report = fields.Text(string='Reporte de Falla')
    other_equipment_data = fields.Text(string='Otros Datos del Equipo')
    repair_order_components_ids = fields.One2many('repair.order.components', 'crm_lead_id', string='Componentes del Equipo')


    # Etapa Desarrollo de Diagnóstico
    # equipment_failure_report
    initial_diagnosis = fields.Text(string='Diagnóstico Inicial')
    repair_product_required_ids = fields.One2many('repair.product.required', 'crm_lead_id', string='Productos Necesarios para Reparar')
    comments = fields.Text(string='Observaciones')
    is_diagnosis_ready = fields.Boolean(string='Diagnóstico Listo?', default=False)


    


    def _expand_client_states(self, states, domain, order):
        return [key for key, val in type(self).client_state.selection]

    def _expand_repair_states(self, states, domain, order):
        return [key for key, val in type(self).repair_state.selection]

    has_quotation = fields.Boolean(string='Está cotizado', compute='_compute_has_quotation', store=True)
    
    @api.depends('order_ids.state')
    def _compute_has_quotation(self):
        for record in self:
            if any(order.state == 'draft' for order in record.order_ids):
                has_quotation = True
                record.client_state = 'quoted'
            else:
                has_quotation = False
            record.has_quotation = has_quotation    
   
    has_confirmed_quotation = fields.Boolean(string='Está confirmado', compute='_compute_has_confirmed_quotation', store=True)         
    @api.depends('order_ids.state')
    def _compute_has_confirmed_quotation(self):
        for record in self:
            if any(order.state == 'sale' for order in record.order_ids):
                has_confirmed_quotation = True
                record.client_state = 'confirmed'
            else:
                has_confirmed_quotation = False
            record.has_confirmed_quotation = has_confirmed_quotation
                
    def action_change_state(self):
        """
        Función para cambiar el estado del cliente
        """
        if self.is_displayed_in_both:
            return

        current_state = self.client_state if self.is_from_client_view else self.repair_state

        if current_state == 'assigned' and not self.n_ticket:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error',
                    'message': 'No se puede cambiar el estado porque no se ha generado el número de ticket',
                    'sticky': False,
                    'type': 'danger',
                }
            }

        # Lista de posible estados
        STATES = ['new', 'assigned', 'dg_ready']
        next_state = STATES[STATES.index(current_state) + 1]

        self.client_state = next_state
        self.repair_state = next_state

        # Si el diagnóstico está listo, mostrar en ambos lados el registro
        if next_state == 'dg_ready':
            self.is_displayed_in_both = True

        # Recargar la vista
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def gen_ticket_number(self):
        """
        Función para generar el número de ticket
        """
        self.n_ticket = f'{(10 - len(str(self.id))) * "0"}{self.id}'