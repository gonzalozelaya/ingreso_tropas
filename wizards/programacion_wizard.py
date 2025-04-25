from odoo import models, fields, api
from odoo.exceptions import ValidationError

class AgregarLineasFaenaWizard(models.TransientModel):
    _name = 'agregar.lineas.faena.wizard'
    _description = 'Wizard para agregar líneas de faena'

    programacion_id = fields.Many2one('programacion.faena', string='Programación', required=True)
    tropa_id = fields.Many2one('ingreso.tropa', string='Tropa', required=True)
    composicion_linea_id = fields.Many2one(
        'composicion.tropa',
        string='Línea de Composición',
        domain="[('ingreso_id', '=', tropa_id)]"
    )
    cabezas_programadas = fields.Integer(string='Cant. de Cabezas a Faenar', required=True)
    destino = fields.Selection([
        ('consumo', 'Consumo Interno'),
        ('exportacion', 'Exportación'),
        ('industrial', 'Industrial'),
        ('otros', 'Otros')
    ], string='Destino', required=True)
    
    corral = fields.Integer(string='Corral',related = 'composicion_linea_id.corral')
    cantidad_restante = fields.Integer(string="Cant. Restante", related="composicion_linea_id.cantidad_restante")
    @api.depends('composicion_linea_id', 'cabezas_programadas')
    def _compute_kilos(self):
        for record in self:
            if record.composicion_linea_id and record.cabezas_programadas:
                record.total_kgs_aprox = record.composicion_linea_id.kilos * record.cabezas_programadas
            else:
                record.total_kgs_aprox = 0
                
    total_kgs_aprox = fields.Float(string='Total Kgs Aprox.', compute='_compute_kilos')

    def action_agregar_linea(self):
        self.ensure_one()
        
        # Obtener el último número correlativo
        ultimo_numero = 0
        ultima_linea = self.env['programacion.faena.linea'].search([], order='numero_final desc', limit=1)
        if ultima_linea:
            ultimo_numero = ultima_linea.numero_final

        # Crear la nueva línea
        self.env['programacion.faena.linea'].create({
            'programacion_id': self.programacion_id.id,
            'numero_inicio': ultimo_numero + 1,
            'numero_final': ultimo_numero + self.cabezas_programadas,
            'cabezas': self.cabezas_programadas,
            'tropa': self.tropa_id.name,
            'corral': self.corral,
            'tipo_hacienda_id': self.composicion_linea_id.tipo_hacienda_id.id,
            'usuario_id': self.env.user.id,
        })
        return {'type': 'ir.actions.act_window_close'}