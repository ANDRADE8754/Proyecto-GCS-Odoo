from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class TechstoreTecnico(models.Model):
    _name = 'techstore.tecnico'
    _description = 'Técnico - TechStore'
    _rec_name = 'nombre'
    _order = 'nombre'

    # Campos Principales
    ced_tecnico = fields.Char(
        string='Cédula del Técnico',
        required=True,
        copy=False,
        index=True,
        help='Cédula o identificación única del técnico'
    )
    correo = fields.Char(
        string='Correo',
        required=True,
        copy=False,
        index=True,
        help='Correo electrónico usado como usuario de acceso a Odoo'
    )
    contrasena = fields.Char(
        string='Contraseña',
        copy=False,
        help='Contraseña inicial para el acceso del técnico a Odoo'
    )
    nombre = fields.Char(
        string='Nombre del Técnico',
        required=True,
        index=True,
        help='Nombre completo del técnico'
    )
    especialidad = fields.Char(
        string='Especialidad',
        required=True,
        help='Área de especialización (Hardware, Software, Redes, Impresoras, etc.)'
    )
    disponibilidad = fields.Boolean(
        string='Disponible',
        default=True,
        help='Indica si el técnico está disponible para nuevas asignaciones'
    )
    usuario_id = fields.Many2one(
        'res.users',
        string='Usuario Odoo',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='Usuario creado automáticamente para el acceso al sistema'
    )
    telefono = fields.Char(
        string='Teléfono',
        help='Número telefónico del técnico'
    )

    # Relaciones One2many
    mantenimiento_ids = fields.One2many(
        'techstore.mantenimiento',
        'ced_tecnico',  # ← CORREGIDO: antes era 'tecnico_asignado'
        string='Mantenimientos Asignados',
        help='Historial de mantenimientos asignados a este técnico'
    )

    # Campos Computables
    carga_trabajo = fields.Integer(
        string='Carga de Trabajo',
        compute='_compute_carga_trabajo',
        store=True,
        help='Cantidad de mantenimientos en progreso'
    )
    color_kanban = fields.Integer(
        string='Color Kanban',
        compute='_compute_color_kanban',
        store=True,
        help='Color para visualización en kanban (1=verde, 2=amarillo, 3=rojo)'
    )

    # Restricciones SQL
    _sql_constraints = [
        ('ced_tecnico_unique', 'UNIQUE(ced_tecnico)', 'La cédula del técnico debe ser única.'),
        ('correo_unique', 'UNIQUE(correo)', 'El correo del técnico debe ser único.'),
        ('telefono_unique', 'UNIQUE(telefono)', 'El teléfono del técnico debe ser único.'),
    ]

    @api.constrains('ced_tecnico')
    def _check_ced_tecnico_unique(self):
        """Verifica la unicidad de la cédula del técnico"""
        for record in self:
            if record.ced_tecnico:
                cedula = record.ced_tecnico.strip()
                if not cedula.isdigit() or len(cedula) != 10:
                    raise ValidationError(_('La cédula del técnico debe contener exactamente 10 dígitos numéricos.'))
                existing = self.search([
                    ('ced_tecnico', '=', cedula),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('Ya existe un técnico con la cédula "%s".') % cedula
                    )

    @api.constrains('correo')
    def _check_correo_unico(self):
        for record in self:
            if record.correo:
                correo = record.correo.strip().lower()
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, correo):
                    raise ValidationError(_('Ingresa un correo válido.'))
                existing = self.search([
                    ('correo', '=', correo),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Ya existe un técnico con el correo "%s".') % correo)

    @api.constrains('telefono')
    def _check_telefono_unico(self):
        for record in self:
            if record.telefono:
                telefono = record.telefono.strip()
                if not telefono.isdigit() or len(telefono) != 10 or not telefono.startswith('0'):
                    raise ValidationError(_('El teléfono debe tener 10 dígitos y comenzar con 0.'))
                existing = self.search([
                    ('telefono', '=', telefono),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_('Ya existe un técnico con el teléfono "%s".') % telefono)

    @api.constrains('nombre')
    def _check_nombre_requerido(self):
        for record in self:
            if not record.nombre or not record.nombre.strip():
                raise ValidationError(_('El nombre del técnico es obligatorio.'))

    @api.constrains('especialidad')
    def _check_especialidad(self):
        for record in self:
            if not record.especialidad or not record.especialidad.strip():
                raise ValidationError(_('La especialidad del técnico es obligatoria.'))

    @api.constrains('contrasena')
    def _check_contrasena(self):
        for record in self:
            if record.contrasena and len(record.contrasena) < 8:
                raise ValidationError(_('La contraseña inicial debe tener al menos 8 caracteres.'))

    @api.constrains('disponibilidad')
    def _check_disponibilidad_asignaciones(self):
        """Si se marca como no disponible, valida que no hay mantenimientos nuevos sin asignar"""
        for record in self:
            if not record.disponibilidad:
                # Permite la transición a no disponible
                pass

    @api.depends('mantenimiento_ids', 'mantenimiento_ids.id_estado')
    def _compute_carga_trabajo(self):
        """Calcula la cantidad de mantenimientos en estados de progreso"""
        estados_progreso = ['nuevo', 'diagnostico', 'reparacion', 'esperando_repuestos']
        
        for record in self:
            carga = len(record.mantenimiento_ids.filtered(
                lambda m: m.id_estado and m.id_estado.nombre_estado in estados_progreso  # ← CORREGIDO
            ))
            record.carga_trabajo = carga

    @api.depends('disponibilidad', 'carga_trabajo')
    def _compute_color_kanban(self):
        """
        Calcula el color para visualización en kanban:
        - 1 (Verde): Disponible y carga < 3
        - 2 (Amarillo): Carga entre 3 y 5
        - 3 (Rojo): Carga > 5 o no disponible
        """
        for record in self:
            if not record.disponibilidad:
                record.color_kanban = 3  # Rojo
            elif record.carga_trabajo > 5:
                record.color_kanban = 3  # Rojo
            elif record.carga_trabajo >= 3:
                record.color_kanban = 2  # Amarillo
            else:
                record.color_kanban = 1  # Verde

    def action_view_mantenimientos_asignados(self):
        """Abre la vista de mantenimientos asignados a este técnico"""
        self.ensure_one()
        action = self.env.ref('techstore_maintenance.action_techstore_mantenimiento').read()[0]
        action['domain'] = [('ced_tecnico', '=', self.id)]  # ← CORREGIDO
        return action

    def action_guardar_y_volver(self):
        return self.env.ref('techstore_maintenance.action_techstore_tecnico').read()[0]

    def action_cancelar_creacion(self):
        if self.exists():
            self.sudo().unlink()
        return self.env.ref('techstore_maintenance.action_techstore_tecnico').read()[0]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('correo'):
                vals['correo'] = vals['correo'].strip().lower()
            if vals.get('telefono'):
                vals['telefono'] = vals['telefono'].strip()
            if vals.get('ced_tecnico'):
                vals['ced_tecnico'] = vals['ced_tecnico'].strip()
            if vals.get('nombre'):
                vals['nombre'] = vals['nombre'].strip()
            if vals.get('especialidad'):
                vals['especialidad'] = vals['especialidad'].strip()
            if vals.get('contrasena'):
                vals['contrasena'] = vals['contrasena'].strip()
        records = super().create(vals_list)
        records._sync_user_account()
        return records

    def write(self, vals):
        """Override write para controlar cambios en disponibilidad"""
        if 'correo' in vals and vals.get('correo'):
            vals['correo'] = vals['correo'].strip().lower()
        if 'telefono' in vals and vals.get('telefono'):
            vals['telefono'] = vals['telefono'].strip()
        if 'ced_tecnico' in vals and vals.get('ced_tecnico'):
            vals['ced_tecnico'] = vals['ced_tecnico'].strip()

        if 'disponibilidad' in vals and not vals['disponibilidad']:
            # Si se marca como no disponible, verificar que no hay mantenimientos en estado 'nuevo'
            for record in self:
                nuevos = record.mantenimiento_ids.filtered(
                    lambda m: m.id_estado and m.id_estado.nombre_estado == 'nuevo'  # ← CORREGIDO
                )
                if nuevos:
                    raise ValidationError(
                        _('No puedes marcar como no disponible un técnico con mantenimientos sin asignar.')
                    )
        result = super().write(vals)
        if any(field in vals for field in ['correo', 'contrasena', 'nombre', 'ced_tecnico']):
            self._sync_user_account()
        return result

    def _sync_user_account(self):
        for record in self:
            correo = (record.correo or '').strip().lower()
            if not correo:
                continue

            existing_user = self.env['res.users'].sudo().search([('login', '=', correo)], limit=1)

            user_vals = {
                'name': record.nombre,
                'login': correo,
                'email': correo,
            }

            if record.usuario_id:
                record.usuario_id.write(user_vals)
                if record.contrasena:
                    record.usuario_id.sudo().write({'password': record.contrasena})
            elif existing_user:
                existing_user.write(user_vals)
                if record.contrasena:
                    existing_user.sudo().write({'password': record.contrasena})
                record.usuario_id = existing_user.id
            else:
                partner = self.env['res.partner'].search([('email', '=', correo)], limit=1)
                if not partner:
                    partner = self.env['res.partner'].create({
                        'name': record.nombre,
                        'email': correo,
                        'phone': record.telefono,
                    })

                user_vals['partner_id'] = partner.id
                user_vals['groups_id'] = [(6, 0, [self.env.ref('base.group_user').id])]
                if not record.contrasena:
                    raise ValidationError(_('Debes definir una contraseña inicial para crear la cuenta del técnico.'))

                user_vals['password'] = record.contrasena
                user = self.env['res.users'].sudo().create(user_vals)
                record.usuario_id = user.id

    @api.model
    def get_especialidades(self):
        """Retorna lista de especialidades comunes"""
        return [
            'Hardware',
            'Software',
            'Redes',
            'Impresoras',
            'Mantenimiento General',
            'Soporte Técnico',
        ]

    def get_carga_trabajo_display(self):
        """Retorna una representación visual de la carga de trabajo"""
        if self.carga_trabajo == 0:
            return _('Sin asignaciones')
        elif self.carga_trabajo <= 2:
            return _('Carga baja')
        elif self.carga_trabajo <= 5:
            return _('Carga media')
        else:
            return _('Carga alta')