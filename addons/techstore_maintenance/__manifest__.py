# techstore_maintenance/__manifest__.py
{
    'name': 'TechStore - Gestion de Mantenimientos',
    'version': '16.0.1.0.0',
    'summary': 'Sistema de gestion de mantenimientos tecnicos para TechStore',
    'author': 'TechStore',
    'category': 'Services/Field Service',
    'depends': [
        'base',       # Modulo base de Odoo (usuarios, empresas)
        'mail',       # Para el chatter (historial de mensajes y cambios)
        'hr',         # Para gestionar empleados (tecnicos)
        'maintenance',# Para el modelo de equipos
        'product',    # Para los repuestos y materiales
    ],
    'data': [
        # El orden importa: seguridad primero, luego datos, luego vistas
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/maintenance_order_views.xml',
        'views/equipment_views.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
        #'report/maintenance_report.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}