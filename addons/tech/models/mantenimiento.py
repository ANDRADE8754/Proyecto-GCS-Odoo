from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TechstoreMantenimiento(models.Model):
    _name = 'techstore.mantenimiento'
    _description = 'Gestión de Mantenimientos'
    _rec_name = 'name'

    name = fields.Char(
        string='Código de Mantenimiento',
        required=True
    )

    equipo_id = fields.Many2one(
        'techstore.equipo',
        string='Equipo',
        required=True,
        ondelete='cascade'
    )

    fecha_ingreso = fields.Date(
        string='Fecha de Ingreso',
        default=fields.Date.today
    )

    fecha_salida = fields.Date(
        string='Fecha de Salida'
    )

    tecnico = fields.Char(
        string='Técnico Responsable'
    )

    descripcion = fields.Text(
        string='Descripción del Problema'
    )

    diagnostico = fields.Text(
        string='Diagnóstico'
    )

    solucion = fields.Text(
        string='Solución Aplicada'
    )

    costo = fields.Float(
        string='Costo'
    )

    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('revision', 'En Revisión'),
        ('reparacion', 'En Reparación'),
        ('finalizado', 'Finalizado'),
        ('entregado', 'Entregado')
    ], string='Estado', default='pendiente')

    activo = fields.Boolean(
        string='Activo',
        default=True
    )

    @api.constrains('costo')
    def _validar_costo(self):
        for record in self:
            if record.costo < 0:
                raise ValidationError(
                    'El costo no puede ser negativo.'
                )