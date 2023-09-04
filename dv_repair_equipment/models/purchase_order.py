from odoo import models, fields, api, _
from datetime import timedelta
from datetime import datetime

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    stock_transfer_status_id = fields.Many2one('stock.transfer.status', string="Orden de Reparación")
    purchase_state = fields.Selection([('required', 'Requerimiento de Compra'), ('in_process', 'En proceso de compra'),
                                       ('received', 'Compra Recibida')], string='Estado', default='required', group_expand='_expand_states', index=True)

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).purchase_state.selection]

    def validate_stock_pickings(self):
        self.ensure_one()
        to_validate_pickings = self.picking_ids.filtered(lambda p: p.state != 'done')
        if to_validate_pickings:
            for picking in to_validate_pickings:
                picking.action_assign()
                picking.action_confirm()
                for mv in picking.move_ids_without_package:
                    mv.quantity_done = mv.product_uom_qty
                picking.button_validate()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def button_confirm(self):
        if self.purchase_state != 'required':
            return
        if self.stock_transfer_status_id.crm_lead_id.partner_id == self.partner_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No tan rápido!',
                    'message': 'El cliente de la orden de reparación no puede ser el mismo que el proveedor de la orden de compra',
                    'sticky': False,
                    'type': 'danger'}}

        super(PurchaseOrder, self).button_confirm()
        if self.stock_transfer_status_id:
            self.purchase_state = 'in_process'
            self.stock_transfer_status_id.transfer_state = 'income'
            self._onchange_client_state()
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    related_purchase_order_ids = fields.Many2many('purchase.order','purchase_order_purchase_order_rel','purchase_order_id','related_purchase_order_id', string="Ordenes de Compra Relacionadas")
    
    # def write(self, vals):
    #     """
    #         Si se modifica el campo de purchase_state, se modifican los estados de las ordenes de compra relacionadas
    #     """
    #     original_purchase_order_id = self.env['purchase.order'].search([('related_purchase_order_ids', 'in', self.id)])

    #     if 'purchase_state' in vals:
    #         if self.related_purchase_order_ids:
    #             self.related_purchase_order_ids.write({'purchase_state': vals['purchase_state']})
    #         elif original_purchase_order_id:
    #             original_purchase_order_id.write({'purchase_state': vals['purchase_state']})

    #     return super(PurchaseOrder, self).write(vals)
            
    related_buy_order_ids = fields.Many2many('purchase.order','related_buy_order_rel','rel_purchase_order_id', 
                                             string="Compra Relacionadas", domain="[('partner_id', '=', partner_id), ('id', '!=', id), ('purchase_state', '=', purchase_state),('related_buy_order_ids', '=', False),('stock_transfer_status_id', '!=', False)]")
    purchase_related = fields.Boolean(string='Tiene compra relacionada')
    
    #Comprobación de que tiene crm_lead_id

    #Dominio de ordenes de compra relacionadas
    # @api.onchange('related_buy_order_ids')
    def onchange_related_buy_order_ids(self):
        # Obtener las líneas de pedido de compra relacionadas previamente agregadas
        previous_related_lines = self.order_line.filtered(lambda line: line.related_purchase_order_line_id)

        # Obtener las líneas de pedido de compra relacionadas que ya no están presentes
        lines_to_remove = previous_related_lines - self.related_buy_order_ids.mapped('order_line').mapped('related_purchase_order_line_id')

        # Eliminar las líneas de pedido de compra relacionadas que ya no están presentes
        self.order_line -= lines_to_remove

        # Crear una lista temporal para almacenar las nuevas líneas de pedido de compra
        new_lines = []

        # Copiar las líneas de pedido de compra de los pedidos relacionados
        for buy_order in self.related_buy_order_ids:
            for line in buy_order.order_line:
                # Verificar si la línea ya ha sido agregada previamente
                if line.related_purchase_order_line_id not in previous_related_lines:
                    vals = {
                        'order_id': self.id,
                        'product_id': line.product_id.id,
                        'name': line.name,
                        'product_qty': line.product_qty,
                        'price_unit': line.price_unit,
                        'product_uom': line.product_uom.id,
                        'date_planned': line.date_planned,
                        'related_purchase_order_line_id': line.id,
                    }
                    new_lines.append((0, 0, vals))

        # Agregar todas las líneas de pedido de compra a self.order_line
        self.order_line = new_lines

    # @api.onchange('related_buy_order_ids')
    # def onchange_purchase_related(self):
    #     if self.related_buy_order_ids:
    #         self.purchase_related = True
    #     else:
    #         self.purchase_related = False
            
    def write(self, vals):
        # Obtener el estado anterior de la compra original
        previous_purchase_state = self.purchase_state
        previous_transfer_state = self.stock_transfer_status_id.transfer_state

        # Actualizar el estado de la compra original
        res = super(PurchaseOrder, self).write(vals)

        # Verificar si el estado ha cambiado
        if 'purchase_state' in vals and self.purchase_state != previous_purchase_state:
            # Actualizar el estado de las compras relacionadas
            for related_order in self.related_buy_order_ids:
                related_order.write({'purchase_state': self.purchase_state})
        
        if previous_transfer_state == 'request':
            for related_order in self.related_buy_order_ids:
                related_order.stock_transfer_status_id.write({'transfer_state': 'income'})
        
        if 'purchase_state' in vals and vals['purchase_state'] == 'in_process':
            for related_order in self.related_buy_order_ids:
                related_order.start_date = fields.Datetime.now()
            self.start_date = fields.Datetime.now()

        if 'purchase_state' in vals and vals['purchase_state'] == 'received':
            for related_order in self.related_buy_order_ids:
                related_order.end_date = fields.Datetime.now()
            self.end_date = fields.Datetime.now()
        return res
    
    #Boton de reporte de Atención al Cliente
    def download_purchase_excel_report(self):
        #Llamo a la funcion que genera el reporte
        selected_invoices = self.env['purchase.order'].browse(self.env.context.get('active_ids', []))
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
        
        name_sheet = 'Gestión Compras'
        title = 'REPORTE - COMPRAS'
        index = 0
        #Header
        headers = [('N°'),('TICKET/PROCESO'),('PROVEEDOR'),('ETAPA'),('FECHA/HORA INICIO'),
                   ('FECHA/HORA FINAL'),('IMPORTE'),('USUARIO ENCARGADO'),('SITUACIÓN')]
        #Genero la data de las facturas seleccionadas
        data=[]
        for invoice in selected_invoices:
            index += 1
            start_date = invoice.start_date.strftime('%d/%m/%Y %H:%M:%S') if invoice.start_date else ''
            end_date = invoice.end_date.strftime('%d/%m/%Y %H:%M:%S') if invoice.end_date else ''
            data.append([index, invoice.stock_transfer_status_id.display_name, invoice.partner_id.name,
                        invoice.purchase_state_t.get(invoice.purchase_state), start_date, end_date, invoice.amount_total,invoice.write_uid.name,
                        invoice.ticket_state_t.get(invoice.ticket_state)])
        
        #Genero el reporte
        report_content = self.env['report.excel'].generate_invoice_excel_report(title, name_sheet, headers, data, first_date, last_date)
        date = datetime.now().strftime('%d/%m/%Y')
        file_name = f'Reporte_Coseinco_Compras_{date}.xlsx'
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
    
    #Campo de estado de ticket para reporte
    ticket_state = fields.Selection([('open', 'Abierto'),('closed', 'Cerrado')], string='Estado de ticket', compute='_compute_ticket_state')

    @api.depends('purchase_state')
    def _compute_ticket_state(self):
        for move in self:
            if move.purchase_state == 'received':
                move.ticket_state = 'closed'
            else:
                move.ticket_state = 'open'
    
    #Verificación de cambio de etapa
    def _onchange_client_state(self):
        report_time = self.env['report.time']
        module = 'Compras'
        
        if self.purchase_state == 'in_process':
            status = 'Abierto'
            preview_ticket = report_time.search([('name', '=', self.stock_transfer_status_id.name),('stage', '=', 'request')], limit=1)
            if preview_ticket:
                preview_ticket.write({
                    'end_date': datetime.now(),
                    'status': 'Cerrado'
                })
                self.env['crm.lead']._create_report_time_record(self.stock_transfer_status_id.name, module, self.purchase_state, self.write_uid.id, status)
    
    #Fechas de inicio y fin de etapa
    start_date = fields.Datetime(string='Fecha/Hora Inicio')
    end_date = fields.Datetime(string='Fecha/Hora Final')

    #Diccionario de tradcciones
    purchase_state_t = {
        'required': 'Requerimiento de Compra',
        'in_process': 'En proceso de compra',
        'received': 'Compra Recibida'
    }

    ticket_state_t = {
        'open': 'Abierto',
        'closed': 'Cerrado'
    }
