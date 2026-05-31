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
    tipo_reporte = fields.Selection(
        [
            ('general', 'Reporte General'),
            ('sla', 'Tiempos de Resolución (SLA)'),
            ('rendimiento', 'Rendimiento por Técnico'),
            ('historial_equipo', 'Historial Clínico por Equipo'),
            ('reingreso', 'Tasa de Reingreso'),
            ('cuellos_botella', 'Cuellos de Botella'),
        ],
        string='Tipo de Reporte',
        default='general',
        required=True,
        help='Selecciona el tipo de reporte a generar'
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
    serial_equipo = fields.Char(
        string='Número Serial del Equipo',
        help='Buscar historial clínico por número serial del equipo'
    )

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for rec in self:
            if rec.fecha_inicio > rec.fecha_fin:
                raise UserError(_('La fecha de inicio no puede ser posterior a la fecha de fin.'))

    def action_generar_reporte_pdf(self):
        """Genera el reporte PDF según el tipo seleccionado"""
        self.ensure_one()
        report_map = {
            'general': 'techstore_maintenance.action_reporte_general_pdf',
            'sla': 'techstore_maintenance.action_reporte_sla_pdf',
            'rendimiento': 'techstore_maintenance.action_reporte_rendimiento_pdf',
            'historial_equipo': 'techstore_maintenance.action_reporte_historial_equipo_pdf',
            'reingreso': 'techstore_maintenance.action_reporte_reingreso_pdf',
            'cuellos_botella': 'techstore_maintenance.action_reporte_cuellos_botella_pdf',
        }
        report_ref = report_map.get(self.tipo_reporte, 'techstore_maintenance.action_reporte_general_pdf')
        return self.env.ref(report_ref).report_action(self)

    def _get_mantenimientos_reporte(self):
        self.ensure_one()
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
        """KPIs generales para el reporte general"""
        self.ensure_one()
        mants = self._get_mantenimientos_reporte()
        total = len(mants)
        retrasados = len(mants.filtered(lambda m: m.esta_retrasado))
        pct_retrasados = (retrasados / total * 100) if total > 0 else 0.0
        
        tiempos = mants.filtered(lambda m: m.tiempo_atencion_horas > 0).mapped('tiempo_atencion_horas')
        promedio = (sum(tiempos) / len(tiempos)) if len(tiempos) > 0 else 0.0
        
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

    # ═══════════════════════════════════════════
    # REPORTE 1: Tiempos de Resolución (SLA)
    # ═══════════════════════════════════════════
    def get_reporte_sla(self):
        """Mide el tiempo promedio desde ingreso hasta entrega.
        Detecta y corrige retrasos en atenciones."""
        self.ensure_one()
        mants = self._get_mantenimientos_reporte()
        total = len(mants)
        
        # Mantenimientos entregados (con fecha de entrega)
        entregados = mants.filtered(lambda m: m.fecha_entrega)
        total_entregados = len(entregados)
        
        # Tiempo promedio de resolución (horas)
        tiempos = entregados.mapped('tiempo_atencion_horas')
        promedio_horas = round(sum(tiempos) / len(tiempos), 2) if tiempos else 0.0
        
        # Desglose por prioridad
        prioridades = self.env['techstore.prioridad'].search([])
        sla_por_prioridad = []
        for prioridad in prioridades:
            mants_prioridad = entregados.filtered(lambda m: m.id_prioridad.id == prioridad.id)
            tiempos_p = mants_prioridad.mapped('tiempo_atencion_horas')
            dentro_sla = len(mants_prioridad.filtered(
                lambda m: m.tiempo_atencion_horas <= prioridad.tiempo_maximo
            ))
            total_p = len(mants_prioridad)
            sla_por_prioridad.append({
                'prioridad': prioridad,
                'nombre': prioridad.get_nombre_display(),
                'total': total_p,
                'tiempo_maximo': prioridad.tiempo_maximo,
                'promedio_horas': round(sum(tiempos_p) / len(tiempos_p), 2) if tiempos_p else 0.0,
                'dentro_sla': dentro_sla,
                'fuera_sla': total_p - dentro_sla,
                'pct_cumplimiento': round(dentro_sla / total_p * 100, 1) if total_p > 0 else 100.0,
                'color': prioridad.color,
            })
        
        # % global de cumplimiento SLA
        total_dentro = sum(s['dentro_sla'] for s in sla_por_prioridad)
        pct_global = round(total_dentro / total_entregados * 100, 1) if total_entregados > 0 else 100.0
        
        # Retrasados activos (sin entregar y fuera de tiempo)
        retrasados_activos = mants.filtered(lambda m: m.esta_retrasado and not m.fecha_entrega)
        
        return {
            'total': total,
            'total_entregados': total_entregados,
            'promedio_horas': promedio_horas,
            'pct_cumplimiento_global': pct_global,
            'sla_por_prioridad': sla_por_prioridad,
            'retrasados_activos': retrasados_activos,
            'total_retrasados_activos': len(retrasados_activos),
        }

    # ═══════════════════════════════════════════
    # REPORTE 2: Rendimiento por Técnico
    # ═══════════════════════════════════════════
    def get_rendimiento_tecnico(self):
        """Cantidad de mantenimientos completados por técnico
        y tiempo promedio de cada uno."""
        self.ensure_one()
        mants = self._get_mantenimientos_reporte()
        
        tecnicos = self.env['techstore.tecnico'].search([])
        rendimiento = []
        for tecnico in tecnicos:
            mants_tecnico = mants.filtered(lambda m: m.ced_tecnico.id == tecnico.id)
            total = len(mants_tecnico)
            completados = mants_tecnico.filtered(lambda m: m.fecha_entrega)
            en_proceso = mants_tecnico.filtered(lambda m: not m.fecha_entrega)
            
            tiempos = completados.mapped('tiempo_atencion_horas')
            promedio = round(sum(tiempos) / len(tiempos), 2) if tiempos else 0.0
            
            retrasados = len(mants_tecnico.filtered(lambda m: m.esta_retrasado))
            
            rendimiento.append({
                'tecnico': tecnico,
                'nombre': tecnico.nombre,
                'especialidad': tecnico.especialidad,
                'total_asignados': total,
                'completados': len(completados),
                'en_proceso': len(en_proceso),
                'promedio_horas': promedio,
                'retrasados': retrasados,
                'disponible': tecnico.disponibilidad,
                'carga_actual': tecnico.carga_trabajo,
            })
        
        # Ordenar por completados (descendente)
        rendimiento.sort(key=lambda x: x['completados'], reverse=True)
        
        return {
            'rendimiento': rendimiento,
            'total_tecnicos': len(tecnicos),
            'total_mantenimientos': len(mants),
        }

    # ═══════════════════════════════════════════
    # REPORTE 3: Historial Clínico por Equipo
    # ═══════════════════════════════════════════
    def get_historial_equipo(self):
        """Busca por número de serie y devuelve todas las fallas previas."""
        self.ensure_one()
        domain = []
        if self.serial_equipo:
            domain = [('serial', 'ilike', self.serial_equipo.strip())]
        elif self.ced_cliente:
            domain = [('ced_cliente', '=', self.ced_cliente.id)]
        
        equipos = self.env['techstore.equipo'].search(domain)
        historial = []
        for equipo in equipos:
            mantenimientos = equipo.mantenimiento_ids.sorted(key=lambda m: m.fecha_ingreso, reverse=True)
            historial.append({
                'equipo': equipo,
                'id_equipo': equipo.id_equipo,
                'serial': equipo.serial,
                'tipo': equipo._get_tipo_equipo_display(equipo.tipo_equipo),
                'marca': equipo.marca,
                'modelo': equipo.modelo or 'N/A',
                'cliente': equipo.ced_cliente.nombre,
                'total_mantenimientos': len(mantenimientos),
                'mantenimientos': mantenimientos,
            })
        
        return {
            'historial': historial,
            'total_equipos': len(equipos),
            'serial_buscado': self.serial_equipo or 'Todos',
        }

    # ═══════════════════════════════════════════
    # REPORTE 4: Tasa de Reingreso (Calidad)
    # ═══════════════════════════════════════════
    def get_tasa_reingreso(self):
        """¿Cuántos equipos vuelven por el mismo problema antes de 30 días?
        Esta es la métrica de calidad más importante."""
        self.ensure_one()
        mants = self._get_mantenimientos_reporte()
        
        # Agrupar mantenimientos por equipo
        equipos_mants = {}
        for m in mants:
            equipo_id = m.id_equipo.id
            if equipo_id not in equipos_mants:
                equipos_mants[equipo_id] = []
            equipos_mants[equipo_id].append(m)
        
        reingresos = []
        total_equipos_analizados = 0
        total_reingresos = 0
        
        for equipo_id, manteniminetos in equipos_mants.items():
            if len(manteniminetos) < 2:
                total_equipos_analizados += 1
                continue
            
            total_equipos_analizados += 1
            # Ordenar por fecha
            manteniminetos_sorted = sorted(manteniminetos, key=lambda m: m.fecha_ingreso)
            
            for i in range(1, len(manteniminetos_sorted)):
                prev = manteniminetos_sorted[i - 1]
                curr = manteniminetos_sorted[i]
                
                # Verificar si volvió dentro de 30 días
                if prev.fecha_entrega:
                    delta = curr.fecha_ingreso - prev.fecha_entrega
                    if delta.days <= 30:
                        total_reingresos += 1
                        reingresos.append({
                            'equipo': curr.id_equipo,
                            'serial': curr.id_equipo.serial,
                            'cliente': curr.ced_cliente.nombre,
                            'mantenimiento_previo': prev.id_mantenimiento,
                            'falla_previa': prev.falla_reportada,
                            'fecha_entrega_previo': prev.fecha_entrega,
                            'mantenimiento_actual': curr.id_mantenimiento,
                            'falla_actual': curr.falla_reportada,
                            'fecha_ingreso_actual': curr.fecha_ingreso,
                            'dias_reingreso': delta.days,
                        })
        
        tasa = round(total_reingresos / total_equipos_analizados * 100, 1) if total_equipos_analizados > 0 else 0.0
        
        return {
            'reingresos': reingresos,
            'total_reingresos': total_reingresos,
            'total_equipos_analizados': total_equipos_analizados,
            'tasa_reingreso': tasa,
        }

    # ═══════════════════════════════════════════
    # REPORTE 5: Cuellos de Botella (Estados)
    # ═══════════════════════════════════════════
    def get_cuellos_botella(self):
        """Cuántos tickets están estancados en cada estado.
        Muestra estados problemáticos y tiempos de permanencia."""
        self.ensure_one()
        # Mantenimientos activos (no entregados)
        mants_activos = self.env['techstore.mantenimiento'].search([
            ('nombre_estado', 'not in', ['entregado']),
        ])

        now = datetime.now()

        def _fecha_inicio_estado(mantenimiento):
            if mantenimiento.state_tracking:
                ultimo = mantenimiento.state_tracking.sorted(key=lambda r: r.fecha_cambio)[-1]
                return ultimo.fecha_cambio
            return mantenimiento.fecha_ingreso
        
        estados = self.env['techstore.estado'].search([], order='secuencia asc')
        cuellos = []
        for estado in estados:
            if estado.nombre_estado == 'entregado':
                continue
            mants_estado = mants_activos.filtered(lambda m: m.id_estado.id == estado.id)
            total = len(mants_estado)
            
            # Calcular tiempo promedio de permanencia en este estado
            tiempos_permanencia = []
            for m in mants_estado:
                fecha_inicio = _fecha_inicio_estado(m)
                if not fecha_inicio:
                    continue
                delta = now - fecha_inicio.replace(tzinfo=None)
                tiempos_permanencia.append(round(delta.total_seconds() / 3600, 2))
            
            promedio_permanencia = round(sum(tiempos_permanencia) / len(tiempos_permanencia), 2) if tiempos_permanencia else 0.0
            retrasados = len(mants_estado.filtered(lambda m: m.esta_retrasado))
            
            cuellos.append({
                'estado': estado,
                'nombre': estado.get_nombre_estado_display(),
                'total': total,
                'retrasados': retrasados,
                'promedio_permanencia_horas': promedio_permanencia,
                'es_critico': total > 5 or retrasados > 2,
                'mantenimientos': mants_estado,
            })
        
        # Total de tickets activos
        total_activos = len(mants_activos)
        total_retrasados = len(mants_activos.filtered(lambda m: m.esta_retrasado))
        
        return {
            'cuellos': cuellos,
            'total_activos': total_activos,
            'total_retrasados': total_retrasados,
            'pct_retrasados': round(total_retrasados / total_activos * 100, 1) if total_activos > 0 else 0.0,
        }
