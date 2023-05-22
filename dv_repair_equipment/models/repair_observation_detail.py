from odoo import api, fields, models

class RepairObservationDetail(models.Model):
  _name = 'repair.observation.detail'

  crm_lead_id = fields.Many2one('crm.lead')
  name = fields.Char(string="Observación", required=True)
  details = fields.Text(string="Detalles")
  date_of_observation = fields.Datetime(string="Fecha de observación", readonly=True, default=fields.Datetime.now, store=True)

