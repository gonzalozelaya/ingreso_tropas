from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)
class IngresoTropa(models.Model):
    _name = 'ingreso.tropa'
    _description = 'Registro de Ingreso de Tropas'
    
    # Campos básicos
    name = fields.Char(string='Referencia', readonly=True, compute='_compute_name')
    fecha_ingreso = fields.Datetime(string='Fecha Ingreso', default=fields.Date.today, required=True)
    hora_ingreso = fields.Float(string='Hora Ingreso')
    num_guia = fields.Integer(
        string='N° de Guía',
        required=True,
        default=lambda self: self._get_next_guia(),
        store = True,
        copy=False
    )
    cert_senasa_dta = fields.Char(string='Cert. SENASA DTA', required=True)
    renspa = fields.Char(string='RENSPA', required=True)
    total_cabezas = fields.Integer(string='Total Cabezas', compute='_compute_total_cabezas')
    kg_vivos = fields.Float(string='Kgrs. Vivos', compute='_compute_kgs_vivos')
    horas_viaje = fields.Float(string='Hrs. Viaje')
    estado_tropa = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('enfaena', 'En Faena'),
        ('hecho', 'Hecho')
    ], string='Estado',default="pendiente")
    
    # Selección para procedencia
    procedencia = fields.Selection([
        ('estancia', 'Estancia'),
        ('mercado', 'Mercado'),
        ('remate_feria', 'Remate Feria')
    ], string='Adquirido', required=True)
    
    observaciones = fields.Text(string='Observaciones')
    
    # Información del transporte
    transporte_id = fields.Many2one('fleet.vehicle', string="Camión")
    proveedor_id = fields.Many2one('res.partner', string='Proveedor', required=True)
        
    # Información de usuario
    usuario_id = fields.Many2one('res.users', string='Usuario', default=lambda self: self.env.user)
    
    # Operadores
    operador_id = fields.Many2one('hr.employee', string='Operador (Corralero)')
    operador_alternativo_id = fields.Many2one('hr.employee', string='Operador Alternativo (Administración)')
    
    # Composición de la tropa
    composicion_tropa_ids = fields.One2many('composicion.tropa', 'ingreso_id', string='Composición Tropa')

    # Animales muertos
    animales_muertos_ids = fields.One2many('animales.muertos', 'ingreso_id', string='Animales Muertos')
    
    # Campos calculados
    peso_promedio = fields.Float(string='Peso Promedio (kg)', compute='_compute_peso_promedio', store=True)

    state = fields.Selection([('ingreso','Ingreso'),('tropa','Tropa')],readonly=True)
    num_tropa = fields.Integer('Tropa',readonly=True)

    #DATOS DE PROVEEDOR
    street = fields.Char('Dirección',related='proveedor_id.street')
    city = fields.Char('Ciudad',related='proveedor_id.city')
    #state = fields.Many2one('res.country.state',string='Estado',related='proveedor_id.state_id')
    cuit = fields.Char('CUIT',related='proveedor_id.vat')
    email = fields.Char('Dirección',related='proveedor_id.email')

    def _get_next_guia(self):
        sequence = self.env['ir.sequence'].search([('code','=','ingreso.tropa.guia')])
        if sequence:
            return sequence._get_current_sequence().number_next_actual
        return ""

    @api.onchange('proveedor_id')
    def _onchange_proveedor(self):
        for record in self:
            if record.proveedor_id.city:
                record.localidad = record.proveedor_id.city
            if record.proveedor_id.state_id:
                record.provincia_id = record.proveedor_id.state_id.id

    @api.depends('num_guia', 'num_tropa', 'state')
    def _compute_name(self):
        for record in self:
            if record.state == 'tropa' and record.num_tropa:
                record.name = f"TROPA-{str(record.num_tropa).zfill(8)}"
            else:
                record.name = f"GUIA-{str(record.num_guia).zfill(8)}"
    
    @api.depends('composicion_tropa_ids')
    def _compute_total_cabezas(self):
        for record in self:
            total_cabezas = 0
            for line in record.composicion_tropa_ids:
                total_cabezas += line.cantidad
            record.total_cabezas = total_cabezas
        return

    @api.depends('composicion_tropa_ids')
    def _compute_kgs_vivos(self):
        for record in self:
            total_kgs = 0
            for line in record.composicion_tropa_ids:
                total_kgs += line.kilos
            record.kg_vivos = total_kgs
        return
    
    @api.depends('kg_vivos', 'total_cabezas')
    def _compute_peso_promedio(self):
        for record in self:
            if record.total_cabezas > 0:
                record.peso_promedio = record.kg_vivos / record.total_cabezas
            else:
                record.peso_promedio = 0
    
    @api.model
    def create(self, vals):
        # Solo consumir secuencia si el número coincide con el próximo esperado
        sequence = self.env['ir.sequence'].search([('code','=','ingreso.tropa.guia')])
        _logger.info(vals.get('num_guia'))
        _logger.info(sequence.number_next_actual)
        if sequence and vals.get('num_guia') == sequence.number_next_actual:
            self.env['ir.sequence'].next_by_code('ingreso.tropa.guia')
        # Generar nombre de referencia
        _logger.info(f"num_guia:{vals}")
        #vals['name'] = f"GUIA-{vals.get('num_guia', '').zfill(8)}"
        return super().create(vals)
    
    def write(self, vals):
        res = super(IngresoTropa, self).write(vals)
        # Si se actualiza el número de guía o tropa, actualizar el nombre
        if 'num_guia' in vals or 'num_tropa' in vals:
            for record in self:
                new_name = record._generate_name()
                if record.name != new_name:
                    record.write({'name': new_name})
        return res

    def action_asignar_tropa(self):
        return {
            'name': 'Asignar Número de Tropa',
            'type': 'ir.actions.act_window',
            'res_model': 'ingreso.tropa.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_guia_id': self.id},
        }

    def _generate_name(self):
        if self.num_tropa:
            return f"TROPA-{str(self.num_tropa).zfill(8)}"
        return f"GUIA-{str(self.num_guia).zfill(8)}"

    def _generate_guia_name(self, num_guia):
        return f"GUIA-{num_guia}"

