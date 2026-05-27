from . import models
from . import controllers
from . import wizard


def techstore_clear_implied(env):
	"""Post-init hook: limpia las relaciones de implied groups creadas por versiones antiguas del módulo.

	Elimina entradas en res_groups_implied_rel donde gid o hid correspondan a grupos definidos
	por este módulo (techstore_maintenance). Esto asegura que no haya herencia automática
	de permisos entre los grupos del módulo.
	"""
	cr = env.cr
	# Ejecutar SQL directo para mayor compatibilidad
	cr.execute("""
		DELETE FROM res_groups_implied_rel
		WHERE gid IN (
			SELECT res_id FROM ir_model_data WHERE module='techstore_maintenance' AND model='res.groups'
		) OR hid IN (
			SELECT res_id FROM ir_model_data WHERE module='techstore_maintenance' AND model='res.groups'
		);
	""")
	cr.execute("""
		UPDATE res_groups
		SET category_id = NULL
		WHERE id IN (
			SELECT res_id FROM ir_model_data WHERE module='techstore_maintenance' AND model='res.groups'
		);
	""")
