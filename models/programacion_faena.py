from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProgramacionFaena(models.Model):
    _name = 'programacion.faena'
    _description = 'Programación Diaria de Faena'
    _order = 'fecha desc, name desc'

    name = fields.Char(string='Referencia', readonly=True, default='Nuevo')
    fecha = fields.Date(string='Fecha', required=True, default=fields.Date.today)
    lineas_faena = fields.One2many('programacion.faena.linea', 'programacion_id', string='Líneas de Faena',readonly=True)
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('procesado', 'Procesado')
    ], string='Estado', default='borrador')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('programacion.faena') or 'Nuevo'
        return super(ProgramacionFaena, self).create(vals)

    def action_confirmar(self):
        self.write({'state': 'confirmado'})

    def action_abrir_wizard_agregar_linea(self):
        self.ensure_one()
        return {
            'name': 'Agregar Líneas de Faena',
            'type': 'ir.actions.act_window',
            'res_model': 'agregar.lineas.faena.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_programacion_id': self.id,
            }
        }

class ProgramacionFaenaLinea(models.Model):
    _name = 'programacion.faena.linea'
    _description = 'Líneas de Programación de Faena'
    _order = 'numero_inicio asc'

    programacion_id = fields.Many2one('programacion.faena', string='Programación', ondelete='cascade')
    numero_inicio = fields.Integer(string='N° Inicio', required=True)
    numero_final = fields.Integer(string='N° Final', required=True)
    cabezas = fields.Integer(string='Cabezas', required=True)
    tropa = fields.Char(string='N° Tropa', required=True)
    corral = fields.Char(string='Corral', required=True)
    tipo_hacienda_id = fields.Many2one('tipo.hacienda', string='Tipo de Hacienda',required = True)
    usuario_id = fields.Many2one('res.users', string='Usuario', required=True)
    codigo_usuario = fields.Char(string='Cód. Usuario', related='usuario_id.login', readonly=True)
    fecha = fields.Date(string='Fecha', related='programacion_id.fecha', readonly=True)