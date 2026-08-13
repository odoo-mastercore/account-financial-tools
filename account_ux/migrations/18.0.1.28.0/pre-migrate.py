# -*- coding: utf-8 -*-
"""Borra las vistas de res.partner que account_ux dejo de traer en 18.

En 15 el modulo tenia views/res_partner_views.xml con tres vistas heredadas.
En 18 ese fichero ya no existe, pero los registros siguen en la base de datos
al venir de una instalacion anterior, y una vista sobrevive a que su modulo
se quede sin codigo: sigue participando en la herencia y en la validacion.

La que rompe es res_partner_view_buttons, que añade un boton
action_open_reconcile al formulario del contacto. Ese metodo lo aportaba
account_accountant sobre res.partner en 15 y en 18 ya no esta, asi que la
carga muere con "action_open_reconcile no es una accion valida en
res.partner" -- y lo hace al validar la vista de cualquier otro modulo que
herede el formulario del contacto, que es lo que despista al leer el error.

Se borra en pre-migrate para que desaparezca antes de que se cargue ningun
otro modulo. Odoo limpiaria estos huerfanos por su cuenta al terminar de
procesar account_ux, pero para entonces ya se ha caido.
"""
import logging

_logger = logging.getLogger(__name__)

ORPHAN_PARTNER_VIEWS = (
    # El boton "Match Payments" con action_open_reconcile.
    'res_partner_view_buttons',
    # Mostraba last_time_entries_checked, campo que tampoco existe ya.
    'view_partner_form',
    # Heredaba base.view_res_partner_filter.
    'view_res_partner_filter',
)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        SELECT data.id, data.name, data.res_id
          FROM ir_model_data data
         WHERE data.module = 'account_ux'
           AND data.model = 'ir.ui.view'
           AND data.name IN %s
        """,
        (ORPHAN_PARTNER_VIEWS,),
    )
    rows = cr.fetchall()
    if not rows:
        _logger.info(
            "account_ux: no quedan vistas huerfanas de res.partner.")
        return

    view_ids = tuple(row[2] for row in rows)
    data_ids = tuple(row[0] for row in rows)

    # Primero las vistas: al borrarlas caen en cascada las que hereden de
    # ellas, si alguien encadeno algo por encima.
    cr.execute("DELETE FROM ir_ui_view WHERE id IN %s", (view_ids,))
    deleted = cr.rowcount
    cr.execute("DELETE FROM ir_model_data WHERE id IN %s", (data_ids,))

    _logger.info(
        "account_ux: %s vista(s) huerfana(s) de res.partner eliminadas: %s.",
        deleted, ', '.join(sorted(row[1] for row in rows)),
    )
