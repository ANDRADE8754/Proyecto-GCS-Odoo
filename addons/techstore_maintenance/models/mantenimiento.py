from datetime import datetime, timedelta
import logging

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class TechstoreMantenimiento(models.Model):
    _name = 'techstore.mantenimiento'
    _description = 'Mantenimiento - TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'id_mantenimiento'
    _order = 'fecha_ingreso desc'

    id_mantenimiento = fields.Char(
        string='ID del Mantenimiento',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default='Nuevo',
        help='Identificador único del mantenimiento'
    )

    ced_cliente = fields.Many2one(
        'techstore.cliente',
        string='Cliente',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Cliente propietario del equipo'
    )
    id_equipo = fields.Many2one(
        'techstore.equipo',
        string='Equipo',
        required=True,
        ondelete='restrict',
        tracking=True,
        help='Equipo a intervenir'
    )
    ced_tecnico = fields.Many2one(
        'techstore.tecnico',
        string='Técnico Asignado',
        ondelete='set null',
        tracking=True,
        help='Técnico responsable del mantenimiento'
    )
    id_prioridad = fields.Many2one(
        'techstore.prioridad',
        string='Prioridad',
        required=True,
        default=lambda self: self.env['techstore.prioridad'].search([('nombre', '=', 'media')], limit=1),
        tracking=True,
        help='Nivel de prioridad del mantenimiento'
    )
    id_estado = fields.Many2one(
        'techstore.estado',
        string='Estado',
        required=True,
        default=lambda self: self.env['techstore.estado'].search([('nombre_estado', '=', 'ingresado')], limit=1),
        tracking=True,
        help='Estado actual del mantenimiento'
        ,group_expand='_group_expand_id_estado'
    )

    nombre_estado = fields.Selection(
        related='id_estado.nombre_estado',
        string='Nombre del Estado',
        store=True,
        readonly=True,
        help='Nombre técnico del estado actual'
    )

    es_estado_final = fields.Boolean(
        related='id_estado.es_estado_final',
        string='¿Es Estado Final?',
        store=True,
        readonly=True,
        help='Indica si el estado actual es final'
    )

    fecha_ingreso = fields.Datetime(
        string='Fecha de Ingreso',
        required=True,
        default=fields.Datetime.now,
        readonly=True,
        tracking=True,
        help='Fecha de registro del mantenimiento'
    )
    fecha_entrega = fields.Datetime(
        string='Fecha de Entrega',
        tracking=True,
        help='Fecha en que se entrega el equipo al cliente'
    )
    fecha_estimada_entrega = fields.Datetime(
        string='Fecha Estimada de Entrega',
        compute='_compute_fecha_estimada_entrega',
        store=True,
        help='Fecha estimada según la prioridad'
    )

    falla_reportada = fields.Text(
        string='Falla Reportada',
        required=True,
        tracking=True,
        help='Descripción del problema reportado por el cliente'
    )
    descripcion_problema = fields.Text(
        string='Descripción del Problema',
        help='Análisis inicial del incidente'
    )
    diagnostico = fields.Text(
        string='Diagnóstico',
        help='Diagnóstico técnico realizado'
    )
    solucion = fields.Text(
        string='Solución Aplicada',
        help='Descripción de la solución implementada'
    )
    
    justificacion_cambio_estado = fields.Text(
        string='Justificación del Cambio de Estado',
        help='Justificación cuando se cambia el estado del mantenimiento'
    )
    
    pruebas_cambio_estado = fields.Text(
        string='Pruebas del Cambio de Estado',
        help='Pruebas realizadas al cambiar de estado'
    )

    tiempo_atencion_horas = fields.Float(
        string='Tiempo de Atención (Horas)',
        compute='_compute_tiempo_atencion_horas',
        store=True,
        help='Horas entre ingreso y entrega'
    )
    esta_retrasado = fields.Boolean(
        string='¿Está Retrasado?',
        compute='_compute_esta_retrasado',
        store=True,
        help='Indica si el mantenimiento está retrasado respecto a la prioridad'
    )

    puede_pasar_diagnostico = fields.Boolean(
        string='Puede pasar a Diagnóstico',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    puede_pasar_pendiente_asignacion = fields.Boolean(
        string='Puede pasar a Pendiente de Asignacion',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    puede_pasar_reparacion = fields.Boolean(
        string='Puede pasar a Reparación',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    puede_pasar_esperando_repuestos = fields.Boolean(
        string='Puede pasar a Esperando Repuestos',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    puede_pasar_control_calidad = fields.Boolean(
        string='Puede pasar a Control de Calidad',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    puede_pasar_listo_entrega = fields.Boolean(
        string='Puede pasar a Listo para Entrega',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    # Compatibilidad con vistas antiguas que usan "finalizado".
    puede_pasar_finalizado = fields.Boolean(
        string='Puede pasar a Listo para Entrega',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )
    puede_pasar_entregado = fields.Boolean(
        string='Puede pasar a Entregado',
        compute='_compute_pasos_estado',
        help='Control visual para mostrar el siguiente paso permitido'
    )

    fecha_pausa_repuestos = fields.Datetime(
        string='Fecha Pausa por Repuestos',
        help='Fecha en que se pausó el mantenimiento por falta de repuestos (para pausar métricas SLA)'
    )
    tiempo_pausado_horas = fields.Float(
        string='Tiempo Pausado (Horas)',
        default=0.0,
        help='Horas acumuladas en estado Esperando Repuestos (excluidas del SLA)'
    )
    
    es_tecnico_jefe = fields.Boolean(
        string='Usuario es Técnico Jefe',
        compute='_compute_es_tecnico_jefe',
        help='Indica si el usuario actual es técnico jefe o superior'
    )
    
    es_recepcionista = fields.Boolean(
        string='Usuario es Recepcionista',
        compute='_compute_es_recepcionista',
        help='Indica si el usuario actual es recepcionista'
    )

    es_administrador = fields.Boolean(
        string='Usuario es Administrador',
        compute='_compute_es_administrador',
        help='Indica si el usuario actual es administrador del sistema'
    )

    es_gerencia = fields.Boolean(
        string='Usuario es Gerencia',
        compute='_compute_es_gerencia',
        help='Indica si el usuario actual es gerencia o administrador'
    )
    
    puede_modificar_datos_iniciales = fields.Boolean(
        string='Puede Modificar Datos Iniciales',
        compute='_compute_puede_modificar_datos_iniciales',
        help='Indica si se pueden modificar cliente, equipo y prioridad'
    )

    es_estado_nuevo = fields.Boolean(
        string='Estado es Ingresado',
        compute='_compute_es_estado_nuevo',
        help='Indica si el mantenimiento está en estado ingresado'
    )

    state_tracking = fields.One2many(
        'techstore.mantenimiento.historial',
        'mantenimiento_id',
        string='Historial de Estados',
        readonly=True,
        help='Registro de cambios de estado del mantenimiento'
    )

    # Flujo de estados con bifurcacion en 'reparacion':
    # ingresado → pendiente_asignacion → diagnostico → reparacion → [esperando_repuestos ↔ reparacion] → control_calidad → listo_entrega → entregado
    _SECUENCIA_ESTADOS = {
        'ingresado': ['pendiente_asignacion'],
        'pendiente_asignacion': ['diagnostico'],
        'diagnostico': ['reparacion'],
        'reparacion': ['esperando_repuestos', 'control_calidad'],
        'esperando_repuestos': ['reparacion'],  # Vuelve a reparacion cuando llegan repuestos
        'control_calidad': ['listo_entrega'],
        'listo_entrega': ['entregado'],
        'entregado': [],
    }

    _sql_constraints = [
        ('id_mantenimiento_unique', 'UNIQUE(id_mantenimiento)', 'El ID del mantenimiento debe ser único.'),
        ('fecha_entrega_coherencia', 'CHECK(fecha_entrega IS NULL OR fecha_entrega >= fecha_ingreso)', 'La fecha de entrega no puede ser anterior a la fecha de ingreso.'),
    ]

    @api.onchange('ced_cliente')
    def _onchange_ced_cliente(self):
        if self.ced_cliente:
            if self.id_equipo and self.id_equipo.ced_cliente.id != self.ced_cliente.id:
                self.id_equipo = False
            return {'domain': {'id_equipo': [('ced_cliente', '=', self.ced_cliente.id)]}}
        return {'domain': {'id_equipo': [('id', '=', False)]}}

    @api.onchange('id_equipo')
    def _onchange_id_equipo(self):
        if self.id_equipo:
            self.ced_cliente = self.id_equipo.ced_cliente
            # Validar que el equipo exista
            if not self.id_equipo.exists():
                return {'warning': {
                    'title': _('Error'),
                    'message': _('El equipo seleccionado no existe o ha sido eliminado.')
                }}

    @api.onchange('ced_cliente')
    def _onchange_ced_cliente_validar(self):
        """Validar que el cliente exista y tenga datos válidos"""
        if self.ced_cliente:
            if not self.ced_cliente.exists():
                return {'warning': {
                    'title': _('Error'),
                    'message': _('El cliente seleccionado no existe o ha sido eliminado.')
                }}
            if not self.ced_cliente.ced_cliente or not self.ced_cliente.nombre:
                return {'warning': {
                    'title': _('Advertencia'),
                    'message': _('El cliente debe tener cédula y nombre registrados.')
                }}

    @api.onchange('id_prioridad')
    def _onchange_id_prioridad_validar(self):
        """Validar que la prioridad exista"""
        if self.id_prioridad:
            if not self.id_prioridad.exists():
                return {'warning': {
                    'title': _('Error'),
                    'message': _('La prioridad seleccionada no existe o ha sido eliminada.')
                }}

    @api.onchange('falla_reportada')
    def _onchange_falla_reportada_validar(self):
        """Validar que la falla reportada tenga contenido mínimo"""
        if self.falla_reportada:
            texto_limpio = self.falla_reportada.strip()
            if len(texto_limpio) < 10:
                return {'warning': {
                    'title': _('Descripción Insuficiente'),
                    'message': _('La descripción de la falla debe tener al menos 10 caracteres. '
                              'Proporciona una descripción más detallada del problema.')
                }}
            # Verificar que no sea solo números o caracteres especiales
            if not any(c.isalpha() for c in texto_limpio):
                return {'warning': {
                    'title': _('Descripción Inválida'),
                    'message': _('La descripción de la falla debe contener caracteres alfabéticos válidos.')
                }}

    @api.depends('id_prioridad', 'fecha_ingreso')
    def _compute_fecha_estimada_entrega(self):
        for record in self:
            if record.id_prioridad and record.fecha_ingreso:
                horas = record.id_prioridad.tiempo_maximo or 0
                record.fecha_estimada_entrega = record.fecha_ingreso + timedelta(hours=horas)
            else:
                record.fecha_estimada_entrega = False

    @api.depends('fecha_ingreso', 'fecha_entrega', 'tiempo_pausado_horas', 'fecha_pausa_repuestos')
    def _compute_tiempo_atencion_horas(self):
        for record in self:
            if record.fecha_ingreso and record.fecha_entrega:
                delta = record.fecha_entrega - record.fecha_ingreso
                total_horas = delta.total_seconds() / 3600
                pausa_actual = 0.0
                if record.fecha_pausa_repuestos:
                    pausa_delta = datetime.now() - record.fecha_pausa_repuestos.replace(tzinfo=None)
                    pausa_actual = max(pausa_delta.total_seconds() / 3600, 0.0)
                horas_efectivas = max(total_horas - (record.tiempo_pausado_horas + pausa_actual), 0.0)
                record.tiempo_atencion_horas = round(horas_efectivas, 2)
            else:
                record.tiempo_atencion_horas = 0.0

    @api.depends('fecha_estimada_entrega', 'id_estado')
    def _compute_esta_retrasado(self):
        for record in self:
            if record.fecha_estimada_entrega and record.id_estado and not record.id_estado.es_estado_final:
                record.esta_retrasado = datetime.now() > record.fecha_estimada_entrega.replace(tzinfo=None)
            else:
                record.esta_retrasado = False

    @api.model
    def _group_expand_id_estado(self, estados, domain, order):
        return self.env['techstore.estado'].search([], order='secuencia asc, id asc')

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        result = super().read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

        groupby_field = groupby[0] if isinstance(groupby, (list, tuple)) and groupby else groupby
        if groupby_field != 'id_estado':
            return result

        all_estados = self.env['techstore.estado'].search([], order='secuencia asc, id asc')
        groups_by_id = {}
        for group in result:
            value = group.get('id_estado')
            if isinstance(value, tuple) and value:
                groups_by_id[value[0]] = group

        for estado in all_estados:
            if estado.id in groups_by_id:
                continue
            result.append({
                'id_estado': (estado.id, estado.display_name),
                'id_estado_count': 0,
                '__domain': [('id_estado', '=', estado.id)],
                '__context': {},
                '__fold': False,
            })

        result.sort(key=lambda group: next((index for index, estado in enumerate(all_estados) if group.get('id_estado') and group['id_estado'][0] == estado.id), len(all_estados)))
        return result

    @api.depends('id_estado')
    def _compute_pasos_estado(self):
        for record in self:
            estado_actual = record.id_estado.nombre_estado if record.id_estado else 'ingresado'
            record.puede_pasar_pendiente_asignacion = estado_actual == 'ingresado'
            record.puede_pasar_diagnostico = estado_actual == 'pendiente_asignacion'
            record.puede_pasar_reparacion = estado_actual in ('diagnostico', 'esperando_repuestos')
            record.puede_pasar_esperando_repuestos = estado_actual == 'reparacion'
            record.puede_pasar_control_calidad = estado_actual == 'reparacion'
            record.puede_pasar_listo_entrega = estado_actual == 'control_calidad'
            record.puede_pasar_finalizado = record.puede_pasar_listo_entrega
            record.puede_pasar_entregado = estado_actual == 'listo_entrega'

    @api.depends()
    def _compute_es_tecnico_jefe(self):
        """Verifica si el usuario actual pertenece al grupo Jefe Técnico o superior"""
        is_boss = self.env.user.has_group('techstore_maintenance.techstore_group_technical_boss')
        for record in self:
            record.es_tecnico_jefe = is_boss

    @api.depends()
    def _compute_es_recepcionista(self):
        """Verifica si el usuario actual pertenece al grupo Recepcionista"""
        is_receptionist = self.env.user.has_group('techstore_maintenance.techstore_group_receptionist')
        for record in self:
            record.es_recepcionista = is_receptionist

    @api.depends()
    def _compute_es_administrador(self):
        """Verifica si el usuario actual pertenece al grupo Administrador del Sistema"""
        is_admin = self.env.user.has_group('techstore_maintenance.techstore_group_admin')
        for record in self:
            record.es_administrador = is_admin

    @api.depends()
    def _compute_es_gerencia(self):
        """Verifica si el usuario actual pertenece al grupo Gerencia o superior"""
        is_manager = self.env.user.has_group('techstore_maintenance.techstore_group_manager')
        for record in self:
            record.es_gerencia = is_manager

    @api.depends('id_estado')
    def _compute_puede_modificar_datos_iniciales(self):
        """Permite modificar datos iniciales solo en estado ingresado y si el usuario tiene permisos"""
        is_receptionist = self.env.user.has_group('techstore_maintenance.techstore_group_receptionist')
        is_manager = self.env.user.has_group('techstore_maintenance.techstore_group_manager')
        for record in self:
            estado_actual = record.id_estado.nombre_estado if record.id_estado else 'ingresado'
            record.puede_modificar_datos_iniciales = estado_actual == 'ingresado' and (is_receptionist or is_manager)

    @api.depends('id_estado')
    def _compute_es_estado_nuevo(self):
        """Verifica si el estado actual es ingresado"""
        for record in self:
            estado_actual = record.id_estado.nombre_estado if record.id_estado else 'ingresado'
            record.es_estado_nuevo = estado_actual == 'ingresado'

    @api.constrains('ced_cliente', 'id_equipo')
    def _check_equipo_pertenece_cliente(self):
        for record in self:
            if record.ced_cliente and record.id_equipo and record.id_equipo.ced_cliente.id != record.ced_cliente.id:
                raise ValidationError(
                    _('El equipo "%s" no pertenece al cliente "%s".') % (
                        record.id_equipo.id_equipo,
                        record.ced_cliente.nombre,
                    )
                )

    @api.constrains('fecha_entrega', 'fecha_ingreso')
    def _check_fecha_entrega_coherencia(self):
        for record in self:
            if record.fecha_entrega and record.fecha_ingreso and record.fecha_entrega < record.fecha_ingreso:
                raise ValidationError(_('La fecha de entrega no puede ser anterior a la fecha de ingreso.'))

    @api.constrains('id_estado', 'fecha_entrega')
    def _check_fecha_entrega_requerida(self):
        for record in self:
            if record.id_estado and record.id_estado.es_estado_final and not record.fecha_entrega:
                raise ValidationError(_('La fecha de entrega es requerida cuando el estado es "%s".') % record.id_estado.nombre_estado)

    @api.constrains('ced_cliente')
    def _check_cliente_valido(self):
        """Validar que el cliente tenga datos completos"""
        for record in self:
            if record.ced_cliente:
                if not record.ced_cliente.ced_cliente:
                    raise ValidationError(
                        _('El cliente debe tener una cédula registrada antes de usarlo en un mantenimiento.')
                    )
                if not record.ced_cliente.nombre:
                    raise ValidationError(
                        _('El cliente debe tener un nombre registrado antes de usarlo en un mantenimiento.')
                    )
                # En el modelo `techstore.cliente` el campo de correo se llama `correo`.
                if not record.ced_cliente.correo and not record.ced_cliente.telefono:
                    raise ValidationError(
                        _('El cliente debe tener al menos un correo o teléfono de contacto registrado.')
                    )

    @api.constrains('falla_reportada')
    def _check_falla_reportada_valida(self):
        """Validar que la falla reportada tenga contenido significativo"""
        for record in self:
            if record.falla_reportada:
                texto_limpio = record.falla_reportada.strip()
                if len(texto_limpio) < 10:
                    raise ValidationError(
                        _('La descripción de la falla debe tener al menos 10 caracteres. '
                          'Proporciona más detalles sobre el problema reportado.')
                    )
                if not any(c.isalpha() for c in texto_limpio):
                    raise ValidationError(
                        _('La descripción de la falla debe contener caracteres alfabéticos válidos.')
                    )

    @api.model_create_multi
    def create(self, vals_list):
        def _to_m2o_id(value):
            if isinstance(value, int):
                return value
            if isinstance(value, (list, tuple)):
                return value[0] if value else False
            if isinstance(value, str) and value.isdigit():
                return int(value)
            return False

        for vals in vals_list:
            vals['ced_cliente'] = _to_m2o_id(vals.get('ced_cliente'))
            vals['id_equipo'] = _to_m2o_id(vals.get('id_equipo'))

            if not vals.get('ced_cliente') and not vals.get('id_equipo'):
                raise ValidationError(_('Debes seleccionar Cliente y Equipo desde la lista desplegable antes de guardar el mantenimiento.'))

            if not vals.get('ced_cliente') and self.env.context.get('default_ced_cliente'):
                vals['ced_cliente'] = self.env.context.get('default_ced_cliente')
            if not vals.get('id_mantenimiento') or vals['id_mantenimiento'] == 'Nuevo':
                vals['id_mantenimiento'] = self.env['ir.sequence'].next_by_code('techstore.mantenimiento') or _('New')
            if not vals.get('ced_cliente') and vals.get('id_equipo'):
                equipo = self.env['techstore.equipo'].browse(vals['id_equipo'])
                if equipo.exists():
                    vals['ced_cliente'] = equipo.ced_cliente.id
            if not vals.get('ced_cliente'):
                _logger.warning(
                    'Create mantenimiento sin ced_cliente. vals=%s context_defaults={default_ced_cliente:%s, default_id_equipo:%s}',
                    vals,
                    self.env.context.get('default_ced_cliente'),
                    self.env.context.get('default_id_equipo'),
                )
                raise ValidationError(_('Debes seleccionar un cliente válido antes de guardar el mantenimiento.'))
            if not vals.get('id_equipo'):
                raise ValidationError(_('Debes seleccionar un equipo válido del cliente antes de guardar el mantenimiento.'))
            if not vals.get('id_estado'):
                estado_ingresado = self.env['techstore.estado'].search([('nombre_estado', '=', 'ingresado')], limit=1)
                if estado_ingresado:
                    vals['id_estado'] = estado_ingresado.id
            if not vals.get('id_prioridad'):
                prioridad_media = self.env['techstore.prioridad'].search([('nombre', '=', 'media')], limit=1)
                if prioridad_media:
                    vals['id_prioridad'] = prioridad_media.id
        records = super().create(vals_list)
        records._crear_historial_estado_inicial()
        return records

    def write(self, vals):
        estados_previos = {}
        if 'id_estado' in vals:
            estados_previos = {record.id: record.id_estado.id for record in self}
        # Validar que no se modifiquen datos iniciales después de creado
        for record in self:
            estado_actual = record.id_estado.nombre_estado if record.id_estado else 'ingresado'
            if estado_actual != 'ingresado':
                # Campos que no se pueden modificar después de crear el mantenimiento
                campos_iniciales = ['ced_cliente', 'id_equipo', 'id_prioridad', 'falla_reportada']
                campos_a_modificar = [c for c in campos_iniciales if c in vals]
                if campos_a_modificar:
                    raise ValidationError(
                        _('No puedes modificar los datos iniciales (%s) una vez que el mantenimiento ha salido del estado "Ingresado".') % 
                        ', '.join(campos_a_modificar)
                    )
        
        if 'id_equipo' in vals and not vals.get('ced_cliente'):
            equipo = self.env['techstore.equipo'].browse(vals['id_equipo'])
            if equipo.exists():
                vals['ced_cliente'] = equipo.ced_cliente.id

        if 'id_estado' in vals:
            nuevo_estado = self.env['techstore.estado'].browse(vals['id_estado'])
            if nuevo_estado and nuevo_estado.exists():
                for record in self:
                    estado_actual = record.id_estado.nombre_estado if record.id_estado else 'ingresado'
                    estados_permitidos = self._SECUENCIA_ESTADOS.get(estado_actual, [])
                    if nuevo_estado.nombre_estado not in estados_permitidos and nuevo_estado.nombre_estado != estado_actual:
                        raise ValidationError(
                            _('Debes mover el mantenimiento en secuencia. Desde "%s" solo puedes pasar a "%s".') % (
                                estado_actual,
                                ', '.join(estados_permitidos) or _('ninguno'),
                            )
                        )
                    if nuevo_estado.nombre_estado == 'diagnostico' and not (vals.get('ced_tecnico') or record.ced_tecnico):
                        raise ValidationError(_('Para pasar a Diagnóstico debes asignar un técnico.'))

        result = super().write(vals)

        if 'id_estado' in vals:
            estado = self.env['techstore.estado'].browse(vals['id_estado'])
            if estado.exists() and estado.es_estado_final:
                for record in self:
                    if not record.fecha_entrega:
                        record.fecha_entrega = fields.Datetime.now()

            for record in self:
                if estados_previos.get(record.id) != record.id_estado.id:
                    record._crear_historial_estado(
                        observacion=record.justificacion_cambio_estado or ''
                    )

        return result

    def _crear_historial_estado(self, fecha_cambio=None, observacion=None):
        historial_obj = self.env['techstore.mantenimiento.historial'].sudo()
        for record in self:
            if not record.id_estado:
                continue
            historial_obj.create({
                'mantenimiento_id': record.id,
                'id_estado': record.id_estado.id,
                'fecha_cambio': fecha_cambio or fields.Datetime.now(),
                'usuario_id': self.env.user.id,
                'observacion': observacion or '',
            })

    def _crear_historial_estado_inicial(self):
        for record in self:
            record._crear_historial_estado(
                fecha_cambio=record.fecha_ingreso or fields.Datetime.now(),
                observacion='Creacion del mantenimiento'
            )

    def action_set_diagnostico(self):
        self.ensure_one()
        return self._open_state_wizard('diagnostico')

    def action_set_pendiente_asignacion(self):
        self.ensure_one()
        return self._open_state_wizard('pendiente_asignacion')

    def action_set_reparacion(self):
        self.ensure_one()
        return self._open_state_wizard('reparacion')

    def action_set_esperando_repuestos(self):
        self.ensure_one()
        return self._open_state_wizard('esperando_repuestos')

    def action_set_control_calidad(self):
        self.ensure_one()
        return self._open_state_wizard('control_calidad')

    def action_set_listo_entrega(self):
        self.ensure_one()
        return self._open_state_wizard('listo_entrega')

    def action_set_entregado(self):
        self.ensure_one()
        return self._open_state_wizard('entregado')

    def action_reset_nuevo(self):
        self.ensure_one()
        return self._open_state_wizard('ingresado')

    def _open_state_wizard(self, estado_objetivo):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cambiar estado'),
            'res_model': 'techstore.mantenimiento.estado.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref('techstore_maintenance.view_techstore_mantenimiento_estado_wizard_form').id,
            'target': 'new',
            'context': {
                'default_mantenimiento_id': self.id,
                'default_estado_objetivo': estado_objetivo,
            },
        }

    def _aplicar_cambio_estado(self, estado_objetivo, justificacion, tecnico_id=False):
        self.ensure_one()
        if not justificacion or not justificacion.strip():
            raise ValidationError(_('La justificación es obligatoria para cambiar el estado.'))

        estado_actual = self.id_estado.nombre_estado if self.id_estado else 'ingresado'
        estados_permitidos = self._SECUENCIA_ESTADOS.get(estado_actual, [])
        if estado_objetivo not in estados_permitidos:
            raise ValidationError(_('Debes seguir la secuencia de estados. Desde "%s" solo puedes pasar a "%s".') % (
                estado_actual,
                ', '.join(estados_permitidos) or _('ninguno'),
            ))

        estado = self.env['techstore.estado'].search([('nombre_estado', '=', estado_objetivo)], limit=1)
        if not estado:
            raise ValidationError(_('No se encontró el estado "%s".') % estado_objetivo)

        valores = {'id_estado': estado.id}

        tecnico = tecnico_id or self.ced_tecnico
        if estado_objetivo == 'diagnostico':
            if not tecnico:
                raise ValidationError(_('Para pasar a Diagnóstico debes asignar un técnico.'))
            valores['ced_tecnico'] = tecnico.id
        elif tecnico_id:
            valores['ced_tecnico'] = tecnico_id.id

        # Pausar/reanudar reloj SLA para Esperando Repuestos
        if estado_objetivo == 'esperando_repuestos':
            valores['fecha_pausa_repuestos'] = fields.Datetime.now()
        elif estado_actual == 'esperando_repuestos' and estado_objetivo == 'reparacion':
            # Calcular tiempo pausado y acumularlo
            if self.fecha_pausa_repuestos:
                delta = datetime.now() - self.fecha_pausa_repuestos.replace(tzinfo=None)
                valores['tiempo_pausado_horas'] = self.tiempo_pausado_horas + round(delta.total_seconds() / 3600, 2)
                valores['fecha_pausa_repuestos'] = False

        if estado_objetivo in ('listo_entrega', 'entregado') and not self.fecha_entrega:
            valores['fecha_entrega'] = fields.Datetime.now()

        self.write(valores)

        mensaje = _(
            'Cambio de estado a <b>%s</b>.<br/><b>Justificación:</b> %s'
        ) % (estado.get_nombre_estado_display(), justificacion)
        if estado_objetivo == 'diagnostico' and tecnico:
            mensaje += _('<br/><b>Técnico asignado:</b> %s') % tecnico.nombre
        self.message_post(body=mensaje)

    def asignar_tecnico_automatico(self):
        for record in self:
            if record.ced_tecnico:
                continue
            tecnicos = self.env['techstore.tecnico'].search(
                [('disponibilidad', '=', True)],
                order='carga_trabajo asc, id asc'
            )
            if not tecnicos:
                raise ValidationError(_('No hay tecnicos disponibles para asignacion automatica.'))

            tipo_equipo = ''
            if record.id_equipo:
                tipo_equipo = record.id_equipo._get_tipo_equipo_display(record.id_equipo.tipo_equipo)
            tipo_equipo_norm = (tipo_equipo or '').lower()

            tecnicos_match = [
                t for t in tecnicos
                if tipo_equipo_norm and tipo_equipo_norm in (t.especialidad or '').lower()
            ]
            if not tecnicos_match:
                tecnicos_match = [
                    t for t in tecnicos
                    if 'hardware' in (t.especialidad or '').lower()
                ]

            candidatos = tecnicos_match or tecnicos
            tecnico = sorted(candidatos, key=lambda t: t.carga_trabajo)[0]
            record.write({'ced_tecnico': tecnico.id})

    @api.model
    def actualizar_disponibilidad_tecnicos(self):
        tecnicos = self.env['techstore.tecnico'].sudo().search([])
        for tecnico in tecnicos:
            tecnico.disponibilidad = tecnico.carga_trabajo <= 5

    def _notificar_retraso(self):
        template = self.env.ref('techstore_maintenance.email_template_retraso', raise_if_not_found=False)
        for record in self:
            if not template:
                continue
            template.send_mail(record.id, force_send=True)

    def verificar_recordatorio_cierre(self):
        template = self.env.ref('techstore_maintenance.email_template_recordatorio_cierre', raise_if_not_found=False)
        if not template:
            return

        limite = fields.Datetime.now() - timedelta(hours=48)
        registros = self.search([('id_estado.nombre_estado', '=', 'listo_entrega')])
        for record in registros:
            fecha_inicio = record.fecha_entrega or record.fecha_ingreso
            if record.state_tracking:
                ultimo = record.state_tracking.sorted(key=lambda r: r.fecha_cambio)[-1]
                if ultimo.fecha_cambio:
                    fecha_inicio = ultimo.fecha_cambio
            if fecha_inicio and fecha_inicio <= limite:
                template.send_mail(record.id, force_send=True)

    @api.model
    def get_dashboard_data(self):
        hoy = fields.Date.today()
        inicio_hoy = datetime.combine(hoy, datetime.min.time())
        fin_hoy = datetime.combine(hoy, datetime.max.time())
        hace_7_dias = fields.Datetime.now() - timedelta(days=7)

        activos_hoy = self.search_count([
            ('fecha_ingreso', '>=', inicio_hoy),
            ('fecha_ingreso', '<=', fin_hoy),
        ])
        retrasados_count = self.search_count([('esta_retrasado', '=', True)])

        entregados_semana = self.search([('fecha_entrega', '>=', hace_7_dias)])
        tiempos = [t for t in entregados_semana.mapped('tiempo_atencion_horas') if t > 0]
        tiempo_promedio_semana = round(sum(tiempos) / len(tiempos), 2) if tiempos else 0.0

        total_semana = self.search_count([('fecha_ingreso', '>=', hace_7_dias)])
        tasa_completitud_semana = round((len(entregados_semana) / total_semana) * 100, 1) if total_semana > 0 else 0.0

        return {
            'activos_hoy': activos_hoy,
            'retrasados_count': retrasados_count,
            'tiempo_promedio_semana': tiempo_promedio_semana,
            'tasa_completitud_semana': tasa_completitud_semana,
        }

    def action_view_cliente(self):
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

    def action_view_equipo(self):
        self.ensure_one()
        if not self.id_equipo:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Equipo'),
            'res_model': 'techstore.equipo',
            'res_id': self.id_equipo.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_tecnico(self):
        self.ensure_one()
        if not self.ced_tecnico:
            return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': _('Técnico'),
            'res_model': 'techstore.tecnico',
            'res_id': self.ced_tecnico.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_asignar_tecnico(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Asignar Técnico'),
            'view_mode': 'form',
            'res_model': 'techstore.mantenimiento',
            'res_id': self.id,
            'target': 'new',
            'context': {'from_assignment': True},
        }

    def action_guardar_y_volver(self):
        return self.env.ref('techstore_maintenance.action_techstore_mantenimiento').read()[0]

    def action_cancelar_creacion(self):
        """Cancela la creación de un nuevo mantenimiento y vuelve a la lista principal."""
        if self.exists():
            self.sudo().unlink()
        return self.env.ref('techstore_maintenance.action_techstore_mantenimiento').read()[0]

    def action_client_cancel_creation(self):
        """Acción cliente: cerrar la ventana del formulario sin tocar la BD.

        Diseñada para usarse en el formulario de creación (registro sin id).
        Devuelve una acción cliente que cierra la vista actual en el navegador.
        """
        return {'type': 'ir.actions.act_window_close'}
    
    def action_descartar(self):
        # Solo permitir descartar (eliminar) si el mantenimiento está en estado 'ingresado'
        for record in self:
            estado_actual = record.id_estado.nombre_estado if record.id_estado else 'ingresado'
            if estado_actual != 'ingresado':
                raise ValidationError(_('Solo se puede descartar un mantenimiento en estado "ingresado".'))
            try:
                if record.exists() and record.id:
                    record.sudo().unlink()
            except Exception:
                # Si falla el unlink, continuar y devolver la acción de lista
                pass
        return {
            'type': 'ir.actions.act_window',
            'name': 'Mantenimientos',
            'res_model': 'techstore.mantenimiento',
            'view_mode': 'kanban,tree,form',
            'target': 'current',
        }

