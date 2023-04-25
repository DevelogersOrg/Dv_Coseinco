# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).#

from odoo import api, fields, models, tools

class WebsiteFloatingWsp(models.Model):
	_name = 'website_floating_wsp'
	_description = 'Floating Whatsapp'

	name = fields.Char(string='Nombre', required=False)
	phone = fields.Char('Teléfono', required=True)
	message = fields.Char('Mensaje', default=' ', )
	position = fields.Selection([('left', 'Left'), ('right', 'Right')], default='left', String='Selection')
	margin = fields.Char('Margen (px)', default='21')
	margin_bottom = fields.Char('Margen inferior (px)', default='21')
	popup_message = fields.Char('Mensaje emergente', default=' ')
	show_popup = fields.Boolean('Mostrar ventana emergente', defaut=True,)
	auto_open_timeout = fields.Integer('Tiempo de espera de apertura automática', default=0, )
	header_title = fields.Char('Título del encabezado', default='Chat de WhatsApp', )
	size = fields.Char('Tamaño', default='72px',)
