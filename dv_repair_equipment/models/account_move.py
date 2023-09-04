from odoo import models, fields, api, _
import base64
import logging
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.misc import formatLang, format_date, get_lang
from werkzeug.wrappers import Response
from odoo.http import request
from odoo.modules.module import get_module_resource
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    move_state = fields.Selection([('in_process', 'En Proceso'), ('tb_invoiced', 'Por Facturar'), (
        'invoiced', 'Facturado')], string='Estado', default='in_process', group_expand='_expand_states', index=True)
    crm_lead_id = fields.Many2one('crm.lead', string='Cotización')
    #crm_lead_client_state = fields.Selection(string='Estado de crm', related='crm_lead_id.client_state')
    
    client_id = fields.Many2one(
        'res.partner', string="Cliente", related='crm_lead_id.partner_id')
    repair_product_required_ids = fields.One2many(
        'repair.product.required', string='Productos necesitados', related='crm_lead_id.repair_product_required_ids')
    repair_order_components_ids = fields.One2many(
        'repair.order.components', string='Componentes', related='crm_lead_id.repair_order_components_ids')
    repair_observation_detail_ids = fields.One2many(
        'repair.observation.detail', string='Observaciones', related='crm_lead_id.repair_observation_detail_ids')
    equipment_failure_report = fields.Text(
        string='Reporte de falla', related='crm_lead_id.equipment_failure_report')
    initial_diagnosis = fields.Text(
        string='Diagnóstico inicial', related='crm_lead_id.initial_diagnosis')
    conclusion = fields.Text(
        string='Conclusión', related='crm_lead_id.conclusion')
    ready_to_invoice = fields.Boolean(string='Listo para facturar')

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).move_state.selection]

    def change_move_state(self):
        STATES = ['in_process', 'tb_invoiced', 'invoiced']
        self.move_state = STATES[STATES.index(
            self.move_state) + 1] if self.move_state != 'invoiced' else 'invoiced'
        if self.move_state == 'invoiced':
            self.create_invoice()
        self._onchange_client_state()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def create_invoice(self):
        self.ensure_one()
        self.ready_to_invoice = True

    # Tesoreria
    treasury_state = fields.Selection([('to_pay', 'Por Cobrar'), ('paid', 'Cobrado')],
                                      string='Estado de cobranza', default='to_pay', group_expand='_expand_treasury_states', index=True)

    def _expand_treasury_states(self, states, domain, order):
        return [key for key, val in type(self).treasury_state.selection]

    def action_treasury_state_pay(self):
        self.treasury_state = 'paid'
        self.payment_state = 'paid'
        self._onchange_treasury_state()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    # def action_post(self):
    #    res = super().sudo().action_post()
    #    return res

    quotation_terms_conditions_id = fields.Many2one(
        'quotation.terms.conditions', string='Términos y condiciones')
    quotation_time_period_for_payment_type_id = fields.Many2one(
        'quotation.time.period', string='Forma de pago')
    quotation_time_period_for_shipping_time_id = fields.Many2one(
        'quotation.time.period', string='Tiempo de entrega')
    quotation_time_period_for_guarantee_id = fields.Many2one(
        'quotation.time.period', string='Garantía')
    quotation_time_period_for_validity_id = fields.Many2one(
        'quotation.time.period', string='Validez de la cotización')

    quotation_related = fields.Boolean(string='Tiene cotización relacionada')
    
    def get_report_files(self):
        pdf = self.env.ref(
            'dv_repair_equipment.action_report_account_move')._render_qweb_pdf(self.id)[0]
        pdf_data = base64.b64encode(pdf)
        ir_attachment_ids = self.env['ir.attachment'].create({'name': 'Informe Técnico.pdf',
                                  'res_name': 'Informe Técnico.pdf',
                                  'datas': pdf_data})
        attachment_ids = ir_attachment_ids.ids
        default_attachment_ids = []
        for attachment in attachment_ids:
            default_attachment_ids.append((4, attachment))
        return default_attachment_ids

    def action_invoice_sent(self):
        res = super().action_invoice_sent()
        _logger.info(f"res['context'] 1: {res['context']}")
        if 'default_attachment_ids' in res['context']:
            new_default_attachment_ids = res['context']['default_attachment_ids'] + self.get_report_files()
        else:
            new_default_attachment_ids = self.get_report_files()
        vals = {'default_attachment_ids': new_default_attachment_ids}
        res['context'].update(vals)
        _logger.info(f"res['context'] 2: {res['context']}")
        return res

    #Enlace de cotizacion con factura
    quotation_id = fields.Many2many('account.move', 'account_move_account_move_rel','account_move_id','related_account_move_id', 
                                    string='Enlace cotizaciones', 
                                    domain="[('partner_id', '=', partner_id), ('id', '!=', id), ('move_state', '=', move_state), ('crm_lead_id', '!=', False), ('quotation_id', '=', False)]")
        
    #@api.onchange('quotation_id')
    def onchange_quotation_id(self):
        # Obtener las líneas de factura relacionadas previamente agregadas
        previous_related_lines = self.invoice_line_ids.filtered(lambda line: line.related_account_move_line_id)

        # Obtener las líneas de factura relacionadas que ya no están presentes
        lines_to_remove = previous_related_lines - self.quotation_id.mapped('invoice_line_ids').mapped('related_account_move_line_id')

        # Eliminar las líneas de factura relacionadas que ya no están presentes
        self.invoice_line_ids -= lines_to_remove

        # Crear una lista temporal para almacenar las nuevas líneas de factura
        new_lines = []

        # Copiar las líneas de factura de las cotizaciones relacionadas
        for quotation in self.quotation_id:
            for line in quotation.invoice_line_ids:
                # Verificar si la línea ya ha sido agregada previamente
                if line.related_account_move_line_id not in previous_related_lines:
                    vals = {
                        'account_id': line.account_id.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'quantity': line.quantity,
                        'price_unit': line.price_unit,
                        'discount': line.discount,
                        'price_subtotal': line.price_subtotal,
                        'price_total': line.price_total,
                        'debit': line.debit,
                        'credit': line.credit,
                        'tax_ids': [(6, 0, line.tax_ids.ids)],
                        'related_account_move_line_id': line.id,
                        #'number_id': line.ids[0],
                        'amount_currency': line.amount_currency,
                        'currency_id': line.currency_id.id,
                    }
                    new_lines.append((0, 0, vals))
        _logger.info(f"new_lines: {new_lines}")
        self.invoice_line_ids = new_lines
        self._onchange_invoice_line_ids()
        if self.quotation_id:
            self.quotation_related = True
        else:
            self.quotation_related = False
        _logger.info(f"new_lines: {new_lines}")
    
    # @api.onchange('quotation_id')
    # def onchange_quotation_related(self):
    #     if self.quotation_id:
    #         self.quotation_related = True
    #     else:
    #         self.quotation_related = False

    def name_get(self):
        result = []
        for move in self:
            if self._context.get('name_groupby'):
                name = '**%s**, %s' % (self.env['account.move'].format_date(move.date), move._get_move_display_name())
                if move.ref:
                    name += '     (%s)' % move.ref
                if move.partner_id.name:
                    name += ' - %s' % move.partner_id.name
            else:
                name = move._get_move_display_name(show_ref=True)
            if move.crm_lead_id:
                name = f"{move.crm_lead_id.display_name} / {name}"
            result.append((move.id, name))
        return result
    
    def write(self, vals):
        # Obtener el estado anterior de la compra original
        previous_move_state = self.move_state
        previous_treasury_state = self.treasury_state

        # Actualizar el estado de la compra original
        res = super(AccountMove, self).write(vals)

        # Verificar si el estado ha cambiado
        if 'move_state' in vals and self.move_state != previous_move_state:
            # Actualizar el estado de las Facturación relacionadas
            for related_quotation in self.quotation_id:
                related_quotation.write({'move_state': self.move_state})
        if 'treasury_state' in vals and previous_treasury_state == 'to_pay':
            # Actualizar el estado de Tesoreria
            for related_quotation in self.quotation_id:
                related_quotation.write({'treasury_state': 'paid'})
        return res
    
    # def compute_product_totals(self):
    #     for move in self:
    #         for line in move.invoice_line_ids:
    #             line.compute_product_totals()

    #Campo de estado de ticket para reporte
    ticket_move_state = fields.Selection([('open', 'Abierto'),('closed', 'Cerrado')], string='Estado de ticket', compute='_compute_ticket_state')
    ticket_treasury_state = fields.Selection([('open', 'Abierto'),('closed', 'Cerrado')], string='Estado de ticket', compute='_compute_ticket_state')
    @api.depends('move_state', 'treasury_state')
    def _compute_ticket_state(self):
        for move in self:
            if move.move_state == 'invoiced':
                move.ticket_move_state = 'closed'
            else:
                move.ticket_move_state = 'open'
            if move.treasury_state == 'paid':
                move.ticket_treasury_state = 'closed'
            else:
                move.ticket_treasury_state = 'open'

    #Boton para descargar el reporte de Facturación
    def download_invoice_excel_report(self):
        #Llamo a la funcion que genera el reporte
        selected_invoices = self.env['account.move'].browse(self.env.context.get('active_ids', []))
        #Datos de creación de registros
        if len(selected_invoices) > 1:
            sorted_invoices = sorted(selected_invoices, key=lambda x: x.create_date)
            last_date = sorted_invoices[0].create_date.strftime('%d/%m/%Y %H:%M:%S')
            first_date = sorted_invoices[-1].create_date.strftime('%d/%m/%Y %H:%M:%S')
        #Si solo hay un registro
        else:
            sorted_invoices = sorted(selected_invoices, key=lambda x: x.create_date)
            last_date = selected_invoices.create_date.strftime('%d/%m/%Y %H:%M:%S')
            first_date = last_date
        
        name_sheet = 'Gestion Facturacion'
        title = 'REPORTE - FACTURACION'
        index = 0
        #Header
        headers = [('N°'),('TICKET/PROCESO'),('BIEN/SERVICIO'),('CLIENTE '),('ETAPA'),('FECHA/HORA INICIO'),
                   ('FECHA/HORA FINAL'),('USUARIO ENCARGADO'),('COMPROBANTE'),('IMPORTE'),('SITUACIÓN')]
        #Genero la data de las facturas seleccionadas
        data=[]
        for invoice in selected_invoices:
            index += 1
            data.append([index, invoice.crm_lead_id.name, invoice.crm_lead_id.product_or_service,
                        invoice.partner_id.name, invoice.move_state,'','',invoice.crm_lead_id.repair_user_id.name,
                        invoice.invoice_origin,invoice.amount_total_signed,invoice.ticket_move_state])
        
        #Genero el reporte
        report_content = self.env['report.excel'].generate_invoice_excel_report(title, name_sheet, headers, data, first_date, last_date)
        date = datetime.now().strftime('%d/%m/%Y')
        file_name = f'Reporte_Coseinco_Facturacion_{date}.xlsx'
        # Create a new attachment
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',  # This indicates that it's a binary attachment
            'datas': report_content,
            'res_model': self._name,
            'res_id': 0,
        })

        # Return an action to download the attachment
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    
    #Boton para descargar el reporte de Tesoreria
    def download_treasury_excel_report(self):
        #Llamo a la funcion que genera el reporte
        selected_invoices = self.env['account.move'].browse(self.env.context.get('active_ids', []))
        #Datos de creación de registros
        if len(selected_invoices) > 1:
            sorted_invoices = sorted(selected_invoices, key=lambda x: x.create_date)
            last_date = sorted_invoices[0].create_date.strftime('%d/%m/%Y %H:%M:%S')
            first_date = sorted_invoices[-1].create_date.strftime('%d/%m/%Y %H:%M:%S')
        #Si solo hay un registro
        else:
            sorted_invoices = sorted(selected_invoices, key=lambda x: x.create_date)
            last_date = selected_invoices.create_date.strftime('%d/%m/%Y %H:%M:%S')
            first_date = last_date
        
        name_sheet = 'Gestion Cobranza'
        title = 'REPORTE - TESORERIA'
        index = 0
        #Header
        headers = [('N°'),('TICKET/PROCESO'),('BIEN/SERVICIO'),('CLIENTE '),('ETAPA'),('FECHA/HORA INICIO'),
                   ('FECHA/HORA FINAL'),('USUARIO ENCARGADO'),('COMPROBANTE'),('IMPORTE'),('SITUACIÓN')]
        #Genero la data de las facturas seleccionadas
        data=[]
        for invoice in selected_invoices:
            index += 1
            data.append([index, invoice.crm_lead_id.name, invoice.crm_lead_id.product_or_service,
                        invoice.partner_id.name, invoice.treasury_state,'','',invoice.invoice_user_id.name,
                        invoice.invoice_origin,invoice.amount_total_signed,invoice.ticket_treasury_state])
        
        #Genero el reporte
        report_content = self.env['report.excel'].generate_invoice_excel_report(title, name_sheet, headers, data, first_date, last_date)
        date = datetime.now().strftime('%d/%m/%Y')
        file_name = f'Reporte_Coseinco_Tesoreria_{date}.xlsx'
        # Create a new attachment
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',  # This indicates that it's a binary attachment
            'datas': report_content,
            'res_model': self._name,
            'res_id': 0,
        })

        # Return an action to download the attachment
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
    
    #Verificación de cambio de etapa Facturación
    def _onchange_client_state(self):
        report_time = self.env['report.time']
        module = 'Facturación'
        
        if self.move_state == 'invoiced':
            status = 'Cerrado'
            preview_ticket = report_time.search([('name', '=', self.crm_lead_id.name),('stage', '=', 'tb_invoiced')], limit=1)
            if preview_ticket:
                preview_ticket.write({
                    'end_date': datetime.now(),
                    'status': 'Cerrado'
                })
                self.env['crm.lead']._create_report_time_record(self.crm_lead_id.name, module, self.move_state, self.write_uid.id, status)
            preview_picking_ticket = report_time.search([('name', '=', self.crm_lead_id.name),('stage', '=', 'delivered')], limit=1)
            if preview_picking_ticket:
                preview_picking_ticket.write({
                    'end_date': datetime.now(),
                })

    #Verificación de cambio de etapa Tesoreria
    def _onchange_treasury_state(self):
        report_time = self.env['report.time']
        module = 'Tesoreria'
        if self.treasury_state == 'paid':
            status = 'Cerrado'
            preview_ticket = report_time.search([('name', '=', self.crm_lead_id.name),('stage', '=', 'to_pay')], limit=1)
            if preview_ticket:
                preview_ticket.write({
                    'end_date': datetime.now(),
                    'status': 'Cerrado'
                })
                self.env['crm.lead']._create_report_time_record(self.crm_lead_id.name, module, self.treasury_state, self.write_uid.id, status)