class ComposicionTropa(models.Model):
    _name = 'composicion.tropa'
    _description = 'Composición de la Tropa'

    name = fields.Char('Nombre',compute='_compute_name')
    ingreso_id = fields.Many2one('ingreso.tropa', string='Ingreso')
    cantidad = fields.Integer(string='Cant.', required=True)
    cantidad_restante = fields.Integer(string='Cant. Restante',readonly=True)
    animal = fields.Many2one('tipo.animal', string="Animales")
    kilos = fields.Float(string='Kilos')
    corral = fields.Integer(string='Corral')
    # Relación con posible catálogo de tipos de hacienda
    tipo_hacienda_id = fields.Many2one('tipo.hacienda', string='Tipo de Hacienda',required = True)
    promedio_cabeza = fields.Float('Promedio por cabeza',compute='compute_peso_promedio')

    @api.model
    def create(self, vals):
         vals['cantidad_restante'] = vals['cantidad']
         return super(ComposicionTropa, self).create(vals)

    @api.depends('tipo_hacienda_id','cantidad')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.tipo_hacienda_id.display_name} ({record.cantidad_restante})"

    @api.depends('kg_vivos', 'total_cabezas')
    def _compute_peso_promedio(self):
        for record in self:
            if record.total_cabezas > 0:
                record.promedio_cabeza = record.kilos / record.cantidad
            else:
                record.peso_promedio = 0
    
class TipoHacienda(models.Model):
    _name = 'tipo.hacienda'
    _description = 'Tipos de Hacienda'
    
    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Descripción', required=True)
    sex = fields.Selection([('m','M'),('f','F')],string='Sexo')
    display_name = fields.Char(string='Nombre en pantalla',compute='_compute_display_name')
    
    @api.depends('name','code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}]{record.name}"

class TipoAnimal(models.Model):
    _name = 'tipo.animal'
    _description = 'Animales'

    code = fields.Char(string='Código', required=True)
    name = fields.Char(string='Descripción', required=True)
    display_name = fields.Char(string='Nombre en pantall',compute='_compute_display_name')

    @api.depends('name','code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}]{record.name}"

