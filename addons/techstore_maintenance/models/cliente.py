from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re
import string


class TechstoreCliente(models.Model):
    _name = 'techstore.cliente'
    _description = 'Cliente - TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'nombre'
    _order = 'nombre'

    # Campos Principales
    ced_cliente = fields.Char(
        string='Cédula del Cliente',
        required=True,
        copy=False,
        index=True,
        help='Cédula o identificación única del cliente'
    )
    nombre = fields.Char(
        string='Nombre del Cliente',
        required=True,
        index=True,
        help='Nombre completo del cliente'
    )
    name = fields.Char(
        string='Nombre',
        compute='_compute_name',
        store=True,
        help='Campo name para compatibilidad con vistas Many2one'
    )
    tipo_cliente = fields.Selection(
        [('corporativo', 'Corporativo'), ('particular', 'Particular')],
        string='Tipo de Cliente',
        default='particular',
        required=True,
        help='Selecciona si el cliente es corporativo o particular'
    )
    telefono = fields.Char(
        string='Teléfono',
        help='Número telefónico del cliente'
    )
    correo = fields.Char(
        string='Correo Electrónico',
        help='Correo electrónico del cliente'
    )
    direccion = fields.Text(
        string='Dirección',
        help='Dirección física del cliente'
    )

    # Relaciones One2many
    equipo_ids = fields.One2many(
        'techstore.equipo',
        'ced_cliente',
        string='Equipos',
        help='Equipos registrados para este cliente'
    )
    mantenimiento_ids = fields.One2many(
        'techstore.mantenimiento',
        'ced_cliente',
        string='Mantenimientos',
        help='Historial de mantenimientos del cliente'
    )

    # Restricciones SQL
    _sql_constraints = [
        ('ced_cliente_unique', 'UNIQUE(ced_cliente)', 'La cédula del cliente debe ser única.'),
    ]

    @api.depends('nombre')
    def _compute_name(self):
        """Copia el nombre al campo name para compatibilidad con vistas"""
        for record in self:
            record.name = record.nombre

    @staticmethod
    def _validar_cedula_ecuador(cedula):
        """Valida una cédula ecuatoriana usando el algoritmo módulo 10
        
        Una cédula válida:
        - Tiene exactamente 10 dígitos
        - El primer dígito indica la provincia (01-24)
        - El último dígito es verificador calculado por módulo 10
        """
        # Limpiar espacios y caracteres especiales
        cedula = cedula.strip() if cedula else ""
        
        # Debe contener solo dígitos
        if not cedula.isdigit():
            return False, _("La cédula debe contener solo dígitos.")
        
        # Debe tener exactamente 10 dígitos
        if len(cedula) != 10:
            return False, _("La cédula debe tener exactamente 10 dígitos.")
        
        # No puede ser todos ceros o repetidos
        if cedula == '0' * 10 or len(set(cedula)) == 1:
            return False, _("La cédula no puede contener solo ceros o dígitos repetidos.")
        
        # Validar rango de provincia (primer dígito debe ser 01-24)
        provincia = int(cedula[:2])
        if provincia < 1 or provincia > 24:
            return False, _("La provincia indicada en la cédula no es válida (01-24).")
        
        # Validar dígito verificador usando el algoritmo oficial ecuatoriano
        suma = 0
        for i in range(9):
            digito = int(cedula[i])
            if i % 2 == 0:
                digito *= 2
                if digito > 9:
                    digito -= 9
            suma += digito

        digito_verificador_calculado = (10 - (suma % 10)) % 10
        
        # Comparar con el dígito verificador real
        digito_real = int(cedula[9])
        if digito_verificador_calculado != digito_real:
            return False, _("El dígito verificador de la cédula es incorrecto.")
        
        return True, None

    @staticmethod
    def _validar_telefono_ecuador(telefono):
        """Valida un número telefónico ecuatoriano
        
        Formato válido:
        - Exactamente 10 dígitos
        - Debe comenzar con 0
        - Solo números, sin espacios ni caracteres especiales (se limpian)
        """
        if not telefono:
            return True, None  # Teléfono es opcional
        
        # Limpiar espacios, guiones y caracteres comunes
        telefono_limpio = re.sub(r'[\s\-\(\)\+]', '', telefono)
        
        # Debe contener solo dígitos
        if not telefono_limpio.isdigit():
            return False, _("El teléfono debe contener solo dígitos.")
        
        # Debe tener exactamente 10 dígitos
        if len(telefono_limpio) != 10:
            return False, _("El teléfono debe tener exactamente 10 dígitos.")
        
        # Debe comenzar con 0
        if not telefono_limpio.startswith('0'):
            return False, _("El teléfono ecuatoriano debe comenzar con 0.")
        
        # Validar que no sea todos ceros o repetidos
        if len(set(telefono_limpio)) == 1:
            return False, _("El teléfono no puede contener solo dígitos repetidos.")
        
        return True, telefono_limpio

    @api.onchange('ced_cliente')
    def _onchange_ced_cliente_validar(self):
        """Valida la cédula en tiempo real mientras se escribe"""
        if self.ced_cliente:
            # Limpiar espacios
            self.ced_cliente = self.ced_cliente.strip()
            
            es_valida, mensaje_error = self._validar_cedula_ecuador(self.ced_cliente)
            if not es_valida:
                return {'warning': {
                    'title': _('Cédula Inválida'),
                    'message': mensaje_error
                }}
            
            # Solo verificar duplicados si el registro ya está guardado
            if self.id:
                existing = self.search([
                    ('ced_cliente', '=', self.ced_cliente),
                    ('id', '!=', self.id)
                ])
                if existing:
                    return {'warning': {
                        'title': _('⚠️ Cédula Duplicada'),
                        'message': _('Esta cédula ya está registrada en el sistema. '
                                   'Por favor, verifica que no sea un cliente existente.')
                    }}

    @api.onchange('telefono')
    def _onchange_telefono_validar(self):
        """Valida el teléfono en tiempo real mientras se escribe"""
        if self.telefono:
            es_valido, mensaje_error = self._validar_telefono_ecuador(self.telefono)
            if not es_valido:
                return {'warning': {
                    'title': _('❌ Teléfono Inválido'),
                    'message': _('El teléfono debe tener 10 dígitos y comenzar con 0. '
                               'Ejemplo: 0987654321')
                }}
            else:
                # Si es válido, limpiar y formatear
                self.telefono = mensaje_error
                
                # Solo verificar duplicados si el registro ya está guardado
                if self.id:
                    existing = self.search([
                        ('telefono', '=', self.telefono),
                        ('id', '!=', self.id)
                    ])
                    if existing:
                        return {'warning': {
                            'title': _('⚠️ Teléfono Duplicado'),
                            'message': _('Este teléfono ya pertenece a otro cliente. '
                                       'Si crees que es un error, contacta con administración.')
                        }}

    @api.onchange('correo')
    def _onchange_correo_validar(self):
        """Valida el correo en tiempo real mientras se escribe"""
        if self.correo:
            self.correo = self.correo.strip().lower()
            
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, self.correo):
                return {'warning': {
                    'title': _('❌ Correo Inválido'),
                    'message': _('Ingresa un correo válido. '
                               'Ejemplo: usuario@example.com')
                }}
            
            # Solo verificar duplicados si el registro ya está guardado
            if self.id:
                existing = self.search([
                    ('correo', '=', self.correo),
                    ('id', '!=', self.id)
                ])
                if existing:
                    return {'warning': {
                        'title': _('⚠️ Correo Duplicado'),
                        'message': _('Este correo ya está registrado en el sistema. '
                                   'Verifica si ese cliente ya existe.')
                    }}

    @api.constrains('ced_cliente')
    def _check_cedula_valida(self):
        """Valida que la cédula sea una cédula ecuatoriana válida"""
        for record in self:
            if record.ced_cliente:
                es_valida, mensaje_error = self._validar_cedula_ecuador(record.ced_cliente)
                if not es_valida:
                    raise ValidationError(
                        _('❌ Cédula Inválida\n\n%s\n\n'
                          'Verifica que hayas ingresado correctamente la cédula ecuatoriana.') % mensaje_error
                    )

    @api.constrains('telefono')
    def _check_telefono_valido(self):
        """Valida que el teléfono sea un número ecuatoriano válido"""
        for record in self:
            if record.telefono:
                es_valido, mensaje_error = self._validar_telefono_ecuador(record.telefono)
                if not es_valido:
                    raise ValidationError(
                        _('❌ Teléfono Inválido\n\n%s\n\n'
                          'Formato esperado: 0987654321 (10 dígitos, comienza con 0)') % mensaje_error
                    )

    @api.constrains('telefono')
    def _check_telefono_unico(self):
        """Verifica que el teléfono sea único (no se repita)"""
        for record in self:
            if record.telefono:
                telefono_limpio = re.sub(r'[\s\-\(\)\+]', '', record.telefono)
                existing = self.search([
                    ('telefono', '=', telefono_limpio),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('⚠️ Este teléfono ya está registrado.\n\n'
                          'El cliente "%s" ya tiene este número de teléfono.\n'
                          'Verifica que no sea un cliente duplicado.') % existing.nombre
                    )

    @api.constrains('correo')
    def _check_correo_valido(self):
        """Valida que el correo sea válido"""
        for record in self:
            if record.correo:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, record.correo):
                    raise ValidationError(
                        _('❌ Correo Inválido\n\n'
                          'El correo "%s" no tiene un formato válido.\n\n'
                          'Formato esperado: usuario@example.com') % record.correo
                    )

    @api.constrains('correo')
    def _check_correo_unico(self):
        """Verifica que el correo sea único (no se repita)"""
        for record in self:
            if record.correo:
                existing = self.search([
                    ('correo', '=', record.correo),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('⚠️ Este correo ya está registrado.\n\n'
                          'El cliente "%s" ya tiene este correo electrónico.\n'
                          'Verifica que no sea un cliente duplicado.') % existing.nombre
                    )

    @api.model
    def create(self, vals):
        """Override create para loguear creación y limpiar datos"""
        # Limpiar y validar cédula
        if vals.get('ced_cliente'):
            vals['ced_cliente'] = vals['ced_cliente'].strip()
        
        # Limpiar y validar teléfono
        if vals.get('telefono'):
            telefono = vals['telefono']
            es_valido, telefono_limpio = self._validar_telefono_ecuador(telefono)
            if es_valido and isinstance(telefono_limpio, str):
                vals['telefono'] = telefono_limpio
        
        # Limpiar correo
        if vals.get('correo'):
            vals['correo'] = vals['correo'].strip().lower()
        
        record = super().create(vals)
        record.message_post(
            body=_('Cliente creado correctamente.'),
            message_type='notification'
        )
        return record

    def write(self, vals):
        """Override write para registrar cambios y limpiar datos"""
        # Limpiar y validar cédula si se modifica
        if vals.get('ced_cliente'):
            vals['ced_cliente'] = vals['ced_cliente'].strip()
        
        # Limpiar y validar teléfono si se modifica
        if vals.get('telefono'):
            telefono = vals['telefono']
            es_valido, telefono_limpio = self._validar_telefono_ecuador(telefono)
            if es_valido and isinstance(telefono_limpio, str):
                vals['telefono'] = telefono_limpio
        
        # Limpiar correo si se modifica
        if vals.get('correo'):
            vals['correo'] = vals['correo'].strip().lower()
        
        result = super().write(vals)
        if vals:
            cambios = []
            if 'ced_cliente' in vals:
                cambios.append('Cédula')
            if 'telefono' in vals:
                cambios.append('Teléfono')
            if 'correo' in vals:
                cambios.append('Correo')
            
            if cambios:
                self.message_post(
                    body=_('Información del cliente actualizada: %s') % ', '.join(cambios),
                    message_type='notification'
                )
        return result

    def action_view_equipos(self):
        self.ensure_one()
        action = self.env.ref('techstore_maintenance.action_techstore_equipo').read()[0]
        action['domain'] = [('ced_cliente', '=', self.id)]
        action['context'] = {'default_ced_cliente': self.id}
        return action

    def action_view_mantenimientos(self):
        self.ensure_one()
        action = self.env.ref('techstore_maintenance.action_techstore_mantenimiento').read()[0]
        action['domain'] = [('ced_cliente', '=', self.id)]
        action['context'] = {'default_ced_cliente': self.id}
        return action

    def action_guardar_y_volver(self):
        """Guarda y vuelve a la lista de clientes."""
        return self.env.ref('techstore_maintenance.action_techstore_cliente').read()[0]

    def action_cancelar_creacion(self):
        """Cancela la creación: elimina el registro si existe y vuelve a la lista."""
        if self.exists():
            try:
                self.sudo().unlink()
            except Exception:
                pass
        return self.env.ref('techstore_maintenance.action_techstore_cliente').read()[0]