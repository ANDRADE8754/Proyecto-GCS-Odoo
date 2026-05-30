from datetime import datetime, timedelta, time
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TechstoreReporteWizard(models.TransientModel):
    _name = 'techstore.reporte.wizard'
    _description = 'Asistente de Reportes - TechStore'

    fecha_inicio = fields.Date(
        string='Fecha de Inicio',
        required=True,
        default=lambda self: fields.Date.today() - timedelta(days=30),
        help='Fecha de inicio para el rango de reporte'
    )
    fecha_fin = fields.Date(
        string='Fecha de Fin',
        required=True,
        default=fields.Date.today,
        help='Fecha de fin para el rango de reporte'
    )
    ced_tecnico = fields.Many2one(
        'techstore.tecnico',
        string='Técnico Asignado',
        help='Filtrar por un técnico específico'
    )
    ced_cliente = fields.Many2one(
        'techstore.cliente',
        string='Cliente',
        help='Filtrar por un cliente específico'
    )
    id_prioridad = fields.Many2one(
        'techstore.prioridad',
        string='Prioridad',
        help='Filtrar por nivel de prioridad'
    )
    id_estado = fields.Many2one(
        'techstore.estado',
        string='Estado',
        help='Filtrar por estado del mantenimiento'
    )

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for rec in self:
            if rec.fecha_inicio > rec.fecha_fin:
                raise UserError(_('La fecha de inicio no puede ser posterior a la fecha de fin.'))

    def action_generar_reporte_pdf(self):
        self.ensure_one()
        return self.env.ref('techstore_maintenance.action_reporte_general_pdf').report_action(self)

    def _get_mantenimientos_reporte(self):
        self.ensure_one()
        # Convertir fechas de Date a Datetime para la comparación en el dominio
        start_datetime = datetime.combine(self.fecha_inicio, time.min)
        end_datetime = datetime.combine(self.fecha_fin, time.max)

        domain = [
            ('fecha_ingreso', '>=', start_datetime),
            ('fecha_ingreso', '<=', end_datetime)
        ]

        if self.ced_tecnico:
            domain.append(('ced_tecnico', '=', self.ced_tecnico.id))
        if self.ced_cliente:
            domain.append(('ced_cliente', '=', self.ced_cliente.id))
        if self.id_prioridad:
            domain.append(('id_prioridad', '=', self.id_prioridad.id))
        if self.id_estado:
            domain.append(('id_estado', '=', self.id_estado.id))

        return self.env['techstore.mantenimiento'].search(domain, order='fecha_ingreso asc')

    def get_report_kpis(self):
        self.ensure_one()
        mants = self._get_mantenimientos_reporte()
        total = len(mants)
        retrasados = len(mants.filtered(lambda m: m.esta_retrasado))
        pct_retrasados = (retrasados / total * 100) if total > 0 else 0.0
        
        tiempos = mants.filtered(lambda m: m.tiempo_atencion_horas > 0).mapped('tiempo_atencion_horas')
        promedio = (sum(tiempos) / len(tiempos)) if len(tiempos) > 0 else 0.0
        
        # Conteo por estados
        estados_count = {}
        for e in mants.mapped('id_estado'):
            estados_count[e.nombre_estado] = len(mants.filtered(lambda m: m.id_estado.id == e.id))
            
        return {
            'total': total,
            'retrasados': retrasados,
            'pct_retrasados': round(pct_retrasados, 1),
            'promedio_tiempo': round(promedio, 1),
            'estados_count': estados_count
        }

