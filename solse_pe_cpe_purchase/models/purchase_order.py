# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from datetime import datetime
import logging

_logging = logging.getLogger(__name__)

class PurchaseOrder(models.Model):
	_inherit = "purchase.order"

	def _prepare_invoice(self):
		self.ensure_one()
		res = super(PurchaseOrder, self)._prepare_invoice()

		self.ensure_one()
		move_type = self._context.get('default_move_type', 'in_invoice')
		journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
		if not journal:
			raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

		partner_invoice_id = self.partner_id.address_get(['invoice'])['invoice']
		journal_id = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
		tipo_documento = self.env['l10n_latam.document.type']
		tipo_doc_id = tipo_documento.search([('code', '=', '01'), ('sub_type', '=', 'purchase')], limit=1)
		reg = self
		tipo_transaccion = 'contado'
		if reg.payment_term_id:
			tipo_transaccion = reg.payment_term_id.tipo_transaccion or 'contado'

		invoice_vals = {
			'ref': self.partner_ref or '',
			'move_type': move_type,
			'purchase_id': self.id,
			'journal_id': journal_id.id,
			'l10n_latam_document_type_id': tipo_doc_id.id,
			'narration': self.notes,
			'currency_id': self.currency_id.id,
			'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id,
			'partner_id': partner_invoice_id,
			'fiscal_position_id': (self.fiscal_position_id or self.fiscal_position_id.get_fiscal_position(partner_invoice_id)).id,
			'payment_reference': self.partner_ref or '',
			'partner_bank_id': self.partner_id.bank_ids[:1].id,
			'invoice_origin': self.name,
			'invoice_payment_term_id': self.payment_term_id.id,
			'invoice_line_ids': [],
			'company_id': self.company_id.id,
			'tipo_transaccion': tipo_transaccion,
		}
		res.update(invoice_vals)
		return res
