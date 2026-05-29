from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class TechstoreEquipo(models.Model):
    _name = 'techstore.equipo'
    _description = 'Equipo - TechStore'
    _rec_name = 'id_equipo'
    _order = 'id_equipo desc'

    # Campos Principales
    id_equipo = fields.Char(
        string='ID del Equipo',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('techstore.equipo') or _('New'),
        help='Identificador único del equipo generado automáticamente'
    )
    ced_cliente = fields.Many2one(
        'techstore.cliente',
        string='Cliente',
        required=True,
        ondelete='cascade',
        index=True,
        help='Cliente propietario del equipo'
    )
    tipo_equipo = fields.Selection(
        [
            ('laptop', 'Laptop'),
            ('pc', 'PC Escritorio'),
            ('impresora', 'Impresora'),
            ('periferico', 'Periférico')
        ],
        string='Tipo de Equipo',
        required=True,
        index=True,
        help='Clasificación del equipo'
    )
    marca = fields.Char(
        string='Marca',
        required=True,
        help='Marca o fabricante del equipo'
    )
    modelo = fields.Char(
        string='Modelo',
        help='Modelo específico del equipo'
    )
    serial = fields.Char(
        string='Número Serial',
        required=True,
        help='Número de serie del equipo'
    )
    observaciones = fields.Text(
        string='Observaciones',
        help='Notas adicionales sobre el equipo'
    )

    # Relaciones One2many
    mantenimiento_ids = fields.One2many(
        'techstore.mantenimiento',
        'id_equipo',
        string='Mantenimientos',
        help='Historial de mantenimientos del equipo'
    )

    # Restricciones SQL
    _sql_constraints = [
        ('id_equipo_unique', 'UNIQUE(id_equipo)', 'El ID del equipo debe ser único.'),
        ('serial_ced_cliente_unique', 'UNIQUE(serial, ced_cliente)', 
         'El número serial debe ser único por cliente.'),
    ]

    @api.constrains('serial', 'ced_cliente')
    def _check_serial_unique_per_client(self):
        """Verifica que el serial sea único por cliente"""
        for record in self:
            if record.serial and record.ced_cliente:
                existing = self.search([
                    ('serial', '=', record.serial),
                    ('ced_cliente', '=', record.ced_cliente.id),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('El número serial "%s" ya existe para este cliente.') % record.serial
                    )

    def action_view_mantenimientos(self):
        """Abre la vista de mantenimientos del equipo"""
        self.ensure_one()
        action = self.env.ref('techstore_maintenance.action_techstore_mantenimiento').read()[0]
        action['domain'] = [('id_equipo', '=', self.id)]
        action['context'] = {
            'default_id_equipo': self.id,
            'default_ced_cliente': self.ced_cliente.id
        }
        return action

    def action_view_cliente(self):
        """Abre el formulario del cliente propietario"""
        self.ensure_one()
        if not self.ced_cliente:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cliente'),
            'res_model': 'techstore.cliente',
            'res_id': self.ced_cliente.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_guardar_y_volver(self):
        """Guarda y vuelve a la lista de equipos."""
        return self.env.ref('techstore_maintenance.action_techstore_equipo').read()[0]

    def action_cancelar_creacion(self):
        """Cancela la creación: elimina el registro si existe y vuelve a la lista."""
        if self.exists():
            try:
                self.sudo().unlink()
            except Exception:
                pass
        return self.env.ref('techstore_maintenance.action_techstore_equipo').read()[0]

    @api.model
    def create(self, vals):
        """Override create para asegurar la secuencia"""
        if vals.get('id_equipo', _('New')) == _('New'):
            vals['id_equipo'] = self.env['ir.sequence'].next_by_code('techstore.equipo') or _('New')
        return super().create(vals)

    def unlink(self):
        """Override unlink para controlar eliminación"""
        for record in self:
            if record.mantenimiento_ids:
                raise ValidationError(
                    _('No puedes eliminar un equipo que tiene mantenimientos asociados. '
                      'Por favor, elimina primero los mantenimientos.')
                )
        return super().unlink()

    @api.model
    def _get_tipo_equipo_display(self, tipo):
        """Helper para obtener la representación visual del tipo de equipo"""
        tipo_dict = dict(self._fields['tipo_equipo'].selection)
        return tipo_dict.get(tipo, tipo)