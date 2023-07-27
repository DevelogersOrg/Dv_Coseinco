from odoo import models, fields

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    related_account_move_line_id = fields.Many2one('account.move.line', string='Factura relacionada', ondelete='set null')
    number_id = fields.Integer(string='ID relacionada')