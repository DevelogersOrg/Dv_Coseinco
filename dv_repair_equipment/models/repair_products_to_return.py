from odoo import api, fields, models, _

class RepairProductsToReturn(models.Model):
    _name = 'repair.products.to.return'
    _description = 'Productos a devolver, para la Orden de Reparación'

    product_id = fields.Many2one('product.product', string='Producto', required=True)
    details = fields.Text(string='Detalles')
    quantity = fields.Integer(string="Cantidad", default=1)

    