# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_round
from datetime import datetime
from . import constantes
import logging

_logging = logging.getLogger(__name__)

class SaleOrder(models.Model):
	_inherit = "sale.order"

	orden_compra = fields.Char("Orden de compra")

	def _prepare_invoice(self):
		self.ensure_one()
		res = super(SaleOrder, self)._prepare_invoice()
		reg = self
		res['orden_compra'] = reg.orden_compra
		return res

	def _prepare_invoice(self):
		self.ensure_one()
		res = super(SaleOrder, self)._prepare_invoice()

		tipo_documento = self.env['l10n_latam.document.type']
		l10n_latam_document_type_id = False
		partner_id = self.partner_id.parent_id or self.partner_id
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

		return res

class SaleOrderLine(models.Model):
	_inherit = "sale.order.line"

	pe_affectation_code = fields.Selection(selection='_get_pe_reason_code', string='Tipo de afectación', default='10', help='Tipo de afectación al IGV')

	def _prepare_invoice_line(self, **optional_values):
		self.ensure_one()
		res = super(SaleOrderLine, self)._prepare_invoice_line()
		res['pe_affectation_code'] = self.pe_affectation_code
		return res

	@api.model
	def _get_pe_reason_code(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG7')

	@api.model
	def _get_pe_tier_range(self):
		return self.env['pe.datas'].get_selection('PE.CPE.CATALOG8')

	def _set_free_tax(self):
		if self.pe_affectation_code not in ('10', '20', '30', '40'):
			ids = self.tax_id.ids
			vat = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito']), ('id', 'in', ids)])
			self.discount = 100
			if not vat:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito'])], limit=1)
				self.tax_id = [(6, 0, ids + res.ids)]
		else:
			if self.discount == 100:
				self.discount = 0
			ids = self.tax_id.ids
			vat = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['gratuito']), ('id', 'in', ids)])
		if vat:
			res = self.env['account.tax'].search([('id', 'in', ids), ('id', 'not in', vat.ids)]).ids
			self.tax_id = [(6, 0, res)]

	@api.onchange('discount')
	def onchange_affectation_code_discount(self):
		for rec in self:
			if rec.discount != 100:
				pass
			elif rec.pe_affectation_code not in ['11', '12', '13', '14', '15', '16', '17', '21', '31', '32', '33', '34', '35', '36']:
				rec.pe_affectation_code = '11'

	@api.onchange('pe_affectation_code')
	def onchange_pe_affectation_code(self):
		# Catalogo 7
		# (10) Gravado - Operación Onerosa; ​(11) Gravado - Retiro por premio; ​(12) Gravado - Retiro por donación; ​ ​ 
		# (13) Gravado - Retiro;​ (14)​ Gravado - Retiro por publicidad; ​ (15) Gravado - Bonificaciones; ​(16)​ Gravado - Retiro por entrega a trabajadores
		if self.pe_affectation_code in ('10'):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['igv']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['igv']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['igv'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			self._set_free_tax()

		elif self.pe_affectation_code in ('11', '12', '13', '14', '15', '16', '17'):
			self.tax_id = [(6, 0, [])]
			self._set_free_tax()
		
		# (20) Exonerado - Operación Onerosa;
		elif self.pe_affectation_code in ('20'):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exonerado']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exonerado']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exonerado'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			self._set_free_tax()
		# (21) Exonerado – Transferencia gratuita
		elif self.pe_affectation_code in ('21'):
			self.tax_id = [(6, 0, [])]
			self._set_free_tax()
		# (30) Inafecto - Operación Onerosa; ​ ​ 
		elif self.pe_affectation_code in ('30'):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['inafecto']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['inafecto'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			#self.discount = 100
		# (31) Inafecto - Retiro por bonificación; ​ ​ (32) Inafecto - Retiro; ​ ​ 
		# (33) Inafecto - Retiro por muestras médicas; ​ ​ (34) Inafecto - Retiro por convenio colectivo; ​ ​ (35) Inafecto - Retiro por premio; ​ ​ 
		# (36) Inafecto - Retiro por publicidad
		elif self.pe_affectation_code in ('31', '32', '33', '34', '35', '36'):
			self.tax_id = [(6, 0, [])]
			self._set_free_tax()
			#self._set_free_tax()
		# (40) Exportación
		elif self.pe_affectation_code in ('40', ):
			ids = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exportacion']).ids
			res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exportacion']), ('id', 'in', ids)])
			if not res:
				res = self.env['account.tax'].search([('l10n_pe_edi_tax_code', '=', constantes.IMPUESTO['exportacion'])], limit=1)
			self.tax_id = [(6, 0, ids + res.ids)]
			self._set_free_tax()

	def set_pe_affectation_code(self):
		igv = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['igv'])
		if self.tax_id:
			if igv:
				if self.discount == 100:
					self.pe_affectation_code = '11'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '10'
		vat = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exonerado'])
		if self.tax_id:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '21'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '20'
		vat = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['inafecto'])
		if self.tax_id:
			if vat:
				if self.discount == 100:
					self.pe_affectation_code = '31'
					self._set_free_tax()
				else:
					self.pe_affectation_code = '30'
		vat = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code == constantes.IMPUESTO['exportacion'])
		if self.tax_id:
			if vat:
				self.pe_affectation_code = '40'

	@api.onchange('product_id')
	def _onchange_product_id(self):
		for rec in self.filtered(lambda x: x.product_id):
			rec.set_pe_affectation_code()

		self = self.with_context(check_move_validity=False)

	def get_price_unit(self, all=False):
		self.ensure_one()
		price_unit = self.price_unit
		if all:
			price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			tax_id = self.tax_id
		else:
			tax_id = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
		res = tax_id.with_context(round=False).compute_all(price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
		return res

	def get_price_unit_sunat(self, all=False):
		self.ensure_one()
		price_unit = self.price_unit
		if all:
			price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
			tax_id = self.tax_id
		else:
			tax_id = self.tax_id.filtered(lambda tax: tax.l10n_pe_edi_tax_code != constantes.IMPUESTO['gratuito'])
			
		res = tax_id.with_context(round=False).compute_all_sunat(price_unit, self.move_id.currency_id, 1, self.product_id, self.move_id.partner_id)
		return res
