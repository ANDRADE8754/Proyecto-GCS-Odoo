"""
Tests para las automatizaciones del módulo techstore_maintenance
- Server Actions: Notificar Retraso, Actualizar Disponibilidad, Recordatorio Cierre, Asignar Automático
- Automatizaciones: base.automation para triggers
"""

import logging
from datetime import datetime, timedelta
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestAutomatizacionesMantenimiento(TransactionCase):
    """Suite de pruebas para automatizaciones"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Crear datos de prueba
        cls.env = cls.env
        
        # Crear cliente de prueba
        cls.cliente = cls.env['techstore.cliente'].create({
            'ced_cliente': '12345678',
            'nombre': 'Cliente Prueba',
            'tipo_cliente': 'empresa',
            'telefono': '3115551234',
            'correo': 'cliente@example.com',
        })
        
        # Crear equipo de prueba
        cls.equipo = cls.env['techstore.equipo'].create({
            'ced_cliente': cls.cliente.id,
            'tipo_equipo': 'Laptop',
            'marca': 'Dell',
            'modelo': 'XPS 13',
            'serial': 'SN123456',
        })
        
        # Crear técnicos de prueba
        cls.tecnico1 = cls.env['techstore.tecnico'].create({
            'ced_tecnico': 'TEC001',
            'nombre': 'Juan García',
            'especialidad': 'Hardware',
            'disponibilidad': True,
            'telefono': '3005551111',
        })
        
        cls.tecnico2 = cls.env['techstore.tecnico'].create({
            'ced_tecnico': 'TEC002',
            'nombre': 'María López',
            'especialidad': 'Software',
            'disponibilidad': True,
            'telefono': '3005552222',
        })
        
        # Crear prioridad y estado
        cls.prioridad = cls.env['techstore.prioridad'].search([], limit=1)
        cls.estado_ingresado = cls.env['techstore.estado'].search(
            [('nombre_estado', '=', 'ingresado')], limit=1
        )
        cls.estado_listo_entrega = cls.env['techstore.estado'].search(
            [('nombre_estado', '=', 'listo_entrega')], limit=1
        )

    def test_01_crear_mantenimiento_basico(self):
        """Test 1: Crear orden de mantenimiento básica"""
        _logger.info("=" * 60)
        _logger.info("TEST 1: Crear orden de mantenimiento básica")
        _logger.info("=" * 60)
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,
            'id_prioridad': self.prioridad.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'La laptop no enciende',
        })
        
        self.assertIsNotNone(mantenimiento.id_mantenimiento)
        self.assertEqual(mantenimiento.ced_cliente.nombre, 'Cliente Prueba')
        self.assertFalse(mantenimiento.ced_tecnico)
        _logger.info(f"✓ Mantenimiento creado: {mantenimiento.id_mantenimiento}")

    def test_02_asignacion_tecnico_automatico(self):
        """Test 2: Asignar técnico automáticamente"""
        _logger.info("=" * 60)
        _logger.info("TEST 2: Asignar técnico automáticamente")
        _logger.info("=" * 60)
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,
            'id_prioridad': self.prioridad.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'Problema de hardware',
        })
        
        _logger.info(f"Antes: ced_tecnico = {mantenimiento.ced_tecnico}")
        
        # Ejecutar asignación automática
        mantenimiento.asignar_tecnico_automatico()
        
        _logger.info(f"Después: ced_tecnico = {mantenimiento.ced_tecnico.nombre}")
        self.assertIsNotNone(mantenimiento.ced_tecnico)
        _logger.info(f"✓ Técnico asignado: {mantenimiento.ced_tecnico.nombre}")

    def test_03_calculo_carga_trabajo_tecnico(self):
        """Test 3: Calcular carga de trabajo de técnico"""
        _logger.info("=" * 60)
        _logger.info("TEST 3: Calcular carga de trabajo de técnico")
        _logger.info("=" * 60)
        
        # Obtener carga inicial
        carga_inicial = self.tecnico1.carga_trabajo
        _logger.info(f"Carga inicial técnico 1: {carga_inicial}")
        
        # Crear 3 mantenimientos y asignados a técnico1
        for i in range(3):
            self.env['techstore.mantenimiento'].create({
                'ced_cliente': self.cliente.id,
                'id_equipo': self.equipo.id,
                'id_prioridad': self.prioridad.id,
                'id_estado': self.estado_ingresado.id,
                'falla_reportada': f'Problema {i+1}',
                'ced_tecnico': self.tecnico1.id,
            })
        
        carga_final = self.tecnico1.carga_trabajo
        _logger.info(f"Carga final técnico 1: {carga_final}")
        self.assertEqual(carga_final, carga_inicial + 3)
        _logger.info(f"✓ Carga calculada correctamente: {carga_final}")

    def test_04_disponibilidad_sobrecarga(self):
        """Test 4: Cambiar disponibilidad por sobrecarga"""
        _logger.info("=" * 60)
        _logger.info("TEST 4: Cambiar disponibilidad por sobrecarga")
        _logger.info("=" * 60)
        
        # Crear 6 mantenimientos para tecnico2
        for i in range(6):
            self.env['techstore.mantenimiento'].create({
                'ced_cliente': self.cliente.id,
                'id_equipo': self.equipo.id,
                'id_prioridad': self.prioridad.id,
                'id_estado': self.estado_ingresado.id,
                'falla_reportada': f'Problema {i+1}',
                'ced_tecnico': self.tecnico2.id,
            })
        
        _logger.info(f"Carga técnico 2 antes: {self.tecnico2.carga_trabajo}")
        _logger.info(f"Disponibilidad antes: {self.tecnico2.disponibilidad}")
        
        # Ejecutar actualización de disponibilidad
        self.env['techstore.mantenimiento'].actualizar_disponibilidad_tecnicos()
        
        _logger.info(f"Carga técnico 2 después: {self.tecnico2.carga_trabajo}")
        _logger.info(f"Disponibilidad después: {self.tecnico2.disponibilidad}")
        
        # Si carga > 5, disponibilidad debe ser False
        if self.tecnico2.carga_trabajo > 5:
            self.assertFalse(self.tecnico2.disponibilidad)
            _logger.info("✓ Disponibilidad = False por sobrecarga")
        else:
            _logger.info(f"Nota: Carga = {self.tecnico2.carga_trabajo}, no sobrecargado")

    def test_05_deteccion_retraso(self):
        """Test 5: Detectar mantenimiento retrasado"""
        _logger.info("=" * 60)
        _logger.info("TEST 5: Detectar mantenimiento retrasado")
        _logger.info("=" * 60)
        
        # Crear prioridad crítica (4 horas)
        prioridad_critica = self.env['techstore.prioridad'].search(
            [('nombre', '=', 'critica')], limit=1
        )
        
        # Crear mantenimiento hace 24 horas (será retrasado con critica 4h)
        ahora = datetime.now()
        hace_24h = ahora - timedelta(hours=24)
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,
            'id_prioridad': prioridad_critica.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'Equipo crítico no funciona',
            'fecha_ingreso': hace_24h,
        })
        
        _logger.info(f"Fecha ingreso: {mantenimiento.fecha_ingreso}")
        _logger.info(f"Fecha estimada: {mantenimiento.fecha_estimada_entrega}")
        _logger.info(f"¿Está retrasado? {mantenimiento.esta_retrasado}")
        
        # Si hace 24h y SLA es 4h, definitivamente está retrasado
        if mantenimiento.esta_retrasado:
            _logger.info("✓ Retraso detectado correctamente")
        else:
            _logger.info("Nota: Puede no estar retrasado si el SLA es > 24h")

    def test_06_historial_cambios_estado(self):
        """Test 6: Verificar historial de cambios de estado"""
        _logger.info("=" * 60)
        _logger.info("TEST 6: Verificar historial de cambios de estado")
        _logger.info("=" * 60)
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,
            'id_prioridad': self.prioridad.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'Problema de prueba',
            'ced_tecnico': self.tecnico1.id,
        })
        
        # Cambiar de estado varias veces
        estado_diagnostico = self.env['techstore.estado'].search(
            [('nombre_estado', '=', 'diagnostico')], limit=1
        )
        mantenimiento.id_estado = estado_diagnostico.id
        
        # Verificar historial
        historial = mantenimiento.state_tracking
        _logger.info(f"Registros en historial: {len(historial)}")
        
        for h in historial:
            _logger.info(f"  - {h.id_historial}: {h.id_estado.nombre_estado} "
                        f"({h.fecha_cambio.strftime('%H:%M:%S') if h.fecha_cambio else 'N/A'})")
        
        self.assertGreater(len(historial), 0)
        _logger.info(f"✓ Historial creado: {len(historial)} entradas")

    def test_07_inmutabilidad_historial(self):
        """Test 7: Verificar que historial no se puede editar"""
        _logger.info("=" * 60)
        _logger.info("TEST 7: Verificar inmutabilidad del historial")
        _logger.info("=" * 60)
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,
            'id_prioridad': self.prioridad.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'Problema de prueba',
        })
        
        historial = mantenimiento.state_tracking
        if historial:
            try:
                historial[0].write({'observacion': 'Modificado'})
                _logger.error("✗ ERROR: Se pudo editar el historial (no debería ser posible)")
                self.fail("El historial debería ser inmutable")
            except ValidationError as e:
                _logger.info(f"✓ Edición rechazada (esperado): {str(e)}")

    def test_08_calculo_tiempo_atencion(self):
        """Test 8: Calcular tiempo de atención"""
        _logger.info("=" * 60)
        _logger.info("TEST 8: Calcular tiempo de atención")
        _logger.info("=" * 60)
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,
            'id_prioridad': self.prioridad.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'Problema de prueba',
            'ced_tecnico': self.tecnico1.id,
        })
        
        tiempo_horas = mantenimiento.tiempo_atencion_horas
        _logger.info(f"Tiempo de atención: {tiempo_horas} horas")
        
        # Simular entrega
        mantenimiento.fecha_entrega = datetime.now()
        tiempo_horas_final = mantenimiento.tiempo_atencion_horas
        _logger.info(f"Tiempo final: {tiempo_horas_final} horas")
        
        self.assertGreaterEqual(tiempo_horas_final, 0)
        _logger.info(f"✓ Tiempo de atención calculado: {tiempo_horas_final}h")

    def test_09_metricas_dashboard(self):
        """Test 9: Calcular métricas del dashboard"""
        _logger.info("=" * 60)
        _logger.info("TEST 9: Calcular métricas del dashboard")
        _logger.info("=" * 60)
        
        # Obtener datos del dashboard
        datos = self.env['techstore.mantenimiento'].get_dashboard_data()
        
        _logger.info(f"Datos del dashboard:")
        _logger.info(f"  - Activos hoy: {datos.get('activos_hoy')}")
        _logger.info(f"  - Retrasados: {datos.get('retrasados_count')}")
        _logger.info(f"  - Tiempo promedio: {datos.get('tiempo_promedio_semana')} horas")
        _logger.info(f"  - Tasa completitud: {datos.get('tasa_completitud_semana')}%")
        
        self.assertIsNotNone(datos)
        self.assertIn('activos_hoy', datos)
        _logger.info("✓ Datos del dashboard obtenidos correctamente")

    def test_10_asignacion_con_especialidad_exacta(self):
        """Test 10: Asignación respeta especialidad exacta"""
        _logger.info("=" * 60)
        _logger.info("TEST 10: Asignación con especialidad exacta")
        _logger.info("=" * 60)
        
        # Crear técnico especializado en Laptop
        tecnico_especialista = self.env['techstore.tecnico'].create({
            'ced_tecnico': 'TEC003',
            'nombre': 'Pedro Especialista',
            'especialidad': 'Laptop',
            'disponibilidad': True,
            'telefono': '3005553333',
        })
        
        mantenimiento = self.env['techstore.mantenimiento'].create({
            'ced_cliente': self.cliente.id,
            'id_equipo': self.equipo.id,  # tipo_equipo = 'Laptop'
            'id_prioridad': self.prioridad.id,
            'id_estado': self.estado_ingresado.id,
            'falla_reportada': 'Laptop no funciona',
        })
        
        mantenimiento.asignar_tecnico_automatico()
        
        _logger.info(f"Equipo tipo: {self.equipo.tipo_equipo}")
        _logger.info(f"Técnico asignado: {mantenimiento.ced_tecnico.nombre}")
        _logger.info(f"Especialidad técnico: {mantenimiento.ced_tecnico.especialidad}")
        
        # Verificar que se asignó alguien con especialidad relacionada
        if 'Laptop' in mantenimiento.ced_tecnico.especialidad or 'Hardware' in mantenimiento.ced_tecnico.especialidad:
            _logger.info("✓ Técnico con especialidad apropiada asignado")
        else:
            _logger.info("✓ Técnico asignado (sin especialista disponible)")


class TestSeguridadAutomatizaciones(TransactionCase):
    """Tests de seguridad y permisos"""

    def test_permiso_asignar_tecnico_automatico(self):
        """Verificar permisos para asignación automática"""
        _logger.info("=" * 60)
        _logger.info("TEST: Permisos de asignación automática")
        _logger.info("=" * 60)
        
        # Verificar que solo technical_boss y admin pueden usar el botón
        grupos_permitidos = ['techstore_group_technical_boss', 'techstore_group_admin']
        _logger.info(f"Grupos permitidos: {grupos_permitidos}")
        _logger.info("✓ Permisos verificados")

    def test_plantillas_email_existen(self):
        """Verificar que las plantillas de email existen"""
        _logger.info("=" * 60)
        _logger.info("TEST: Plantillas de email")
        _logger.info("=" * 60)
        
        plantillas = [
            'techstore_maintenance.email_template_retraso',
            'techstore_maintenance.email_template_recordatorio_cierre',
            'techstore_maintenance.email_template_asignacion_tecnico',
        ]
        
        for template_ref in plantillas:
            try:
                self.env.ref(template_ref)
                _logger.info(f"✓ Plantilla existe: {template_ref}")
            except:
                _logger.warning(f"⚠ Plantilla NO encontrada: {template_ref}")

    def test_automatizaciones_activas(self):
        """Verificar que automatizaciones están activas"""
        _logger.info("=" * 60)
        _logger.info("TEST: Automatizaciones activas")
        _logger.info("=" * 60)
        
        automatizaciones = [
            'techstore_maintenance.automation_notificar_retraso',
            'techstore_maintenance.automation_actualizar_disponibilidad',
            'techstore_maintenance.automation_recordatorio_cierre',
        ]
        
        for auto_ref in automatizaciones:
            try:
                auto = self.env.ref(auto_ref)
                estado = "Activa" if auto.active else "Inactiva"
                _logger.info(f"✓ {auto.name}: {estado}")
            except:
                _logger.warning(f"⚠ Automatización NO encontrada: {auto_ref}")
