from odoo import api, fields, models


class StockTransferStatusLine(models.Model):
    _name = 'stock.transfer.status.line'
    _description = 'Stock Transfer Status Line'

    stock_transfer_status_id = fields.Many2one('stock.transfer.status', string="Estado de Almacen")
    product_id = fields.Many2one('product.product')
    
    