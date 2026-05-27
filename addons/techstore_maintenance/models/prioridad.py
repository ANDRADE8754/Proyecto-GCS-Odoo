from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TechstorePrioridad(models.Model):
    _name = 'techstore.prioridad'
    _description = 'Prioridad - Mantenimiento TechStore'
    _rec_name = 'nombre'
    _order = 'tiempo_maximo'

    # Campos Principales
    id_prioridad = fields.Char(
        string='ID de Prioridad',
        required=True,
        copy=False,
        index=True,
        help='Identificador único de la prioridad'
    )
    nombre = fields.Selection(
        [
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
            ('critica', 'Crítica')
        ],
        string='Nombre de Prioridad',
        required=True,
        index=True,
        help='Nivel de prioridad'
    )
    tiempo_maximo = fields.Integer(
        string='Tiempo Máximo (Horas)',
        required=True,
        help='Horas máximas permitidas para completar el mantenimiento'
    )
    color = fields.Char(
        string='Color',
        help='Color para visualización en kanban y reportes'
    )

    # Restricciones SQL
    _sql_constraints = [
        ('id_prioridad_unique', 'UNIQUE(id_prioridad)', 'El ID de prioridad debe ser único.'),
        ('nombre_unique', 'UNIQUE(nombre)', 'El nombre de prioridad debe ser único.'),
    ]

    @api.constrains('tiempo_maximo')
    def _check_tiempo_maximo(self):
        """Valida que el tiempo máximo sea positivo"""
        for record in self:
            if record.tiempo_maximo <= 0:
                raise ValidationError(
                    _('El tiempo máximo debe ser un valor positivo.')
                )

    @api.model
    def create(self, vals):
        """Override create para asignar color automático"""
        if not vals.get('color'):
            color_map = {
                'baja': '#00b800',  # Verde
                'media': '#ffb800',  # Amarillo/Naranja claro
                'alta': '#ff6600',   # Naranja
                'critica': '#ff0000'  # Rojo
            }
            vals['color'] = color_map.get(vals.get('nombre'), '#808080')
        return super().create(vals)

    def get_nombre_display(self):
        """Retorna la representación visual del nombre"""
        nombre_dict = dict(self._fields['nombre'].selection)
        return nombre_dict.get(self.nombre, self.nombre)

    def get_color_rgb(self):
        """Retorna el color en formato RGB"""
        return self.color or '#808080'
