# -*- coding: utf-8 -*-

from odoo import fields, http, SUPERUSER_ID, tools, _
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

import logging
_logger = logging.getLogger(__name__)

"""class WebsiteSalControllerCPE(http.Controller):
	@http.route(['/shop/departamento_infos/<model("res.country.state"):departamento>'], type='json', auth="public", methods=['GET', 'POST'], website=True)
	def departamento_infos(self, departamento, mode, **kw):
		return dict(
			provincias=[(st.id, st.name, st.l10n_pe_code) for st in departamento.get_website_sale_privincias(mode=mode)],
		)

	@http.route(['/shop/provincia_infos/<model("res.city"):provincia>'], type='json', auth="public", methods=['GET', 'POST'], website=True)
	def provincia_infos(self, provincia, mode, **kw):
		return dict(
			distritos=[(st.id, st.name, st.code) for st in provincia.get_website_sale_distritos(mode=mode)],
		)

	@http.route(['/shop/buscar/<int:nro>/<string:type>'], type='json', auth="public", methods=['GET', 'POST'], website=True)
	def buscar_vat(self, nro, type, **kw):
		return dict(
			request.env['res.partner'].consulta_datos_simple(type, nro),
		)
"""
class WebsiteSaleCPE(WebsiteSale):

	@http.route(['/shop/address'], type='http', methods=['GET', 'POST'], auth="public", website=True, sitemap=False)
	def address(self, **kw):
		Partner = request.env['res.partner'].with_context(show_address=1).sudo()
		order = request.website.sale_get_order()

		redirection = self.checkout_redirection(order)
		if redirection:
			return redirection

		mode = (False, False)
		can_edit_vat = False
		def_country_id = order.partner_id.country_id
		values, errors = {}, {}

		partner_id = int(kw.get('partner_id', -1))

		# IF PUBLIC ORDER
		if order.partner_id.id == request.website.user_id.sudo().partner_id.id:
			mode = ('new', 'billing')
			can_edit_vat = True
			country_code = request.session['geoip'].get('country_code')
			if country_code:
				def_country_id = request.env['res.country'].search([('code', '=', country_code)], limit=1)
			else:
				def_country_id = request.website.user_id.sudo().country_id
		# IF ORDER LINKED TO A PARTNER
		else:
			if partner_id > 0:
				if partner_id == order.partner_id.id:
					mode = ('edit', 'billing')
					can_edit_vat = order.partner_id.can_edit_vat()
				else:
					shippings = Partner.search([('id', 'child_of', order.partner_id.commercial_partner_id.ids)])
					if partner_id in shippings.mapped('id'):
						mode = ('edit', 'shipping')
					else:
						return Forbidden()
				if mode:
					values = Partner.browse(partner_id)
			elif partner_id == -1:
				mode = ('new', 'shipping')
			else: # no mode - refresh without post?
				return request.redirect('/shop/checkout')

		# IF POSTED
		if 'submitted' in kw:
			pre_values = self.values_preprocess(order, mode, kw)
			errors, error_msg = self.checkout_form_validate(mode, kw, pre_values)
			post, errors, error_msg = self.values_postprocess(order, mode, pre_values, errors, error_msg)

			if errors:
				errors['error_message'] = error_msg
				values = kw
			else:
				partner_id = self._checkout_form_save(mode, post, kw)
				if mode[1] == 'billing':
					order.partner_id = partner_id
					#order.pe_invoice_code = post['pe_invoice_code'] or False
					order.pasar_variables_web(post)
					order.with_context(not_self_saleperson=True).onchange_partner_id()
					# This is the *only* thing that the front end user will see/edit anyway when choosing billing address
					order.partner_invoice_id = partner_id
					if not kw.get('use_same'):
						kw['callback'] = kw.get('callback') or \
							(not order.only_services and (mode[0] == 'edit' and '/shop/checkout' or '/shop/address'))
				elif mode[1] == 'shipping':
					order.partner_shipping_id = partner_id

				order.message_partner_ids = [(4, partner_id), (3, request.website.partner_id.id)]
				if not errors:
					ruta = kw.get('callback') or '/shop/confirm_order'
					rpt_r = request.redirect(ruta)
					return rpt_r

		country = 'country_id' in values and values['country_id'] != '' and request.env['res.country'].browse(int(values['country_id']))
		country = country and country.exists() or def_country_id
		country = (country or request.website.company_id.country_id)

		tipos_docs = request.env['l10n_latam.identification.type'].search([('country_id', '=', request.website.company_id.country_id.id)])
		domain_cpe = [('table_code', '=', "PE.TABLA10"), ('code', 'in', ['01', '03', '00'])]
		tipos_comprobantes = [{
			'id': '01', 'name': 'Factura'},
			{'id': '03', 'name': 'Boleta'},
			{'id': '11', 'name': 'Otro documento'}]

		ingresa = True if 'state_id' in values else False
		if 'state_id' in values:
			if type(values['state_id']) == str or type(values['state_id']) == int:
				provincias = request.env['res.country.state'].search([('id', '=', values['state_id'])], limit=1).get_website_sale_privincias() if 'state_id' in values else False
			else:
				provincias = values['state_id'].get_website_sale_privincias()
		else:
			provincias = False
		
		if 'city_id' in values:
			if type(values['city_id']) == str or type(values['city_id']) == int:
				distritos = request.env['res.city'].search([('id', '=', values['city_id'])], limit=1).get_website_sale_distritos() if 'city_id' in values else False
			else:
				distritos = values['city_id'].get_website_sale_distritos()
		else:
			distritos = False

		render_values = {
			'website_sale_order': order,
			'partner_id': partner_id,
			'mode': mode,
			'checkout': values,
			'can_edit_vat': can_edit_vat,
			'country': country,
			'countries': country.get_website_sale_countries(mode=mode[1]),
			"states": country.get_website_sale_states(mode=mode[1]),
			'error': errors,
			'callback': kw.get('callback'),
			'only_services': order and order.only_services,
			'tipos_docs': tipos_docs,
			'tipos_comprobantes': tipos_comprobantes,
			'provincias': provincias,
			'distritos': distritos,
		}
		return request.render("website_sale.address", render_values)

	@http.route(['/solse/departamento_infos/<model("res.country.state"):departamento>'], type='json', auth="public", methods=['POST'], website=True)
	def departamento_infos(self, departamento, mode, **kw):
		return dict(
			provincias=[(st.id, st.name, st.l10n_pe_code) for st in departamento.get_website_sale_privincias(mode=mode)],
		)

	@http.route(['/solse/provincia_infos/<model("res.city"):provincia>'], type='json', auth="public", methods=['POST'], website=True)
	def provincia_infos(self, provincia, mode, **kw):
		return dict(
			distritos=[(st.id, st.name, st.code) for st in provincia.get_website_sale_distritos(mode=mode)],
		)

	@http.route(['/solse/buscar/<int:nro>/<string:type>'], type='json', auth="public", methods=['POST'], website=True)
	def buscar_vat(self, nro, type, **kw):
		return dict(
			request.env['res.partner'].consulta_datos_simple(type, nro),
		)
	


	def checkout_form_validate(self, mode, all_form_values, data):
		# mode: tuple ('new|edit', 'billing|shipping')
		# all_form_values: all values before preprocess
		# data: values after preprocess
		error = dict()
		error_message = []

		# Required fields from form
		required_fields = [f for f in (all_form_values.get('field_required') or '').split(',') if f]
		# Required fields from mandatory field function
		required_fields += mode[1] == 'shipping' and self._get_mandatory_shipping_fields() or self._get_mandatory_billing_fields()
		# Check if state required
		country = request.env['res.country']
		if data.get('country_id'):
			country = country.browse(int(data.get('country_id')))
			if 'state_code' in country.get_address_fields() and country.state_ids:
				required_fields += ['state_id']

		# error message for empty required fields
		for field_name in required_fields:
			if not data.get(field_name):
				error[field_name] = 'missing'

		# email validation
		if data.get('email') and not tools.single_email_re.match(data.get('email')):
			error["email"] = 'error'
			error_message.append(_('Invalid Email! Please enter a valid email address.'))

		# vat validation
		"""Partner = request.env['res.partner']
		if data.get("vat") and hasattr(Partner, "check_vat"):
			if data.get("country_id"):
				data["vat"] = Partner.fix_eu_vat_number(data.get("country_id"), data.get("vat"))
			partner_dummy = Partner.new({
				'vat': data['vat'],
				'country_id': (int(data['country_id'])
							   if data.get('country_id') else False),
			})
			try:
				partner_dummy.check_vat()
			except ValidationError:
				error["vat"] = 'error'"""

		if [err for err in error.values() if err == 'missing']:
			error_message.append(_('Some required fields are empty.'+str(error)))

		return error, error_message

	def _checkout_form_save(self, mode, checkout, all_values):
		Partner = request.env['res.partner']
		if mode[0] == 'new':
			partner_existe = False
			if 'doc_number' in checkout:
				tipo_documento = request.env['l10n_latam.identification.type'].sudo().search([('id', '=', checkout['l10n_latam_identification_type_id'])], limit=1)
				if tipo_documento.l10n_pe_vat_code != '0':
					partner_existe = request.env['res.partner'].sudo().search([('l10n_latam_identification_type_id', '=', checkout['l10n_latam_identification_type_id']),('doc_number', '=', checkout['doc_number'])], limit=1)
			if partner_existe:
				partner_existe.sudo().write(checkout)
				partner_id = partner_existe.id
			else:
				partner_id = Partner.sudo().with_context(tracking_disable=True).create(checkout).id
		elif mode[0] == 'edit':
			partner_id = int(all_values.get('partner_id', 0))
			if partner_id:
				# double check
				order = request.website.sale_get_order()
				shippings = Partner.sudo().search([("id", "child_of", order.partner_id.commercial_partner_id.ids)])
				if partner_id not in shippings.mapped('id') and partner_id != order.partner_id.id:
					return Forbidden()
				Partner.browse(partner_id).sudo().write(checkout)
		return partner_id
	
		
	def values_postprocess(self, order, mode, values, errors, error_msg):
		new_values = {}
		authorized_fields = request.env['ir.model']._get('res.partner').get_authorized_fields('res.partner')#._get_form_writable_fields()
		for k, v in values.items():
			# don't drop empty value, it could be a field to reset
			if k in authorized_fields and v is not None:
				new_values[k] = v
			else:  # DEBUG ONLY
				if k not in ('field_required', 'partner_id', 'callback', 'submitted'): # classic case
					_logger.debug("website_sale postprocess: %s value has been dropped (empty or not writable)" % k)

		new_values['team_id'] = request.website.salesteam_id and request.website.salesteam_id.id
		new_values['user_id'] = request.website.salesperson_id and request.website.salesperson_id.id

		if request.website.specific_user_account:
			new_values['website_id'] = request.website.id

		if mode[0] == 'new':
			new_values['company_id'] = request.website.company_id.id

		lang = request.lang.code if request.lang.code in request.website.mapped('language_ids.code') else None
		if lang:
			new_values['lang'] = lang
		if mode == ('edit', 'billing') and order.partner_id.type == 'contact':
			new_values['type'] = 'other'
		if mode[1] == 'shipping':
			new_values['parent_id'] = order.partner_id.commercial_partner_id.id
			new_values['type'] = 'delivery'

		return new_values, errors, error_msg