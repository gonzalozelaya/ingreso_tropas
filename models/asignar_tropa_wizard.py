from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
import logging

_logger = logging.getLogger(__name__)
class IngresoTropaWizard(models.Model):
    _name = 'ingreso.tropa.wizard'
    _description = 'Wizard para asignar número de tropa'
    
    # Campos del wizard
    guia_id = fields.Many2one('ingreso.tropa', string='Tropa por N° de Guía', required=True)
    numero_tropa = fields.Char(
        string='Número de Tropa',
        default=lambda self: self._get_next_tropa_suggestion(),
        help="Número sugerido (se confirmará al guardar)",
        required = True,
    )
    show_number_edit = fields.Boolean(string='Editar numero', default=False)
    
    # Campos relacionados (solo lectura)
    fecha_ingreso = fields.Datetime(related='guia_id.fecha_ingreso', string='Fecha Ingreso', readonly=True)
    hora_ingreso = fields.Float(related='guia_id.hora_ingreso', string='Hora Ingreso', readonly=True)
    numero_guia = fields.Char(
        string='N° de Guía',
    )
    total_cabezas = fields.Integer(related='guia_id.total_cabezas', string='Total Cabezas', readonly=True)
    kgs_vivos = fields.Float(related='guia_id.kg_vivos', string='Kgrs. Vivos', readonly=True)
    
    # Líneas de composición editable
    composicion_line_ids = fields.One2many(
        'ingreso.tropa.wizard.line', 
        'wizard_id', 
        string='Composición de Tropa',
        required=True
    )

    @api.constrains('composicion_line_ids')
    def _check_tipo_tercero(self):
        for record in self:
            _logger.info('Check')
            for line in record.composicion_line_ids:
               if line.corral == 0:
                   raise ValidationError('Corral requerido en las lineas de composición')
    
    @api.model
    def default_get(self, fields):
        res = super(IngresoTropaWizard, self).default_get(fields)
        if self.env.context.get('active_id'):
            guia_id = self.env.context['active_id']
            res['guia_id'] = guia_id
            
            # Cargar las líneas de composición existentes
            guia = self.env['ingreso.tropa'].browse(guia_id)
            lineas = []
            for linea in guia['composicion_tropa_ids']:
                lineas.append((0, 0, {
                    'tipo_hacienda_id': linea.tipo_hacienda_id.id,
                    'cantidad': linea.cantidad,
                    'kilos': linea.kilos,
                    'composicion_id': linea.id,
                }))
            res['composicion_line_ids'] = lineas
        return res
    
    def action_asignar_tropa(self):
        self.ensure_one()
        # Validación mejorada
        if not self.composicion_line_ids:
            raise UserError("No hay líneas de composición para procesar")
        lineas_sin_corral = self.composicion_line_ids.filtered(lambda linea: not linea.corral)
        if lineas_sin_corral:
            raise UserError(
                "Debe asignar un corral a todas las líneas de composición. "
                "Líneas sin corral: \n" +
                "\n".join([f"- Tipo: {linea.tipo_hacienda_id.name}" for linea in lineas_sin_corral])
            )
        
        # Actualización con verificación
        for linea in self.composicion_line_ids:
            _logger.info(f"Linea {linea.composicion_id}")
            if not linea.composicion_id:
                raise UserError(f"Línea {linea.id} no tiene relación con composición original")
            
            _logger.info("Antes de escribir - Corral: %s, Línea ID: %s", linea.composicion_id.corral, linea.composicion_id.id)
            
            # Usamos sudo() para evitar problemas de permisos
            linea.composicion_id.sudo().write({'corral': linea.corral})
            
            # Forzamos la lectura de la base de datos
            _logger.info("Después de escribir - Corral: %s, Línea ID: %s", linea.composicion_id.corral, linea.composicion_id.id)
            
            if linea.composicion_id.corral != linea.corral:
                _logger.error("Fallo al actualizar corral! Esperado: %s, Actual: %s", 
                            linea.corral, linea.composicion_id.corral)
        
        # Actualización del registro principal
        self.action_update_sequence(self.numero_tropa)
        self.guia_id.write(
            {'num_tropa':self.numero_tropa,'state':'tropa'}
        )
        # Borrado seguro del wizard
        wizard_id = self.id
        self.unlink()
        
        return {'type': 'ir.actions.act_window_close'}

    def _get_next_tropa_suggestion(self):
        sequence = self.env['ir.sequence'].search([('code','=','ingreso.tropa.tropa')])
        if sequence:
            return sequence._get_current_sequence().number_next_actual
        return ""

    def action_update_sequence(self, new_number):
        """Actualiza la secuencia con el nuevo número"""
        self.ensure_one()
        try:
            # Convertir a entero para validar
            num = int(new_number)
        except ValueError:
            raise UserError(_("El número de tropa debe ser un valor numérico"))
        
        sequence = self.env['ir.sequence'].search([('code', '=', 'ingreso.tropa.tropa')])
        if sequence:
            sequence.sudo().write({
                'number_next': num + 1  # Preparamos la secuencia para el próximo número
            })
            # Actualizar el número mostrado en el wizard principal
            self.write({'numero_tropa': str(num)})


    

class IngresoTropaWizardLine(models.Model):
    _name = 'ingreso.tropa.wizard.line'
    _description = 'Líneas de composición en el wizard'
    
    wizard_id = fields.Many2one('ingreso.tropa.wizard', string='Wizard')
    composicion_id = fields.Many2one('composicion.tropa', string='Línea Original')
    
    tipo_hacienda_id = fields.Many2one(
        'tipo.hacienda', 
        string='Tipo de Hacienda',
        readonly=True
    )
    cantidad = fields.Integer(
        string='Cantidad',
        readonly=True
    )
    kilos = fields.Float(
        string='Kilos',
        readonly=True
    )
    corral = fields.Integer(
        string='Corral',
        required=True
    )
    promedio_cabeza = fields.Float(
        string='Promedio por cabeza',
        compute='_compute_promedio',
        readonly=True
    )
    
    @api.depends('kilos', 'cantidad')
    def _compute_promedio(self):
        for record in self:
            if record.cantidad > 0:
                record.promedio_cabeza = record.kilos / record.cantidad
            else:
                record.promedio_cabeza = 0


class UpdateTropaSequenceWizard(models.TransientModel):
    _name = 'update.tropa.sequence.wizard'
    _description = 'Wizard para actualizar número de secuencia de tropa'
    
    current_number = fields.Char(string='Número Actual', readonly=True)
    new_number = fields.Char(
        string='Nuevo Número',
        required=True,
        help="Ingrese el nuevo número de tropa. La secuencia continuará desde este número + 1"
    )
    main_wizard_id = fields.Many2one('ingreso.tropa.wizard', string='Wizard Principal')
    
    def action_confirm(self):
        self.ensure_one()
        if not self.main_wizard_id:
            raise UserError(_("No se encontró el wizard principal"))
        
        # Validar que el nuevo número sea diferente
        if self.new_number == self.current_number:
            raise UserError(_("El nuevo número debe ser diferente al actual"))
        
        # Delegar la actualización al wizard principal
        self.main_wizard_id.action_update_sequence(self.new_number)
        
        return {'type': 'ir.actions.act_window_close'}