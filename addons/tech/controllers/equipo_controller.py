from odoo import http
from odoo.http import request


class EquipoController(http.Controller):

    # ===================================
    # CREAR
    # ===================================

    @http.route(
        '/api/equipos',
        type='json',
        auth='user',
        methods=['POST'],
        csrf=False
    )
    def crear_equipo(self, **data):

        equipo = request.env['techstore.equipo'].sudo()

        return equipo.crear_equipo({
            'name': data.get('name'),
            'cliente_id': data.get('cliente_id'),
            'tipo_equipo': data.get('tipo_equipo'),
            'marca': data.get('marca'),
            'modelo': data.get('modelo'),
            'serial': data.get('serial'),
            'estado': data.get('estado'),
            'observaciones': data.get('observaciones')
        })

    # ===================================
    # LISTAR TODOS
    # ===================================

    @http.route(
        '/api/equipos',
        type='json',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def listar_equipos(self):

        equipos = request.env['techstore.equipo'].sudo().search([])

        data = []

        for equipo in equipos:
            data.append({
                'id': equipo.id,
                'name': equipo.name,
                'cliente': equipo.cliente_id.name,
                'marca': equipo.marca,
                'modelo': equipo.modelo,
                'estado': equipo.estado
            })

        return data

    # ===================================
    # OBTENER POR ID
    # ===================================

    @http.route(
        '/api/equipos/<int:id>',
        type='json',
        auth='user',
        methods=['GET'],
        csrf=False
    )
    def obtener_equipo(self, id):

        equipo = request.env['techstore.equipo'].sudo().browse(id)

        if not equipo.exists():
            return {
                'success': False,
                'message': 'Equipo no encontrado'
            }

        return equipo.obtener_equipo()

    # ===================================
    # ACTUALIZAR
    # ===================================

    @http.route(
        '/api/equipos/<int:id>',
        type='json',
        auth='user',
        methods=['PUT'],
        csrf=False
    )
    def actualizar_equipo(self, id, **data):

        equipo = request.env['techstore.equipo'].sudo().browse(id)

        if not equipo.exists():
            return {
                'success': False,
                'message': 'Equipo no encontrado'
            }

        return equipo.actualizar_equipo(data)

    # ===================================
    # ELIMINAR
    # ===================================

    @http.route(
        '/api/equipos/<int:id>',
        type='json',
        auth='user',
        methods=['DELETE'],
        csrf=False
    )
    def eliminar_equipo(self, id):

        equipo = request.env['techstore.equipo'].sudo().browse(id)

        if not equipo.exists():
            return {
                'success': False,
                'message': 'Equipo no encontrado'
            }

        return equipo.eliminar_equipo()