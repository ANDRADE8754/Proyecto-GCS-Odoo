# Sistema de Gestión de Mantenimientos Técnicos para TechStore

Este proyecto consiste en el desarrollo de una solución tecnológica orientada a la optimización, control y automatización del proceso de gestión de mantenimientos técnicos de la empresa **TechStore**. El enfoque principal del sistema está regido por altos estándares de calidad de software, aseguramiento de la calidad (SQA), métricas detalladas de rendimiento y procesos de mejora continua.

---

## 👥 Integrantes del Grupo
* Alejandro Andrade
* Jonathan Lozada
* Marco Serrano
* Christian Sanchez

---

## 📝 Información General del Proyecto

### 1. Contexto del Problema
TechStore ofrece servicios de venta, soporte técnico y mantenimiento de equipos tecnológicos a clientes corporativos y particulares. Históricamente, la gestión de estos servicios se ha ejecutado de manera manual o mediante hojas de cálculo, desencadenando múltiples inconvenientes operativos:
* Pérdida recurrente de registros de mantenimiento e inconsistencias graves en los datos.
* Duplicidad de información y dificultad para consultar historiales técnicos de los equipos.
* Asignación incorrecta de técnicos y retrasos en los tiempos de atención.
* Falta de seguimiento de los estados de reparación y ausencia de control de prioridades.
* Carencia absoluta de métricas y KPIs para evaluar la calidad del servicio y el rendimiento del taller.

### 2. Objetivo General
Desarrollar una solución tecnológica integral para la gestión de mantenimientos técnicos de TechStore, aplicando rigurosamente conceptos de ingeniería de requisitos, calidad de software, aseguramiento de la calidad (ISO 25010 / SQM), métricas de software, pruebas estructuradas, estándares de la industria y procesos de mejora continua.

### 3. Arquitectura del Sistema (Módulos Principales)
El sistema unifica los procesos a través de los siguientes módulos interconectados que llevan la información de extremo a extremo:
* **Gestión de Clientes:** Registro y administración de datos de contacto de clientes particulares y corporativos, centralizando su historial general de atención. El cliente es el punto inicial del proceso.
* **Gestión de Equipos:** Trazabilidad e ingreso de dispositivos al taller (Laptops, PCs, Impresoras, Monitores, etc.) registrando marca, modelo, número de serie, estado y observaciones.
* **Gestión de Mantenimientos:** Creación de órdenes de trabajo, asignación de prioridades (críticas, medias, bajas), registro de diagnósticos, fallas y control de tiempos de resolución.
* **Gestión de Técnicos:** Control de personal, administración de especialidades, disponibilidad y distribución equitativa de la carga laboral para optimizar la productividad.
* **Flujo de Estados:** Seguimiento en tiempo real del ciclo de vida del mantenimiento a través de las etapas: *Nuevo ➔ Diagnóstico ➔ Reparación ➔ Esperando Repuestos ➔ Finalizado ➔ Entregado*.
* **Reportes y KPIs:** Dashboard de analítica que toma información de todos los módulos anteriores para transformarla en métricas de rendimiento (tiempos promedio de atención, tasas de productividad, tickets retrasados y niveles de satisfacción del cliente) para tomar decisiones basadas en datos.

---

## 🐳 Guía de Uso: Base de Datos, Respaldos y Restauración Automática

El entorno utiliza **Docker Compose** para orquestar la aplicación (Odoo 18 + PostgreSQL 15). Incluye scripts automatizados integrados dentro de los ciclos de vida de los contenedores para facilitar el despliegue rápido, limpio y seguro en ambientes de desarrollo y pruebas.

### 📋 Requisitos Previos y Estructura
Asegúrate de contar con una estructura de carpetas local similar a esta en la raíz de tu proyecto para que los volúmenes se monten correctamente:
```text
├── addons/          # Módulos personalizados de Odoo (se monta en /mnt/extra-addons)
├── backups/         # Almacenamiento local de dumps y filestore (Mapeado a contenedores)
├── scripts/         # Scripts adicionales de utilidad para el contenedor de Odoo
└── docker-compose.yml
```

# 📑 Manual de Operación: Ciclo de Vida y Gestión de Backups

Este documento detalla el funcionamiento interno de la infraestructura de persistencia, restauración automática y generación de respaldos para el entorno de desarrollo basado en Docker.

---

## 🚀 1. Inicialización y Restauración Automática (Levantar el Entorno)

Para levantar el ecosistema completo de contenedores (Base de datos, servicio de restauración y Odoo), ejecuta el siguiente comando en tu terminal:

```bash
docker compose up -d
```

### ¿Qué sucede al ejecutar este comando?

