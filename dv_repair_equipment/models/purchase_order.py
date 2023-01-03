from odoo import models, fields, api, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    stock_transfer_status_id = fields.Many2one('stock.transfer.status', string="Orden de Reparación")
    purchase_state = fields.Selection([('in_process', 'En proceso de compra'), ('required', 'Requerimiento de Compra'), ('received', 'Compra Recibida')], string='Estado', default='required', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).purchase_state.selection]

    def validate_stock_pickings(self):
        self.ensure_one()
        if self.picking_ids:
            for picking in self.picking_ids:
                picking.action_assign()
                picking.action_confirm()
                for mv in picking.move_ids_without_package:
                    mv.quantity_done = mv.product_uom_qty
                picking.button_validate()

    def button_confirm(self):
        if self.purchase_state != 'in_process':
            return
        self.state = 'draft'
        res = super(PurchaseOrder, self).button_confirm()
        if self.stock_transfer_status_id:
            self.purchase_state = 'required'
            self.stock_transfer_status_id.transfer_state = 'income'
        return res

