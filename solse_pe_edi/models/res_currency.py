# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from . import amount_to_text_es
from num2words import num2words
import math

class Currency(models.Model):
	_inherit = 'res.currency'
	
	singular_name = fields.Char("Nombre singular")
	plural_name = fields.Char("Nombre plural")
	fraction_name = fields.Char("Nombre de la fracción")
	show_fraction = fields.Boolean("Mostrar fracción")
	mostrar_monto_ingles = fields.Boolean("Mostrar en ingles")

	pe_currency_code = fields.Selection('_get_pe_invoice_code', "Currrency Code")

	@api.model
	def _get_pe_invoice_code(self):
		return self.env['pe.datas'].get_selection("PE.TABLA04")
	
	def amount_to_text(self, amount):
		self.ensure_one()
		if amount<2 and amount>=1:
				currency = self.singular_name or self.plural_name or self.name or ""
		else:
			currency = self.plural_name or self.name or ""
		sufijo = self.fraction_name or ""
		amount_text = amount_to_text_es.amount_to_text(amount, currency, sufijo, self.show_fraction) 
		return amount_text

	def amount_to_text_en(self, numero):
		self.ensure_one()
		numero = round(numero, 2)
		dec, ent = math.modf(numero)
		dec = round(dec, 2)
		dec = int(dec * 100)
		num_ent_letra = num2words(ent, lang='en', to='cardinal')
		moneda = 'AMERICAN DOLLARS'
		num_letra = num_ent_letra.upper().replace('-', ' ') + ' AND ' + str(dec).zfill(2) + '/100 ' + moneda
		return num_letra
