# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class PosConfig(models.Model):
	_inherit = 'pos.config'
	
	# module_account
	# auto_open_invoice = fields.Boolean("Factura automática")

	iface_journals = fields.Boolean("Mostrar documentos de venta", help="Habilita el uso de documentos electrónicos desde el Punto de Venta", default=True)
	documento_venta_ids = fields.Many2many("l10n_latam.document.type", string="Documentos de venta", domain=[("sub_type", "=", "sale")])

class PosSession(models.Model):
	_inherit = 'pos.session'

	def _check_invoices_are_posted(self):
		unposted_invoices = self.order_ids.account_move.filtered(lambda x: x.state not in ['posted', 'annul', 'cancel'])
		if unposted_invoices:
			raise UserError(_('You cannot close the POS when invoices are not posted.\n'
							  'Invoices: %s') % str.join('\n',
														 ['%s - %s' % (invoice.name, invoice.state) for invoice in
														  unposted_invoices]))


	def compute_cash_balance(self):
		self._compute_cash_balance()