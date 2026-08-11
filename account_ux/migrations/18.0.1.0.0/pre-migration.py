from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """
    The objective of this is delete the original view form the module how bring the functionality
    adding in the previous commit
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    # This inherited view was removed from the module in 16.0, but upgrades
    # keep the database record. It still targets the old currency_rate field
    # and prevents the new Odoo 18 base view from being validated.
    obsolete_view = env.ref(
        "account_ux.view_account_change_no_exchange_currency",
        raise_if_not_found=False,
    )
    if obsolete_view:
        obsolete_view.unlink()

    view = env.ref("account_ux.view_account_form", raise_if_not_found=False)
    if view:
        view.unlink()