1. **Contenedor `proyectoCS-db` (PostgreSQL 15):** Se inicia la base de datos con las siguientes optimizaciones:
   - Desactiva `fsync` y `synchronous_commit` para mejor rendimiento en desarrollo
   - Expone un healthcheck que verifica la disponibilidad cada 5 segundos
   - Monta el volumen `odoo-db-data` para persistencia de datos

2. **Contenedor `proyectoCS-restore`:** Una vez que PostgreSQL está listo, se ejecuta automáticamente:
   - Verifica si existe el archivo `/backups/db_demo.dump`
   - Si existe, elimina la base de datos `odoo` previa (si la hubiera)
   - Restaura la base de datos desde el backup
   - Limpia los assets en caché (`ir.attachment`)
   - Restaura el filestore (carpeta con archivos/documentos adjuntos)
   - Detecta y archiva archivos huérfanos en `_orphans_backup` para mantener la integridad
   - Si NO existe backup, crea una base de datos vacía

3. **Contenedor `proyectoCS` (Odoo 16):** Una vez que la restauración se completa:
   - Se inicia la aplicación Odoo
   - Preselecciona la base de datos `odoo`
   - Monta los módulos personalizados desde `./addons`
   - Accesible en `http://localhost:8071`

---

## 💾 2. Creación de Backups

Para generar un backup de la base de datos actual y sus archivos adjuntos, ejecuta:

```bash
docker compose --profile tools run --rm backup
```

### ¿Qué se respalda?

- **Base de datos:** Dump en formato binario en `/backups/db_demo.dump`
- **Filestore:** Carpeta de archivos en `/backups/filestore/odoo/`
- **Limpieza automática:** Se eliminan assets en caché y archivos huérfanos

### Ubicación de los Backups

Una vez ejecutado, encontrarás en la carpeta `./backups/`:

```text
backups/
├── db_demo.dump                    # Dump de la base de datos PostgreSQL
└── filestore/
    └── odoo/
        ├── 0/
        ├── 1/
        └── ... (archivos y documentos de Odoo)
```

---

## 🔄 3. Restauración Manual de Backups

Si necesitas restaurar un backup anterior o cambiar la fuente de datos, tienes dos opciones:

### Opción A: Restauración Automática al Levantar (Recomendado)

```bash
# El arquivo db_demo.dump debe estar en ./backups/
docker compose down -v  # Elimina volúmenes antiguos (¡CUIDADO!)
docker compose up -d    # Restaura automáticamente
```

### Opción B: Restauración Manual

```bash
# Ejecutar manualmente el servicio restore
docker compose --profile tools run --rm restore
```

---

## 📋 4. Gestión de Ciclo de Vida

### Iniciar el Entorno
```bash
docker compose up -d
```

### Detener el Entorno
```bash
docker compose down
```

### Detener y Eliminar Volúmenes (Restaura a Estado Limpio)
```bash
docker compose down -v
```

### Ver Logs de los Contenedores
```bash
# Todos los contenedores
docker compose logs -f

# Contenedor específico
docker compose logs -f odoo
docker compose logs -f db
docker compose logs -f restore
```

### Verificar Estado
```bash
docker compose ps
```

---

## ⚙️ 5. Estructura de Datos y Volúmenes

El proyecto utiliza volúmenes Docker para persistencia:

| Volumen | Contenedor | Propósito |
|---------|-----------|----------|
| `odoo-db-data` | `db` | Base de datos PostgreSQL |
| `odoo-web-data` | `odoo`, `restore`, `backup` | Filestore y datos de Odoo |

### Montos de Carpetas Locales

| Carpeta Local | Montaje en Contenedor | Propósito |
|---------------|--------------------|----------|
| `./backups/` | `/backups` | Almacenamiento de dumps y filestore |
| `./addons/` | `/mnt/extra-addons` | Módulos personalizados de Odoo |
| `./scripts/` | `/scripts` | Scripts adicionales de utilidad |

---

## 🛠️ 6. Troubleshooting Común

### El servicio `restore` falla
- Verifica que exista el archivo `./backups/db_demo.dump`
- Revisa los logs: `docker compose logs restore`

### Odoo no se conecta a la base de datos
- Asegúrate de que el contenedor `db` está saludable: `docker compose ps`
- Espera a que el healthcheck pase (hasta 50 segundos)

### Quiero limpiar todo y empezar desde cero
```bash
docker compose down -v
docker compose up -d
```

### Cambiar la contraseña de PostgreSQL
Edita el `docker-compose.yml` y modifica `POSTGRES_PASSWORD=odoo`
Luego ejecuta `docker compose down -v && docker compose up -d`