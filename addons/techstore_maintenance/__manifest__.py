{
    'name': 'TechStore - Gestión de Mantenimientos Técnicos',
    'version': '1.0.0',
    'category': 'TechStore/Mantenimiento',
    'author': 'TechStore',
    'summary': 'Módulo de gestión de mantenimientos técnicos para TechStore',
    'description': 'Módulo personalizado para gestionar mantenimientos técnicos, asignación de técnicos y seguimiento de órdenes de trabajo',
    'depends': [
        'base',
        'mail',
        'web',
        'hr',        
        'maintenance',
        'product',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/secuencia_data.xml',
        # Reportes
        'reports/reports.xml',
        'reports/mantenimiento_orden.xml',
        'reports/certificado_entrega.xml',
        'reports/equipo_historial.xml',
        'reports/reporte_general_pdf.xml',
        # Vistas de negocio
        'views/dashboard_banner.xml',
        'views/equipo_views.xml',
        'views/cliente_views.xml',
        'views/tecnico_views.xml',
        'views/estado_views.xml',
        'views/prioridad_views.xml',
        'views/mantenimiento_views.xml',
        'views/mantenimiento_estado_wizard_views.xml',
        # Wizards
        'wizard/reporte_wizard_views.xml',
        # Menús y Datos Maestros
        'views/menu.xml',          # ← SIEMPRE AL FINAL
        'data/maestro_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'techstore_maintenance/static/src/js/close_form_action.js',
        ],
    },
    'license': 'LGPL-3',
}