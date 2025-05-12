{
    'name': 'Ingreso de Tropas',
    'version': '1.0',
    'summary': 'Gestión de Ingreso de Tropas Ganaderas',
    'description': """
        Módulo para gestionar el ingreso de camiones con tropas de ganado
        Incluye registro de proveedores, composición de tropas y documentación requerida
    """,
    'author': 'OutsourceArg',
    'depends': ['base', 'contacts', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/ingreso_tropa_views.xml',
        'views/ingreso_tropa_wizard.xml',
        'views/programacion_faena_views.xml',
        'views/transporte_views.xml',
        'wizards/programacion_wizard_views.xml',
        'data/sequence.xml',
    ],
    'installable': True,
    'application': True,
}