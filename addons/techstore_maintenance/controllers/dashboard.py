# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class TechstoreDashboardController(http.Controller):

    @http.route('/techstore_maintenance/dashboard_banner', type='json', auth='user')
    def get_dashboard_banner(self):
        mantenimiento_obj = request.env['techstore.mantenimiento']
        tecnico_obj = request.env['techstore.tecnico']
        cliente_obj = request.env['techstore.cliente']
        equipo_obj = request.env['techstore.equipo']

        total_mantenimientos = mantenimiento_obj.search_count([])
        retrasados = mantenimiento_obj.search_count([('esta_retrasado', '=', True)])
        
        # Estados
        nuevos = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'nuevo')])
        en_diagnostico = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'diagnostico')])
        en_reparacion = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'reparacion')])
        esperando_repuestos = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'esperando_repuestos')])
        en_control_calidad = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'control_calidad')])
        listo_entrega = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'listo_entrega')])
        entregados = mantenimiento_obj.search_count([('id_estado.nombre_estado', '=', 'entregado')])

        en_proceso = nuevos + en_diagnostico + en_reparacion + esperando_repuestos + en_control_calidad
        completados = listo_entrega + entregados

        total_tecnicos = tecnico_obj.search_count([])
        tecnicos_disponibles = tecnico_obj.search_count([('disponibilidad', '=', True)])

        total_clientes = cliente_obj.search_count([])
        total_equipos = equipo_obj.search_count([])

        # Promedio tiempo atención
        tiempos = mantenimiento_obj.search([('tiempo_atencion_horas', '>', 0)]).mapped('tiempo_atencion_horas')
        promedio_horas = round(sum(tiempos) / len(tiempos), 1) if tiempos else 0.0

        # Rendimiento general SLA
        tasa_cumplimiento = round(((total_mantenimientos - retrasados) / total_mantenimientos * 100), 1) if total_mantenimientos > 0 else 100.0

        # Valores para la plantilla QWeb
        values = {
            'total': total_mantenimientos,
            'retrasados': retrasados,
            'en_proceso': en_proceso,
            'completados': completados,
            'total_tecnicos': total_tecnicos,
            'tecnicos_disponibles': tecnicos_disponibles,
            'total_clientes': total_clientes,
            'total_equipos': total_equipos,
            'promedio_horas': promedio_horas,
            'tasa_cumplimiento': tasa_cumplimiento,
            'nuevos': nuevos,
            'en_diagnostico': en_diagnostico,
            'en_reparacion': en_reparacion,
            'esperando_repuestos': esperando_repuestos,
        }

        # Renderizar la plantilla QWeb y retornar
        return request.env['ir.qweb']._render(
            'techstore_maintenance.techstore_dashboard_banner_template', values
        )
