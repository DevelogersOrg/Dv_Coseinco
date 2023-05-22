# -*- coding: utf-8 -*-

from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, Warning
import logging
from collections import defaultdict
from odoo.tools.misc import formatLang, format_date, get_lang
import re
_logging = logging.getLogger(__name__)

TYPE2JOURNAL = {
	'out_invoice':'sale', 
	'in_invoice':'purchase',  
	'out_refund':'sale', 
	'in_refund':'purchase'
}
 
class AccountMove(models.Model):
	_inherit = 'account.move'

	amount_text = fields.Char("Monto en letras", compute="_get_amount_text")
	is_cpe = fields.Boolean('Es CPE', related='l10n_latam_document_type_id.is_cpe', store=True)
	usar_prefijo_personalizado = fields.Boolean('Personalizar prefijo', related='l10n_latam_document_type_id.usar_prefijo_personalizado', store=True)
	pe_sunat_transaction51 = fields.Selection('_get_pe_sunat_transaction51', string='Tipo de transacción de Sunat', default='0101', readonly=True, states={'draft': [('readonly', False)]})

	moneda_base = fields.Many2one('res.currency', related="company_id.currency_id", store=True, string="Moneda base")
	monto_base_detraccion = fields.Float(string='Monto base detracción', related="company_id.monto_detraccion", store=True)
	
	cuenta_detraccion = fields.Many2one('account.journal', related='company_id.cuenta_detraccion')
	nro_cuenta_detraccion = fields.Char('Cuenta de detracción', compute='_compute_cuenta_detraccion')

	tiene_detraccion = fields.Boolean('Tiende detracción', compute="_compute_detraccion_retencion", store=True)
	detraccion_id = fields.Selection("_get_pe_type_detraccion", string="Detracción", compute="_compute_detraccion_retencion", store=True)
	porc_detraccion = fields.Float(string='% Detracción', compute="_compute_detraccion_retencion", store=True)
	monto_detraccion = fields.Monetary('Monto detracción S/', currency_field='moneda_base', compute="_compute_detraccion_retencion", store=True)
	monto_detraccion_base = fields.Monetary('Monto detracción', currency_field='currency_id',compute="_compute_detraccion_retencion", store=True)

	tiene_retencion = fields.Boolean(string='Tiene retención', compute="_compute_detraccion_retencion", store=True)
	porc_retencion = fields.Float(string='% Retención', related="company_id.por_retencion", store=True)
	monto_retencion = fields.Monetary(string='Monto retención S/', currency_field='moneda_base', compute="_compute_detraccion_retencion", store=True)
	monto_retencion_base = fields.Monetary(string='Monto retención', currency_field='currency_id', compute="_compute_detraccion_retencion", store=True, help="Monto en moneda que no es la base de la compañia")

	monto_neto_pagar = fields.Monetary(string="Neto Pagar S/", currency_field='moneda_base', compute="_compute_detraccion_retencion", store=True)
	monto_neto_pagar_base = fields.Monetary(string="Neto Pagar", currency_field='currency_id', compute="_compute_detraccion_retencion", store=True)

	annul = fields.Boolean('Anulado', readonly=True)
	state = fields.Selection(selection_add=[('annul', 'Anulado'), ], ondelete={'annul': 'cascade'})

	tipo_transaccion = fields.Selection([('contado', 'Contado'), ('credito', 'Credito')], string='Tipo de Transacción', default='contado')
	pe_branch_code = fields.Char("Codigo Sucursal", default="0000")
	sub_type = fields.Selection([('sale', 'Venta'), ('purchase', 'Compras')], compute="_compute_sub_type", store=True)

	amount_by_group_sunat = fields.Char("Ha eliminar")

	def _compute_cuenta_detraccion(self):
		for reg in self:
			if reg.company_id.cuenta_detraccion and reg.company_id.cuenta_detraccion.bank_account_id:
				reg.nro_cuenta_detraccion =  reg.company_id.cuenta_detraccion.name +': '+ reg.company_id.cuenta_detraccion.bank_account_id.acc_number
			else:
				reg.nro_cuenta_detraccion = ''

	@api.depends('line_ids')
	def _compute_cuotas_pago(self):
		for invoice in self:
			invoice_date_due_vals_list = []
			for rec_line in invoice.line_ids.filtered(lambda l: l.account_internal_type=='receivable'):
				amount = rec_line.amount_currency
				invoice_date_due_vals_list.append(rec_line.id)
			
			invoice.lineas_cuotas_pago = [(6, 0, invoice_date_due_vals_list)]

	def obtener_cuotas_pago(self):
		invoice = self
		invoice_date_due_vals_list = []
		first_time = True
		for rec_line in invoice.line_ids.filtered(lambda l: l.account_internal_type=='receivable'):
			amount = rec_line.amount_currency
			if first_time and (invoice.monto_detraccion or invoice.monto_retencion):
				if invoice.currency_id.id == invoice.company_id.currency_id.id:
					amount -= (invoice.monto_detraccion + invoice.monto_retencion)
				else:
					amount -= (invoice.monto_detraccion_base + invoice.monto_retencion_base)
			first_time = False
			datos_json = {
				'amount': rec_line.move_id.currency_id.round(amount),
				'currency_name': rec_line.move_id.currency_id.name,
				'date_maturity': rec_line.date_maturity
			}
			invoice_date_due_vals_list.append(datos_json)

		return invoice_date_due_vals_list

	@api.depends('invoice_line_ids.product_id', 'amount_total', 'partner_id')
	def _compute_detraccion_retencion(self):
		_logging.info("_compute_detraccion_retencion: %s" % self)
		for reg in self:
			#_logging.info('datos de la detraccion')
			#_logging.info(reg.tiene_detraccion)
			datos = reg._validar_detraccion_retencion(False)
			reg.tiene_detraccion = datos['tiene_detraccion']
			reg.detraccion_id = datos['detraccion_id']
			reg.porc_detraccion = datos['porc_detraccion']
			monto_detraccion = datos['monto_detraccion']
			_logging.info("antes monto_detraccion")
			_logging.info(monto_detraccion)
			monto_detraccion = self.redondear_decimales(monto_detraccion)
			reg.monto_detraccion = monto_detraccion
			_logging.info(monto_detraccion)

			monto_detraccion_base = datos['monto_detraccion_base']
			
			# if self.currency_id:
			# 	_logging.info("self.move: %s" % self.name)
			# 	_logging.info("self.currency_id: %s" % self.currency_id)
			# 	_logging.info("self.currency_id: %s" % self.currency_id[0].id)
			# 	_logging.info("self.company_id.currency_id: %s" % self.company_id.currency_id.id)
			if reg.currency_id.id == reg.company_id.currency_id.id:
				monto_detraccion_base = self.redondear_decimales(monto_detraccion_base)
				reg.monto_detraccion_base = monto_detraccion_base
			else:
				monto_detraccion_base = self.redondear_decimales(monto_detraccion_base)
				reg.monto_detraccion_base = monto_detraccion_base

			reg.tiene_retencion = datos['tiene_retencion']
			monto_retencion = datos['monto_retencion']
			reg.monto_retencion = monto_retencion
			monto_retencion_base = datos['monto_retencion_base']
			reg.monto_retencion_base = monto_retencion_base

			monto_neto_pagar = abs(reg.amount_total_signed) - monto_detraccion - monto_retencion
			monto_neto_pagar_base = abs(reg.amount_total) - monto_detraccion_base - monto_retencion_base

			if reg.currency_id.id != reg.company_id.currency_id.id:
				reg.monto_neto_pagar = monto_neto_pagar
				reg.monto_neto_pagar_base = monto_neto_pagar_base
			else:
				reg.monto_neto_pagar = self.redondear_decimales_total(monto_neto_pagar)
				reg.monto_neto_pagar_base = self.redondear_decimales_total_base(monto_neto_pagar_base)

			if reg.tiene_detraccion:
				reg.pe_sunat_transaction51 = '1001'
			elif reg.pe_sunat_transaction51 == '1001':
				reg.pe_sunat_transaction51 = '0101'

	def redondear_decimales(self, monto):
		return round(monto, 0)

	def redondear_decimales_total(self, monto):
		return round(monto, 2)

	def redondear_decimales_total_base(self, monto):
		return round(monto, 2)

	@api.onchange('tiene_retencion')
	def _onchange_check_retencion(self):
		if self.tiene_retencion:
			reg = self
			datos = reg._validar_detraccion_retencion(True)
			reg.tiene_detraccion = datos['tiene_detraccion']
			reg.detraccion_id = datos['detraccion_id']
			reg.porc_detraccion = datos['porc_detraccion']

			monto_detraccion = datos['monto_detraccion']
			reg.monto_detraccion = self.redondear_decimales(monto_detraccion)

			monto_detraccion_base = datos['monto_detraccion_base']
			if self.currency_id.id == self.company_id.currency_id.id:
				reg.monto_detraccion_base = self.redondear_decimales(monto_detraccion_base)
			else:
				reg.monto_detraccion_base = monto_detraccion_base

			reg.tiene_retencion = datos['tiene_retencion']
			monto_retencion = datos['monto_retencion']
			reg.monto_retencion = monto_retencion
			monto_retencion_base = datos['monto_retencion_base']
			reg.monto_retencion_base = monto_retencion_base

			monto_neto_pagar = abs(reg.amount_total_signed) - monto_detraccion - monto_retencion
			monto_neto_pagar_base = abs(reg.amount_total) - monto_detraccion_base - monto_retencion_base

			if reg.currency_id.id != reg.company_id.currency_id.id:
				reg.monto_neto_pagar = monto_neto_pagar
				reg.monto_neto_pagar_base = monto_neto_pagar_base
			else:
				reg.monto_neto_pagar = self.redondear_decimales_total(monto_neto_pagar)
				reg.monto_neto_pagar_base = self.redondear_decimales_total_base(monto_neto_pagar_base)

			if reg.tiene_detraccion:
				reg.pe_sunat_transaction51 = '1001'
			elif reg.pe_sunat_transaction51[:2] != '02':
				reg.pe_sunat_transaction51 = '0101'
	
	def _get_l10n_latam_documents_domain(self):
		self.ensure_one()
		if self.move_type in ['out_refund', 'in_refund']:
			internal_types = ['credit_note']
		else:
			internal_types = ['debit_note', 'invoice']
		
		return [('internal_type', 'in', internal_types), ('country_id', '=', self.company_id.country_id.id), ('company_id', '=', self.company_id.id)]

	@api.depends('journal_id', 'partner_id', 'company_id', 'move_type')
	def _compute_l10n_latam_available_document_types(self):
		self.l10n_latam_available_document_type_ids = False
		for rec in self.filtered(lambda x: x.journal_id and x.l10n_latam_use_documents and x.partner_id):
			rec.l10n_latam_available_document_type_ids = self.env['l10n_latam.document.type'].search(rec._get_l10n_latam_documents_domain())

	@api.depends('amount_total')
	def _get_amount_text(self):
		for invoice in self:
			if invoice.amount_total<2 and invoice.amount_total>=1:
				currency_name = invoice.currency_id.singular_name or invoice.currency_id.plural_name or invoice.currency_id.name or ""
			else:
				currency_name = invoice.currency_id.plural_name or invoice.currency_id.name or ""
			fraction_name = invoice.currency_id.fraction_name or ""
			amount_text = invoice.currency_id.amount_to_text(invoice.amount_total)
			invoice.amount_text= amount_text

	@api.model
	def _get_pe_sunat_transaction51(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG51')

	def _validar_detraccion_retencion(self, forzar_retencion):
		datos_rpt = {
			"tiene_detraccion": False,
			"detraccion_id": False,
			"porc_detraccion": 0.0,
			"monto_detraccion": 0.0,
			"monto_detraccion_base": 0.0,
			"tiene_retencion": False,
			"monto_retencion": 0.0,
			"monto_retencion_base": 0.0,
		}
		if abs(self.amount_total_signed) < self.company_id.monto_detraccion or self.partner_id.doc_type != "6":
			return datos_rpt

		tiene_detraccion = False
		detraccion_id = False

		for linea in self.invoice_line_ids:
			if linea.product_id.aplica_detraccion:
				tiene_detraccion = True
				detraccion_id = linea.product_id.detraccion_id
		
		if tiene_detraccion:
			monto_detraccion = abs(self.amount_total_signed) * (detraccion_id.value / 100.0) if detraccion_id.value > 0 else 0.0
			#monto_detraccion = self.redondear_decimales(monto_detraccion)
			monto_detraccion_base = abs(self.amount_total) * (detraccion_id.value / 100.0) if detraccion_id.value > 0 else 0.0
			#monto_detraccion_base = round(monto_detraccion_base)
			
			#if self.currency_id.id == self.company_id.currency_id.id:
			#	monto_detraccion_base = self.redondear_decimales(monto_detraccion_base)
			datos_rpt = {
				"tiene_detraccion": True,
				"detraccion_id": detraccion_id.code,
				"porc_detraccion": detraccion_id.value,
				"monto_detraccion": monto_detraccion,
				"monto_detraccion_base": monto_detraccion_base,
				"tiene_retencion": False,
				"monto_retencion": 0.0,
				"monto_retencion_base": 0.0,
			}
			return datos_rpt

		if self.partner_id.buen_contribuyente:
			return datos_rpt

		monto_retencion = abs(self.amount_total_signed) * (self.porc_retencion / 100.0)
		monto_retencion = self.redondear_decimales(monto_retencion)
		monto_retencion_base = abs(self.amount_total) * (self.porc_retencion / 100.0)
		#monto_retencion_base = round(monto_retencion_base)
		if self.currency_id.id == self.company_id.currency_id.id:
			monto_retencion_base = self.redondear_decimales(monto_retencion_base)
		if self.company_id.agente_retencion and self.move_type in ['in_invoice', 'in_refund']:
			datos_rpt = {
				"tiene_detraccion": False,
				"detraccion_id": False,
				"porc_detraccion": 0.0,
				"monto_detraccion": 0.0,
				"monto_detraccion_base": 0.0,
				"tiene_retencion": True,
				"monto_retencion": monto_retencion,
				"monto_retencion_base": monto_retencion_base,
			}
		elif self.move_type in ['out_invoice', 'out_refund'] and (self.tiene_retencion or forzar_retencion):
			datos_rpt = {
				"tiene_detraccion": False,
				"detraccion_id": False,
				"porc_detraccion": 0.0,
				"monto_detraccion": 0.0,
				"monto_detraccion_base": 0.0,
				"tiene_retencion": True,
				"monto_retencion": monto_retencion,
				"monto_retencion_base": monto_retencion_base,
			}
		return datos_rpt


	@api.depends('move_type')
	def _compute_sub_type(self):
		for reg in self:
			if reg.move_type in TYPE2JOURNAL:
				reg.sub_type = TYPE2JOURNAL[reg.move_type]
			else:
				reg.sub_type = False

	@api.model
	def _get_pe_type_detraccion(self):
		return self.env['pe.datas'].get_selection("PE.CPE.CATALOG54")

	"""def _get_last_sequence_domain(self, relaxed=False):
		where_string, param = super()._get_last_sequence_domain(relaxed)
		#if self.is_cpe and self.is_sale_document() and self.l10n_latam_document_type_id:
		if (self.is_cpe or self.usar_prefijo_personalizado) and self.is_sale_document() and self.journal_id.l10n_latam_use_documents and self.l10n_latam_document_type_id:
			where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
			param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
		elif self.l10n_latam_document_type_id:
			where_string += " AND l10n_latam_document_type_id = %(l10n_latam_document_type_id)s"
			param['l10n_latam_document_type_id'] = self.l10n_latam_document_type_id.id or 0
			
		return where_string, param"""

	def button_annul(self):
		self.button_cancel()
		self.write({'annul': True, 'state': 'annul'})
		return True
