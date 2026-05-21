{
    'name': 'TechStore Mantenimiento',
    'version': '1.0',
    'summary': 'Sistema de gestión de mantenimientos técnicos',
    'description': """
        Módulo para:
        - Gestión de clientes
        - Gestión de equipos
        - Gestión de mantenimientos
        - Gestión de técnicos
        - APIs REST
    """,

    'author': 'TechStore',
    'website': 'https://techstore.com',

    'category': 'Services',
    'license': 'LGPL-3',

    'depends': [
        'base',
        'mail'
    ],

    'data': [
        'security/ir.model.access.csv',

        'views/equipo_views.xml',
    ],

    'installable': True,
    'application': True,

    'auto_install': False,
}

