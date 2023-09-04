from odoo import models, fields, api, _
from odoo.modules.module import get_module_resource
from datetime import datetime
import io
import os
import xlsxwriter
import base64

class report_excel(models.Model):
    _name = 'report.excel'
    #Reporte en Excel
    def generate_invoice_excel_report(self,title,name_sheet,headers,data,first_date,last_date):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(name_sheet)

        # Quitar las lineas de cuadricula
        worksheet.hide_gridlines(2)

        row = 8
        col = 1
        
        #Número de encabezados
        num_headers = len(headers)

        # Crear un formato para el titulo
        title_format = workbook.add_format({
            'bold': True,
            'font_name': 'Calibri',
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter',
        })

        # Set the title in the worksheet
        worksheet.merge_range('B3:I3', (title), title_format)
        
        #Text
        text_format = workbook.add_format({
            'bold': True,
            'font_name': 'Calibri',
            'font_size': 11,
        })
        worksheet.merge_range('B5:C5', ('Fecha Inicio:'), text_format)
        worksheet.merge_range('B7:C7', ('Fecha Fin:'), text_format)
        
        # Insertar la imagen en una celda
        worksheet.insert_image(1, num_headers-1, get_module_resource('dv_repair_equipment', 'static/src/img', 'coseinco.png'))

        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'font_name': 'Calibri',
            'font_size': 11,
            'align': 'center',
            'border': 1,
        })

        worksheet.merge_range(4,num_headers - 3, 4, num_headers, first_date, date_format)
        worksheet.merge_range(6,num_headers - 3, 6, num_headers, last_date, date_format)
        # Create a format for the header row
        header_format = workbook.add_format({
            'bold': True,
            'font_name': 'Calibri',
            'font_size': 11,
            'bg_color': '#002060',  # Blue background color
            'font_color': 'white',  # White font color
            'align': 'center',  # Center alignment
            'valign': 'vcenter',  # Vertical center alignment
            'border': 1,  # Add a border around each cell
        })

        # Headers
        headers = headers
        for header in headers:
            worksheet.write(row, col, header, header_format)
            col += 1

        # Create a format for the data rows with borders
        data_format = workbook.add_format({
            'font_name': 'Calibri',
            'font_size': 11,
            'align': 'center',  # Center alignment
            'valign': 'vcenter',  # Vertical center alignment
            'border': 1,  # Add a border around each cell
        })

        # Data
        for row_data in data:
            row += 1
            # Write the row data in a single line
            worksheet.write_row(row, 1, row_data, data_format)

        # Adjust column widths to content
        worksheet.set_column(1, len(headers), 19)

        workbook.close()
        output.seek(0)
        return base64.b64encode(output.read())