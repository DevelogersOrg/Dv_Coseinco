# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from datetime import datetime
import pytz
import logging
from dateutil.parser import parse as parse_date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT

tz = pytz.timezone('America/Lima')
_logging = logging.getLogger(__name__)

class PosOrder(models.Model):
	_inherit = "pos.order"

	refund_order_id = fields.Many2one('pos.order', string="POS para el que esta factura es el crédito")
	refund_invoice_id = fields.Many2one('account.move', string="Factura para la que esta factura es el crédito")
	
	partner_shipping_id = fields.Many2one('res.partner', string='Dirección de entrega', readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Delivery address for current sales order.")
	payment_term_id = fields.Many2one('account.payment.term', string='Términos de pago')
	team_id = fields.Many2one('crm.team', 'Canal de ventas')
	sale_order_id = fields.Many2one('sale.order', string='Referencia del pedido', copy=False)
	pos_user_id = fields.Many2one(comodel_name='res.users', string='Vendedor POS', help="Persona que utiliza la caja registradora. Puede ser un relevista, un estudiante o un empleado interino.", default=lambda self: self.env.uid, states={'done': [('readonly', True)], 'invoiced': [('readonly', True)]})

	pe_credit_note_code = fields.Selection(selection="_get_pe_crebit_note_type", string="Código de nota de crédito")
	pe_invoice_type = fields.Selection([("annul", "Anular"), ("refund", "Nota de crédito")], "Tipo de factura")
	pe_motive = fields.Char("Razón de la nota de crédito")
	pe_license_plate = fields.Char("Placa", size=10)
	pe_invoice_date = fields.Datetime("Hora de la fecha de la factura", copy=False)

	l10n_latam_document_type_id = fields.Many2one('l10n_latam.document.type', string='Tipo de documento')
	number = fields.Char(string='Número', readonly=True, copy=False)
	invoice_sequence_number = fields.Integer(string='Secuencia de números de factura', readonly=True, copy=False)
	date_invoice = fields.Date("Fecha de la factura")

	@api.constrains("sale_order_id")
	def check_sale_order_id(self):
		for order in self:
			if order.sale_order_id:
				if self.search_count([('sale_order_id','=', order.sale_order_id.id)])>1:
					raise ValidationError(_('La orden de venta ya existe y viola la restricción de campo único'))
	
	def invoice_print(self):
		return self.account_move.action_invoice_print()

	def action_invoice_sent(self):
		res = self.account_move.sudo().action_invoice_sent()
		res['context']['res_id'] = res['context'].pop('default_res_id', False)
		return res
	
	def _prepare_invoice_vals(self):
		res = super(PosOrder, self)._prepare_invoice_vals()
		timezone = pytz.timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
		res['invoice_origin'] = self.sale_order_id.name or self.name
		res['partner_shipping_id'] = self.partner_shipping_id.id
		res['invoice_payment_term_id'] = self.payment_term_id.id
		res['fiscal_position_id'] = self.fiscal_position_id
		res['team_id'] = self.team_id.id
		res['invoice_date'] = self.date_invoice or self.date_order.astimezone(timezone).date()
		if not res.get('name') and res.get('move_type') == 'out_refund':
			res['name'] = '/'
		else:
			res['name'] = self.number

		res['pe_credit_note_code'] = self.pe_credit_note_code or False
		res['pe_invoice_date'] = self.pe_invoice_date or False
		if self.l10n_latam_document_type_id.id:
			res['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id
		

		if res.get('move_type') == 'out_refund':
			res['reversed_entry_id'] = self.refund_invoice_id.id
			doc_nota_credito = False
			if self.refund_invoice_id.l10n_latam_document_type_id and self.refund_invoice_id.l10n_latam_document_type_id.nota_credito:
				doc_nota_credito = self.refund_invoice_id.l10n_latam_document_type_id.nota_credito
			else:
				doc_nota_credito = self.env['l10n_latam.document.type'].search([('code', '=', '07')], limit=1)

			if doc_nota_credito:
				res['l10n_latam_document_type_id'] = doc_nota_credito.id

			
			if 'l10n_latam_document_type_id' not in res:
				doc_nota_credito = self.env['l10n_latam.document.type'].search([('code', '=', '07')], limit=1)
				res['l10n_latam_document_type_id'] = doc_nota_credito.id

		if self.pe_invoice_type == 'refund':
			res['ref'] = self.pe_motive or False
		return res

	def _prepare_invoice_line(self, line):
		line.set_pe_affectation_code();
		res = super()._prepare_invoice_line(line)
		res.update({
			'pe_affectation_code': line.pe_affectation_code,
		})
		if self.sale_order_id:
			res['sale_line_ids'] = [(6, 0, [line.order_line_id.id])]
		return res

	@api.model
	def _order_fields(self, ui_order):
		res = super(PosOrder, self)._order_fields(ui_order)
		res['pe_invoice_date'] = ui_order.get('pe_invoice_date', False)
		tipo_doc_venta = ui_order.get('l10n_latam_document_type_id', False)
		if tipo_doc_venta:
			res['l10n_latam_document_type_id'] = tipo_doc_venta
			res['to_invoice'] = True
		else:
			res['to_invoice'] = False
		reg_datetime = datetime.now(tz)
		fecha = reg_datetime.strftime("%Y-%m-%d")
		res['date_invoice'] = parse_date(ui_order.get('date_invoice', fecha)).strftime(DATE_FORMAT)
		return res

	@api.model
	def _get_pe_crebit_note_type(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG9")

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		super(PosOrder, self)._onchange_partner_id()
		self.ensure_one()
		if self.partner_id and self.env.context.get('force_pe_journal'):
			partner_id = self.partner_id.parent_id or self.partner_id
			tipo_documento = self.env['l10n_latam.document.type']
			if partner_id.doc_type in ["6"]:
				tipo_doc_id = tipo_documento.search([('code', '=', '01'), ('sub_type', '=', 'sale')], limit=1)
				if tipo_doc_id:
					self.l10n_latam_document_type_id = tipo_doc_id.id
			else:
				tipo_doc_id = tipo_documento.search([('code', '=', '03'), ('sub_type', '=', 'sale')], limit=1)
				if tipo_doc_id:
					self.l10n_latam_document_type_id = tipo_doc_id.id

	def action_pos_order_invoice(self):
		for order in self:
			"""if not self.config_id.module_account:
				return False"""
			if order.pe_invoice_type == 'annul':
				raise ValidationError(
					_("La factura fue cancelada, no puede crear una nota de crédito"))
		res = super(PosOrder, self).action_pos_order_invoice()
		for order_id in self.filtered(lambda x: x.account_move):
			if not order_id.number:
				order_id.number = order_id.account_move.name
		return res

	@api.model
	def _process_order(self, order, draft, existing_order):
		res = super()._process_order(order, draft, existing_order)
		if not res:
			return res
		order = self.browse(res)
		return res

	@api.model
	def create_from_ui(self, orders, draft=False):
		for i, order in enumerate(orders):
			if order.get('data', {}).get('l10n_latam_document_type_id') and not order.get('partial_payment'):
				orders[i]['to_invoice'] = True
			else:
				orders[i]['to_invoice'] = False
		return super(PosOrder, self).create_from_ui(orders, draft=draft)

	@api.model
	def generar_enviar_xml_cpe(self, datos):
		datos_rpt = []
		pos_order_id = datos.get('pos_order_id', False)
		for id_reg in pos_order_id:
			reg = self.env['pos.order'].search([('id', '=', id_reg)], limit=1)
			if not reg.account_move.pe_cpe_id:
				continue
			reg.account_move.pe_cpe_id.generate_cpe()
			if reg.account_move.company_id.pe_is_sync and reg.account_move.l10n_latam_document_type_id.is_synchronous:
				reg.account_move.pe_cpe_id.action_send()
			datos_rpt.append({'serie': reg.account_move.l10n_latam_document_number or reg.account_move.name, 'id_account_move': reg.account_move.id})
		return datos_rpt

	@api.model
	def generar_enviar_xml_cpe(self, datos):
		datos_rpt = []
		pos_order_id = datos.get('pos_order_id', False)
		for id_reg in pos_order_id:
			reg = self.env['pos.order'].search([('id', '=', id_reg)], limit=1)
			if reg.account_move.pe_cpe_id:
				reg.account_move.pe_cpe_id.generate_cpe()
				if reg.account_move.company_id.pe_is_sync and reg.account_move.l10n_latam_document_type_id.is_synchronous:
					reg.account_move.pe_cpe_id.action_send()

			datos_rpt.append({'serie': reg.account_move.l10n_latam_document_number or reg.account_move.name, 'id_account_move': reg.account_move.id})
		return datos_rpt

	def refund(self):
		res = super(PosOrder, self).refund()
		order_id = res.get("res_id", False)
		if not order_id:
			return res
		for order in self.browse([order_id]):
			order.refund_order_id = self.id
			order.refund_invoice_id = self.account_move.id
			order.pe_invoice_type = self.env.context.get("default_pe_invoice_type", False)
			if order.pe_invoice_type == 'annul' and order.refund_invoice_id:
				if order.refund_invoice_id.state == 'posted':
					#order.invoice_journal = order.session_id.config_id.journal_id.id
					_logging.info('anular la factura')
				else:
					raise ValidationError("No puedes cancelar la factura, debes crear una nota de crédito")
			else:
				"""invoice_journal = self.invoice_journal.credit_note_id or self.invoice_journal
				order.invoice_journal = invoice_journal.id or False"""
				_logging.info('crear nota de credito')
		return res

			

class PosOrderLine(models.Model):
	_inherit = "pos.order.line"
	
	tax_ids = fields.Many2many('account.tax', readonly=False)
	sequence = fields.Integer(string='Secuencia', default=10, readonly=True)
	origin = fields.Char(string='Documento fuente', readonly=True)
	#layout_category_id = fields.Many2one('sale.layout_category', string='Section', readonly=True)
	order_line_id = fields.Many2one('sale.order.line', string='Líneas de pedido', readonly=True)
	#analytic_tag_ids = fields.Many2many('account.analytic.tag', string='Analytic Tags')
	pe_affectation_code = fields.Selection(selection='_get_pe_reason_code', string='Tipo de afectación', default='10', help='Tipo de afectación al IGV')

	@api.model
	def _get_pe_reason_code(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG7')

	def set_pe_affectation_code(self):
		igv = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '1000')
		if self.tax_ids:
			if igv:
				if self.discount == 100:
					self.pe_affectation_code = '11'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '10'
		vat = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9997')
		if self.tax_ids:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '21'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '20'
		vat = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9998')
		if self.tax_ids:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '31'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '30'
		vat = self.tax_ids.filtered(lambda tax: tax.l10n_pe_edi_tax_code == '9995')
		if self.tax_ids:
			if vat:
				self.pe_affectation_code = '40'
	

class AccountMoveLine(models.Model):
	_inherit = "account.move.line"

	def reconcile(self):
		results = {}

		if not self:
			return results

		for line in self:
			if line.move_id.state != 'posted':
				return results

		res = super(AccountMoveLine, self).reconcile()
		return res