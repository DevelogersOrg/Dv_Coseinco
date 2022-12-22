from odoo import models, fields, api

class RepairOrderComponents(models.Model):
    _name = 'repair.order.components'
    _description = 'Componentes del Producto, para la Orden de Reparación'

    name = fields.Char(string='Nombre', required=True)
    features = fields.Text(string='Características')
    details = fields.Text(string='Detalles')
    crm_lead_id = fields.Many2one('crm.lead', string='Orden de Reparación')