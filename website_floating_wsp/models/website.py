# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).#

from odoo import api, fields, models, tools
import logging
_logger = logging.getLogger(__name__)

class Website(models.Model):
	_inherit = "website" 
	
	floating_wsp_id = fields.Many2one('website_floating_wsp', string="Tema de Whatsapp de botón flotante")

	phone = fields.Char('Teléfono', required=True, related='floating_wsp_id.phone')
	message = fields.Char('Mensaje', default=' ', related='floating_wsp_id.message')
	position = fields.Selection([('left', 'Left'), ('right', 'Right')], default='left', String='Posición', related='floating_wsp_id.position')
	margin = fields.Char(string='Margen (px)', default='21', related='floating_wsp_id.margin')
	margin_bottom = fields.Char(string='Margen inferior (px)', default='21', related='floating_wsp_id.margin_bottom')
	popup_message = fields.Char('Mensaje emergente', default=' ', related='floating_wsp_id.popup_message')
	show_popup = fields.Boolean('Mostrar ventana emergente', defaut=True, related='floating_wsp_id.show_popup')
	auto_open_timeout = fields.Integer('Tiempo de espera de apertura automática', default=0,  related='floating_wsp_id.auto_open_timeout')
	header_title = fields.Char('Título del encabezado', default='Chat de WhatsApp', related='floating_wsp_id.header_title')
	size = fields.Char('Tamaño', default='72px', related='floating_wsp_id.size')
