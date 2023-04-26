from odoo import models, fields, api

class RepairEquipmentType(models.Model):
    _name = 'repair.equipment.type'
    _description = 'Tipo de Equipo a Reparar'

    name = fields.Char(string='Tipo de Equipo', required=True)