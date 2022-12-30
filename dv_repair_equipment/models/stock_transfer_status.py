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
        [('income', 'Ingreso de Respuestos'), ('request', 'Solicitud de Respuestos'), ('delivery', 'Entrega de Respuestos')],
        string='Estado', group_expand='_expand_transfer_states', index=True)
    picking_state = fields.Selection(
        [('tb_confirmed', 'Equipo a confirmar recepción'), ('confirmed', 'Recepción de Equipo Confirmado'), ('to_ship', 'Despacho Programado'), ('delivered', 'Entregado')],
        string='Estado', group_expand='_expand_picking_states', index=True)


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
    def _compute_need_to_purchase(self):
        if self.transfer_state != 'income':
            self.need_to_purchase = False

        for product in self.repair_product_required_ids:
            if product.qty_to_order > 0:
                self.need_to_purchase = True
                return
        
        self.need_to_purchase = False

    def create_purchase_orders(self):
        if not self.need_to_purchase:
            return
        
        products_to_buy = [product for product in self.repair_product_required_ids if product.qty_to_order > 0]

        for product in products_to_buy:
            purchase_order = {
                'partner_id': self.crm_lead_id.partner_id.id,
                'order_line': [(0, 0, {
                    'product_id': product.product_id.id,
                    'name': product.product_id.name,
                    'product_qty': product.qty_to_order,
                    'price_unit': product.product_id.list_price,
                    'product_uom': product.product_id.uom_id.id,
                    })],
            }
            self.env['purchase.order'].create(purchase_order)
        
        self.transfer_state = 'request'
        self.need_to_purchase = False

