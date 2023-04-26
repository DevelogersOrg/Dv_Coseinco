from odoo import api, fields, models

class RepairObservationDetail(models.Model):
  _name = 'repair.observation.detail'

  crm_lead_id = fields.Many2one('crm.lead')
  name = fields.Char(string="Observación", required=True)
  date_of_observation = fields.Datetime(string="Fecha de observación", default=fields.Datetime.now, readonly=True)
  details = fields.Text(string="Detalles")