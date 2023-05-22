# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

DEFAULT_PLE_DATA = '%(month)s%(day)s%(ple_id)s%(report_03)s%(operacion)s%(contenido)s%(moneda)s%(ple)s'
DEFAULT_FORMAT_DICT = {
	'header_format': {
		'bold': True,
		'text_wrap': True,
		'valign': 'top',
		'fg_color': '#D7E4BC',
		'border': 1,
	},
	'text_format': {
		'num_format': '@',
	},
}

def number_to_ascii_chr(n) :
	try :
		n = int(n)
	except :
		_logging.info('error en lineaaaaaaaaaaaaaa 52')
		n = 0
	digits = []
	if n > 0 :
		while n :
			digits.append(int(n % 26))
			n //= 26
	else :
		digits.append(0)
	digits = ''.join(chr(numero+65) for numero in digits[::-1])
	return digits

def get_last_day(day) :
	first_next = day.replace(day=28) + datetime.timedelta(days=4)
	return (first_next - datetime.timedelta(days=first_next.day))

def get_selection_name(env, model, field, value):
	return dict(env[model].fields_get(field, 'selection').get(field, {}).get('selection',{})).get(value)

class SolsePeCpeReport(models.Model):
	_name = 'solse.pe.cpe.report'
	_description =  "Reportes CPE"

	name = fields.Char('Nombre')
	company_id = fields.Many2one(comodel_name='res.company', string='Compañía', required=True, default=lambda self:self.env.user.company_id)
	reporte_nombre = fields.Char(string='Nombre del Excel')
	reporte_binary = fields.Binary(string='Excel', readonly=True)
	date_generated = fields.Datetime(string='Fecha de generación', readonly=True)
	fecha_inicio = fields.Date('Fecha de inicio', required=True)
	fecha_fin = fields.Date('Fecha Fin', required=True)
	factura_ids = fields.Many2many(comodel_name='account.move', string='Facturas', readonly=True)
	partner_id = fields.Many2one('res.partner', 'Contacto para envió')
	es_de_alerta = fields.Boolean('Es de Alerte', help="Es usado exclusivamente para informar de errores o inconsistencias en los comprobanes electronicos, los comprobantes con estado aceptado no seran tomados en cuenta")

	def update_report(self) :
		domain_company = []
		empresas = self.env['res.company'].sudo().search([])
		pais_id = self.env.ref('base.pe').id
		if len(empresas) > 1:
			domain_company = [('company_id','=',self.company_id.id), ('company_id.partner_id.country_id','=',pais_id)]
		
		lines = []
		if self.es_de_alerta:
			lines = [
				('is_cpe', '=', True),
				('state','in',['posted']),
				('estado_sunat','in',['01', '03', '07', '09']),
				('no_enviar_rnoaceptados', '=', False),
				('journal_id.type','in',['sale']),
			]
		else:
			lines = [
				('is_cpe', '=', True),
				('invoice_date','>=',str(self.fecha_inicio)),
				('invoice_date','<=',str(self.fecha_fin)),
				('state','in',['posted', 'annul', 'cancel']),
				('journal_id.type','in',['sale']),
			]
		paremtros_buscar = domain_company + lines
		lines = self.env[self.factura_ids._name].search(paremtros_buscar, order='invoice_date asc')
		self.factura_ids = lines

	def generate_report(self) :
		self.update_report()
		lines_to_write_01 = []
		lines = self.factura_ids.sudo()
		for move in lines :
			m = move.journal_id.type
			m_01 = []
			m_01.append(move.l10n_latam_document_number)
			m_01.append(move.currency_id.name)
			m_01.append(str(move.tipo_cambio or 1))
			m_01.append(str(move.amount_total))
			m_01.append(str(move.amount_untaxed_signed))
			
			m_01.append(str(move.amount_tax_signed))
			m_01.append(str(move.total_operaciones_exoneradas))
			m_01.append(str(move.total_operaciones_gratuitas))
			m_01.append(str(move.total_operaciones_inafectas))
			m_01.append(str(move.total_operaciones_exportadas))
			

			estado_sunat = get_selection_name(self.env, 'account.move', 'estado_sunat', move.estado_sunat or '01')
			m_01.append(estado_sunat or '')
			m_01.append(move.partner_id.display_name)
			m_01.append(move.partner_id.doc_number or '-')
			m_01.append(str(move.invoice_date))
			m_01.append('0000')
			estado = get_selection_name(self.env, 'account.move', 'state', move.state)
			m_01.append(estado)

			if m_01 :
				try :
					lines_to_write_01.append('|'.join(m_01))
				except Exception as e:
					raise UserError('Error: Datos no cumplen con los parámetros establecidos por SUNAT'+str(m_01))

		name_01 = "Reporte comprobantes electrónicos"
		lines_to_write_01.append('')
		txt_string_01 = '\r\n'.join(lines_to_write_01)
		dict_to_write = dict()
		if txt_string_01 :
			headers = [
				'Número de comprobante',
				'Moneda',
				'Tipo de Cambio',
				'Monto Total',
				'Monto sin Impuestos',
				'IGV',
				'Exoneradas',
				'Gratuitas',
				'Inafectas',
				'Exportación',
				'Estado Sunat',
				'Nombre de contacto - Cliente',
				'Número de RUC / DNI',
				'Fecha de factura / Recibo',
				'Sucursal',
				'Estado',
			]
			xlsx_file_base_64 = self._generate_xlsx_base64_bytes(txt_string_01, name_01[2:], headers=headers)
			dict_to_write.update({
				'reporte_binary': xlsx_file_base_64.encode(),
				'reporte_nombre': name_01 + '.xlsx',
			})
		else :
			dict_to_write.update({
				'reporte_binary': False,
				'reporte_nombre': False,
			})

		dict_to_write.update({
			'date_generated': str(fields.Datetime.now()),
		})
		res = self.write(dict_to_write)
		return res

	def _generate_xlsx_base64_bytes(self, txt_string, sheet_name, headers=[], custom_format_dict=dict()) :
		xlsx_file = BytesIO()
		xlsx_writer = pandas.ExcelWriter(xlsx_file, engine='xlsxwriter')
		df = pandas.read_csv(StringIO(txt_string), sep='|', header=None, dtype=str)
		df.to_excel(xlsx_writer, sheet_name, startrow=1, index=False, header=False)
		workbook  = xlsx_writer.book
		worksheet = xlsx_writer.sheets[sheet_name]
		format_dict = {k:workbook.add_format(v) for k,v in DEFAULT_FORMAT_DICT.items()}
		if custom_format_dict and isinstance(custom_format_dict, dict()) :
			for custom_format, custom_format_value in custom_format_dict.items() :
				format_dict.update({
					custom_format: workbook.add_format(custom_format_value),
				})
		len_headers = 0
		if headers and isinstance(headers, list) :
			len_headers = len(headers)
		for col_num, value in enumerate(df.columns.values) :
			col_name = number_to_ascii_chr(col_num)
			header_text = str(value)
			col_format = 'text_format'
			if len_headers :
				if col_num < len_headers :
					csv_file = headers[col_num]
					#csv_file = 'Header' or {'header_text': 'Header', 'col_format': 'format_name'}
					if not isinstance(csv_file, dict) :
						csv_file = {'header_text': str(csv_file)}
					if 'header_text' in csv_file :
						header_text = str(csv_file.get('header_text'))
					if 'col_format' in csv_file :
						col_format = str(csv_file.get('col_format'))
			if col_format not in format_dict :
				col_format = 'text_format'
			col_format = format_dict.get(col_format)
			csv_file = worksheet.write(0, col_num, header_text, format_dict.get('header_format'))
			csv_file = worksheet.set_column(':'.join([col_name, col_name]), max(25, len(header_text) // 2), col_format)
		xlsx_writer.save()
		xlsx_file_value = base64.b64encode(xlsx_file.getvalue()).decode()
		return xlsx_file_value

	# Tarea programada para enviar reporte de comprobantes
	def tp_enviar_reporte_comprobantes(self):
		registro = self.env['solse.pe.cpe.report'].search([('es_de_alerta', '=', False)], limit=1)
		current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		fecha = datetime.datetime.now()
		start = datetime.date(fecha.year, int(fecha.month), 1)
		end = get_last_day(start)

		if not registro:
			paramtros_busqueda = {
				'name': 'Reporte de comprobantes',
				'reporte_nombre': 'Reporte comprobantes',
				'fecha_inicio': str(start),
				'fecha_fin': str(end),
				'es_de_alerta': False,
			}
			registro = self.env['solse.pe.cpe.report'].create(paramtros_busqueda)
		else:
			registro.write({
				'fecha_inicio': str(start),
				'fecha_fin': str(end),
			})

		registro.generate_report()
		registro.enviar_mensaje()

	# Tarea programada para enviar reporte de comprobantes con estado rechazado u observado
	def tp_enviar_reporte_comprobantes_no_aceptados(self):
		registro = self.env['solse.pe.cpe.report'].search([('es_de_alerta', '=', True)], limit=1)
		current_offset = fields.Datetime.context_timestamp(self, fields.Datetime.now()).utcoffset()
		fecha = datetime.datetime.now()
		start = datetime.date(fecha.year, int(fecha.month), 1)
		end = get_last_day(start)

		if not registro:
			paramtros_busqueda = {
				'name': 'Reporte de comprobantes',
				'reporte_nombre': 'Reporte comprobantes',
				'fecha_inicio': str(start),
				'fecha_fin': str(end),
				'es_de_alerta': True,
			}
			registro = self.env['solse.pe.cpe.report'].create(paramtros_busqueda)
		else:
			registro.write({
				'fecha_inicio': str(start),
				'fecha_fin': str(end),
			})

		registro.generate_report()
		registro.enviar_mensaje()

	def enviar_mensaje(self):
		if not self.partner_id.email:
			return
		account_mail = self.obtener_datos_correo()
		context = account_mail.get('context')
		if not context:
			return
		template_id = account_mail['context'].get('default_template_id')
		if not template_id:
			return
		attachment_ids = []
		if context.get('default_attachment_ids', False):
			for attach in context.get('default_attachment_ids'):
				attachment_ids += attach[2]

		mail_id = self.env['mail.template'].browse(template_id)
		mail_id.send_mail((self.id), force_send=True, email_values={'attachment_ids': attachment_ids})

	def obtener_archivos_cpe(self):
		attachment_ids = []
		Attachment = self.env['ir.attachment']
		attach = {}
		attach['name'] = self.reporte_nombre
		attach['type'] = 'binary'
		attach['datas'] = self.reporte_binary
		attach['res_model'] = 'mail.compose.message'
		attachment_id = self.env['ir.attachment'].create(attach)
		attachment_ids = []
		attachment_ids.append(attachment_id.id)
			
		return attachment_ids

	def obtener_datos_correo(self):
		self.ensure_one()
		ir_model_data = self.env['ir.model.data']
		try:
			template_id = ir_model_data.get_object_reference('solse_pe_cpe_report', 'cpe_envio_estado_email')[1]
		except ValueError:
			template_id = False
		try:
			compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
		except ValueError:
			compose_form_id = False

		attachment_ids = self.obtener_archivos_cpe()

		ctx = {
			'default_model': 'solse.pe.cpe.report',
			'default_res_id': self.ids[0],
			'default_use_template': bool(template_id),
			'default_template_id': template_id,
			'default_composition_mode': 'comment',
			'default_attachment_ids': [(6, 0, attachment_ids)],
			#'custom_layout': "sale.mail_template_data_notification_email_sale_order",
			'force_email': True
		}
		return {
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form_id, 'form')],
			'view_id': compose_form_id,
			'target': 'new',
			'context': ctx,
		}


