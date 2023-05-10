from odoo import api, fields, models

class RepairObservationDetail(models.Model):
  _name = 'repair.observation.detail'

  crm_lead_id = fields.Many2one('crm.lead')
  name = fields.Char(string="Observación", required=True)
  date_of_observation = fields.Datetime(string="Fecha de observación", readonly=True)
  details = fields.Text(string="Detalles")

  @api.model
  def create(self, vals):
      vals['date_of_observation'] = fields.Datetime.now()
      return super(RepairObservationDetail, self).create(vals)