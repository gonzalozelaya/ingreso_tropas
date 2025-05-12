from odoo import models, fields, api

class Transporte(models.Model):
    _name = 'tropa.transporte'
    _description = 'Gestión de Camiones Propios y de Terceros'

    # Campos básicos
    name = fields.Char('Nombre',compute = '_compute_name')
    tipo = fields.Selection(
        selection=[('P', 'Camión Propio'), ('T', 'Camión de Tercero')],
        string='Tipo',
        required=True,
        default='P'
    )
    dominio = fields.Char(string='Dominio', required=True, help="Patente del vehículo")
    marca = fields.Char(string='Marca', required = True)
    numero_senasa = fields.Char(string='Número SENASA', size=10)
    
    # Chofer (relación con otro modelo o campos directos)
    codigo_chofer = fields.Integer(string='Código Chofer', size=3)
    chofer_id = fields.Many2one('res.partner', string='Chofer')  # En vez de campos directos
    chofer_nombre = fields.Char(string='Apellido y Nombre', size=50)
    
    # Fechas de vencimiento
    vencimiento_rto = fields.Date(string='Vencimiento RTO')
    vencimiento_seguro = fields.Date(string='Vencimiento Seguro')
    vencimiento_patente = fields.Date(string='Vencimiento Patente')
    vencimiento_senasa = fields.Date(string='Vencimiento SENASA')
    vencimiento_jujuy = fields.Date(string='Vencimiento JUJUY')
    
    # Campos condicionales para Terceros
    empresa_transporte = fields.Char(string='Empresa de Transporte', size=50)
    dueno_nombre = fields.Char(string='Dueño (Nombre y Apellido)', size=50)
    cuit_empresa_dueno = fields.Char(string='CUIT Empresa/Dueño', size=13, help="Formato: XX-XXXXXXXX-X")
    chofer_tercero_nombre = fields.Char(string='Chofer Tercero (Apellido y Nombre)', size=50)
    cuit_chofer_tercero = fields.Char(string='CUIT Chofer Tercero', size=13)

    @api.depends('dominio','marca')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.marca} {record.dominio}"
        

    # Restricciones y lógica adicional
    @api.constrains('tipo')
    def _check_tipo_tercero(self):
        for record in self:
            if record.tipo == 'T' and not (record.empresa_transporte or record.dueno_nombre):
                raise models.ValidationError("Para camiones de terceros, debe ingresar Empresa o Dueño.")