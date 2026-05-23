# techstore_maintenance/models/equipment_ext.py
from odoo import models, fields
 
 
class MaintenanceEquipmentExt(models.Model):
    """
    Extiende el modelo de equipos de Odoo con campos adicionales
    y el campo inverso para ver el historial de ordenes.
    """
    _inherit = 'maintenance.equipment'  # _inherit extiende un modelo existente
 
    # Campo de solo lectura: muestra todas las ordenes de este equipo
    techstore_order_ids = fields.One2many(
        'techstore.maintenance.order',
        'equipment_id',
        string='Ordenes de Mantenimiento'
    )
 
    # Campo para contar rapidamente cuantos mantenimientos ha tenido
    maintenance_count = fields.Integer(
        string='Total Mantenimientos',
        compute='_compute_maintenance_count'
    )
 
    def _compute_maintenance_count(self):
        for equipment in self:
            equipment.maintenance_count = len(equipment.techstore_order_ids)