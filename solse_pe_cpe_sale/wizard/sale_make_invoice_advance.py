# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class SaleAdvancePaymentInv(models.TransientModel):
	_inherit = "sale.advance.payment.inv"

	def _prepare_invoice_values(self, order, name, amount, so_line):
		res = super(SaleAdvancePaymentInv, self)._prepare_invoice_values(order, name, amount, so_line)
		tipo_documento = self.env['l10n_latam.document.type']
		l10n_latam_document_type_id = False
		partner_id = order.partner_id.parent_id or order.partner_id
		doc_type = partner_id.doc_type
		if not doc_type:
			return res
		if doc_type in '6':
			tipo_doc_id = tipo_documento.search([('code', '=', '01'), 
				('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id

		elif doc_type in '1':
			tipo_doc_id = tipo_documento.search([('code', '=', '03'), 
				('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id
		else:
			tipo_doc_id = tipo_documento.search([('code', '=', '03'), 
				('sub_type', '=', 'sale')], limit=1)
			if tipo_doc_id:
				l10n_latam_document_type_id = tipo_doc_id.id
		
		if l10n_latam_document_type_id:
			res['l10n_latam_document_type_id'] = l10n_latam_document_type_id

		res['pe_sunat_transaction51'] = '0102'
		return res

