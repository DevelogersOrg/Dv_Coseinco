# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning

import base64
import datetime
from io import StringIO, BytesIO
import pandas
import logging
_logging = logging.getLogger(__name__)

class SolsePeCpeDescargar(models.Model):
	_name = 'solse.pe.cpe.descargar'
	_description = "Descargar CPE's"

	name = fields.Char('Nombre')
	datas_zip_fname = fields.Char("Nombre de archivo zip",  readonly=True)
	datas_zip = fields.Binary("Datos Zip", readonly=True)