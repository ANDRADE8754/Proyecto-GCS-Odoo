from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TechstoreEquipo(models.Model):
    _name = 'techstore.equipo'
    _description = 'Gestión de Equipos'
    _rec_name = 'name'

    name = fields.Char(
        string='Nombre del Equipo',
        required=True
    )

    cliente_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True
    )

    tipo_equipo = fields.Selection([
        ('laptop', 'Laptop'),
        ('pc', 'PC'),
        ('impresora', 'Impresora'),
        ('monitor', 'Monitor'),
        ('otro', 'Otro')
    ], string='Tipo de Equipo', required=True)

    marca = fields.Char(string='Marca')

    modelo = fields.Char(string='Modelo')

    serial = fields.Char(
        string='Número Serial',
        required=True
    )

    estado = fields.Selection([
        ('nuevo', 'Nuevo'),
        ('revision', 'En Revisión'),
        ('reparacion', 'En Reparación'),
        ('finalizado', 'Finalizado'),
        ('entregado', 'Entregado')
    ], string='Estado', default='nuevo')

    observaciones = fields.Text(string='Observaciones')

    mantenimiento_ids = fields.One2many(
        'techstore.mantenimiento',
        'equipo_id',
        string='Mantenimientos'
    )

    _sql_constraints = [
        (
            'serial_unique',
            'unique(serial)',
            'El número serial ya existe.'
        )
    ]

    @api.constrains('serial')
    def _validar_serial(self):
        for record in self:
            if len(record.serial) < 5:
                raise ValidationError(
                    'El serial debe tener al menos 5 caracteres.'
                )

    # =========================
    # CRUD PERSONALIZADO
    # =========================

    @api.model
    def crear_equipo(self, vals):

        equipo = self.create(vals)

        return {
            'success': True,
            'message': 'Equipo creado correctamente',
            'id': equipo.id
        }

    def obtener_equipo(self):

        self.ensure_one()

        return {
            'id': self.id,
            'name': self.name,
            'cliente': self.cliente_id.name,
            'tipo_equipo': self.tipo_equipo,
            'marca': self.marca,
            'modelo': self.modelo,
            'serial': self.serial,
            'estado': self.estado,
            'observaciones': self.observaciones
        }

    def actualizar_equipo(self, vals):

        self.ensure_one()

        self.write(vals)

        return {
            'success': True,
            'message': 'Equipo actualizado correctamente'
        }

    def eliminar_equipo(self):

        self.ensure_one()

        self.unlink()

        return {
            'success': True,
            'message': 'Equipo eliminado correctamente'
        }