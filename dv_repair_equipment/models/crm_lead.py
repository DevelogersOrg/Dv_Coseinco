from odoo import models, fields, api
from datetime import timedelta
import base64
import io
import os
from PIL import Image

import logging
_logger = logging.getLogger(__name__)
class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # Estados de cliente y tecnico
    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Detalles del diagnóstico'), ('dg_ready', 'Diagnóstico inicial'), (
        'quoted', 'Cotizado'), ('confirmed', 'Confirmado'), ], string='Estado', default='new', group_expand='_expand_client_states', index=True)
    repair_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Detalles del diagnóstico'), ('dg_ready', 'Diagnóstico inicial'),
                ('waiting_for_products', 'Esperando repuestos'), ('confirmed', 'Confirmado'), ('in_repair', 'En Reparación'), ('ready', 'Servicio Culminado')],
                string='Estado', default='new', group_expand='_expand_repair_states', index=True)
    is_from_client_view = fields.Boolean(string='Es parte de la vista de cliente?')
    is_displayed_in_both = fields.Boolean(string='Se muestra en ambos lados?', default=False)
    
    name = fields.Char(
        'Asunto', compute='_compute_name', default='Borrador')
    
    def name_get(self):
        res = []
        for record in self:
            name = f'{(10 - len(str(record.id))) * "0"}{record.id}'
            res.append((record.id, name))
        return res
    
    def _compute_name(self):
        for record in self:
            record.name = f'{(10 - len(str(record.id))) * "0"}{record.id}'
    repair_order_type_id = fields.Many2one('repair.order.type', string='Tipo de Servicio a Desarrollar')

    service_description = fields.Text(string='Descripción del Servicio', store=True)

    partner_id = fields.Many2one(
        'res.partner', string='Cliente', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.", )
    repair_user_id = fields.Many2one(
        'res.users', string="Tecnico", check_company=True, tracking=True)

    # Esta variable deternima si el cliente está en la vista de cliente o en la vista de técnico
    is_now_in_client_view = fields.Boolean(string='Está en la vista de cliente?', compute='_compute_is_in_client_view', store=False)

    # Datos de Equipo
    n_active = fields.Char(string='N° Activo', store=True)
    n_serie = fields.Char(string='N° Serie', store=True)
    repair_equipment_type_id = fields.Many2one('repair.equipment.type', string='Tipo de Equipo', store=True)
    equipment_model = fields.Char(string='Modelo', store=True)
    equipment_accessories = fields.Char(string='Accesorios', store=True)
    equipment_failure_report = fields.Text(string='Reporte de Falla por el Cliente', store=True)
    other_equipment_data = fields.Text(string='Otros Datos del Equipo', store=True)
    repair_order_components_ids = fields.One2many('repair.order.components', 'crm_lead_id', string='Componentes del Equipo', store=True)


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
        [('new', 'Nuevo Ingreso'), ('assigned', 'Pendiente'), ('dg_ready', 'Pendiente'), ('ext_technician', 'Diagnóstico externo'),
        ('dg_ready_ready', 'Por Cotizar'), ('quoted', 'Esperando'),('warehouse', 'En Almacén'), ('purchase', 'En proceso de compra'),
        ('ready_to_repair', 'Por reparar'),('repairing', 'En reparación'),('to_finish', 'Por concluir'),('confirmed', 'Confirmado')],
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

    stock_transfter_status_id = fields.Many2one('stock.transfer.status', string='Estado de la Transferencia en Almacén')
    account_move_id = fields.Many2one('account.move', string='Factura')

    given_products_state_probe_by_client = fields.Binary(string='Imagen de prueba')
    given_products_state_probe_by_warehouse = fields.Binary(string='Imagen de prueba')

    # Campos para diagnostico de tecnico externo
    need_external_diagnosis = fields.Boolean(string='Necesita Diagnóstico Externo?', default=False)
    external_technician_id = fields.Many2one('res.partner', string='Técnico Externo')
    

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
            for repair_product_required_ids in record.repair_product_required_ids:
                repair_products_to_return_ids.append((0, 0, {
                    'product_id': repair_product_required_ids.product_id.id,
                    'details': repair_product_required_ids.description,
                    'quantity': repair_product_required_ids.quantity,
                }))
            # eliminamos los productos que ya estan en la lista de productos a devolver
            record.repair_products_to_return_ids = [(5, 0, 0)]                
            record.repair_products_to_return_ids = repair_products_to_return_ids

    @api.depends('order_ids.state')
    def _compute_has_quotation(self):
        for record in self:
            if any(order.state == 'draft' for order in record.order_ids):
                has_quotation = True
                if record.product_or_service == 'service':
                    record.client_state = 'quoted'
                    record.crm_lead_state = 'quoted'
            else:
                has_quotation = False
            record.has_quotation = has_quotation    
   
    def action_create_transfer_status(self):
        self.ensure_one()
        if self.stock_transfter_status_id:
            return

        stock_transfter_status = {
            'crm_lead_id': self.id,
            'is_a_warehouse_order': True,
            'transfer_state': 'new',
        }
        self.stock_transfter_status_id = self.env['stock.transfer.status'].create(stock_transfter_status)

        
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


    def action_change_both_state(self):
        if self.is_displayed_in_both:
            return
            
        self.name = f'{(10 - len(str(self.id))) * "0"}{self.id}'
        if self.product_or_service == 'product': return self.change_state_for_products()
        current_state = self.client_state if self.is_from_client_view else self.repair_state
        if not self.is_diagnosis_ready_to_continue(current_state):
            return self.show_error_message('Alto ahi!!', 'Falta información para pasar al siguiente estado')

        # Lista de posible estados
        STATES = ['new', 'assigned', 'dg_ready']
        next_state = STATES[STATES.index(current_state) + 1]
        self.client_state = next_state
        self.repair_state = next_state
        self.crm_lead_state = next_state

        # Si el diagnóstico está listo, mostrar en ambos lados el registro
        if next_state == 'dg_ready':
            self.is_displayed_in_both = True
        return self.reload_view()

    def is_diagnosis_ready_to_continue(self, current_state):
        if current_state != 'assigned':
            return True
        if self.partner_id and self.repair_user_id and self.equipment_failure_report:
            return True
        else:
            return False

    def change_state_for_products(self):
        if not self.has_quotation:
            return self.show_error_message('Alto ahi!!', 'Necesitas tener una cotización para continuar')

        self.client_state = 'confirmed'
        self.repair_state = 'ready'
        self.crm_lead_state = 'warehouse'
        self.action_create_transfer_status()
        return self.reload_view()


    def action_new_quotation(self):
        if not self.can_create_new_quotation():
            return self.show_error_message('Aún no!!', 'Te faltan datos para poder crear una cotización')

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
            'default_tag_ids': [(6, 0, self.tag_ids.ids)],}

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

        if self.product_or_service == 'service':
            # Agregar una sección de mano de obra
            # order_lines.append((0, 0, {'display_type': 'line_section', 'name': 'Mano de Obra',}))
            action['context']['default_comments'] = self.comments
            action['context']['default_initial_diagnosis'] = self.initial_diagnosis,
            action['context']['default_equipment_failure_report'] = self.equipment_failure_report,
            action['context']['default_repair_user_id'] = self.repair_user_id.id,

        # Datos opcionales
        action['context']['default_order_line'] = order_lines
        if self.team_id:
            action['context']['default_team_id'] = self.team_id.id,
        if self.user_id:
            action['context']['default_user_id'] = self.user_id.id
        return action

    def can_create_new_quotation(self):
        if self.partner_id and self.repair_product_required_ids and self.product_or_service == 'product':
            return True
        if self.client_state in ['dg_ready', 'quoted'] and self.is_diagnosis_ready and self.is_now_in_client_view:
            return True
        else:
            return False
        


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
        if self.need_external_diagnosis and self.crm_lead_state != 'dg_ready':
            return self.show_error_message('Alto ahi!!', 'Necesitas terminar el diagnóstico externo para continuar')

        if not self.initial_diagnosis:
            return self.show_error_message('Alto ahi!!', 'Necesitas agregar un diagnóstico para continuar')
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
        return self.reload_view()

    def do_repair(self):
        if self.repair_state != 'confirmed':
            return self.show_error_message('Error', 'Se debe haber confirmado el servicio para continuar')
        
        self.repair_state = 'in_repair'
        self.crm_lead_state = 'repairing'
        # Recargar la vista
        return self.reload_view()

    def conclude_repair(self):
        if self.final_product_state and self.conclusion and self.reparation_proofs:
            self.repair_state = 'ready'
            self.crm_lead_state = 'confirmed'
            if self.repair_products_to_return_ids:
                self.sudo().create_order_to_picking()
            self.sudo().create_account_move()

            return self.reload_view()

        return self.show_error_message('Aun no!!!', 'Debes llenar todos los campos para continuar')

    def create_order_to_picking(self):
        self.ensure_one()
        stock_transfter_status = {
            'crm_lead_id': self.id,
            'is_a_warehouse_order': False,
            'transfer_state': 'new',
            'picking_state': 'tb_confirmed',
            'is_now_picking_order': True,
        }
        self.stock_transfter_status_id = self.env['stock.transfer.status'].create(stock_transfter_status)

    def create_account_move(self):
        assigned_picking_ids = self.order_ids.picking_ids.filtered(lambda p: p.state == 'assigned')
        if assigned_picking_ids:
            _logger.info(f"self.order_ids: {self.order_ids}")
            _logger.info(f"assigned_picking_ids: {assigned_picking_ids}")
            for picking in assigned_picking_ids:
                picking.action_assign()
                picking.action_confirm()
                for mv in picking.move_ids_without_package:
                    mv.quantity_done = mv.product_uom_qty
                picking.button_validate()
        self.order_ids._create_invoices()
        self.order_ids.invoice_ids.crm_lead_id = self.id
        
    def _create_account_move(self):
        if self.repair_state != 'ready' and self.product_or_service == 'service':
            return self.show_error_message('Error', 'El servicio debe estar listo para continuar')
        
        invoice_lines = []
        for product in self.repair_product_required_ids:
            invoice_lines.append((0, 0, {
                'product_id': product.product_id.id,
                'name': product.product_id.name,
                'quantity': product.quantity,
                'price_unit': product.product_id.list_price,
            }))

        self.account_move_id = self.env['account.move'].create({
            'move_state': 'in_process',
            'crm_lead_id': self.id,
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': invoice_lines,
            })

    def start_external_diagnosis(self):
        self.crm_lead_state = 'ext_technician'
        self.need_external_diagnosis = True
        return self.reload_view()

    def stop_external_diagnosis(self):
        if not self.external_technician_id:
            return self.show_error_message('Error', 'Debes seleccionar un tecnico externo para continuar')

        self.crm_lead_state = 'dg_ready'
        return self.reload_view()

    def reload_view(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    quotation_terms_conditions_id = fields.Many2one('quotation.terms.conditions', string='Términos y condiciones')
    quotation_time_period_for_payment_type_id = fields.Many2one('quotation.time.period', string='Forma de pago')
    quotation_time_period_for_shipping_time_id = fields.Many2one('quotation.time.period', string='Tiempo de entrega')
    quotation_time_period_for_guarantee_id = fields.Many2one('quotation.time.period', string='Garantía')
    quotation_time_period_for_validity_id = fields.Many2one('quotation.time.period', string='Validez de la cotización')

    #Adjuntar archivos en diagnóstico
    diagnostic_attachment = fields.Many2many('ir.attachment', string='Archivos Adjuntos')
    diagnostic_preview_images = fields.Html(compute='_compute_diagnostic_preview_images', string='Vista previa de imágenes en diagnóstico')

    def _compute_diagnostic_preview_images(self):
        for record in self:
            images = record.diagnostic_attachment.filtered(lambda attachment: attachment.mimetype.startswith('image/'))
            if images:
                image_tags = []
                for image in images:
                    image_tags.append(f'<a class="oe_lightbox" href="/web/image/{image.id}/preview"><img src="/web/image/{image.id}/preview" alt="{image.name}" style="height: 100px; margin: 0 10px 10px 0;"></a>')
                image_gallery = '<div class="image-gallery">' + ''.join(image_tags) + '</div>'
                record.diagnostic_preview_images = image_gallery
                record.other_diagnostic_preview_images = image_gallery
            else:
                record.diagnostic_preview_images = False
                record.other_diagnostic_preview_images = False
    
    other_diagnostic_attachment = fields.Many2many('ir.attachment', 'diagnostic_attachment_rel', string='Archivos Adjuntos', compute='_compute_other_diagnostic_attachment', store=True)
    other_diagnostic_preview_images = fields.Html(compute='_compute_diagnostic_preview_images', string='Vista previa de imágenes')
    @api.depends('diagnostic_attachment')
    def _compute_other_diagnostic_attachment(self):
        for record in self:
            record.other_diagnostic_attachment = record.diagnostic_attachment

    #Adjuntar archivos en reparacion
    reparation_attachment = fields.Many2many('ir.attachment', 'reparation_attachment_rel', string='Archivos Adjuntos')
    reparation_preview_images = fields.Html(compute='_compute_reparation_preview_images', string='Vista previa de imágenes en reparación')

    def _compute_reparation_preview_images(self):
        for record in self:
            images = record.reparation_attachment.filtered(lambda attachment: attachment.mimetype.startswith('image/'))
            if images:
                image_tags = []
                for image in images:
                    image_tags.append(f'<a class="oe_lightbox" href="/web/image/{image.id}/preview"><img src="/web/image/{image.id}/preview" alt="{image.name}" style="height: 100px; margin: 0 10px 10px 0;"></a>')
                image_gallery = '<div class="image-gallery">' + ''.join(image_tags) + '</div>'
                record.reparation_preview_images = image_gallery
                record.other_reparation_preview_images = image_gallery
            else:
                record.reparation_preview_images = False
                record.other_reparation_preview_images = False
    
    other_reparation_attachment = fields.Many2many('ir.attachment', 'other_reparation_attachment_rel', string='Archivos Adjuntos', compute='_compute_other_reparation_attachment', store=True)
    other_reparation_preview_images = fields.Html(compute='_compute_reparation_preview_images', string='Vista previa de imágenes')
    @api.depends('reparation_attachment')
    def _compute_other_reparation_attachment(self):
        for record in self:
            record.other_reparation_attachment = record.reparation_attachment
    
    #Adjuntar archivos en confirmacion
    confirmation_attachment = fields.Many2many('ir.attachment', 'confirmation_attachment_rel', string='Archivos Adjuntos')
    confirmation_preview_images = fields.Html(compute='_compute_confirmation_preview_images', string='Vista previa de imágenes')

    def _compute_confirmation_preview_images(self):
        for record in self:
            images = record.confirmation_attachment.filtered(lambda attachment: attachment.mimetype.startswith('image/'))
            if images:
                image_tags = []
                for image in images:
                    image_tags.append(f'<a class="oe_lightbox" href="/web/image/{image.id}/preview"><img src="/web/image/{image.id}/preview" alt="{image.name}" style="height: 100px; margin: 0 10px 10px 0;"></a>')
                image_gallery = '<div class="image-gallery">' + ''.join(image_tags) + '</div>'
                record.confirmation_preview_images = image_gallery
                record.other_confirmation_preview_images = image_gallery
            else:
                record.confirmation_preview_images = False
                record.other_confirmation_preview_images = False
    
    other_confirmation_attachment = fields.Many2many('ir.attachment', 'other_confirmation_attachment_rel', string='Archivos Adjuntos', compute='_compute_other_confirmation_attachment', store=True)
    other_confirmation_preview_images = fields.Html(compute='_compute_confirmation_preview_images', string='Vista previa de imágenes')
    @api.depends('confirmation_attachment')
    def _compute_other_confirmation_attachment(self):
        for record in self:
            record.other_confirmation_attachment = record.confirmation_attachment

    
    def transfer_binary_to_many2many(self):
        for record in self:
            #Si hay given_products_state_probe_by_client
            if record.given_products_state_probe_by_client:
                attachment_data = {
                    'name': 'img_diagnóstico',
                    'type': 'binary',
                    'datas': record.given_products_state_probe_by_client,
                    'res_model': self._name,
                    'res_id': record.id,
                }
                attachment = self.env['ir.attachment'].create(attachment_data)
                record.diagnostic_attachment = [(4, attachment.id)]
            #Si hay given_products_state_probe_by_warehouse
            if record.given_products_state_probe_by_warehouse:
                attachment_data = {
                    'name': 'img_reparación',
                    'type': 'binary',
                    'datas': record.given_products_state_probe_by_warehouse,
                    'res_model': self._name,
                    'res_id': record.id,
                }
                attachment = self.env['ir.attachment'].create(attachment_data)
                record.reparation_attachment = [(4, attachment.id)]
            #Si hay reparation_proofs
            if record.reparation_proofs:
                attachment_data = {
                    'name': 'img_reparado',
                    'type': 'binary',
                    'datas': record.reparation_proofs,
                    'res_model': self._name,
                    'res_id': record.id,
                }
                attachment = self.env['ir.attachment'].create(attachment_data)
                record.confirmation_attachment = [(4, attachment.id)]
    
    def transfer_attachments_for_leads(self):
        #Busca todos los leads que tengan given_products_state_probe_by_client
        leads_with_binary = self.search([('given_products_state_probe_by_client', '!=', False)])
        if leads_with_binary:
            for lead in leads_with_binary:
                lead.transfer_binary_to_many2many()
        #Busca todos los leads que tengan given_products_state_probe_by_warehouse
        leads_with_binary = self.search([('given_products_state_probe_by_warehouse', '!=', False)])
        if leads_with_binary:
            for lead in leads_with_binary:
                lead.transfer_binary_to_many2many()
        #Busca todos los leads que tengan reparation_proofs
        leads_with_binary = self.search([('reparation_proofs', '!=', False)])
        if leads_with_binary:
            for lead in leads_with_binary:
                lead.transfer_binary_to_many2many()
    
    #Eliminar archivos adjuntos
    def delete_attachment(self):
        all_records = self.env['crm.lead'].search([])
        for record in all_records:
            record.given_products_state_probe_by_client = False
            record.given_products_state_probe_by_warehouse = False
            record.reparation_proofs = False
    
    @api.model_create_single
    def create(self, values):
        lead = super(CrmLead, self).create(values)
        report_time = self.env['report.time'].create({
            'name': lead.display_name,
            'module': 'Atención al Cliente',
            'stage': lead.client_state,
        })
        return lead