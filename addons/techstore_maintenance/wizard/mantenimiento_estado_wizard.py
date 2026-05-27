from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class TechstoreMantenimientoEstadoWizard(models.TransientModel):
    _name = 'techstore.mantenimiento.estado.wizard'
    _description = 'Cambio Secuencial de Estado de Mantenimiento'

    mantenimiento_id = fields.Many2one(
        'techstore.mantenimiento',
        string='Mantenimiento',
        required=True,
        readonly=True,
        ondelete='cascade',
    )
    estado_objetivo = fields.Selection(
        [
            ('diagnostico', 'Diagnóstico'),
            ('reparacion', 'Reparación'),
            ('esperando_repuestos', 'Esperando Repuestos'),
            ('finalizado', 'Finalizado'),
            ('entregado', 'Entregado'),
            ('nuevo', 'Nuevo'),
        ],
        string='Estado objetivo',
        required=True,
        readonly=True,
    )
    mostrar_tecnico = fields.Boolean(
        string='Mostrar Técnico',
        compute='_compute_mostrar_tecnico',
        readonly=True,
    )
    tecnico_id = fields.Many2one(
        'techstore.tecnico',
        string='Técnico',
        domain="[('disponibilidad', '=', True)]",
    )
    justificacion = fields.Text(
        string='Justificación',
        required=True,
    )
    pruebas = fields.Text(
        string='Pruebas Realizadas',
        help='Describe las pruebas realizadas al cambiar de estado',
    )

    @api.onchange('estado_objetivo')
    def _onchange_estado_objetivo(self):
        if self.estado_objetivo != 'diagnostico':
            self.tecnico_id = False

    @api.depends('estado_objetivo')
    def _compute_mostrar_tecnico(self):
        for record in self:
            record.mostrar_tecnico = record.estado_objetivo == 'diagnostico'

    def action_confirmar(self):
        self.ensure_one()
        if not self.mantenimiento_id:
            raise ValidationError(_('Falta el mantenimiento a actualizar.'))
        
        # Actualizar los campos de justificación y pruebas
        self.mantenimiento_id.write({
            'justificacion_cambio_estado': self.justificacion,
            'pruebas_cambio_estado': self.pruebas or '',
        })
        
        self.mantenimiento_id._aplicar_cambio_estado(
            self.estado_objetivo,
            self.justificacion,
            self.tecnico_id,
        )
        return {'type': 'ir.actions.act_window_close'}