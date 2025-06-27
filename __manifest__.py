{
    'name': 'Ingreso de Tropas',
    'version': '1.0',
    'summary': 'Gestión de Ingreso de Tropas Ganaderas',
    'description': """
        Módulo para gestionar el ingreso de camiones con tropas de ganado
        Incluye registro de proveedores, composición de tropas y documentación requerida
    """,
    'author': 'OutsourceArg',
    'depends': ['base', 'contacts', 'fleet','delivery_iot'],
    'data': [
        'security/ir.model.access.csv',
        'views/ingreso_tropa_views.xml',
        'views/ingreso_tropa_wizard.xml',
        'views/programacion_faena_views.xml',
        'views/transporte_views.xml',
        'views/faena_impresion.xml',
        'views/faena_impresion_detalle.xml',
        'wizards/programacion_wizard_views.xml',
        'data/sequence.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ingreso_tropas/static/src/widgets/*'
        ],
    },
    'installable': True,
    'application': True,
}