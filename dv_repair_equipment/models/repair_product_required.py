from odoo import models, fields, api

class RepairProductRequired(models.Model):
    _name = "repair.product.required"
    _description = "Productos Necesarios para Reparar"

    product_id = fields.Many2one('product.product', string='Producto', required=True)
    description = fields.Char(string='Descripción')
    quantity = fields.Integer(string='Cantidad', required=True)
    crm_lead_id = fields.Many2one('crm.lead', string='Orden de Reparación')