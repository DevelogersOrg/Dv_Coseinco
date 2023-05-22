# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from dateutil import parser

class ResPartner(models.Model):
	_inherit = 'res.partner'

	@api.model
	def obtener_direcciones(self, partner):
		partner_id = partner.get('id', False)
		child_ids = partner.get('child_ids', [])
		if partner_id:  # Modifying existing partner
			return [(st.id, st.name, st.street, st.country_id.id, st.state_id.id, st.city_id.id, st.l10n_pe_district.id, st.zip) for st in self.env['res.partner'].search([('id', 'in', child_ids)])] 
		return []

	@api.model
	def create_from_ui(self, partner):
		if partner.get('last_update', False):
			last_update = partner.get('last_update', False)
			if len(last_update) == 27:
				partner['last_update'] = fields.Datetime.to_string(
					parser.parse(last_update))
		if partner.get('is_validate', False):
			if partner.get('is_validate', False) == 'true':
				partner['is_validate'] = True
			else:
				partner['is_validate'] = False
		if not partner.get('state', False):
			partner['state'] = 'ACTIVO'
		if not partner.get('condition', False):
			partner['condition'] = 'HABIDO'
		if partner.get('doc_type', False) and partner.get('doc_type', False) == '6':
			partner['company_type'] = "company"
		if partner.get('l10n_latam_identification_type_id', False):
			partner['l10n_latam_identification_type_id'] = int(partner.get(
				'l10n_latam_identification_type_id'))
		res = super(ResPartner, self).create_from_ui(partner)
		return res