from odoo import models, fields, api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    client_state = fields.Selection([('new', 'Nuevo Ingreso'), ('assigned', 'Asignado para Diagnóstico'), ('dg_ready', 'Diagnostico Listo'), ('quoted', 'Cotizado'), ('confirmed', 'Confirmado'),], string='Estado', default='new', group_expand='_expand_states', index=True)

    repair_order_type_id = fields.Selection([('remote', 'Remoto'), ('in_person', 'Presencial'), ('workshop', 'Taller'), ('external', 'Externo')], string='Tipo de Servicio a Desarrollar', required=True, default='remote')
    mesage_client = fields.Text(string='Mensaje al Cliente')
    repair_order_id = fields.Many2one('repair.order', string='Orden de Reparación')

    name = fields.Char(
        'Asunto', index=True, required=True,
        compute='_compute_name', readonly=False, store=True)
    ticket_number = fields.Char(string='Número de Ticket', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('crm.lead'))
    partner_id = fields.Many2one(
        'res.partner', string='Cliente', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference."
        ,required=True)
    
    repair_user_id = fields.Many2one('res.users', string="Tecnico", default=lambda self: self.env.user, check_company=True, required=True)




    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).client_state.selection]


    def action_create_repair_order(self):
        self.env['repair.order'].create({'crm_lead_id': self.id, 'product_id': 5, 'name': self.name, 'product_uom': 1, 'location_id': 1})
    