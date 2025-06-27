from odoo import fields, api, models
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)
class ImpresionTickets(models.Model):
    _name = 'ingreso.impresion'
    _description = 'Impresión de Tickets de Pesaje'

    impresion_ids = fields.One2many('ingreso.impresion.detalle', 'impresion_id', string="Detalle")
    cantidad_impresiones = fields.Integer(
        string='Total de Impresiones',
        compute='_compute_cantidad_impresiones',
        store=True,
        help="Número total de etiquetas impresas"
    )
    programacion_id = fields.Many2one('programacion.faena', string="Programación", required=True)
    linea_actual_id = fields.Many2one('programacion.faena.linea', string="Línea Actual")
    labels_amount = fields.Integer('Nro. de etiquetas', default=1)
    tipo = fields.Selection([
        ('ingresa', 'Ingresa'),
        ('pendiente', 'Pendiente'),
        ('decomiso', 'Decomiso')
    ], string='Tipo', default='ingresa')
    observaciones = fields.Text('Observaciones')
    peso = fields.Float('Peso (kg)')
    estado = fields.Selection([
        ('inicio', 'Inicio'),
        ('proceso', 'En Proceso'),
        ('finalizado', 'Finalizado')
    ], string='Estado', default='inicio')
    
    # Campos para control de progreso
    lineas_ids = fields.One2many('programacion.faena.linea', 
                                compute='_compute_lineas_programacion',
                                string='Líneas de Programación')
    linea_index = fields.Integer('Índice de Línea Actual', default=0)
    cantidad_procesada = fields.Integer('Cantidad Procesada', default=0)

    # Campos calculados para reemplazar los eval
    total_lineas = fields.Integer(
        string='Total de Líneas',
        compute='_compute_totales',
        store=True,
        help="Número total de líneas en la programación"
    )
    
    cabezas_linea_actual = fields.Integer(
        string='Cabezas',
        related='linea_actual_id.cabezas',
        readonly=True,
        store=True,
        help="Número de cabezas en la línea actual"
    )
    
    tropa_linea_actual = fields.Char(
        string='Tropa',
        related='linea_actual_id.tropa',
        readonly=True,
        store=True,
        help="Número de tropa de la línea actual"
    )
    
    corral_linea_actual = fields.Char(
        string='Corral',
        related='linea_actual_id.corral',
        readonly=True,
        store=True,
        help="Corral asignado a la línea actual"
    )
    
    tipo_hacienda_linea_actual = fields.Char(
        string='Tipo Hacienda',
        related='linea_actual_id.tipo_hacienda_id.name',
        readonly=True,
        store=True,
        help="Tipo de hacienda de la línea actual"
    )

    #IOT
    iot_device_id = fields.Many2one('iot.device', "Báscula")
    iot_device_identifier = fields.Char(related='iot_device_id.identifier')
    iot_ip = fields.Char(related='iot_device_id.iot_ip')
    weight = fields.Float('Peso',store=True)
    weight_to_show = fields.Float('Mostrar peso', compute='_compute_weight_to_show', store=True, readonly=True)
    manual_weight = fields.Boolean('Ajuste manual',default=False )
    manual_measurement = fields.Boolean('Manual', default = True)

    @api.depends('weight')
    def _compute_weight_to_show(self):
        for record in self:
            record.weight_to_show = record.weight
            
    @api.depends('lineas_ids')
    def _compute_totales(self):
        for rec in self:
            rec.total_lineas = len(rec.lineas_ids)

    @api.depends('impresion_ids')
    def _compute_cantidad_impresiones(self):
        for rec in self:
            rec.cantidad_impresiones = len(rec.impresion_ids)

    @api.model
    def create(self, vals):
        """Sobreescribir create para inicializar valores"""
        if 'programacion_id' in vals:
            programacion = self.env['programacion.faena'].browse(vals['programacion_id'])
            if programacion.lineas_faena:
                vals.update({
                    'linea_actual_id': programacion.lineas_faena[0].id,
                    'linea_index': 0,
                })
        return super(ImpresionTickets, self).create(vals)
    
    @api.depends('programacion_id')
    def _compute_lineas_programacion(self):
        for rec in self:
            rec.lineas_ids = rec.programacion_id.lineas_faena.sorted('numero_inicio')
    
    def action_iniciar_proceso(self):
        """Inicia el proceso de pesaje e impresión"""
        self.ensure_one()
        if not self.lineas_ids:
            raise UserError("No hay líneas programadas para procesar")
        
        self.write({
            'estado': 'proceso',
            'linea_actual_id': self.lineas_ids[0].id,
            'linea_index': 0,
            'cantidad_procesada': self.lineas_ids[0].numero_inicio or 1  # Inicia desde numero_inicio o 1 si es None
        })
        return self._actualizar_vista()
    
    def action_siguiente_linea(self):
        """Avanza a la siguiente línea de programación"""
        self.ensure_one()
        next_index = self.linea_index + 1
        if next_index < len(self.lineas_ids):
            self.write({
                'linea_actual_id': self.lineas_ids[next_index].id,
                'linea_index': next_index,
                'cantidad_procesada': self.lineas_ids[next_index].numero_inicio or 1,  # Inicia desde numero_inicio
                'peso': 0.0,
                'labels_amount': 1
            })
        else:
            self.write({'estado': 'finalizado'})
        return self._actualizar_vista()
    
    def action_imprimir_etiqueta(self):
        """Imprime la etiqueta actual y registra el pesaje"""
        self.ensure_one()
        if self.peso <= 0:
            raise UserError("Debe ingresar un peso válido antes de imprimir")
        
        # Crear registro de detalle
        self.env['ingreso.impresion.detalle'].create({
            'impresion_id': self.id,
            'peso': self.weight,
            'linea_id': self.linea_actual_id.id,
            'numero_impresion':self.cantidad_procesada
        })
        
        # Actualizar cantidad procesada
        self.cantidad_procesada += self.labels_amount
        
        # Actualizar número actual en la línea
        if self.linea_actual_id:
            self.linea_actual_id.write({
                'numero_actual': self.cantidad_procesada
            })
        
        # Verificar si se completó la línea actual
        if self.cantidad_procesada >= (self.linea_actual_id.numero_inicio or 1) + self.linea_actual_id.cabezas - 1:
            return self.action_siguiente_linea()
        
        return self._actualizar_vista()
    
    def _actualizar_vista(self):
        """Actualiza la vista sin cambiar de pantalla"""
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def ver_impresiones(self):
        """Acción para ver el listado de impresiones detalladas"""
        self.ensure_one()
        return {
            'name': 'Detalle de Impresiones',
            'type': 'ir.actions.act_window',
            'res_model': 'ingreso.impresion.detalle',
            'view_mode': 'tree,form',
            'domain': [('impresion_id', '=', self.id)],
            'context': {
                'default_impresion_id': self.id,
                'create': False,  # Opcional: si quieres deshabilitar la creación desde esta vista
            },
            'target': 'current',
        }

    @api.model
    def action_abrir_impresion_tickets(self):
        """Acción inteligente que abre la vista adecuada"""
        # Buscar si hay impresiones en proceso
        impresion_en_proceso = self.search([('estado', '=', 'proceso')], limit=1)
        _logger.info("Abriendo menú de impresión de tickets")
        
        if impresion_en_proceso:
            _logger.info(f"Redirigiendo a impresión en proceso ID: {impresion_en_proceso.id}")
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'ingreso.impresion',
                'res_id': impresion_en_proceso.id,
                'views': [(False, 'form')],
                'target': 'current',
                'context': {'form_view_initial_mode': 'edit'},
            }
        else:
            _logger.info("Redirigiendo a listado de programaciones")
            # Mostrar listado de programaciones confirmadas disponibles
            return {
                'type': 'ir.actions.act_window',
                'name': 'Seleccionar Programación',
                'res_model': 'programacion.faena',
                'view_mode': 'tree,form',
                'target': 'current',
                'domain': [('state', '=', 'confirmado')],
            }

class ImpresionDetalle(models.Model):
    _name = 'ingreso.impresion.detalle'

    name = fields.Char('Nombre',compute='_compute_name')
    impresion_id = fields.Many2one('ingreso.impresion')
    fecha = fields.Datetime(default=fields.Datetime.now)
    peso = fields.Float()
    numero_impresion = fields.Integer('Número de Impresión')
    linea_id = fields.Many2one('programacion.faena.linea')
    tropa = fields.Char(related='linea_id.tropa', string="Tropa", readonly=True)
    corral = fields.Char(related='linea_id.corral', string="Corral", readonly=True)
    tipo_hacienda = fields.Char(related='linea_id.tipo_hacienda_id.name', string="Tipo Hacienda", readonly=True)

    @api.depends('numero_impresion','linea_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.linea_id.name} - {record.numero_impresion}"

    def correccion(self):
        for record in self:
            return
    def reimprimir(self):
        for record in self:
            return