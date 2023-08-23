from odoo import api, fields, models
from odoo.exceptions import UserError
import base64
import io
import os
from PIL import Image
# from odoo.tools import sudo


class StockTransferStatus(models.Model):
    _name = 'stock.transfer.status'
    _description = 'Stock Transfer Status'

    name = fields.Char(string='Codigo', compute="_compute_name", store=True)
    crm_lead_id = fields.Many2one('crm.lead')
    repair_product_required_ids = fields.Many2many(
                                'repair.product.required', compute='_compute_repair_product_required_ids', store=True, string="Productos necesitados")
    repair_products_to_return_ids = fields.Many2many(
                                'repair.products.to.return', string='Productos a devolver', compute='_compute_repair_products_to_return_ids', store=True)

    client_id = fields.Many2one('res.partner', string="Cliente", related='crm_lead_id.partner_id')
    delivery_address_id = fields.Many2one('res.partner', string='Direccion Delivery')
    
    company_id = fields.Many2one('res.partner', string="Empresa", related='crm_lead_id.partner_id.parent_id')
    reciever_name = fields.Char(string="Nombre del receptor")
    reciever_phone = fields.Char(string="Teléfono del receptor")
    reciever_function = fields.Char(string="Función del receptor")
    reciever_id = fields.Char(string="Cédula del receptor")
    reciever_direction = fields.Char(string="Dirección del receptor")
    ship_date = fields.Datetime(string="Fecha y hora de despacho")


    sale_order_id = fields.Many2one('sale.order')
    need_to_purchase = fields.Boolean(compute="_compute_need_to_purchase", store=False)

    is_a_warehouse_order = fields.Boolean(string="Es una orden de compra?")
    is_now_picking_order = fields.Boolean(string="Es ahora una orden de despacho?")
    
    transfer_state = fields.Selection(
        [('new', 'Solicitud de Repuestos'), ('request', 'En proceso de compra'), ('income', 'Ingreso de Repuestos'), ('delivery', 'Entrega de Repuestos')],
        string='Estado', group_expand='_expand_transfer_states', index=True)
    picking_state = fields.Selection(
        [('tb_confirmed', 'Equipo a confirmar recepción'), ('confirmed', 'Recepción de Equipo Confirmado'), ('to_ship', 'Despacho Programado'), ('shiped', 'Despachado'),('delivered', 'Entregado')],
        string='Estado', group_expand='_expand_picking_states', index=True, default='tb_confirmed')

    purchase_order_id = fields.Many2one('purchase.order', string="Orden de compra")
    is_now_in_warehouse_view = fields.Boolean(string='Está en la vista de almacen?', compute='_compute_is_in_warehouse_view', store=False)
    given_products_state_probe_by_technician = fields.Binary(string='Imagen de prueba')



    def _compute_is_in_warehouse_view(self):
        for record in self:
            record.is_now_in_warehouse_view = self.env.context.get('default_is_a_warehouse_order')


    def _expand_transfer_states(self, states, domain, order):
        return [key for key, val in type(self).transfer_state.selection]

    def _expand_picking_states(self, states, domain, order):
        return [key for key, val in type(self).picking_state.selection]

    @api.depends('crm_lead_id.repair_product_required_ids')
    def _compute_repair_product_required_ids(self):
        for record in self:
            record.repair_product_required_ids = record.crm_lead_id.repair_product_required_ids

    @api.depends('crm_lead_id.repair_products_to_return_ids')
    def _compute_repair_products_to_return_ids(self):
        for record in self:
            record.repair_products_to_return_ids = record.crm_lead_id.repair_products_to_return_ids

    @api.depends('crm_lead_id')
    def _compute_name(self):
        for record in self:
            record.name = record.crm_lead_id.name

    # TODO: Testear si las cantidades se actualizan
    @api.depends('repair_product_required_ids.qty_to_order')
    def _compute_need_to_purchase(self):
        for record in self:
            if record.transfer_state != 'request':
                record.need_to_purchase = False

            for product in record.repair_product_required_ids:
                if product.qty_to_order > 0:
                    record.need_to_purchase = True
                    return
            
            record.need_to_purchase = False

    def create_purchase_orders(self):
        if not self.need_to_purchase:
            return
        
        products_to_buy = [product for product in self.repair_product_required_ids if product.qty_to_order > 0]
        order_line = []

        for product in products_to_buy:
            order_line.append((0, 0, {
                    'product_id': product.product_id.id,
                    'name': product.product_id.name,
                    'product_qty': product.qty_to_order,
                    'price_unit': product.product_id.list_price,
                    'product_uom': product.product_id.uom_id.id,
                    }))
        purchase_order_data ={
                'partner_id': self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).partner_id.id,
                'stock_transfer_status_id': self.id,
                'purchase_state': 'required',
                'order_line': order_line,
                'state': 'draft',
            }
        purchase_order = self.env['purchase.order'].create(purchase_order_data)
        
        self.transfer_state = 'request'
        self.need_to_purchase = False
        self.purchase_order_id = purchase_order.id
        self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).write({
            'crm_lead_state': 'purchase',
        })
        return {
            'effect': {
            'fadeout': 'slow',
            'message': 'Compra(s) creada(s) con exito',
            'type': 'rainbow_man',
            }}


    def confirm_stock_pickings(self):
        # TODO Error: Nada para lo que comprobar disponibilidad.
        if not self.purchase_order_id:
            return

        self.purchase_order_id.validate_stock_pickings()
        self.purchase_order_id.purchase_state = 'received'
        self.deliver_products()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def deliver_products(self):
        if self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).product_or_service == 'service':
            return self.deliver_products_to_tech()
        if self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).product_or_service == 'product':
            return self.deliver_products_to_customer()
        else:
            raise models.ValidationError(
                f"El estado de venta: {self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).crm_lead_state} no coincide con los valores esperados (service, product)")

    def deliver_products_to_tech(self):
        self.transfer_state = 'delivery'
        self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).write({
            'crm_lead_state': 'ready_to_repair',
            'repair_state': 'confirmed',
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def deliver_products_to_customer(self):
        self.transfer_state = 'delivery'
        self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).write({
            'crm_lead_state': 'confirmed',
        })
        self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).create_order_to_picking()
        self.env['crm.lead'].sudo().browse(self.crm_lead_id.id).create_account_move()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
        
    picking_type_id = fields.Many2one('stock.picking.type', string='Tipo de operacion')
    stock_picking_id = fields.Many2one('stock.picking', string="Trasnferencia")
    
    def create_stock_picking(self):
        """
            Crea una transferencia de stock al crear un despacho
        """
        if not self.picking_type_id:
            raise UserError("Seleccione un tipo de operacion")
        
            
        if self.picking_type_id.code == 'outgoing':
            move_ids_without_package = []
            for product in self.repair_products_to_return_ids:
                move_ids_without_package.append((0, 0, {
                    'name': product.product_id.name,
                    'product_id': product.product_id.id,
                    'product_uom_qty': product.quantity,
                    'product_uom': product.product_id.uom_id.id,
                }))
            pick = {
                'picking_type_id': self.picking_type_id.id,
                'partner_id': self.client_id.id,
                'origin': self.name,
                'location_dest_id': self.client_id.id,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'delivery_boy_partner_id': self.delivery_boy_partner_id.id,
                'location_id': self.picking_type_id.default_location_src_id.id,
                'move_ids_without_package': move_ids_without_package,
                #'move_type': 'direct'
            }
        if self.picking_type_id.code == 'incoming':
            move_ids_without_package = []
            for product in self.repair_product_required_ids:
                move_ids_without_package.append((0, 0, {
                    'name': product.product_id.name,
                    'product_id': product.product_id.id,
                    'product_uom_qty': product.quantity,
                    'product_uom': product.product_id.uom_id.id,
                }))
            pick = {
                'picking_type_id': self.picking_type_id.id,
                'partner_id': self.client_id.id,
                'origin': self.name,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id,
                'location_id': self.client_id.id,
                'delivery_boy_partner_id': self.delivery_boy_partner_id.id,
                'location_id': self.picking_type_id.default_location_dest_id.id,
                'move_ids_without_package': move_ids_without_package,
                #'move_type': 'direct'
            }

        self.stock_picking_id = self.env['stock.picking'].create(pick)
        
        
    def change_picking_state(self):
        """
            Cambia el estado de la transferencia de stock
        """
        if self.picking_state == False:
            self.picking_state = 'tb_confirmed'
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }

        STATES = ['tb_confirmed','confirmed','to_ship', 'shiped', 'delivered']
        self.picking_state = STATES[STATES.index(self.picking_state) + 1] if self.picking_state != 'delivered' else 'delivered'
        if self.picking_state in 'to_ship':
            self.change_account_move_state()
            if not self.stock_picking_id:
                self.create_stock_picking()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def change_account_move_state(self):
        account_move_ids = self.env['account.move'].search([('crm_lead_id', '=', self.crm_lead_id.id)])
        for account_move in account_move_ids:
            account_move.move_state = 'tb_invoiced'


    # DELIVERY BOY
    delivery_boy_partner_id = fields.Many2one(string="Delivery Boy", comodel_name="res.partner")

    #Adjuntar archivos
    stock_transfer_attachment = fields.Many2many('ir.attachment', string='Archivos Adjuntos')
    preview_images = fields.Html(compute='_compute_preview_images', string='Vista previa de imágenes')
    
    def _compute_preview_images(self):
        for record in self:
            images = record.stock_transfer_attachment.filtered(lambda attachment: attachment.mimetype.startswith('image/'))
            if images:
                image_tags = []
                for image in images:
                    image_tags.append(f'<a class="oe_lightbox" href="/web/image/{image.id}/preview"><img src="/web/image/{image.id}/preview" alt="{image.name}" style="height: 100px; margin: 0 10px 10px 0;"></a>')
                image_gallery = '<div class="image-gallery">' + ''.join(image_tags) + '</div>'
                record.preview_images = image_gallery
            else:
                record.preview_images = False

    def transfer_binary_to_many2many(self):
        for record in self:
            #Si hay given_products_state_probe_by_technician
            if record.given_products_state_probe_by_technician:
                attachment_data = {
                    'name': 'img_despacho',
                    'type': 'binary',
                    'datas': record.given_products_state_probe_by_technician,
                    'res_model': self._name,
                    'res_id': record.id,
                }
                attachment = self.env['ir.attachment'].create(attachment_data)
                record.stock_transfer_attachment = [(4, attachment.id)]
    
    def transfer_attachments_for_leads(self):
        #Busca todos los leads que tengan given_products_state_probe_by_client
        leads_with_binary = self.search([('given_products_state_probe_by_technician', '!=', False)])
        if leads_with_binary:
            for lead in leads_with_binary:
                lead.transfer_binary_to_many2many()
    
    #Eliminar archivos adjuntos
    def delete_attachment(self):
        all_records = self.env['stock.transfer.status'].search([])
        for record in all_records:
            record.given_products_state_probe_by_technician = False