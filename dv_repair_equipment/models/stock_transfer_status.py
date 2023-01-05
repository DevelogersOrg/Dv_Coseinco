from odoo import api, fields, models


class StockTransferStatus(models.Model):
    _name = 'stock.transfer.status'
    _description = 'Stock Transfer Status'

    name = fields.Char(string='Codigo', compute="_compute_name", store=True)
    crm_lead_id = fields.Many2one('crm.lead')
    repair_product_required_ids = fields.Many2many(
                                'repair.product.required', compute='_compute_repair_product_required_ids', store=True, string="Productos necesitados")
    sale_order_id = fields.Many2one('sale.order')
    need_to_purchase = fields.Boolean(compute="_compute_need_to_purchase", store=False)

    is_a_warehouse_order = fields.Boolean(string="Es una orden de compra?")
    
    transfer_state = fields.Selection(
        [('new', 'Solicitud de Repuestos'), ('request', 'En proceso de compra'), ('income', 'Ingreso de Repuestos'), ('delivery', 'Entrega de Repuestos')],
        string='Estado', group_expand='_expand_transfer_states', index=True)
    picking_state = fields.Selection(
        [('tb_confirmed', 'Equipo a confirmar recepción'), ('confirmed', 'Recepción de Equipo Confirmado'), ('to_ship', 'Despacho Programado'), ('delivered', 'Entregado')],
        string='Estado', group_expand='_expand_picking_states', index=True)

    purchase_order_id = fields.Many2one('purchase.order', string="Orden de compra")


    def _expand_transfer_states(self, states, domain, order):
        return [key for key, val in type(self).transfer_state.selection]

    def _expand_picking_states(self, states, domain, order):
        return [key for key, val in type(self).picking_state.selection]

    @api.depends('crm_lead_id.repair_product_required_ids')
    def _compute_repair_product_required_ids(self):
        for record in self:
            record.repair_product_required_ids = record.crm_lead_id.repair_product_required_ids

    @api.depends('crm_lead_id.n_ticket')
    def _compute_name(self):
        for record in self:
            record.name = record.crm_lead_id.n_ticket

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
                'partner_id': self.crm_lead_id.partner_id.id,
                'stock_transfer_status_id': self.id,
                'purchase_state': 'required',
                'order_line': order_line,
            }
        purchase_order = self.env['purchase.order'].create(purchase_order_data)
        
        self.transfer_state = 'request'
        self.need_to_purchase = False
        self.purchase_order_id = purchase_order.id
        self.crm_lead_id.crm_lead_state = 'purchase'
        return {
            'effect': {
            'fadeout': 'slow',
            'message': 'Compra(s) creada(s) con exito',
            'type': 'rainbow_man',
            }}


    def confirm_stock_pickings(self):
        if not self.purchase_order_id:
            return

        self.purchase_order_id.validate_stock_pickings()
        self.transfer_state = 'delivery'
        self.purchase_order_id.purchase_state = 'received'
        self.crm_lead_id.crm_lead_state = 'ready_to_repair'
        self.crm_lead_id.repair_state = 'confirmed'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
    
    def deliver_products_to_tech(self):
        if self.purchase_order_id or self.transfer_state != 'new':
            return
        self.transfer_state = 'delivery'
        self.crm_lead_id.crm_lead_state = 'ready_to_repair'
        self.crm_lead_id.repair_state = 'confirmed'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


