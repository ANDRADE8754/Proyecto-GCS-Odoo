from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TechstoreEstado(models.Model):
    _name = 'techstore.estado'
    _description = 'Estado - Mantenimiento TechStore'
    _order = 'secuencia'
    _rec_name = 'nombre_estado'

    # Campos Principales
    id_estado = fields.Char(
        string='ID del Estado',
        required=True,
        copy=False,
        index=True,
        help='Identificador único del estado'
    )
    nombre_estado = fields.Selection(
        [
            ('ingresado', 'Ingresado'),
            ('pendiente_asignacion', 'Pendiente de Asignación'),
            ('diagnostico', 'Diagnóstico'),
            ('reparacion', 'Reparación'),
            ('esperando_repuestos', 'Esperando Repuestos'),
            ('control_calidad', 'Control de Calidad'),
            ('listo_entrega', 'Listo para Entrega'),
            ('entregado', 'Entregado')
        ],
        string='Nombre del Estado',
        required=True,
        index=True,
        help='Estado del mantenimiento'
    )
    secuencia = fields.Integer(
        string='Secuencia',
        default=10,
        help='Orden de visualización'
    )

    # Campo Computable
    es_estado_final = fields.Boolean(
        string='¿Es Estado Final?',
        compute='_compute_es_estado_final',
        store=True,
        help='Indica si es un estado final (listo para entrega o entregado)'
    )

    # Restricciones SQL
    _sql_constraints = [
        ('id_estado_unique', 'UNIQUE(id_estado)', 'El ID del estado debe ser único.'),
        ('nombre_estado_unique', 'UNIQUE(nombre_estado)', 'El nombre del estado debe ser único.'),
    ]

    @api.depends('nombre_estado')
    def _compute_es_estado_final(self):
        """Determina si es un estado final"""
        for record in self:
            record.es_estado_final = record.nombre_estado in ['listo_entrega', 'entregado']

    def __str__(self):
        # Build a safe string representation without assuming a singleton
        estado_dict = dict(self._fields['nombre_estado'].selection)
        names = [estado_dict.get(rec.nombre_estado, rec.nombre_estado) for rec in self]
        return names[0] if len(names) == 1 else ', '.join(names)

    def get_nombre_estado_display(self):
        """Retorna la representación visual del nombre del estado"""
        # Return display string for single record or comma-joined for multiple
        estado_dict = dict(self._fields['nombre_estado'].selection)
        names = [estado_dict.get(rec.nombre_estado, rec.nombre_estado) for rec in self]
        return names[0] if len(names) == 1 else ', '.join(names)

    @api.model
    def name_create(self, name):
        raise ValidationError(
            _('Los estados no se crean desde este campo. Use el menú de Estados para crear un estado válido.')
        )

    @api.model
    def action_link_existing_records_xml_id(self):
        """Asocia estados y prioridades existentes en la BD con sus XML IDs en ir_model_data
        para prevenir UniqueViolation al actualizar el módulo en entornos con DBs restauradas.
        """
        queries = [
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_nuevo', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-001' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_nuevo');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_pendiente_asignacion', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-008' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_pendiente_asignacion');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_diagnostico', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-002' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_diagnostico');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_reparacion', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-003' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_reparacion');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_esperando_repuestos', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-004' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_esperando_repuestos');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_control_calidad', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-005' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_control_calidad');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_listo_entrega', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-006' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_listo_entrega');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_estado_entregado', 'techstore_maintenance', 'techstore.estado', id, false
            FROM techstore_estado WHERE id_estado = 'EST-007' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_estado_entregado');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_prioridad_baja', 'techstore_maintenance', 'techstore.prioridad', id, false
            FROM techstore_prioridad WHERE id_prioridad = 'PRI-001' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_prioridad_baja');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_prioridad_media', 'techstore_maintenance', 'techstore.prioridad', id, false
            FROM techstore_prioridad WHERE id_prioridad = 'PRI-002' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_prioridad_media');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_prioridad_alta', 'techstore_maintenance', 'techstore.prioridad', id, false
            FROM techstore_prioridad WHERE id_prioridad = 'PRI-003' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_prioridad_alta');
            """,
            """
            INSERT INTO ir_model_data (name, module, model, res_id, noupdate)
            SELECT 'techstore_prioridad_critica', 'techstore_maintenance', 'techstore.prioridad', id, false
            FROM techstore_prioridad WHERE id_prioridad = 'PRI-004' AND NOT EXISTS (SELECT 1 FROM ir_model_data WHERE module = 'techstore_maintenance' AND name = 'techstore_prioridad_critica');
            """
        ]
        for query in queries:
            self.env.cr.execute(query)
