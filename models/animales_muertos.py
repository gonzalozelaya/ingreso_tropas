from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AnimalesMuertos(models.Model):
    _name = 'animales.muertos'

    name = fields.Char('Nombre',compute='_compute_name')
    ingreso_id = fields.Many2one('ingreso.tropa', string='Ingreso')
    cantidad = fields.Integer(string='Cant.', required=True)
    # Relación con posible catálogo de tipos de hacienda
    tipo_hacienda_id = fields.Many2one('tipo.hacienda', string='Tipo de Hacienda',required = True)
    notas = fields.Text("Notas")

    @api.depends('tipo_hacienda_id','cantidad')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.tipo_hacienda_id.display_name} ({record.cantidad})"