from odoo import models, fields

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    related_purchase_order_line_id = fields.Many2one('purchase.order.line', string='Compra relacionada', display_name='order_id')