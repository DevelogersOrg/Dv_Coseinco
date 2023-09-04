from odoo import models, fields, api, _
from datetime import datetime

class report_time(models.Model):
    _name = 'report.time'

    name = fields.Char(string='TICKET/PROCESO')
    module = fields.Char(string='MODULO')
    stage = fields.Char(string='ETAPA')
    start_date = fields.Datetime(string='FECHA/HORA INICIO')
    end_date = fields.Datetime(string='FECHA/HORA FIN')
    time = fields.Float(string='TIEMPO EFECTIVO', digits = (3,2) , compute= '_compute_time', store=True)
    user_id = fields.Many2one('res.users', string='USUARIO')
    status = fields.Char(string='STATUS')

    @api.depends('start_date', 'end_date')
    def _compute_time(self):
        for record in self:
            if record.start_date and record.end_date:
                start_date = fields.Datetime.from_string(record.start_date)
                end_date = fields.Datetime.from_string(record.end_date)
                record.time = (end_date - start_date).total_seconds() / 60.0
            else:
                record.time = 0.0

    #Boton de reporte de Atención al Cliente
    def download_time_excel_report(self):
        #Llamo a la funcion que genera el reporte
        selected_invoices = self.env['report.time'].browse(self.env.context.get('active_ids', []))
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
        
        name_sheet = 'Reporte Tiempos '
        title = 'REPORTE - TIEMPOS'
        index = 0
        #Header
        headers = [('TICKET/PROCESO'),('MODULO'),('ETAPA'),('FECHA/HORA INICIO'),
                   ('FECHA/HORA FINAL'),('TIEMPO EFECTIVO'),('USUARIO ENCARGADO'),('STATUS')]
        #Genero la data de las facturas seleccionadas
        data=[]
        for invoice in selected_invoices:
            start_date = invoice.start_date.strftime('%d/%m/%Y %H:%M:%S') if invoice.start_date else ''
            end_date = invoice.end_date.strftime('%d/%m/%Y %H:%M:%S') if invoice.end_date else ''
            data.append([invoice.name, invoice.module, invoice.stage, start_date,
                         end_date, invoice.time, invoice.user_id.name, invoice.status])
        
        #Genero el reporte
        report_content = self.env['report.excel'].generate_invoice_excel_report(title, name_sheet, headers, data, first_date, last_date)
        date = datetime.now().strftime('%d/%m/%Y')
        file_name = f'Reporte_Coseinco_Tiempos_{date}.xlsx'
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
