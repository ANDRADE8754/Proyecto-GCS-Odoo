from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TechstoreMantenimientoHistorial(models.Model):
    _name = 'techstore.mantenimiento.historial'
    _description = 'Historial de Estados - Mantenimiento TechStore'
    _order = 'fecha_cambio desc, id desc'

    mantenimiento_id = fields.Many2one(
        'techstore.mantenimiento',
        string='Mantenimiento',
        required=True,
        ondelete='cascade',
        index=True,
    )
    id_estado = fields.Many2one(
        'techstore.estado',
        string='Estado',
        required=True,
        ondelete='restrict',
        index=True,
    )
    fecha_cambio = fields.Datetime(
        string='Fecha de Cambio',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario',
        default=lambda self: self.env.user,
        readonly=True,
    )
    observacion = fields.Text(
        string='Observacion',
        help='Detalle del cambio de estado'
    )

    def write(self, vals):
        raise ValidationError(_('El historial de estados es inmutable.'))

    def unlink(self):
        raise ValidationError(_('El historial de estados no se puede eliminar.'))
