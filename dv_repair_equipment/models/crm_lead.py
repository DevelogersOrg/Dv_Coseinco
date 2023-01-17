from odoo import models, fields, api


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Estados de cliente y tecnico
    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), (
        'quoted', 'Cotizado'), ('confirmed', 'Confirmado'), ], string='Estado', default='new', group_expand='_expand_client_states', index=True)
    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'),
                ('waiting_for_products', 'Esperando repuestos'), ('confirmed', 'Confirmado'), ('in_repair', 'En Reparación'), ('ready', 'Servicio Culminado')],
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
    repair_user_id = fields.Many2one(
        'res.users', string="Tecnico", check_company=True, )

    # Esta variable deternima si el cliente está en la vista de cliente o en la vista de técnico
    is_now_in_client_view = fields.Boolean(string='Está en la vista de cliente?', compute='_compute_is_in_client_view', store=False)

    # Datos de Equipo
    n_active = fields.Char(string='N° Activo')
    n_serie = fields.Char(string='N° Serie')
    repair_equipment_type_id = fields.Many2one('repair.equipment.type', string='Tipo de Equipo')
    equipment_model = fields.Char(string='Modelo')
    equipment_accessories = fields.Char(string='Accesorios')
    equipment_failure_report = fields.Text(string='Reporte de Falla por el Cliente')
    other_equipment_data = fields.Text(string='Otros Datos del Equipo')
    repair_order_components_ids = fields.One2many('repair.order.components', 'crm_lead_id', string='Componentes del Equipo')


    # Etapa Desarrollo de Diagnóstico
    equipment_failure_report_for_tech = fields.Text(string='Reporte de Falla por el Cliente', related='equipment_failure_report', store=False, readonly=True)
    initial_diagnosis = fields.Text(string='Diagnóstico Inicial')
    repair_product_required_ids = fields.One2many('repair.product.required', 'crm_lead_id', string='Productos a incluir')
    comments = fields.Text(string='Observaciones')
    is_diagnosis_ready = fields.Boolean(string='Diagnóstico Listo?', default=False)

    # Campos para el seguimiento de la cotización
    has_quotation = fields.Boolean(string='Está cotizado', compute='_compute_has_quotation', store=True)
    has_confirmed_quotation = fields.Boolean(string='Está confirmado', compute='_compute_has_confirmed_quotation', store=True)

    # Campo para un seguimiento detallado de las ordenes de reparación
    crm_lead_state = fields.Selection(
        [('new', 'Nuevo Ingreso'), ('assigned', 'Pendiente'), ('assigned_ready', 'Por confirmar'), ('dg_ready', 'Pendiente'),
        ('dg_ready_ready', 'Por Cotizar'), ('quoted', 'Esperando'),('warehouse', 'En Almacén'), ('purchase', 'En proceso de compra'),('ready_to_repair', 'Por reparar'),('repairing', 'En reparación'),('to_finish', 'Por concluir'),('confirmed', 'Confirmado')],
        default='new', string='Estado de la Orden de Reparación'
        )

    # Es un servicio o un producto?
    product_or_service = fields.Selection([('product', 'Bien'), ('service', 'Servicio')], string='Bien / servicio', default='service')

    # Campos para el seguimiento de la orden de reparación
    repair_observation_detail_ids = fields.One2many('repair.observation.detail', 'crm_lead_id', string='Observaciones')

    # Campor para la finalización de la orden de reparación
    final_product_state = fields.Char(string='Estado de la Reparación')
    conclusion = fields.Text(string='Conclusión')
    reparation_proofs = fields.Binary(string='Prueba de Reparación')
    repair_products_to_return_ids = fields.Many2many('repair.products.to.return', string='Productos a devolver', compute='_compute_repair_products_to_return_ids', store=True)

    @api.depends('repair_order_components_ids', 'repair_product_required_ids')
    def _compute_repair_products_to_return_ids(self):
        for record in self:
            repair_products_to_return_ids = []
            for repair_order_component in record.repair_order_components_ids:
                repair_products_to_return_ids.append((0, 0, {
                    'product_id': repair_order_component.product_id.id,
                    'details': repair_order_component.details,
                    'quantity': repair_order_component.quantity,
                }))
            for repair_product_required in record.repair_product_required_ids:
                repair_products_to_return_ids.append((0, 0, {
                    'product_id': repair_product_required.product_id.id,
                    'details': repair_product_required.description,
                    'quantity': repair_product_required.quantity,
                }))
            record.repair_products_to_return_ids = repair_products_to_return_ids

    @api.depends('order_ids.state')
    def _compute_has_quotation(self):
        for record in self:
            if any(order.state == 'draft' for order in record.order_ids):
                has_quotation = True
                record.client_state = 'quoted'
                record.crm_lead_state = 'quoted'
            else:
                has_quotation = False
            record.has_quotation = has_quotation    
   
    def action_create_transfer_status(self):
        self.ensure_one()
        stock_transfter_status = {
            'crm_lead_id': self.id,
            'is_a_warehouse_order': True,
            'transfer_state': 'new',
        }
        self.env['stock.transfer.status'].create(stock_transfter_status)

    @api.depends('order_ids.state')
    def _compute_has_confirmed_quotation(self):
        for record in self:
            if any(order.state == 'sale' for order in record.order_ids):
                has_confirmed_quotation = True
                record.client_state = 'confirmed'
                if record.repair_product_required_ids:
                    record.action_create_transfer_status()
                    record.crm_lead_state = 'warehouse'
                    record.repair_state = 'waiting_for_products'
                else:
                    record.repair_state = 'confirmed'
                    record.crm_lead_state = 'ready_to_repair'
            else:
                has_confirmed_quotation = False
            record.has_confirmed_quotation = has_confirmed_quotation


    def _compute_is_in_client_view(self):
        for record in self:
            record.is_now_in_client_view = self.env.context.get('default_is_from_client_view')

        
    def _expand_client_states(self, states, domain, order):
        return [key for key, val in type(self).client_state.selection]


    def _expand_repair_states(self, states, domain, order):
        return [key for key, val in type(self).repair_state.selection]


    def action_change_state(self):
        """
        Función para cambiar el estado del cliente
        """
        if self.is_displayed_in_both:
            return

        if self.product_or_service == 'product':
            if not self.repair_product_required_ids or not self.partner_id:
                # raise models.ValidationError(f'{self.repair_product_required_ids} -- {self.partner_id}')
                return self.show_error_message('Alto ahi!!', 'Se necesita al menos un producto para continuar y un cliente')
            
            self.client_state = 'confirmed'
            self.crm_lead_state = 'warehouse'
            self.action_create_transfer_status()
            return {
            'type': 'ir.actions.client',
            'tag': 'reload',}

        current_state = self.client_state if self.is_from_client_view else self.repair_state

        if current_state == 'assigned' and not self.n_ticket:
            # Si no hay número de ticket, se envía una alerta
            return self.show_error_message('Sin número de ticket', 'Se necesita un número de ticket para continuar')


        # Lista de posible estados
        STATES = ['new', 'assigned', 'dg_ready']
        next_state = STATES[STATES.index(current_state) + 1]
        self.client_state = next_state
        self.repair_state = next_state
        self.crm_lead_state = next_state


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
        if self.n_ticket:
            return self.show_error_message('Error', 'No se puede generar el número de ticket porque ya existe')
        
        self.n_ticket = f'{(10 - len(str(self.id))) * "0"}{self.id}'
        self.crm_lead_state = 'assigned_ready'


    def action_new_quotation(self):
        if self.is_now_in_client_view and self.client_state in ['dg_ready', 'quoted'] and self.is_diagnosis_ready:
            action = self.env["ir.actions.actions"]._for_xml_id("sale_crm.sale_action_quotations_new")
            action['context'] = {
                'search_default_opportunity_id': self.id,
                'default_opportunity_id': self.id,
                'search_default_partner_id': self.partner_id.id,
                'default_partner_id': self.partner_id.id,
                'default_campaign_id': self.campaign_id.id,
                'default_medium_id': self.medium_id.id,
                'default_origin': self.name,
                'default_source_id': self.source_id.id,
                'default_company_id': self.company_id.id or self.env.company.id,
                'default_tag_ids': [(6, 0, self.tag_ids.ids)],
                'default_initial_diagnosis': self.initial_diagnosis,
                'default_equipment_failure_report': self.equipment_failure_report,
                'default_repair_user_id': self.repair_user_id.id,
            }

            # Datos opcionales
            order_lines = []
            if self.repair_product_required_ids:
                for product in self.repair_product_required_ids:
                    order_lines.append((0, 0, {
                        'product_id': product.product_id.id,
                        'name': product.product_id.name,
                        'product_uom_qty': product.quantity,
                        'price_unit': product.product_id.list_price,
                        'product_template_id' : product.product_id.product_tmpl_id.id,
                        'product_uom': product.product_id.uom_id.id,
                    }))
            # Agregar una sección de mano de obra
            order_lines.append((0, 0, {
            'display_type': 'line_section',
            'name': 'Mano de Obra',
            }))
            action['context']['default_order_line'] = order_lines
            if self.comments:
                action['context']['default_comments'] = self.comments
            if self.team_id:
                action['context']['default_team_id'] = self.team_id.id,
            if self.user_id:
                action['context']['default_user_id'] = self.user_id.id
            return action

        else:
            return self.show_error_message('Aún no!!', 'Para crear una cotización, debes estar en la vista de Atención al cliente y el diagnóstico debe estar listo')

    
    def show_error_message(self, title:str, message:str):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
                'type': 'danger',
            }
        }

    def set_diagnosis_ready(self):
        self.is_diagnosis_ready = True
        self.crm_lead_state = 'dg_ready_ready'
        return {
            'effect': {
            'fadeout': 'slow',
            'message': 'Gracias',
            'type': 'rainbow_man',
            }}

    def set_repair_to_concluded(self):
        self.crm_lead_state = 'to_finish'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def do_repair(self):
        if self.repair_state != 'confirmed':
            return self.show_error_message('Error', 'Se debe haber confirmado el servicio para continuar')
        
        self.repair_state = 'in_repair'
        self.crm_lead_state = 'repairing'
        # Recargar la vista
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def conclude_repair(self):
        if self.final_product_state and self.conclusion and self.reparation_proofs:
            self.repair_state = 'ready'
            self.crm_lead_state = 'confirmed'
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        return self.show_error_message('Aun no!!!', 'Debes llenar todos los campos para continuar')