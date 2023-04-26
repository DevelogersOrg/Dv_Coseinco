from odoo import models, fields
class QuotationTermsConditions(models.Model):
    _name = 'quotation.terms.conditions'
    _description = 'Quotation Terms and Conditions'
    name = fields.Text(string='Términos y condiciones', required=True)