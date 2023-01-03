from odoo import models, fields, api

class RepairProductRequired(models.Model):
    _name = "repair.product.required"
    _description = "Productos Necesarios para Reparar"

    product_id = fields.Many2one('product.product', string='Producto', required=True)
    description = fields.Char(string='Nota para almacen')
    quantity = fields.Integer(string='Cantidad', required=True)
    product_qty_available = fields.Float(related='product_id.qty_available')
    crm_lead_id = fields.Many2one('crm.lead', string='Orden de Reparación')
    
    qty_to_order = fields.Float(string="Cantidad faltante", compute='_compute_qty_to_order', store=True)
    
    @api.depends('product_qty_available','quantity')
    def _compute_qty_to_order(self):
        for record in self:
            if record.product_qty_available > record.quantity:
                qty_to_order = 0
            else:
                qty_to_order = record.quantity - record.product_qty_available
            record.qty_to_order = qty_to_order