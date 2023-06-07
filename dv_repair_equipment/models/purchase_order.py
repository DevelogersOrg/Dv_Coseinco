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
            
