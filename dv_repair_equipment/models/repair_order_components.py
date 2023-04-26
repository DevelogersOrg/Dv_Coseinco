from odoo import models, fields, api

class RepairOrderComponents(models.Model):
    _name = 'repair.order.components'
    _description = 'Componentes del Producto, para la Orden de Reparación'

    product_id = fields.Many2one('product.product', string='Producto', required=True)
    details = fields.Text(string='Detalles')
    quantity = fields.Integer(string='Cantidad', required=True, default=1)
    crm_lead_id = fields.Many2one('crm.lead', string='Orden de Reparación')