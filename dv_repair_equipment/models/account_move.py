from odoo import models, fields, api, _
import base64
import logging
from odoo.exceptions import UserError
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
                                    string='Enlace cotizaciones', domain=[('state', '!=', 'draft'), ('treasury_state', '=', 'to_pay'), ('amount_untaxed_signed', '!=', '0')])
    
    
    @api.onchange('quotation_id')
    def _onchange_quotation_id(self):
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
                        'related_account_move_line_id': line._origin.id,
                        'amount_currency': line.amount_currency,
                        'currency_id': line.currency_id.id,
                    }
                    new_lines.append((0, 0, vals))
        _logger.info(f"new_lines: {new_lines}")
        self.invoice_line_ids = new_lines
        self._onchange_invoice_line_ids()