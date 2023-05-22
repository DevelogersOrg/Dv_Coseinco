# -*- coding: utf-8 -*-
from odoo import http, SUPERUSER_ID
import re
import logging
_logging = logging.getLogger(__name__)

class WebPeCpe(http.Controller):
	@http.route('/facturas/', type='http', auth='public', website=True)
	def render_cpe_page(self, **kw):
		if http.request.httprequest.method == 'POST':
			try:
				req = http.request.httprequest.values
				company_id = http.request.website.company_id
				doc_type = (not req.get('doc_type') or req.get('doc_type') == "-") and False or req.get('doc_type')
				doc_number = (not req.get('doc_number') or req.get('doc_number') == "-") and False or req.get('doc_number') or False
				num = req.get('number').split("-")
				if not req.get('number', False) and not re.match(r'^(B|F){1}[A-Z0-9]{3}\-\d+$', req.get('number')):
					return http.request.render('solse_pe_cpe_public.cpe_page_reponse', {'invoice': {'error': True}})
				partner_obj = http.request.env['res.partner']
				if doc_number and doc_type == '6':
					if not partner_obj.validate_ruc(doc_number):
						return http.request.render('solse_pe_cpe_public.cpe_page_reponse', {'invoice': {'error': True}})
				if doc_number and doc_type == '1':
					if len(doc_number) != 8:
						return http.request.render('solse_pe_cpe_public.cpe_page_reponse', {'invoice': {'error': True}})
				
				"""journal = http.request.env['account.journal'].sudo().search([('is_cpe', '=', True), ('sequence_id.prefix', '=', "%s-" % num[0]), ('pe_invoice_code', '=', req.get('document_type'))])
				if journal and len(journal) > 1:
					journal = http.request.env['account.journal'].sudo().search([('company_id', '=', company_id.id),('is_cpe', '=', True), ('sequence_id.prefix', '=', "%s-" % num[0]), ('pe_invoice_code', '=', req.get('document_type'))])
				if not journal or len(journal) > 1:
					return http.request.render('solse_pe_cpe_public.cpe_page_reponse', {'invoice': {'error': True}})
				number = str(int(num[1])).zfill(journal.sequence_id.padding)"""

				query_buscar = [('pe_invoice_code', '=', req.get('document_type')), ('partner_id.doc_type', '=', doc_type),
							('partner_id.doc_number', '=', doc_number), ('invoice_date', '=', req.get('date_invoice')),
							('name', 'ilike', "%s-%s" % (num[0], num[1])), ('amount_total', '=', req.get('amount_total')),
							('company_id.partner_id.vat', '=', company_id.vat)]

				invoice = http.request.env['account.move'].sudo().search(query_buscar)
				res = invoice and invoice.get_public_cpe() or {}
				return http.request.render('solse_pe_cpe_public.cpe_page_reponse', {'invoice': res})
			except Exception:
				return http.request.render('solse_pe_cpe_public.cpe_page_reponse', {'invoice': {'error': True}})
		return http.request.render('solse_pe_cpe_public.cpe_page', {})
