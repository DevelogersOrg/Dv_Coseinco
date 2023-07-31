from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    stock_transfer_status_id = fields.Many2one('stock.transfer.status', string="Orden de Reparación")
    purchase_state = fields.Selection([('required', 'Requerimiento de Compra'), ('in_process', 'En proceso de compra'),('received', 'Compra Recibida')], string='Estado', default='required', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).purchase_state.selection]

    def validate_stock_pickings(self):
        self.ensure_one()
        to_validate_pickings = self.picking_ids.filtered(lambda p: p.state != 'done')
        if to_validate_pickings:
            for picking in to_validate_pickings:
                picking.action_assign()
                picking.action_confirm()
                for mv in picking.move_ids_without_package:
                    mv.quantity_done = mv.product_uom_qty
                picking.button_validate()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_confirm(self):
        if self.purchase_state != 'required':
            return
        if self.stock_transfer_status_id.crm_lead_id.partner_id == self.partner_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No tan rápido!',
                    'message': 'El cliente de la orden de reparación no puede ser el mismo que el proveedor de la orden de compra',
                    'sticky': False,
                    'type': 'danger'}}

        super(PurchaseOrder, self).button_confirm()
        if self.stock_transfer_status_id:
            self.purchase_state = 'in_process'
            self.stock_transfer_status_id.transfer_state = 'income'
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    related_purchase_order_ids = fields.Many2many('purchase.order','purchase_order_purchase_order_rel','purchase_order_id','related_purchase_order_id', string="Ordenes de Compra Relacionadas")
    
    def write(self, vals):
        """
            Si se modifica el campo de purchase_state, se modifican los estados de las ordenes de compra relacionadas
        """
        original_purchase_order_id = self.env['purchase.order'].search([('related_purchase_order_ids', 'in', self.id)])

        if 'purchase_state' in vals:
            if self.related_purchase_order_ids:
                self.related_purchase_order_ids.write({'purchase_state': vals['purchase_state']})
            elif original_purchase_order_id:
                original_purchase_order_id.write({'purchase_state': vals['purchase_state']})

        return super(PurchaseOrder, self).write(vals)
            
    related_buy_order_ids = fields.Many2many('purchase.order','related_buy_order_rel','rel_purchase_order_id', 
                                             string="Compra Relacionadas", domain=[('purchase_state', '=', 'required'),('related_buy_order_ids', '=', False)])
    purchase_related = fields.Boolean(string='Tiene compra relacionada')

    # @api.onchange('related_buy_order_ids')
    def onchange_related_buy_order_ids(self):
        # Obtener las líneas de pedido de compra relacionadas previamente agregadas
        previous_related_lines = self.order_line.filtered(lambda line: line.related_purchase_order_line_id)

        # Obtener las líneas de pedido de compra relacionadas que ya no están presentes
        lines_to_remove = previous_related_lines - self.related_buy_order_ids.mapped('order_line').mapped('related_purchase_order_line_id')

        # Eliminar las líneas de pedido de compra relacionadas que ya no están presentes
        self.order_line -= lines_to_remove

        # Crear una lista temporal para almacenar las nuevas líneas de pedido de compra
        new_lines = []

        # Copiar las líneas de pedido de compra de los pedidos relacionados
        for buy_order in self.related_buy_order_ids:
            for line in buy_order.order_line:
                # Verificar si la línea ya ha sido agregada previamente
                if line.related_purchase_order_line_id not in previous_related_lines:
                    vals = {
                        'order_id': self.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.product_qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.product_uom.id,
                        'date_planned': line.date_planned,
                        'related_purchase_order_line_id': line.id,
                    }
                    new_lines.append((0, 0, vals))

        # Agregar todas las líneas de pedido de compra a self.order_line
        self.order_line = new_lines

    # @api.onchange('related_buy_order_ids')
    # def onchange_purchase_related(self):
    #     if self.related_buy_order_ids:
    #         self.purchase_related = True
    #     else:
    #         self.purchase_related = False
            
    def write(self, vals):
        # Obtener el estado anterior de la compra original
        previous_state = self.purchase_state

        # Actualizar el estado de la compra original
        res = super(PurchaseOrder, self).write(vals)

        # Verificar si el estado ha cambiado
        if 'purchase_state' in vals and self.purchase_state != previous_state:
            # Actualizar el estado de las compras relacionadas
            self.related_buy_order_ids.write({'purchase_state': self.purchase_state})

        return res