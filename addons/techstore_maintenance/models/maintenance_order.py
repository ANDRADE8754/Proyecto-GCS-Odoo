# techstore_maintenance/models/maintenance_order.py
from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime
 
 
class TechstoreMaintenanceMaterial(models.Model):
    """
    Tabla de lineas de materiales/repuestos usados en un mantenimiento.
    Cada fila = un repuesto utilizado en una orden especifica.
    """
    _name = 'techstore.maintenance.material'
    _description = 'Material de Mantenimiento'
 
    # Referencia a la orden padre (Many2one = muchos materiales -> una orden)
    order_id = fields.Many2one(
        'techstore.maintenance.order',
        string='Orden de Mantenimiento',
        required=True,
        ondelete='cascade'  # Si se borra la orden, se borran sus materiales
    )
 
    # Referencia al producto/repuesto del catalogo de Odoo
    product_id = fields.Many2one(
        'product.product',
        string='Repuesto / Material',
        required=True
    )
 
    quantity = fields.Float(
        string='Cantidad',
        required=True,
        default=1.0
    )
 
    unit_price = fields.Float(
        string='Precio Unitario',
        digits=(16, 2)  # 2 decimales
    )
 
    # Campo calculado: se actualiza automaticamente cuando cambian cantidad o precio
    subtotal = fields.Float(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,  # store=True guarda el resultado en la BD para poder filtrarlo
        digits=(16, 2)
    )
 
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        """Calcula el subtotal cada vez que cambia la cantidad o el precio."""
        for line in self:
            line.subtotal = line.quantity * line.unit_price
 
 
class TechstoreMaintenanceOrder(models.Model):
    """
    Tabla principal del modulo. Cada registro = una orden de mantenimiento.
    Hereda de 'mail.thread' para tener el chatter (historial de cambios).
    Hereda de 'mail.activity.mixin' para poder programar actividades.
    """
    _name = 'techstore.maintenance.order'
    _description = 'Orden de Mantenimiento TechStore'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_request asc'  # Ordena por urgencia, luego por fecha
 
    # ---- CAMPOS DE IDENTIFICACION ----
 
    name = fields.Char(
        string='Numero de Orden',
        readonly=True,
        copy=False,
        default='Nuevo'  # Se reemplaza al guardar con la secuencia
    )
 
    # ---- CAMPOS DEL CLIENTE Y EQUIPO ----
 
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True  # tracking=True registra los cambios en el chatter
    )
 
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipo',
        required=True,
        tracking=True
    )
 
    description = fields.Text(
        string='Descripcion del Problema',
        required=True
    )
 
    # ---- CAMPOS DE ESTADO Y PRIORIDAD ----
 
    # selection es una lista desplegable con opciones fijas
    state = fields.Selection([
        ('draft',       'Pendiente'),
        ('diagnosis',   'En Diagnostico'),
        ('in_progress', 'En Proceso'),
        ('done',        'Listo'),
        ('delivered',   'Entregado'),
        ('cancelled',   'Cancelado'),
    ],
        string='Estado',
        default='draft',
        required=True,
        tracking=True
    )
 
    priority = fields.Selection([
        ('0', 'Baja'),
        ('1', 'Media'),
        ('2', 'Alta'),
        ('3', 'Urgente'),
    ],
        string='Prioridad',
        default='1',
        tracking=True
    )
 
    # ---- CAMPOS DEL TECNICO ----
 
    technician_id = fields.Many2one(
        'hr.employee',
        string='Tecnico Responsable',
        tracking=True
    )
 
    # ---- CAMPOS DE FECHAS ----
 
    date_request = fields.Datetime(
        string='Fecha de Ingreso',
        default=fields.Datetime.now,
        required=True
    )
 
    date_start = fields.Datetime(
        string='Inicio del Trabajo',
        tracking=True
    )
 
    date_finish = fields.Datetime(
        string='Finalizacion del Trabajo',
        tracking=True
    )
 
    date_delivery = fields.Date(
        string='Fecha de Entrega al Cliente',
        tracking=True
    )
 
    # ---- CAMPO TECNICO (DIAGNOSTICO Y ACTIVIDADES) ----
 
    diagnosis = fields.Text(
        string='Diagnostico Tecnico'
    )
 
    activities_done = fields.Text(
        string='Actividades Realizadas'
    )
 
    # ---- LINEAS DE MATERIALES ----
 
    # One2many = una orden tiene muchas lineas de materiales
    material_ids = fields.One2many(
        'techstore.maintenance.material',
        'order_id',
        string='Materiales y Repuestos'
    )
 
    # Campo calculado: suma todos los subtotales de las lineas
    total_cost = fields.Float(
        string='Costo Total',
        compute='_compute_total_cost',
        store=True,
        digits=(16, 2)
    )
 
    # Campo calculado: tiempo de resolucion en horas
    resolution_hours = fields.Float(
        string='Horas de Resolucion',
        compute='_compute_resolution_hours',
        store=True
    )
 
    user_id = fields.Many2one(
        'res.users',
        string='Registrado por',
        default=lambda self: self.env.user
    )
 
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company
    )
 
    # ---- METODOS COMPUTADOS ----
 
    @api.depends('material_ids.subtotal')
    def _compute_total_cost(self):
        """Suma el subtotal de todas las lineas de materiales."""
        for order in self:
            order.total_cost = sum(order.material_ids.mapped('subtotal'))
 
    @api.depends('date_request', 'date_finish')
    def _compute_resolution_hours(self):
        """Calcula las horas entre el ingreso y la finalizacion."""
        for order in self:
            if order.date_request and order.date_finish:
                delta = order.date_finish - order.date_request
                order.resolution_hours = delta.total_seconds() / 3600
            else:
                order.resolution_hours = 0.0
 
    # ---- METODO DE CREACION (asigna el numero de secuencia) ----
 
    @api.model
    def create(self, vals):
        """
        Se ejecuta automaticamente cuando se crea un nuevo registro.
        Asigna el numero de secuencia (TS-0001, TS-0002...).
        """
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'techstore.maintenance.order'
            ) or 'Nuevo'
        return super().create(vals)
 
    # ---- METODOS DE TRANSICION DE ESTADOS ----
    # Estos metodos son llamados por los botones en la vista
 
    def action_set_diagnosis(self):
        """Cambia el estado a En Diagnostico."""
        self.write({'state': 'diagnosis', 'date_start': fields.Datetime.now()})
 
    def action_set_in_progress(self):
        """Cambia el estado a En Proceso."""
        self.write({'state': 'in_progress'})
 
    def action_set_done(self):
        """Cambia el estado a Listo y registra la fecha de finalizacion."""
        self.write({'state': 'done', 'date_finish': fields.Datetime.now()})
 
    def action_set_delivered(self):
        """Cambia el estado a Entregado y registra la fecha de entrega."""
        self.write({'state': 'delivered', 'date_delivery': fields.Date.today()})
 
    def action_cancel(self):
        """Cancela la orden."""
        self.write({'state': 'cancelled'})
 
    def action_reset_draft(self):
        """Regresa la orden a Pendiente (solo para Admin)."""
        self.write({'state': 'draft'})
 
    # ---- RESTRICCION: validar fechas ----
 
    @api.constrains('date_request', 'date_finish')
    def _check_dates(self):
        """Valida que la fecha de finalizacion no sea anterior a la de ingreso."""
        for order in self:
            if order.date_finish and order.date_request:
                if order.date_finish < order.date_request:
                    raise ValidationError(
                        'La fecha de finalizacion no puede ser anterior a la fecha de ingreso.'
                    )